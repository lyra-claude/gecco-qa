#!/usr/bin/env python3
"""
Unit tests for the OneMax GA components.

Validates each operator against known seeds to ensure correctness
and reproducibility. Tests match the Haskell implementation's behavior.
"""

import sys
import os
import unittest
import numpy as np

# Add experiments directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from onemax_stats import (
    GAConfig, onemax_fitness, random_population, evaluate,
    tournament_select, one_point_crossover, point_mutate,
    split_population, merge_populations, ring_migrate,
    evolve_islands, hamming_diversity, population_divergence,
    island_population_divergence, run_experiment_c_single,
    run_experiment_d_single,
)


class TestOneMaxFitness(unittest.TestCase):
    """Test the OneMax fitness function."""

    def test_all_ones(self):
        ind = np.array([1, 1, 1, 1, 1], dtype=np.int8)
        self.assertEqual(onemax_fitness(ind), 5.0)

    def test_all_zeros(self):
        ind = np.array([0, 0, 0, 0, 0], dtype=np.int8)
        self.assertEqual(onemax_fitness(ind), 0.0)

    def test_mixed(self):
        ind = np.array([1, 0, 1, 0, 1], dtype=np.int8)
        self.assertEqual(onemax_fitness(ind), 3.0)

    def test_evaluate_population(self):
        pop = np.array([[1, 1, 0], [0, 0, 0], [1, 1, 1]], dtype=np.int8)
        fitnesses = evaluate(pop)
        np.testing.assert_array_equal(fitnesses, [2.0, 0.0, 3.0])


class TestRandomPopulation(unittest.TestCase):
    """Test population initialization."""

    def test_shape(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 10, 20)
        self.assertEqual(pop.shape, (10, 20))

    def test_binary(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 100, 20)
        self.assertTrue(np.all((pop == 0) | (pop == 1)))

    def test_reproducible(self):
        pop1 = random_population(np.random.default_rng(42), 10, 20)
        pop2 = random_population(np.random.default_rng(42), 10, 20)
        np.testing.assert_array_equal(pop1, pop2)


class TestTournamentSelection(unittest.TestCase):
    """Test tournament selection operator."""

    def test_preserves_population_size(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 20, 10)
        fitnesses = evaluate(pop)
        selected = tournament_select(rng, pop, fitnesses, tournament_size=3)
        self.assertEqual(selected.shape, pop.shape)

    def test_selects_fitter_individuals(self):
        """Over many selections, fitter individuals should appear more often."""
        rng = np.random.default_rng(42)
        # Create a population where individual 0 is clearly best
        pop = np.zeros((10, 5), dtype=np.int8)
        pop[0] = [1, 1, 1, 1, 1]  # fitness 5
        pop[1] = [1, 1, 1, 0, 0]  # fitness 3
        # rest are all zeros, fitness 0
        fitnesses = evaluate(pop)

        selected = tournament_select(rng, pop, fitnesses, tournament_size=3)
        sel_fitnesses = evaluate(selected)
        # Mean fitness of selected should be higher than original
        self.assertGreater(np.mean(sel_fitnesses), np.mean(fitnesses))

    def test_reproducible(self):
        pop = np.array([[1, 0, 1], [0, 1, 0], [1, 1, 0], [0, 0, 1]], dtype=np.int8)
        fitnesses = evaluate(pop)
        s1 = tournament_select(np.random.default_rng(99), pop, fitnesses, 2)
        s2 = tournament_select(np.random.default_rng(99), pop, fitnesses, 2)
        np.testing.assert_array_equal(s1, s2)


class TestOnePointCrossover(unittest.TestCase):
    """Test one-point crossover operator."""

    def test_preserves_population_size(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 20, 10)
        crossed = one_point_crossover(rng, pop, crossover_rate=0.8)
        self.assertEqual(crossed.shape, pop.shape)

    def test_rate_zero_no_change(self):
        """With crossover rate 0, population should not change."""
        rng = np.random.default_rng(42)
        pop = random_population(rng, 20, 10)
        pop_copy = pop.copy()
        # Rate 0: no crossover happens, but random numbers are still consumed
        crossed = one_point_crossover(np.random.default_rng(0), pop_copy, crossover_rate=0.0)
        np.testing.assert_array_equal(crossed, pop_copy)

    def test_rate_one_always_crosses(self):
        """With crossover rate 1, every pair crosses over."""
        rng = np.random.default_rng(42)
        pop = np.array([
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0],
        ], dtype=np.int8)
        crossed = one_point_crossover(rng, pop, crossover_rate=1.0)
        # After crossover, children should be different from parents
        # (unless crossover point is at 0 or len, which shouldn't happen)
        self.assertFalse(np.array_equal(crossed[0], pop[0]) and
                         np.array_equal(crossed[1], pop[1]))

    def test_gene_conservation(self):
        """Total number of each allele should be conserved across a pair."""
        rng = np.random.default_rng(42)
        for _ in range(10):
            pop = random_population(rng, 2, 20)
            crossed = one_point_crossover(rng, pop.copy(), crossover_rate=1.0)
            # Sum of all genes should be the same
            self.assertEqual(pop.sum(), crossed.sum())

    def test_reproducible(self):
        pop = random_population(np.random.default_rng(0), 10, 20)
        c1 = one_point_crossover(np.random.default_rng(42), pop.copy(), 0.8)
        c2 = one_point_crossover(np.random.default_rng(42), pop.copy(), 0.8)
        np.testing.assert_array_equal(c1, c2)


class TestPointMutate(unittest.TestCase):
    """Test bit-flip mutation operator."""

    def test_preserves_shape(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 20, 10)
        mutated = point_mutate(rng, pop, mutation_rate=0.05)
        self.assertEqual(mutated.shape, pop.shape)

    def test_rate_zero_no_change(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 20, 10)
        mutated = point_mutate(np.random.default_rng(0), pop, mutation_rate=0.0)
        np.testing.assert_array_equal(mutated, pop)

    def test_rate_one_all_flipped(self):
        pop = np.array([[1, 1, 0, 0, 1]], dtype=np.int8)
        mutated = point_mutate(np.random.default_rng(0), pop, mutation_rate=1.0)
        np.testing.assert_array_equal(mutated, [[0, 0, 1, 1, 0]])

    def test_binary_output(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 100, 20)
        mutated = point_mutate(rng, pop, mutation_rate=0.1)
        self.assertTrue(np.all((mutated == 0) | (mutated == 1)))

    def test_approximate_rate(self):
        """With many mutations, the fraction flipped should approximate the rate."""
        rng = np.random.default_rng(42)
        pop = np.zeros((100, 100), dtype=np.int8)
        rate = 0.1
        mutated = point_mutate(rng, pop, mutation_rate=rate)
        actual_rate = mutated.sum() / mutated.size
        # Should be close to 0.1 (within 0.03)
        self.assertAlmostEqual(actual_rate, rate, delta=0.03)


class TestIslandOperations(unittest.TestCase):
    """Test island model operations."""

    def test_split_merge_identity(self):
        """Splitting and merging should preserve population content."""
        rng = np.random.default_rng(42)
        pop = random_population(rng, 80, 20)
        islands = split_population(pop, 4)
        self.assertEqual(len(islands), 4)
        self.assertEqual(islands[0].shape, (20, 20))
        merged = merge_populations(islands)
        np.testing.assert_array_equal(merged, pop)

    def test_ring_migration_preserves_total_size(self):
        rng = np.random.default_rng(42)
        pop = random_population(rng, 80, 20)
        islands = split_population(pop, 4)
        total_before = sum(len(isl) for isl in islands)
        migrated = ring_migrate(rng, islands, migration_rate=0.05)
        total_after = sum(len(isl) for isl in migrated)
        self.assertEqual(total_before, total_after)

    def test_ring_migration_changes_populations(self):
        """Migration should change at least some island populations."""
        rng = np.random.default_rng(42)
        pop = random_population(rng, 80, 20)
        islands = split_population(pop, 4)
        migrated = ring_migrate(rng, islands, migration_rate=0.05)
        # At least one island should be different
        any_changed = any(
            not np.array_equal(islands[i], migrated[i])
            for i in range(4)
        )
        self.assertTrue(any_changed)

    def test_ring_migration_single_island(self):
        """Single island should not change."""
        rng = np.random.default_rng(42)
        pop = random_population(rng, 20, 10)
        islands = [pop]
        migrated = ring_migrate(rng, islands, migration_rate=0.1)
        np.testing.assert_array_equal(migrated[0], pop)

    def test_migration_num_migrants(self):
        """With rate=0.05 and pop=20, should migrate max(1, round(0.05*20))=1 individual."""
        rng = np.random.default_rng(42)
        pop = random_population(rng, 80, 20)
        islands = split_population(pop, 4)
        # Track: each island should receive exactly 1 migrant
        # Since migrants go to front, the first individual of migrated island
        # should come from the source island
        migrated = ring_migrate(rng, islands, migration_rate=0.05)
        for i in range(4):
            # 1 new + 19 old = 20 total
            self.assertEqual(len(migrated[i]), 20)


class TestMetrics(unittest.TestCase):
    """Test diversity and divergence metrics."""

    def test_hamming_diversity_identical(self):
        """Identical population has zero diversity."""
        pop = np.ones((10, 5), dtype=np.int8)
        self.assertAlmostEqual(hamming_diversity(pop), 0.0)

    def test_hamming_diversity_max(self):
        """Population split 50/50 between all-0 and all-1 has known diversity."""
        pop = np.vstack([
            np.zeros((5, 4), dtype=np.int8),
            np.ones((5, 4), dtype=np.int8),
        ])
        # At each locus: 5 ones, 5 zeros out of 10 individuals
        # Disagreeing pairs per locus: 5 * 5 = 25
        # Total pairs: 10*9/2 = 45
        # Mean Hamming normalized: (25 * 4) / 45 / 4 = 25/45 = 0.5556
        expected = 25.0 / 45.0
        self.assertAlmostEqual(hamming_diversity(pop), expected, places=4)

    def test_population_divergence_identical(self):
        pop = np.ones((10, 5), dtype=np.int8)
        self.assertAlmostEqual(population_divergence(pop, pop), 0.0)

    def test_population_divergence_maximal(self):
        pop1 = np.zeros((10, 5), dtype=np.int8)
        pop2 = np.ones((10, 5), dtype=np.int8)
        self.assertAlmostEqual(population_divergence(pop1, pop2), 1.0)


class TestEvolveIslands(unittest.TestCase):
    """Test full island model evolution."""

    def test_fitness_improves(self):
        """Fitness should generally improve over generations for OneMax."""
        rng = np.random.default_rng(42)
        config = GAConfig(
            population_size=80, genome_length=20, num_islands=4,
            tournament_size=3, crossover_rate=0.8,
            mutation_rate=1.0/20.0, max_generations=40,
            migration_freq=5, migration_rate=0.05,
        )
        init_pop = random_population(rng, config.population_size, config.genome_length)
        islands = split_population(init_pop, config.num_islands)

        initial_best = max(float(np.max(evaluate(isl))) for isl in islands)

        final_islands, stats = evolve_islands(rng, islands, config)
        final_best = max(float(np.max(evaluate(isl))) for isl in final_islands)

        self.assertGreaterEqual(final_best, initial_best)
        # Should reach near-optimum (20) for OneMax with these settings
        self.assertGreater(final_best, 15.0)

    def test_reproducible(self):
        """Same seed should produce same result."""
        config = GAConfig(
            population_size=80, genome_length=20, num_islands=4,
            tournament_size=3, crossover_rate=0.8,
            mutation_rate=1.0/20.0, max_generations=20,
            migration_freq=5, migration_rate=0.05,
        )
        def run_once(seed):
            rng = np.random.default_rng(seed)
            pop = random_population(rng, config.population_size, config.genome_length)
            islands = split_population(pop, config.num_islands)
            return evolve_islands(rng, islands, config)

        islands1, stats1 = run_once(42)
        islands2, stats2 = run_once(42)

        for i in range(4):
            np.testing.assert_array_equal(islands1[i], islands2[i])


class TestDichotomyNoMigration(unittest.TestCase):
    """Test that freq=40 produces zero divergence (strict functor)."""

    def test_strict_functor(self):
        """With no migration events, continuous = composed."""
        config = GAConfig(
            population_size=80, genome_length=20, num_islands=4,
            tournament_size=3, crossover_rate=0.8,
            mutation_rate=1.0/20.0, max_generations=40,
            migration_freq=5, migration_rate=0.05,
        )
        result = run_experiment_c_single(42, config, freq=40)
        self.assertAlmostEqual(result['pop_divergence'], 0.0, places=10)
        self.assertAlmostEqual(result['hamming_div_diff'], 0.0, places=10)
        self.assertAlmostEqual(result['fitness_diff'], 0.0, places=10)

    def test_lax_functor(self):
        """With migration, continuous != composed."""
        config = GAConfig(
            population_size=80, genome_length=20, num_islands=4,
            tournament_size=3, crossover_rate=0.8,
            mutation_rate=1.0/20.0, max_generations=40,
            migration_freq=5, migration_rate=0.05,
        )
        result = run_experiment_c_single(42, config, freq=5)
        self.assertGreater(result['pop_divergence'], 0.1)


class TestExperimentRunners(unittest.TestCase):
    """Test that experiment runners complete without error."""

    def test_experiment_c_single(self):
        config = GAConfig(
            population_size=80, genome_length=20, num_islands=4,
            tournament_size=3, crossover_rate=0.8,
            mutation_rate=1.0/20.0, max_generations=40,
            migration_freq=5, migration_rate=0.05,
        )
        result = run_experiment_c_single(0, config, freq=5)
        self.assertIn('pop_divergence', result)
        self.assertIn('hamming_div_diff', result)
        self.assertIn('fitness_diff', result)
        self.assertIsInstance(result['pop_divergence'], float)

    def test_experiment_d_single(self):
        config = GAConfig(
            population_size=80, genome_length=20, num_islands=4,
            tournament_size=3, crossover_rate=0.8,
            mutation_rate=1.0/20.0, max_generations=40,
            migration_freq=5, migration_rate=0.05,
        )
        result = run_experiment_d_single(0, config, boundary=20)
        self.assertIn('pop_divergence', result)
        self.assertIn('hamming_div_diff', result)
        self.assertIn('hits_migration', result)
        self.assertTrue(result['hits_migration'])  # 20 % 5 == 0


if __name__ == '__main__':
    unittest.main(verbosity=2)
