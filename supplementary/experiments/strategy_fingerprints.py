#!/usr/bin/env python3
"""
Generate strategy fingerprint data for binary GA domains.
4 strategies (flat, hourglass, island, adaptive) on OneMax and Maze.
Outputs TikZ coordinates for the paper.
"""

import numpy as np
from collections import defaultdict


# ─── GA Operators ───────────────────────────────────────────────────

def hamming_diversity(pop):
    """Mean pairwise Hamming distance, normalized to [0, 1]."""
    n = len(pop)
    if n < 2:
        return 0.0
    genome_len = len(pop[0])
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += np.sum(pop[i] != pop[j])
            count += 1
    return total / (count * genome_len)


def tournament_select(pop, fitnesses, tournament_size, rng):
    """Tournament selection, returns new population."""
    n = len(pop)
    selected = []
    for _ in range(n):
        idxs = rng.choice(n, size=tournament_size, replace=False)
        best = idxs[np.argmax(fitnesses[idxs])]
        selected.append(pop[best].copy())
    return selected


def one_point_crossover(pop, cx_rate, rng):
    """One-point crossover."""
    offspring = []
    indices = list(range(len(pop)))
    rng.shuffle(indices)
    for i in range(0, len(indices) - 1, 2):
        p1, p2 = pop[indices[i]].copy(), pop[indices[i + 1]].copy()
        if rng.random() < cx_rate:
            pt = rng.integers(1, len(p1))
            p1[pt:], p2[pt:] = p2[pt:].copy(), p1[pt:].copy()
        offspring.extend([p1, p2])
    if len(indices) % 2 == 1:
        offspring.append(pop[indices[-1]].copy())
    return offspring[:len(pop)]


def bit_flip_mutate(pop, mut_rate, rng):
    """Bit-flip mutation per bit."""
    for ind in pop:
        mask = rng.random(len(ind)) < mut_rate
        ind[mask] = 1 - ind[mask]
    return pop


def one_generation(pop, fitness_fn, tournament_size, cx_rate, mut_rate, rng):
    """One generation: evaluate → select → crossover → mutate."""
    fitnesses = np.array([fitness_fn(ind) for ind in pop])
    selected = tournament_select(pop, fitnesses, tournament_size, rng)
    crossed = one_point_crossover(selected, cx_rate, rng)
    mutated = bit_flip_mutate(crossed, mut_rate, rng)
    return mutated


# ─── Fitness Functions ──────────────────────────────────────────────

def onemax_fitness(genome):
    return np.sum(genome)


def maze_fitness(genome):
    """Simplified maze fitness: BFS-based metrics on 6x6 grid."""
    # Genome encodes 60 walls on a 6x6 grid
    # We use a simplified fitness: path length + dead ends + branching
    grid_size = 6
    n_walls = grid_size * (grid_size - 1) * 2  # 60 for 6x6

    # Build adjacency from genome
    walls = set()
    idx = 0
    # Horizontal walls
    for r in range(grid_size):
        for c in range(grid_size - 1):
            if idx < len(genome) and genome[idx]:
                walls.add(((r, c), (r, c + 1)))
            idx += 1
    # Vertical walls
    for r in range(grid_size - 1):
        for c in range(grid_size):
            if idx < len(genome) and genome[idx]:
                walls.add(((r, c), (r + 1, c)))
            idx += 1

    # BFS from (0,0) to (5,5)
    from collections import deque
    start, end = (0, 0), (grid_size - 1, grid_size - 1)
    visited = {start}
    queue = deque([(start, 0)])
    path_len = 0
    reachable = 1

    while queue:
        (r, c), dist = queue.popleft()
        if (r, c) == end:
            path_len = dist
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < grid_size and 0 <= nc < grid_size:
                edge = ((min(r, nr), min(c, nc)), (max(r, nr), max(c, nc)))
                if (r, c) != (nr, nc):
                    edge = (tuple(sorted([(r, c), (nr, nc)])))
                    edge = (min((r, c), (nr, nc)), max((r, c), (nr, nc)))
                if edge not in walls and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append(((nr, nc), dist + 1))
                    reachable += 1

    # Dead ends: cells with exactly 1 connection
    dead_ends = 0
    for r in range(grid_size):
        for c in range(grid_size):
            if (r, c) not in visited:
                continue
            connections = 0
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < grid_size and 0 <= nc < grid_size:
                    edge = (min((r, c), (nr, nc)), max((r, c), (nr, nc)))
                    if edge not in walls and (nr, nc) in visited:
                        connections += 1
            if connections == 1 and (r, c) != start and (r, c) != end:
                dead_ends += 1

    # Fitness: weighted combination
    max_path = grid_size * grid_size - 1
    path_score = path_len / max_path if path_len > 0 else 0
    dead_end_score = dead_ends / (grid_size * grid_size)
    reachable_score = reachable / (grid_size * grid_size)

    return 0.5 * path_score + 0.3 * dead_end_score + 0.2 * reachable_score


# ─── Strategies ─────────────────────────────────────────────────────

def run_flat(pop_size, genome_len, fitness_fn, n_gen, rng):
    """Flat generational: standard pipeline iterated."""
    pop = [rng.integers(0, 2, size=genome_len) for _ in range(pop_size)]
    divs = [hamming_diversity(pop)]

    for g in range(n_gen):
        pop = one_generation(pop, fitness_fn, tournament_size=3,
                             cx_rate=0.8, mut_rate=1.0 / genome_len, rng=rng)
        divs.append(hamming_diversity(pop))
    return divs


def run_hourglass(pop_size, genome_len, fitness_fn, rng):
    """Hourglass: explore(15) → converge(10) → diversify(25) = 50 gen."""
    pop = [rng.integers(0, 2, size=genome_len) for _ in range(pop_size)]
    divs = [hamming_diversity(pop)]
    base_mut = 1.0 / genome_len

    # Phase 1: explore (high mutation, weak selection)
    for g in range(15):
        pop = one_generation(pop, fitness_fn, tournament_size=2,
                             cx_rate=0.8, mut_rate=base_mut * 2, rng=rng)
        divs.append(hamming_diversity(pop))

    # Phase 2: converge (low mutation, strong selection)
    for g in range(10):
        pop = one_generation(pop, fitness_fn, tournament_size=5,
                             cx_rate=0.8, mut_rate=base_mut * 0.5, rng=rng)
        divs.append(hamming_diversity(pop))

    # Phase 3: diversify (high mutation, weak selection)
    for g in range(25):
        pop = one_generation(pop, fitness_fn, tournament_size=2,
                             cx_rate=0.8, mut_rate=base_mut * 2, rng=rng)
        divs.append(hamming_diversity(pop))

    return divs


def run_island(pop_size, genome_len, fitness_fn, n_gen, rng):
    """Island: 4 subpopulations, ring migration every 5 gen."""
    n_islands = 4
    island_size = pop_size // n_islands
    islands = [[rng.integers(0, 2, size=genome_len) for _ in range(island_size)]
               for _ in range(n_islands)]

    # Initial diversity across all islands
    all_pop = [ind for isle in islands for ind in isle]
    divs = [hamming_diversity(all_pop)]

    for g in range(n_gen):
        # Evolve each island independently
        for i in range(n_islands):
            islands[i] = one_generation(islands[i], fitness_fn, tournament_size=3,
                                        cx_rate=0.8, mut_rate=1.0 / genome_len, rng=rng)

        # Migration every 5 generations: best → next island's worst
        if (g + 1) % 5 == 0:
            for i in range(n_islands):
                src = islands[i]
                dst = islands[(i + 1) % n_islands]
                src_fit = [fitness_fn(ind) for ind in src]
                dst_fit = [fitness_fn(ind) for ind in dst]
                best_idx = np.argmax(src_fit)
                worst_idx = np.argmin(dst_fit)
                dst[worst_idx] = src[best_idx].copy()

        all_pop = [ind for isle in islands for ind in isle]
        divs.append(hamming_diversity(all_pop))

    return divs


def run_adaptive(pop_size, genome_len, fitness_fn, n_gen, rng):
    """Adaptive: explore mode, switch to focus on plateau detection."""
    pop = [rng.integers(0, 2, size=genome_len) for _ in range(pop_size)]
    divs = [hamming_diversity(pop)]
    base_mut = 1.0 / genome_len
    mode = "explore"
    fitness_history = []

    for g in range(n_gen):
        fitnesses = np.array([fitness_fn(ind) for ind in pop])
        best_fit = np.max(fitnesses)
        fitness_history.append(best_fit)

        if mode == "explore":
            pop = one_generation(pop, fitness_fn, tournament_size=2,
                                 cx_rate=0.8, mut_rate=base_mut * 2, rng=rng)
            # Check for plateau: <1% improvement over 5 gen window
            if len(fitness_history) >= 5:
                old = fitness_history[-5]
                if old > 0 and (best_fit - old) / abs(old) < 0.01:
                    mode = "focus"
        else:
            pop = one_generation(pop, fitness_fn, tournament_size=5,
                                 cx_rate=0.8, mut_rate=base_mut * 0.5, rng=rng)

        divs.append(hamming_diversity(pop))

    return divs


# ─── Main ───────────────────────────────────────────────────────────

def graph_coloring_fitness(genome):
    """4-coloring of 20-vertex Erdos-Renyi graph (p=0.3, seed=42)."""
    # Generate fixed graph
    rng_g = np.random.default_rng(42)
    n_verts = 20
    edges = []
    for i in range(n_verts):
        for j in range(i + 1, n_verts):
            if rng_g.random() < 0.3:
                edges.append((i, j))
    # Decode colors: 2 bits per vertex
    colors = []
    for v in range(n_verts):
        c = genome[2 * v] * 2 + genome[2 * v + 1]
        colors.append(c)
    violations = sum(1 for i, j in edges if colors[i] == colors[j])
    return 1.0 - violations / max(len(edges), 1)


def knapsack_fitness(genome):
    """0/1 knapsack: 50 items, capacity = 50% total weight."""
    rng_k = np.random.default_rng(42)
    weights = rng_k.integers(1, 100, size=50)
    values = rng_k.integers(1, 100, size=50)
    capacity = int(0.5 * np.sum(weights))
    total_w = float(np.dot(genome, weights))
    total_v = float(np.dot(genome, values))
    max_v = float(np.sum(values))
    ratio = total_v / max_v
    if total_w <= capacity:
        return ratio
    return max(0.0, ratio - 2.0 * (total_w - capacity) / capacity)


DOMAINS = {
    "Graph Coloring": (40, graph_coloring_fitness),
    "Knapsack": (50, knapsack_fitness),
    "Maze": (60, maze_fitness),
}

STRATEGIES = {
    "Flat": lambda ps, gl, ff, rng: run_flat(ps, gl, ff, 50, rng),
    "Hourglass": lambda ps, gl, ff, rng: run_hourglass(ps, gl, ff, rng),
    "Island": lambda ps, gl, ff, rng: run_island(ps, gl, ff, 50, rng),
    "Adaptive": lambda ps, gl, ff, rng: run_adaptive(ps, gl, ff, 50, rng),
}

POP_SIZE = 60
N_SEEDS = 10  # Multiple seeds for robustness
SAMPLE_GENS = [0, 5, 10, 15, 20, 25, 30, 50]


def main():
    for domain_name, (genome_len, fitness_fn) in DOMAINS.items():
        print(f"\n{'=' * 60}")
        print(f"  {domain_name} (genome_len={genome_len}, pop={POP_SIZE})")
        print(f"{'=' * 60}")

        for strat_name, strat_fn in STRATEGIES.items():
            # Run multiple seeds and average
            all_divs = []
            for seed in range(N_SEEDS):
                rng = np.random.default_rng(seed + 42)
                divs = strat_fn(POP_SIZE, genome_len, fitness_fn, rng)
                all_divs.append(divs)

            # Average across seeds
            min_len = min(len(d) for d in all_divs)
            mean_divs = np.mean([d[:min_len] for d in all_divs], axis=0)

            # Print sampled values
            print(f"\n  {strat_name}:")
            for g in SAMPLE_GENS:
                if g < len(mean_divs):
                    print(f"    gen {g:3d}: {mean_divs[g]:.4f}")

            # Print TikZ coordinates
            coords = []
            for g in SAMPLE_GENS:
                if g < len(mean_divs):
                    coords.append(f"({g},{mean_divs[g]:.4f})")
            print(f"  \\addplot coordinates {{{' '.join(coords)}}};")


if __name__ == "__main__":
    main()
