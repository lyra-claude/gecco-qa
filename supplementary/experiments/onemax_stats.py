#!/usr/bin/env python3
"""
Multi-seed statistical experiments for OneMax island model GA.

Reproduces Experiments C (migration frequency sweep) and D (boundary position
sweep) from the GECCO 2026 paper "Composition Determines Behavior".

The GA implementation matches the Haskell source in
  src/Evolution/{Effects,Operators,Island,Examples/BitString}.hs

Usage:
    python onemax_stats.py              # Run both experiments
    python onemax_stats.py --exp C      # Experiment C only
    python onemax_stats.py --exp D      # Experiment D only
    python onemax_stats.py --seeds 10   # Use 10 seeds instead of 30
    python onemax_stats.py --seed0 42   # Single seed for validation
"""

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable

import numpy as np
from scipy import stats


# ---------------------------------------------------------------------------
# GA Configuration
# ---------------------------------------------------------------------------

@dataclass
class GAConfig:
    population_size: int = 80
    genome_length: int = 20
    num_islands: int = 4
    tournament_size: int = 3
    crossover_rate: float = 0.8
    mutation_rate: float = 0.05  # 1/L where L=20
    max_generations: int = 40
    migration_freq: int = 5
    migration_rate: float = 0.05  # fraction of pop to migrate (gives 1 migrant per island of 20)
    topology: str = "ring"  # "ring", "star", "fully_connected", "random", "none"


# ---------------------------------------------------------------------------
# Core GA operators (matching Haskell implementation)
# ---------------------------------------------------------------------------

def onemax_fitness(individual: np.ndarray) -> float:
    """OneMax: count the number of 1-bits."""
    return float(np.sum(individual))


def random_population(rng: np.random.Generator, pop_size: int, genome_length: int) -> np.ndarray:
    """Generate random binary population. Shape: (pop_size, genome_length)."""
    return rng.integers(0, 2, size=(pop_size, genome_length), dtype=np.int8)


def evaluate(pop: np.ndarray) -> np.ndarray:
    """Evaluate OneMax fitness for entire population. Returns 1D array of fitnesses."""
    return pop.sum(axis=1).astype(float)


def tournament_select(rng: np.random.Generator, pop: np.ndarray, fitnesses: np.ndarray,
                      tournament_size: int) -> np.ndarray:
    """Tournament selection. Matches Haskell: pick k random, keep best, repeat n times.

    The Haskell code (tournamentSelect) does:
        replicateM n (tournament k pop)
    where tournament picks k random individuals and returns the one with highest fitness.
    Selection is WITH replacement (randomChoice from the full pop each time).
    """
    n = len(pop)
    selected_indices = np.empty(n, dtype=int)
    for i in range(n):
        # Pick k random contestants (with replacement, matching Haskell's replicateM k (randomChoice pop))
        contestants = rng.integers(0, n, size=tournament_size)
        # Keep the one with highest fitness
        best_idx = contestants[np.argmax(fitnesses[contestants])]
        selected_indices[i] = best_idx
    return pop[selected_indices].copy()


def one_point_crossover(rng: np.random.Generator, pop: np.ndarray,
                        crossover_rate: float) -> np.ndarray:
    """One-point crossover on pairs. Matches Haskell onePointCrossover.

    The Haskell code pairs up individuals sequentially (p1:p2:rest),
    generates a random double, and if < rate, picks a random crossover point
    in [1, len-1] and swaps tails.
    """
    result = pop.copy()
    n = len(pop)
    genome_len = pop.shape[1]

    i = 0
    while i + 1 < n:
        r = rng.random()
        if r < crossover_rate:
            # Random crossover point in [1, genome_len-1]
            # Haskell: randomInt 1 (max 1 (len - 1))
            point = rng.integers(1, genome_len)  # [1, genome_len) i.e. 1..genome_len-1
            # Swap tails
            result[i, point:], result[i+1, point:] = (
                pop[i+1, point:].copy(), pop[i, point:].copy()
            )
        i += 2
    return result


def point_mutate(rng: np.random.Generator, pop: np.ndarray,
                 mutation_rate: float) -> np.ndarray:
    """Per-gene bit-flip mutation. Matches Haskell pointMutate bitFlip.

    The Haskell code iterates each gene in each individual:
    for each gene, draw random double; if < mutation_rate, flip the bit.
    """
    result = pop.copy()
    # Generate mutation mask
    mask = rng.random(size=pop.shape) < mutation_rate
    # Flip bits where mask is True
    result[mask] = 1 - result[mask]
    return result


# ---------------------------------------------------------------------------
# Island model (matching Haskell Evolution.Island)
# ---------------------------------------------------------------------------

def split_population(pop: np.ndarray, num_islands: int) -> List[np.ndarray]:
    """Split population into islands. Matches Haskell makeIslands."""
    island_size = len(pop) // num_islands
    islands = []
    for i in range(num_islands):
        start = i * island_size
        end = start + island_size
        islands.append(pop[start:end].copy())
    return islands


def merge_populations(islands: List[np.ndarray]) -> np.ndarray:
    """Merge island populations back into one."""
    return np.vstack(islands)


def ring_migrate(rng: np.random.Generator, islands: List[np.ndarray],
                 migration_rate: float) -> List[np.ndarray]:
    """Ring migration. Matches Haskell ringMigrate.

    The Haskell code:
    1. For each island, compute migrant_count = max 1 (round(rate * pop_size))
    2. Shuffle each island's population, take first migrant_count as migrants
    3. Island i sends migrants to island (i+1) mod n
    4. Receiving island: migrants replace the LAST individuals
       (migrantsIn ++ trimmed where trimmed = take (len - len_migrants) pop)
       So migrants go to the FRONT and the last individuals are dropped.

    Wait, re-reading the Haskell more carefully:
        let updatedIslands = zipWith (\\isl migrantsIn ->
                let pop = islandPop isl
                    trimmed = take (length pop - length migrantsIn) pop
                in isl { islandPop = migrantsIn ++ trimmed }
              ) islands (last migrants : init migrants)

    So island 0 receives from island (n-1) (last migrants),
    island 1 receives from island 0, etc.
    That means island i receives migrants from island (i-1) mod n.
    And island i sends its migrants to island (i+1) mod n.

    The receiving island puts migrants at the FRONT and keeps the first
    (pop_size - num_migrants) of its original population. This means the
    LAST individuals in the original ordering are dropped.
    """
    n = len(islands)
    if n <= 1:
        return [isl.copy() for isl in islands]

    # Compute migrants for each island
    migrants_list = []
    for isl in islands:
        pop_size = len(isl)
        num_migrants = max(1, round(migration_rate * pop_size))
        # Shuffle and take first num_migrants
        indices = rng.permutation(pop_size)
        migrants_list.append(isl[indices[:num_migrants]].copy())

    # Apply migration: island i receives migrants from island (i-1) mod n
    # In Haskell: (last migrants : init migrants) means
    #   island 0 gets migrants from island n-1 (last)
    #   island 1 gets migrants from island 0 (first of init)
    #   ...
    result = []
    for i in range(n):
        source_idx = (i - 1) % n  # island i receives from island i-1
        incoming = migrants_list[source_idx]
        pop = islands[i]
        # trimmed = take (pop_size - num_incoming) pop
        trimmed = pop[:len(pop) - len(incoming)]
        # new pop = incoming ++ trimmed
        new_pop = np.vstack([incoming, trimmed])
        result.append(new_pop)

    return result


def star_migrate(rng: np.random.Generator, islands: List[np.ndarray],
                 migration_rate: float) -> List[np.ndarray]:
    """Star migration. Island 0 is the hub; spokes exchange only with hub.

    For each spoke island, select num_migrants random individuals from both
    hub and spoke, then swap them. Spokes never exchange directly.
    """
    n = len(islands)
    if n <= 1:
        return [isl.copy() for isl in islands]

    result = [isl.copy() for isl in islands]
    hub = 0

    for spoke in range(1, n):
        pop_size = len(result[hub])
        num_migrants = max(1, round(migration_rate * pop_size))

        # Select random individuals from hub and spoke
        hub_indices = rng.choice(pop_size, size=num_migrants, replace=False)
        spoke_pop_size = len(result[spoke])
        spoke_indices = rng.choice(spoke_pop_size, size=num_migrants, replace=False)

        # Swap them
        hub_migrants = result[hub][hub_indices].copy()
        spoke_migrants = result[spoke][spoke_indices].copy()
        result[hub][hub_indices] = spoke_migrants
        result[spoke][spoke_indices] = hub_migrants

    return result


def fully_connected_migrate(rng: np.random.Generator, islands: List[np.ndarray],
                            migration_rate: float) -> List[np.ndarray]:
    """Fully connected migration. Every island exchanges with every other.

    For each pair (i, j), exchange num_migrants individuals.
    This is the "laxest" topology -- maximum inter-island coupling.
    """
    n = len(islands)
    if n <= 1:
        return [isl.copy() for isl in islands]

    result = [isl.copy() for isl in islands]

    for i in range(n):
        for j in range(i + 1, n):
            pop_size_i = len(result[i])
            pop_size_j = len(result[j])
            num_migrants = max(1, round(migration_rate * min(pop_size_i, pop_size_j)))

            # Select random individuals from each island
            idx_i = rng.choice(pop_size_i, size=num_migrants, replace=False)
            idx_j = rng.choice(pop_size_j, size=num_migrants, replace=False)

            # Swap
            migrants_i = result[i][idx_i].copy()
            migrants_j = result[j][idx_j].copy()
            result[i][idx_i] = migrants_j
            result[j][idx_j] = migrants_i

    return result


def random_migrate(rng: np.random.Generator, islands: List[np.ndarray],
                   migration_rate: float) -> List[np.ndarray]:
    """Random migration. Randomly pick n edges (same count as ring) and exchange.

    Each migration event, randomly select n pairs of islands (with replacement
    on edges, not self-loops), exchange num_migrants between each pair.
    Number of random edges = n (same as ring) to control for migration volume.
    """
    n = len(islands)
    if n <= 1:
        return [isl.copy() for isl in islands]

    result = [isl.copy() for isl in islands]

    # Generate n random edges (same count as ring topology)
    for _ in range(n):
        # Pick two distinct islands
        i = rng.integers(0, n)
        j = rng.integers(0, n - 1)
        if j >= i:
            j += 1  # avoid self-loop

        pop_size_i = len(result[i])
        pop_size_j = len(result[j])
        num_migrants = max(1, round(migration_rate * min(pop_size_i, pop_size_j)))

        idx_i = rng.choice(pop_size_i, size=num_migrants, replace=False)
        idx_j = rng.choice(pop_size_j, size=num_migrants, replace=False)

        migrants_i = result[i][idx_i].copy()
        migrants_j = result[j][idx_j].copy()
        result[i][idx_i] = migrants_j
        result[j][idx_j] = migrants_i

    return result


def no_migrate(rng: np.random.Generator, islands: List[np.ndarray],
               migration_rate: float) -> List[np.ndarray]:
    """No migration. Strict composition -- zero coupling between islands."""
    return [isl.copy() for isl in islands]


def migrate(rng: np.random.Generator, islands: List[np.ndarray],
            config: GAConfig) -> List[np.ndarray]:
    """Dispatch to the appropriate migration function based on config.topology."""
    _dispatch = {
        "ring": ring_migrate,
        "star": star_migrate,
        "fully_connected": fully_connected_migrate,
        "random": random_migrate,
        "none": no_migrate,
    }
    fn = _dispatch.get(config.topology)
    if fn is None:
        raise ValueError(f"Unknown topology: {config.topology!r}. "
                         f"Valid: {list(_dispatch.keys())}")
    return fn(rng, islands, config.migration_rate)


def evolve_islands(rng: np.random.Generator, islands: List[np.ndarray],
                   config: GAConfig, start_gen: int = 0,
                   end_gen: Optional[int] = None) -> Tuple[List[np.ndarray], dict]:
    """Run island model evolution. Matches Haskell evolveIslands.

    The Haskell code:
        go gen maxG isls
          | gen >= maxG = return isls
          | otherwise = do
              isls' <- mapM (evolve one gen) isls
              isls'' <- if gen > 0 && gen `mod` migrationFreq == 0
                        then migrate model isls'
                        else return isls'
              go (gen + 1) maxG isls''

    Returns (final_islands, stats_dict).
    """
    if end_gen is None:
        end_gen = config.max_generations

    stats = {
        'best_fitness': [],
        'mean_fitness': [],
        'hamming_div': [],
    }

    for gen in range(start_gen, end_gen):
        # Evolve each island for one generation
        new_islands = []
        for isl in islands:
            # Pipeline: evaluate -> tournament_select -> one_point_crossover -> point_mutate
            fitnesses = evaluate(isl)
            selected = tournament_select(rng, isl, fitnesses, config.tournament_size)
            crossed = one_point_crossover(rng, selected, config.crossover_rate)
            mutated = point_mutate(rng, crossed, config.mutation_rate)
            new_islands.append(mutated)

        islands = new_islands

        # Migrate if it's time
        # Haskell: gen > 0 && gen `mod` migrationFreq == 0
        if gen > 0 and gen % config.migration_freq == 0:
            islands = migrate(rng, islands, config)

        # Log stats
        all_pop = merge_populations(islands)
        all_fit = evaluate(all_pop)
        stats['best_fitness'].append(float(np.max(all_fit)))
        stats['mean_fitness'].append(float(np.mean(all_fit)))
        stats['hamming_div'].append(hamming_diversity(all_pop))

    return islands, stats


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def hamming_diversity(pop: np.ndarray) -> float:
    """Mean pairwise Hamming distance, normalized to [0, 1].

    For binary genomes, this is the average fraction of positions that differ
    between all pairs of individuals.
    """
    n = len(pop)
    if n < 2:
        return 0.0
    genome_len = pop.shape[1]

    # Efficient computation: for each bit position, count the number of 1s
    # Then pairwise Hamming = sum over positions of (k * (n - k)) * 2 / (n * (n-1))
    # where k = number of 1s at that position
    ones_per_position = pop.sum(axis=0)  # shape: (genome_len,)
    # Number of disagreeing pairs at each position
    disagreeing = ones_per_position * (n - ones_per_position)
    # Total pairs
    total_pairs = n * (n - 1) / 2
    # Mean Hamming distance normalized by genome length
    mean_hamming = np.sum(disagreeing) / total_pairs / genome_len
    return float(mean_hamming)


def population_divergence(pop1: np.ndarray, pop2: np.ndarray) -> float:
    """Normalized distance between two populations.

    Compares the allele frequencies at each locus. Returns a value in [0, 1]
    where 0 = identical allele distributions, 1 = maximally different.

    Uses L1 distance on allele frequencies, normalized by genome length.
    """
    if len(pop1) == 0 or len(pop2) == 0:
        return 1.0
    freq1 = pop1.mean(axis=0)  # allele frequency per locus
    freq2 = pop2.mean(axis=0)
    # L1 distance normalized by genome length
    return float(np.mean(np.abs(freq1 - freq2)))


def island_population_divergence(islands1: List[np.ndarray],
                                  islands2: List[np.ndarray]) -> float:
    """Compare two sets of islands (continuous vs composed).

    Returns the mean per-island population divergence.
    """
    divs = []
    for isl1, isl2 in zip(islands1, islands2):
        divs.append(population_divergence(isl1, isl2))
    return float(np.mean(divs))


def fitness_difference(islands1: List[np.ndarray], islands2: List[np.ndarray]) -> float:
    """Absolute difference in best fitness between two sets of islands."""
    fit1 = max(float(np.max(evaluate(isl))) for isl in islands1)
    fit2 = max(float(np.max(evaluate(isl))) for isl in islands2)
    return abs(fit1 - fit2)


# ---------------------------------------------------------------------------
# Experiment C: Migration Frequency Sweep
# ---------------------------------------------------------------------------

def run_experiment_c_single(seed: int, config: GAConfig,
                            freq: int) -> dict:
    """Run a single seed of Experiment C for one migration frequency.

    The dichotomy test: compare continuous 40-gen run I(S1;S2) vs
    composed run I(S1);I(S2) where S1 = first 20 gens, S2 = second 20 gens.
    The boundary resets the migration counter.
    """
    cfg = GAConfig(
        population_size=config.population_size,
        genome_length=config.genome_length,
        num_islands=config.num_islands,
        tournament_size=config.tournament_size,
        crossover_rate=config.crossover_rate,
        mutation_rate=config.mutation_rate,
        max_generations=config.max_generations,
        migration_freq=freq,
        migration_rate=config.migration_rate,
    )
    boundary = 20  # Split at gen 20

    # --- Continuous run: I(S1 ; S2) ---
    rng_cont = np.random.default_rng(seed)
    init_pop = random_population(rng_cont, cfg.population_size, cfg.genome_length)
    islands_cont = split_population(init_pop, cfg.num_islands)
    final_cont, stats_cont = evolve_islands(rng_cont, islands_cont, cfg,
                                             start_gen=0, end_gen=cfg.max_generations)

    # --- Composed run: I(S1) ; I(S2) ---
    # Same initial population and RNG state
    rng_comp = np.random.default_rng(seed)
    init_pop2 = random_population(rng_comp, cfg.population_size, cfg.genome_length)
    islands_comp = split_population(init_pop2, cfg.num_islands)

    # Phase 1: generations 0..boundary-1
    islands_phase1, _ = evolve_islands(rng_comp, islands_comp, cfg,
                                        start_gen=0, end_gen=boundary)

    # Phase 2: generations boundary..max_gen-1
    # KEY: migration counter resets at the boundary. In the Haskell code,
    # the generation counter used for migration check is the actual gen number.
    # When we compose, the second phase starts at gen=boundary but the migration
    # schedule resets because in a "composed" run, we restart the go loop
    # from gen=0 for the second phase (conceptually). But actually, the paper says
    # "resetting the migration schedule at the boundary".
    #
    # To match: run phase 2 with gen starting from 0 (so migration check uses
    # gen % freq == 0 with gen starting from 0, not from boundary).
    islands_phase2, _ = evolve_islands(rng_comp, islands_phase1, cfg,
                                        start_gen=0, end_gen=cfg.max_generations - boundary)

    # Compute metrics
    pop_div = island_population_divergence(final_cont, islands_phase2)
    ham_div_cont = hamming_diversity(merge_populations(final_cont))
    ham_div_comp = hamming_diversity(merge_populations(islands_phase2))
    ham_div_diff = abs(ham_div_cont - ham_div_comp)
    fit_diff = fitness_difference(final_cont, islands_phase2)

    # Schedule difference: number of migration events displaced
    # In continuous: migrations at gen g where g > 0 and g % freq == 0, for g in [0, max_gen)
    cont_events = set(g for g in range(cfg.max_generations) if g > 0 and g % freq == 0)
    # In composed: phase1 events at g > 0 and g % freq == 0 for g in [0, boundary)
    # phase2 events at g > 0 and g % freq == 0 for g in [0, max_gen - boundary)
    # mapped to absolute: boundary + g
    comp_events_p1 = set(g for g in range(boundary) if g > 0 and g % freq == 0)
    comp_events_p2 = set(boundary + g for g in range(cfg.max_generations - boundary)
                         if g > 0 and g % freq == 0)
    comp_events = comp_events_p1 | comp_events_p2
    sched_diff = len(cont_events.symmetric_difference(comp_events))

    return {
        'seed': seed,
        'freq': freq,
        'sched_diff': sched_diff,
        'pop_divergence': pop_div,
        'hamming_div_diff': ham_div_diff,
        'fitness_diff': fit_diff,
        'hamming_div_cont': ham_div_cont,
        'hamming_div_comp': ham_div_comp,
    }


def run_experiment_c(seeds: List[int], config: GAConfig,
                     frequencies: List[int] = None) -> List[dict]:
    """Run Experiment C: migration frequency sweep."""
    if frequencies is None:
        frequencies = [2, 5, 10, 20, 40]

    results = []
    total = len(frequencies) * len(seeds)
    done = 0

    for freq in frequencies:
        for seed in seeds:
            result = run_experiment_c_single(seed, config, freq)
            results.append(result)
            done += 1
            if done % 10 == 0 or done == total:
                print(f"  Experiment C: {done}/{total} runs complete", flush=True)

    return results


# ---------------------------------------------------------------------------
# Experiment D: Boundary Position Sweep
# ---------------------------------------------------------------------------

def run_experiment_d_single(seed: int, config: GAConfig,
                            boundary: int) -> dict:
    """Run a single seed of Experiment D for one boundary position.

    Same as C but with fixed migration freq=5, varying boundary position.
    """
    cfg = GAConfig(
        population_size=config.population_size,
        genome_length=config.genome_length,
        num_islands=config.num_islands,
        tournament_size=config.tournament_size,
        crossover_rate=config.crossover_rate,
        mutation_rate=config.mutation_rate,
        max_generations=config.max_generations,
        migration_freq=5,  # fixed
        migration_rate=config.migration_rate,
    )

    # --- Continuous run ---
    rng_cont = np.random.default_rng(seed)
    init_pop = random_population(rng_cont, cfg.population_size, cfg.genome_length)
    islands_cont = split_population(init_pop, cfg.num_islands)
    final_cont, _ = evolve_islands(rng_cont, islands_cont, cfg,
                                    start_gen=0, end_gen=cfg.max_generations)

    # --- Composed run ---
    rng_comp = np.random.default_rng(seed)
    init_pop2 = random_population(rng_comp, cfg.population_size, cfg.genome_length)
    islands_comp = split_population(init_pop2, cfg.num_islands)

    # Phase 1: generations 0..boundary-1
    islands_phase1, _ = evolve_islands(rng_comp, islands_comp, cfg,
                                        start_gen=0, end_gen=boundary)

    # Phase 2: generations 0..(max_gen - boundary - 1), migration counter reset
    islands_phase2, _ = evolve_islands(rng_comp, islands_phase1, cfg,
                                        start_gen=0, end_gen=cfg.max_generations - boundary)

    # Compute metrics
    pop_div = island_population_divergence(final_cont, islands_phase2)
    ham_div_cont = hamming_diversity(merge_populations(final_cont))
    ham_div_comp = hamming_diversity(merge_populations(islands_phase2))
    ham_div_diff = abs(ham_div_cont - ham_div_comp)

    # Does boundary hit a migration event?
    hits_migration = (boundary > 0 and boundary % 5 == 0)

    return {
        'seed': seed,
        'boundary': boundary,
        'hits_migration': hits_migration,
        'pop_divergence': pop_div,
        'hamming_div_diff': ham_div_diff,
        'hamming_div_cont': ham_div_cont,
        'hamming_div_comp': ham_div_comp,
    }


def run_experiment_d(seeds: List[int], config: GAConfig,
                     boundaries: List[int] = None) -> List[dict]:
    """Run Experiment D: boundary position sweep."""
    if boundaries is None:
        boundaries = [15, 17, 20, 23, 25]

    results = []
    total = len(boundaries) * len(seeds)
    done = 0

    for boundary in boundaries:
        for seed in seeds:
            result = run_experiment_d_single(seed, config, boundary)
            results.append(result)
            done += 1
            if done % 10 == 0 or done == total:
                print(f"  Experiment D: {done}/{total} runs complete", flush=True)

    return results


# ---------------------------------------------------------------------------
# Statistical Analysis
# ---------------------------------------------------------------------------

def vargha_delaney_a(group1: np.ndarray, group2: np.ndarray) -> float:
    """Vargha-Delaney A effect size measure.

    A = P(X > Y) + 0.5 * P(X == Y)
    where X ~ group1, Y ~ group2.

    A = 0.5 means no effect. A > 0.5 means group1 tends to be larger.
    """
    m, n = len(group1), len(group2)
    if m == 0 or n == 0:
        return 0.5

    # Use Mann-Whitney U statistic: A = U / (m * n)
    # where U = number of (x, y) pairs where x > y + 0.5 * (x == y)
    count = 0.0
    for x in group1:
        for y in group2:
            if x > y:
                count += 1.0
            elif x == y:
                count += 0.5
    return count / (m * n)


def analyze_experiment_c(results: List[dict]) -> dict:
    """Compute summary statistics and tests for Experiment C."""
    frequencies = sorted(set(r['freq'] for r in results))

    summary = {}
    for freq in frequencies:
        freq_results = [r for r in results if r['freq'] == freq]
        pop_divs = np.array([r['pop_divergence'] for r in freq_results])
        ham_divs = np.array([r['hamming_div_diff'] for r in freq_results])
        fit_diffs = np.array([r['fitness_diff'] for r in freq_results])
        sched_diffs = [r['sched_diff'] for r in freq_results]

        summary[freq] = {
            'sched_diff': sched_diffs[0],  # same for all seeds
            'pop_div_mean': float(np.mean(pop_divs)),
            'pop_div_std': float(np.std(pop_divs, ddof=1)) if len(pop_divs) > 1 else 0.0,
            'pop_div_median': float(np.median(pop_divs)),
            'pop_div_iqr': float(np.percentile(pop_divs, 75) - np.percentile(pop_divs, 25)),
            'ham_div_mean': float(np.mean(ham_divs)),
            'ham_div_std': float(np.std(ham_divs, ddof=1)) if len(ham_divs) > 1 else 0.0,
            'ham_div_median': float(np.median(ham_divs)),
            'fit_diff_mean': float(np.mean(fit_diffs)),
            'n': len(freq_results),
        }

    # Kruskal-Wallis test across non-40 frequencies on pop_divergence
    nonzero_groups = [
        np.array([r['pop_divergence'] for r in results if r['freq'] == f])
        for f in frequencies if f != 40
    ]
    if len(nonzero_groups) >= 2 and all(len(g) >= 2 for g in nonzero_groups):
        kw_stat, kw_p = stats.kruskal(*nonzero_groups)
    else:
        kw_stat, kw_p = float('nan'), float('nan')

    # Pairwise Mann-Whitney U and Vargha-Delaney between each freq pair
    pairwise = {}
    for i, f1 in enumerate(frequencies):
        for f2 in frequencies[i+1:]:
            g1 = np.array([r['pop_divergence'] for r in results if r['freq'] == f1])
            g2 = np.array([r['pop_divergence'] for r in results if r['freq'] == f2])
            if len(g1) >= 2 and len(g2) >= 2:
                u_stat, u_p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
                a_effect = vargha_delaney_a(g1, g2)
            else:
                u_stat, u_p, a_effect = float('nan'), float('nan'), 0.5
            pairwise[(f1, f2)] = {
                'U': float(u_stat), 'p': float(u_p), 'A': float(a_effect)
            }

    return {
        'summary': summary,
        'kruskal_wallis': {'H': float(kw_stat), 'p': float(kw_p)},
        'pairwise': pairwise,
    }


def analyze_experiment_d(results: List[dict]) -> dict:
    """Compute summary statistics and tests for Experiment D."""
    boundaries = sorted(set(r['boundary'] for r in results))

    summary = {}
    for boundary in boundaries:
        b_results = [r for r in results if r['boundary'] == boundary]
        pop_divs = np.array([r['pop_divergence'] for r in b_results])
        ham_divs = np.array([r['hamming_div_diff'] for r in b_results])
        hits = b_results[0]['hits_migration']

        summary[boundary] = {
            'hits_migration': hits,
            'pop_div_mean': float(np.mean(pop_divs)),
            'pop_div_std': float(np.std(pop_divs, ddof=1)) if len(pop_divs) > 1 else 0.0,
            'pop_div_median': float(np.median(pop_divs)),
            'pop_div_iqr': float(np.percentile(pop_divs, 75) - np.percentile(pop_divs, 25)),
            'ham_div_mean': float(np.mean(ham_divs)),
            'ham_div_std': float(np.std(ham_divs, ddof=1)) if len(ham_divs) > 1 else 0.0,
            'ham_div_median': float(np.median(ham_divs)),
            'n': len(b_results),
        }

    # Kruskal-Wallis across all boundaries
    groups = [
        np.array([r['pop_divergence'] for r in results if r['boundary'] == b])
        for b in boundaries
    ]
    if len(groups) >= 2 and all(len(g) >= 2 for g in groups):
        kw_stat, kw_p = stats.kruskal(*groups)
    else:
        kw_stat, kw_p = float('nan'), float('nan')

    # Pairwise Mann-Whitney U
    pairwise = {}
    for i, b1 in enumerate(boundaries):
        for b2 in boundaries[i+1:]:
            g1 = np.array([r['pop_divergence'] for r in results if r['boundary'] == b1])
            g2 = np.array([r['pop_divergence'] for r in results if r['boundary'] == b2])
            if len(g1) >= 2 and len(g2) >= 2:
                u_stat, u_p = stats.mannwhitneyu(g1, g2, alternative='two-sided')
                a_effect = vargha_delaney_a(g1, g2)
            else:
                u_stat, u_p, a_effect = float('nan'), float('nan'), 0.5
            pairwise[(b1, b2)] = {
                'U': float(u_stat), 'p': float(u_p), 'A': float(a_effect)
            }

    return {
        'summary': summary,
        'kruskal_wallis': {'H': float(kw_stat), 'p': float(kw_p)},
        'pairwise': pairwise,
    }


# ---------------------------------------------------------------------------
# Experiment E: Topology Sweep
# ---------------------------------------------------------------------------

def run_experiment_e_single(seed: int, config: GAConfig,
                            topology: str,
                            evaluate_fn: Callable = None,
                            init_fn: Callable = None,
                            crossover_fn: Callable = None,
                            mutate_fn: Callable = None,
                            diversity_fn: Callable = None,
                            divergence_fn: Callable = None) -> List[dict]:
    """Run a single seed of Experiment E for one topology.

    Tracks per-generation metrics: hamming diversity, population divergence
    (mean pairwise inter-island), and best fitness.

    Args:
        evaluate_fn: Function (pop: np.ndarray) -> np.ndarray of fitnesses.
                     Defaults to OneMax evaluate().
        init_fn:     Function (rng, pop_size, genome_length) -> np.ndarray.
                     Defaults to random_population().
        crossover_fn: Function (rng, pop, rate) -> np.ndarray.
                      Defaults to one_point_crossover (binary).
        mutate_fn:    Function (rng, pop, rate) -> np.ndarray.
                      Defaults to point_mutate (bit-flip).
        diversity_fn: Function (pop) -> float.
                      Defaults to hamming_diversity (binary).
        divergence_fn: Function (pop1, pop2) -> float.
                       Defaults to population_divergence (binary).

    Returns a list of dicts, one per generation.
    """
    if evaluate_fn is None:
        evaluate_fn = evaluate
    if init_fn is None:
        init_fn = random_population
    if crossover_fn is None:
        crossover_fn = one_point_crossover
    if mutate_fn is None:
        mutate_fn = point_mutate
    if diversity_fn is None:
        diversity_fn = hamming_diversity
    if divergence_fn is None:
        divergence_fn = population_divergence

    cfg = GAConfig(
        population_size=config.population_size,
        genome_length=config.genome_length,
        num_islands=config.num_islands,
        tournament_size=config.tournament_size,
        crossover_rate=config.crossover_rate,
        mutation_rate=config.mutation_rate,
        max_generations=config.max_generations,
        migration_freq=config.migration_freq,
        migration_rate=config.migration_rate,
        topology=topology,
    )

    rng = np.random.default_rng(seed)
    init_pop = init_fn(rng, cfg.population_size, cfg.genome_length)
    islands = split_population(init_pop, cfg.num_islands)

    rows = []
    for gen in range(cfg.max_generations):
        # Evolve each island for one generation
        new_islands = []
        for isl in islands:
            fitnesses = evaluate_fn(isl)
            selected = tournament_select(rng, isl, fitnesses, cfg.tournament_size)
            crossed = crossover_fn(rng, selected, cfg.crossover_rate)
            mutated = mutate_fn(rng, crossed, cfg.mutation_rate)
            new_islands.append(mutated)

        islands = new_islands

        # Migrate if it's time
        if gen > 0 and gen % cfg.migration_freq == 0:
            islands = migrate(rng, islands, cfg)

        # Compute metrics
        all_pop = merge_populations(islands)
        all_fit = evaluate_fn(all_pop)
        ham_div = diversity_fn(all_pop)
        best_fit = float(np.max(all_fit))

        # Inter-island divergence: mean pairwise divergence across all island pairs
        n_isl = len(islands)
        if n_isl > 1:
            divs = []
            for i in range(n_isl):
                for j in range(i + 1, n_isl):
                    divs.append(divergence_fn(islands[i], islands[j]))
            pop_div = float(np.mean(divs))
        else:
            pop_div = 0.0
            divs = []

        # Per-island diversity
        island_diversities = [diversity_fn(isl) for isl in islands]

        # Per-island best fitness
        island_fitnesses = [float(np.max(evaluate_fn(isl))) for isl in islands]

        # Build row with base metrics
        row = {
            'topology': topology,
            'seed': seed,
            'generation': gen,
            'hamming_diversity': ham_div,
            'population_divergence': pop_div,
            'best_fitness': best_fit,
        }

        # Per-island diversity and fitness columns
        for k in range(n_isl):
            row[f'island_{k}_diversity'] = island_diversities[k]
            row[f'island_{k}_fitness'] = island_fitnesses[k]

        # Full pairwise divergence matrix (upper triangle)
        div_idx = 0
        for i in range(n_isl):
            for j in range(i + 1, n_isl):
                row[f'div_{i}_{j}'] = divs[div_idx] if divs else 0.0
                div_idx += 1

        rows.append(row)

    return rows


def run_experiment_e(seeds: List[int], config: GAConfig,
                     topologies: List[str] = None,
                     evaluate_fn: Callable = None,
                     init_fn: Callable = None,
                     crossover_fn: Callable = None,
                     mutate_fn: Callable = None,
                     diversity_fn: Callable = None,
                     divergence_fn: Callable = None,
                     incremental_csv: str = None,
                     resume: bool = False) -> List[dict]:
    """Run Experiment E: topology sweep.

    Args:
        incremental_csv: If provided, append results to this CSV after each run.
        resume: If True and incremental_csv exists, skip already-completed
                (topology, seed) pairs.
        crossover_fn: Custom crossover operator (default: one_point_crossover).
        mutate_fn: Custom mutation operator (default: point_mutate).
        diversity_fn: Custom diversity metric (default: hamming_diversity).
        divergence_fn: Custom divergence metric (default: population_divergence).
    """
    if topologies is None:
        topologies = ["none", "ring", "star", "fully_connected", "random"]

    # Determine which (topology, seed) pairs to skip
    completed = set()
    file_exists = False
    if incremental_csv:
        file_exists = os.path.exists(incremental_csv)
        if resume and file_exists:
            completed = load_completed_pairs(incremental_csv)
            print(f"  Resume: found {len(completed)} completed (topology, seed) pairs",
                  flush=True)

    results = []
    total = len(topologies) * len(seeds)
    skipped = 0
    done = 0

    for topology in topologies:
        for seed in seeds:
            done += 1
            if (topology, seed) in completed:
                skipped += 1
                continue

            rows = run_experiment_e_single(seed, config, topology,
                                           evaluate_fn=evaluate_fn,
                                           init_fn=init_fn,
                                           crossover_fn=crossover_fn,
                                           mutate_fn=mutate_fn,
                                           diversity_fn=diversity_fn,
                                           divergence_fn=divergence_fn)
            results.extend(rows)

            # Incremental save: append this run's rows immediately
            if incremental_csv and rows:
                need_header = not file_exists
                append_csv(rows, incremental_csv, write_header=need_header)
                file_exists = True  # header written, don't write again

            if (done - skipped) % 10 == 0 or done == total:
                print(f"  Experiment E: {done - skipped}/{total - skipped} runs complete"
                      f" (skipped {skipped})" if skipped else
                      f"  Experiment E: {done}/{total} runs complete",
                      flush=True)

    return results


def analyze_experiment_e(results: List[dict], max_gen: int) -> dict:
    """Compute summary statistics for Experiment E.

    For each topology: mean final diversity, divergence, fitness (with std).
    """
    topologies = sorted(set(r['topology'] for r in results))
    last_gen = max_gen - 1

    summary = {}
    for topo in topologies:
        final_rows = [r for r in results
                      if r['topology'] == topo and r['generation'] == last_gen]
        divs = np.array([r['hamming_diversity'] for r in final_rows])
        pop_divs = np.array([r['population_divergence'] for r in final_rows])
        fits = np.array([r['best_fitness'] for r in final_rows])

        summary[topo] = {
            'n': len(final_rows),
            'diversity_mean': float(np.mean(divs)),
            'diversity_std': float(np.std(divs, ddof=1)) if len(divs) > 1 else 0.0,
            'divergence_mean': float(np.mean(pop_divs)),
            'divergence_std': float(np.std(pop_divs, ddof=1)) if len(pop_divs) > 1 else 0.0,
            'fitness_mean': float(np.mean(fits)),
            'fitness_std': float(np.std(fits, ddof=1)) if len(fits) > 1 else 0.0,
        }

    # Kruskal-Wallis across all topologies on final diversity
    groups_div = [
        np.array([r['hamming_diversity'] for r in results
                  if r['topology'] == t and r['generation'] == last_gen])
        for t in topologies
    ]
    if len(groups_div) >= 2 and all(len(g) >= 2 for g in groups_div):
        kw_div_stat, kw_div_p = stats.kruskal(*groups_div)
    else:
        kw_div_stat, kw_div_p = float('nan'), float('nan')

    # Kruskal-Wallis on final divergence
    groups_divg = [
        np.array([r['population_divergence'] for r in results
                  if r['topology'] == t and r['generation'] == last_gen])
        for t in topologies
    ]
    if len(groups_divg) >= 2 and all(len(g) >= 2 for g in groups_divg):
        kw_divg_stat, kw_divg_p = stats.kruskal(*groups_divg)
    else:
        kw_divg_stat, kw_divg_p = float('nan'), float('nan')

    return {
        'summary': summary,
        'kruskal_wallis_diversity': {'H': float(kw_div_stat), 'p': float(kw_div_p)},
        'kruskal_wallis_divergence': {'H': float(kw_divg_stat), 'p': float(kw_divg_p)},
    }


def print_experiment_e_summary(analysis: dict):
    """Print summary table for Experiment E."""
    print("\n" + "=" * 80)
    print("EXPERIMENT E: Topology Sweep")
    print("=" * 80)
    print(f"\n{'Topology':>18} {'Diversity':>14} {'(std)':>8} "
          f"{'Divergence':>14} {'(std)':>8} {'BestFit':>10} {'(std)':>8} {'n':>4}")
    print("-" * 90)
    for topo in ["none", "ring", "star", "fully_connected", "random"]:
        if topo not in analysis['summary']:
            continue
        s = analysis['summary'][topo]
        print(f"{topo:>18} {s['diversity_mean']:>14.4f} {s['diversity_std']:>8.4f} "
              f"{s['divergence_mean']:>14.4f} {s['divergence_std']:>8.4f} "
              f"{s['fitness_mean']:>10.1f} {s['fitness_std']:>8.2f} {s['n']:>4}")

    kw_div = analysis['kruskal_wallis_diversity']
    kw_divg = analysis['kruskal_wallis_divergence']
    print(f"\nKruskal-Wallis (diversity):  H={kw_div['H']:.3f}, p={kw_div['p']:.6f}")
    print(f"Kruskal-Wallis (divergence): H={kw_divg['H']:.3f}, p={kw_divg['p']:.6f}")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_csv(results: List[dict], filename: str):
    """Save raw results to CSV."""
    if not results:
        return
    keys = results[0].keys()
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    print(f"  Saved: {filename}")


def append_csv(rows: List[dict], filepath: str, write_header: bool = False):
    """Append rows to a CSV file. Writes header if write_header=True.

    Flushes immediately so data survives crashes.
    """
    if not rows:
        return
    keys = rows[0].keys()
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
        f.flush()
        os.fsync(f.fileno())


def load_completed_pairs(filepath: str) -> set:
    """Read an existing CSV and return the set of (topology, seed) pairs present."""
    completed = set()
    if not os.path.exists(filepath):
        return completed
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            completed.add((row['topology'], int(row['seed'])))
    return completed


def print_experiment_c_summary(analysis: dict):
    """Print summary table matching Table 5 format."""
    print("\n" + "=" * 80)
    print("EXPERIMENT C: Migration Frequency Sweep")
    print("=" * 80)
    print(f"\nTable 5 (multi-seed): Island functor laxity vs. migration frequency")
    print(f"{'Freq':>6} {'SchedDiff':>10} {'PopDiv(mean)':>14} {'PopDiv(std)':>13} "
          f"{'PopDiv(med)':>13} {'PopDiv(IQR)':>13} {'HamDiv(mean)':>14} {'FitDiff':>10} {'n':>4}")
    print("-" * 105)
    for freq in sorted(analysis['summary'].keys()):
        s = analysis['summary'][freq]
        print(f"{freq:>6} {s['sched_diff']:>10} {s['pop_div_mean']:>14.3f} "
              f"{s['pop_div_std']:>13.3f} {s['pop_div_median']:>13.3f} "
              f"{s['pop_div_iqr']:>13.3f} {s['ham_div_mean']:>14.3f} "
              f"{s['fit_diff_mean']:>10.1f} {s['n']:>4}")

    kw = analysis['kruskal_wallis']
    print(f"\nKruskal-Wallis (non-40 freqs, pop divergence): H={kw['H']:.3f}, p={kw['p']:.4f}")

    print(f"\nPairwise Mann-Whitney U (pop divergence):")
    print(f"{'Pair':>12} {'U':>10} {'p':>10} {'A (V-D)':>10}")
    print("-" * 45)
    for (f1, f2), pw in sorted(analysis['pairwise'].items()):
        print(f"  {f1} vs {f2:>3} {pw['U']:>10.1f} {pw['p']:>10.4f} {pw['A']:>10.3f}")


def print_experiment_d_summary(analysis: dict):
    """Print summary table matching Table 6 format."""
    print("\n" + "=" * 80)
    print("EXPERIMENT D: Boundary Position Sweep")
    print("=" * 80)
    print(f"\nTable 6 (multi-seed): Divergence vs. composition boundary position (freq=5)")
    print(f"{'Boundary':>10} {'HitsMig?':>10} {'PopDiv(mean)':>14} {'PopDiv(std)':>13} "
          f"{'PopDiv(med)':>13} {'PopDiv(IQR)':>13} {'HamDiv(mean)':>14} {'n':>4}")
    print("-" * 95)
    for boundary in sorted(analysis['summary'].keys()):
        s = analysis['summary'][boundary]
        hits = "YES" if s['hits_migration'] else "no"
        print(f"{boundary:>10} {hits:>10} {s['pop_div_mean']:>14.3f} "
              f"{s['pop_div_std']:>13.3f} {s['pop_div_median']:>13.3f} "
              f"{s['pop_div_iqr']:>13.3f} {s['ham_div_mean']:>14.3f} {s['n']:>4}")

    kw = analysis['kruskal_wallis']
    print(f"\nKruskal-Wallis (all boundaries, pop divergence): H={kw['H']:.3f}, p={kw['p']:.4f}")

    print(f"\nPairwise Mann-Whitney U (pop divergence):")
    print(f"{'Pair':>12} {'U':>10} {'p':>10} {'A (V-D)':>10}")
    print("-" * 45)
    for (b1, b2), pw in sorted(analysis['pairwise'].items()):
        print(f"  {b1} vs {b2:>3} {pw['U']:>10.1f} {pw['p']:>10.4f} {pw['A']:>10.3f}")


# ---------------------------------------------------------------------------
# Single-seed validation (match paper's seed 42)
# ---------------------------------------------------------------------------

def run_single_seed_validation(config: GAConfig, seed: int = 42):
    """Run a single seed to compare with the paper's Tables 5 and 6."""
    print("\n" + "=" * 80)
    print(f"SINGLE-SEED VALIDATION (seed={seed})")
    print("=" * 80)

    # Experiment C
    print("\nExperiment C results (single seed):")
    print(f"{'Freq':>6} {'SchedDiff':>10} {'PopDiv':>10} {'HamDivDiff':>12} {'FitDiff':>10}")
    print("-" * 55)
    for freq in [2, 5, 10, 20, 40]:
        r = run_experiment_c_single(seed, config, freq)
        print(f"{r['freq']:>6} {r['sched_diff']:>10} {r['pop_divergence']:>10.3f} "
              f"{r['hamming_div_diff']:>12.3f} {r['fitness_diff']:>10.1f}")

    print("\nPaper Table 5 reference values:")
    print(f"{'Freq':>6} {'SchedDiff':>10} {'PopDiv':>10} {'HamDivDiff':>12} {'FitDiff':>10}")
    print("-" * 55)
    paper_c = [
        (2, 1, 0.744, 0.110, 0.0),
        (5, 1, 0.812, 0.102, 0.0),
        (10, 1, 0.756, 0.096, 0.0),
        (20, 1, 0.819, 0.129, 0.0),
        (40, 0, 0.000, 0.000, 0.0),
    ]
    for freq, sd, pd, hd, fd in paper_c:
        print(f"{freq:>6} {sd:>10} {pd:>10.3f} {hd:>12.3f} {fd:>10.1f}")

    # Experiment D
    print("\nExperiment D results (single seed):")
    print(f"{'Boundary':>10} {'HitsMig?':>10} {'PopDiv':>10} {'HamDivDiff':>12}")
    print("-" * 45)
    for boundary in [15, 17, 20, 23, 25]:
        r = run_experiment_d_single(seed, config, boundary)
        hits = "YES" if r['hits_migration'] else "no"
        print(f"{r['boundary']:>10} {hits:>10} {r['pop_divergence']:>10.3f} "
              f"{r['hamming_div_diff']:>12.3f}")

    print("\nPaper Table 6 reference values:")
    print(f"{'Boundary':>10} {'HitsMig?':>10} {'PopDiv':>10} {'HamDivDiff':>12}")
    print("-" * 45)
    paper_d = [
        (15, "YES", 0.794, 0.105),
        (17, "no", 0.725, 0.098),
        (20, "YES", 0.812, 0.102),
        (23, "no", 0.744, 0.108),
        (25, "YES", 0.800, 0.102),
    ]
    for b, hm, pd, hd in paper_d:
        print(f"{b:>10} {hm:>10} {pd:>10.3f} {hd:>12.3f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="OneMax island model experiments for GECCO 2026 paper")
    parser.add_argument('--exp', choices=['C', 'D', 'E', 'both'], default='both',
                        help='Which experiment to run (default: both)')
    parser.add_argument('--seeds', type=int, default=30,
                        help='Number of seeds (default: 30)')
    parser.add_argument('--seed0', type=int, default=None,
                        help='Run single seed for validation (overrides --seeds)')
    parser.add_argument('--outdir', type=str, default=None,
                        help='Output directory for CSV files (default: same as script)')
    parser.add_argument('--csv-name', type=str, default=None,
                        help='Override CSV filename for experiment output (e.g. experiment_e_per_island.csv)')
    parser.add_argument('--domain', choices=['onemax', 'maze', 'graph_coloring', 'sorting_network', 'knapsack', 'checkers', 'nothanks'],
                        default='onemax',
                        help='Problem domain (default: onemax). Only applies to Experiment E.')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='Resume experiment E from existing CSV (skip completed runs)')
    parser.add_argument('--islands', type=int, default=None,
                        help='Override number of islands (default: domain-specific)')
    parser.add_argument('--topologies', type=str, default=None,
                        help='Comma-separated list of topologies to test (default: all five)')
    args = parser.parse_args()

    # Determine output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    outdir = args.outdir or script_dir

    # Configuration matching the paper
    config = GAConfig(
        population_size=80,
        genome_length=20,
        num_islands=4,
        tournament_size=3,
        crossover_rate=0.8,
        mutation_rate=1.0 / 20.0,  # 1/L
        max_generations=40,
        migration_freq=5,
        migration_rate=0.05,  # gives max(1, round(0.05 * 20)) = 1 migrant per island
    )

    print("OneMax Island Model Experiments")
    print(f"Config: pop={config.population_size}, L={config.genome_length}, "
          f"islands={config.num_islands}, tourn={config.tournament_size}, "
          f"cx={config.crossover_rate}, mut={config.mutation_rate:.3f}, "
          f"gens={config.max_generations}")
    print(f"Migration: rate={config.migration_rate}, freq={config.migration_freq}")

    # Single-seed validation
    if args.seed0 is not None:
        run_single_seed_validation(config, args.seed0)
        return

    seeds = list(range(args.seeds))
    print(f"\nRunning with {len(seeds)} seeds: {seeds[0]}..{seeds[-1]}")
    t0 = time.time()

    # --- Experiment C ---
    if args.exp in ('C', 'both'):
        print("\n--- Experiment C: Migration Frequency Sweep ---")
        results_c = run_experiment_c(seeds, config)
        analysis_c = analyze_experiment_c(results_c)
        print_experiment_c_summary(analysis_c)
        save_csv(results_c, os.path.join(outdir, 'experiment_c_raw.csv'))

    # --- Experiment D ---
    if args.exp in ('D', 'both'):
        print("\n--- Experiment D: Boundary Position Sweep ---")
        results_d = run_experiment_d(seeds, config)
        analysis_d = analyze_experiment_d(results_d)
        print_experiment_d_summary(analysis_d)
        save_csv(results_d, os.path.join(outdir, 'experiment_d_raw.csv'))

    # --- Experiment E ---
    if args.exp == 'E':
        # Domain-specific configuration
        eval_fn = None  # default: OneMax
        init_fn = None  # default: random_population (uniform binary)
        cx_fn = None    # default: one_point_crossover (binary)
        mut_fn = None   # default: point_mutate (bit-flip)
        div_fn = None   # default: hamming_diversity (binary)
        dvg_fn = None   # default: population_divergence (binary)

        if args.domain == 'maze':
            from maze_domain import (evaluate_maze, random_maze_population,
                                     MAZE_GENOME_LENGTH)
            eval_fn = evaluate_maze
            init_fn = random_maze_population
            config_e = GAConfig(
                population_size=80,
                genome_length=MAZE_GENOME_LENGTH,  # 60
                num_islands=5,
                tournament_size=3,
                crossover_rate=0.8,
                mutation_rate=1.0 / MAZE_GENOME_LENGTH,  # 1/L
                max_generations=100,
                migration_freq=5,
                migration_rate=0.1,
            )
        elif args.domain == 'graph_coloring':
            from graph_coloring_domain import (
                evaluate_graph_coloring, random_graph_coloring_population,
                GRAPH_COLORING_GENOME_LENGTH)
            eval_fn = evaluate_graph_coloring
            init_fn = random_graph_coloring_population
            config_e = GAConfig(
                population_size=80,
                genome_length=GRAPH_COLORING_GENOME_LENGTH,  # 40
                num_islands=5,
                tournament_size=3,
                crossover_rate=0.8,
                mutation_rate=1.0 / GRAPH_COLORING_GENOME_LENGTH,  # 1/40 = 0.025
                max_generations=100,
                migration_freq=5,
                migration_rate=0.1,
            )
        elif args.domain == 'sorting_network':
            from sorting_network_domain import (
                evaluate_sorting_network, random_sorting_network_population,
                SORTING_NETWORK_GENOME_LENGTH)
            eval_fn = evaluate_sorting_network
            init_fn = random_sorting_network_population
            config_e = GAConfig(
                population_size=80,
                genome_length=SORTING_NETWORK_GENOME_LENGTH,  # 28
                num_islands=5,
                tournament_size=3,
                crossover_rate=0.8,
                mutation_rate=1.0 / SORTING_NETWORK_GENOME_LENGTH,  # 1/28 ≈ 0.036
                max_generations=100,
                migration_freq=5,
                migration_rate=0.1,
            )
        elif args.domain == 'knapsack':
            from knapsack_domain import (
                evaluate_knapsack, random_knapsack_population,
                KNAPSACK_GENOME_LENGTH)
            eval_fn = evaluate_knapsack
            init_fn = random_knapsack_population
            config_e = GAConfig(
                population_size=80,
                genome_length=KNAPSACK_GENOME_LENGTH,  # 50
                num_islands=5,
                tournament_size=3,
                crossover_rate=0.8,
                mutation_rate=1.0 / KNAPSACK_GENOME_LENGTH,  # 1/50 = 0.02
                max_generations=100,
                migration_freq=5,
                migration_rate=0.1,
            )
        elif args.domain == 'checkers':
            from checkers_domain import (
                evaluate_checkers, random_checkers_population,
                CHECKERS_GENOME_LENGTH)
            eval_fn = evaluate_checkers
            init_fn = random_checkers_population
            config_e = GAConfig(
                population_size=80,
                genome_length=CHECKERS_GENOME_LENGTH,  # 64
                num_islands=5,
                tournament_size=3,
                crossover_rate=0.8,
                mutation_rate=1.0 / CHECKERS_GENOME_LENGTH,  # 1/64 ≈ 0.016
                max_generations=100,
                migration_freq=5,
                migration_rate=0.1,
            )
        elif args.domain == 'nothanks':
            from nothanks_domain import (
                evaluate_nothanks_fast, random_nothanks_population,
                NOTHANKS_GENOME_LENGTH,
                gaussian_mutate, uniform_crossover,
                euclidean_diversity, euclidean_divergence)
            eval_fn = evaluate_nothanks_fast
            init_fn = random_nothanks_population
            cx_fn = uniform_crossover
            mut_fn = gaussian_mutate
            div_fn = euclidean_diversity
            dvg_fn = euclidean_divergence
            config_e = GAConfig(
                population_size=80,
                genome_length=NOTHANKS_GENOME_LENGTH,  # 13
                num_islands=5,
                tournament_size=3,
                crossover_rate=0.8,
                mutation_rate=1.0 / NOTHANKS_GENOME_LENGTH,  # 1/13 ≈ 0.077
                max_generations=100,
                migration_freq=5,
                migration_rate=0.1,
            )
        else:
            config_e = GAConfig(
                population_size=50,
                genome_length=100,
                num_islands=5,
                tournament_size=3,
                crossover_rate=0.8,
                mutation_rate=1.0 / 100.0,  # 1/L
                max_generations=100,
                migration_freq=5,
                migration_rate=0.1,
            )

        # CLI overrides for island count and topology list
        if args.islands is not None:
            config_e.num_islands = args.islands
            # Ensure population is divisible by island count
            if config_e.population_size % args.islands != 0:
                old_pop = config_e.population_size
                # Round up to nearest multiple
                config_e.population_size = ((old_pop + args.islands - 1) // args.islands) * args.islands
                print(f"  Adjusted population {old_pop} -> {config_e.population_size} "
                      f"(divisible by {args.islands} islands)")
        topo_list = None
        if args.topologies is not None:
            topo_list = [t.strip() for t in args.topologies.split(',')]

        print(f"\nExperiment E config ({args.domain}): pop={config_e.population_size}, "
              f"L={config_e.genome_length}, islands={config_e.num_islands}, "
              f"mig_freq={config_e.migration_freq}, mig_rate={config_e.migration_rate}")
        if topo_list:
            print(f"  Topologies: {topo_list}")
        print(f"\n--- Experiment E: Topology Sweep ({args.domain}) ---")
        csv_name = args.csv_name or f'experiment_e_{args.domain}.csv'
        csv_path = os.path.join(outdir, csv_name)

        # When not resuming and not using incremental saves, clear any existing file
        if not args.resume and os.path.exists(csv_path):
            os.remove(csv_path)

        results_e = run_experiment_e(seeds, config_e,
                                     topologies=topo_list,
                                     evaluate_fn=eval_fn, init_fn=init_fn,
                                     crossover_fn=cx_fn, mutate_fn=mut_fn,
                                     diversity_fn=div_fn, divergence_fn=dvg_fn,
                                     incremental_csv=csv_path,
                                     resume=args.resume)
        analysis_e = analyze_experiment_e(results_e, config_e.max_generations)
        print_experiment_e_summary(analysis_e)
        print(f"  Results saved incrementally to: {csv_path}")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.1f}s")


if __name__ == '__main__':
    main()
