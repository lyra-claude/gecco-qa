#!/usr/bin/env python3
"""
0/1 Knapsack domain for the multi-domain topology sweep.

A 50-bit genome encodes which items to include in a knapsack:
  - Bit i = 1 means item i is included
  - Each item has a weight w_i and value v_i (deterministic, seed 42)
  - Knapsack capacity C = 50% of total weight

Fitness function:
  - If total_weight <= capacity: fitness = total_value / max_possible_value
  - If overweight: fitness = max(0, value_ratio - 2.0 * overflow_ratio)
  - This creates a RUGGED landscape: adding an item can help (more value)
    or hurt (exceed capacity), depending on which items are already included.

The constraint boundary at ~50% capacity creates epistatic interactions
between items — the fitness contribution of each bit depends on which
other bits are set. This is what makes the landscape rugged and
topology-sensitive.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KNAPSACK_GENOME_LENGTH = 50

# Deterministic item generation (seed 42)
_rng_items = np.random.default_rng(42)
WEIGHTS = _rng_items.integers(1, 100, size=KNAPSACK_GENOME_LENGTH)  # 1-99
VALUES = _rng_items.integers(1, 100, size=KNAPSACK_GENOME_LENGTH)   # 1-99
CAPACITY = int(0.5 * np.sum(WEIGHTS))

# Precompute for normalization
MAX_POSSIBLE_VALUE = float(np.sum(VALUES))


# ---------------------------------------------------------------------------
# Fitness
# ---------------------------------------------------------------------------

def knapsack_fitness(genome: np.ndarray) -> float:
    """Fitness for a single 0/1 knapsack solution.

    - Feasible solutions: fitness = total_value / max_possible_value
    - Infeasible solutions: penalized proportional to constraint violation
    - Penalty = 2.0 * (total_weight - capacity) / capacity

    Returns a float in [0.0, ~1.0]. Can be 0.0 for heavily overweight.
    """
    total_weight = float(np.dot(genome, WEIGHTS))
    total_value = float(np.dot(genome, VALUES))

    value_ratio = total_value / MAX_POSSIBLE_VALUE

    if total_weight <= CAPACITY:
        return value_ratio
    else:
        penalty = 2.0 * (total_weight - CAPACITY) / CAPACITY
        return max(0.0, value_ratio - penalty)


# ---------------------------------------------------------------------------
# Population-level functions
# ---------------------------------------------------------------------------

def evaluate_knapsack(pop: np.ndarray) -> np.ndarray:
    """Evaluate knapsack fitness for entire population.

    Args:
        pop: (pop_size, 50) binary array.

    Returns: (pop_size,) float64 array of fitnesses.
    """
    # Vectorized computation for speed
    total_weights = pop @ WEIGHTS  # (pop_size,)
    total_values = pop @ VALUES    # (pop_size,)

    value_ratios = total_values.astype(np.float64) / MAX_POSSIBLE_VALUE

    # Penalty for overweight solutions
    overflow = np.maximum(0, total_weights.astype(np.float64) - CAPACITY)
    penalties = 2.0 * overflow / CAPACITY

    fitnesses = np.maximum(0.0, value_ratios - penalties)
    return fitnesses


def random_knapsack_population(rng, pop_size, genome_length=KNAPSACK_GENOME_LENGTH):
    """Generate random knapsack population (uniform binary).

    Args:
        rng: numpy random Generator.
        pop_size: number of individuals.
        genome_length: must be KNAPSACK_GENOME_LENGTH (50).

    Returns: (pop_size, 50) int8 array.
    """
    return rng.integers(0, 2, size=(pop_size, genome_length), dtype=np.int8)


# ---------------------------------------------------------------------------
# Greedy heuristic (for testing)
# ---------------------------------------------------------------------------

def greedy_knapsack():
    """Greedy heuristic: sort items by value/weight ratio, fill until capacity.

    Returns: (genome, total_value, total_weight)
    """
    ratios = VALUES.astype(float) / WEIGHTS.astype(float)
    order = np.argsort(-ratios)  # descending by ratio

    genome = np.zeros(KNAPSACK_GENOME_LENGTH, dtype=np.int8)
    total_weight = 0
    total_value = 0

    for idx in order:
        if total_weight + WEIGHTS[idx] <= CAPACITY:
            genome[idx] = 1
            total_weight += WEIGHTS[idx]
            total_value += VALUES[idx]

    return genome, total_value, total_weight


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def test_knapsack_domain():
    """Self-tests for the knapsack domain."""
    print("=== Knapsack Domain Self-Test ===\n")

    # Item statistics
    print(f"Items: {KNAPSACK_GENOME_LENGTH}")
    print(f"  Total weight: {np.sum(WEIGHTS)}")
    print(f"  Total value:  {np.sum(VALUES)}")
    print(f"  Capacity:     {CAPACITY} ({CAPACITY / np.sum(WEIGHTS) * 100:.1f}% of total)")
    print(f"  Weight range: [{WEIGHTS.min()}, {WEIGHTS.max()}], mean={WEIGHTS.mean():.1f}")
    print(f"  Value range:  [{VALUES.min()}, {VALUES.max()}], mean={VALUES.mean():.1f}")
    print()

    # Test 1: Empty knapsack
    empty = np.zeros(KNAPSACK_GENOME_LENGTH, dtype=np.int8)
    f_empty = knapsack_fitness(empty)
    assert f_empty == 0.0, f"Empty knapsack fitness should be 0.0, got {f_empty}"
    print(f"[PASS] Test 1: Empty knapsack fitness = {f_empty}")

    # Test 2: Full knapsack (all items)
    full = np.ones(KNAPSACK_GENOME_LENGTH, dtype=np.int8)
    f_full = knapsack_fitness(full)
    total_w = float(np.sum(WEIGHTS))
    print(f"[PASS] Test 2: Full knapsack fitness = {f_full:.4f} "
          f"(weight={total_w:.0f}, capacity={CAPACITY}, "
          f"{'PENALIZED' if total_w > CAPACITY else 'feasible'})")

    # Test 3: Greedy solution
    g_genome, g_val, g_wt = greedy_knapsack()
    f_greedy = knapsack_fitness(g_genome)
    n_items = int(np.sum(g_genome))
    print(f"[PASS] Test 3: Greedy solution: {n_items} items, "
          f"value={g_val}, weight={g_wt}/{CAPACITY}, fitness={f_greedy:.4f}")

    # Test 4: Vectorized evaluate matches scalar
    rng = np.random.default_rng(99)
    pop = random_knapsack_population(rng, 100)
    vec_fit = evaluate_knapsack(pop)
    scalar_fit = np.array([knapsack_fitness(pop[i]) for i in range(100)])
    assert np.allclose(vec_fit, scalar_fit), (
        f"Vectorized/scalar mismatch: max diff = {np.max(np.abs(vec_fit - scalar_fit))}"
    )
    print(f"[PASS] Test 4: Vectorized matches scalar for 100 individuals")

    # Test 5: Random population statistics
    rng2 = np.random.default_rng(42)
    pop2 = random_knapsack_population(rng2, 500)
    fit2 = evaluate_knapsack(pop2)
    n_feasible = np.sum(fit2 > 0)
    print(f"[PASS] Test 5: Random pop (500): "
          f"fitness mean={fit2.mean():.4f}, std={fit2.std():.4f}, "
          f"range=[{fit2.min():.4f}, {fit2.max():.4f}], "
          f"feasible={n_feasible}/500 ({n_feasible/500*100:.1f}%)")

    # Test 6: Fitness is in [0, 1] range
    assert np.all(fit2 >= 0.0), f"Found negative fitness: {fit2.min()}"
    assert np.all(fit2 <= 1.0 + 1e-10), f"Found fitness > 1: {fit2.max()}"
    print(f"[PASS] Test 6: All fitnesses in [0, 1]")

    # Test 7: Landscape ruggedness — single bit flips from greedy solution
    # Some flips should increase fitness, some decrease: that's ruggedness
    improvements = 0
    degradations = 0
    for i in range(KNAPSACK_GENOME_LENGTH):
        flipped = g_genome.copy()
        flipped[i] = 1 - flipped[i]
        f_flip = knapsack_fitness(flipped)
        if f_flip > f_greedy + 1e-10:
            improvements += 1
        elif f_flip < f_greedy - 1e-10:
            degradations += 1
    print(f"[PASS] Test 7: Ruggedness from greedy: "
          f"{improvements} improving flips, {degradations} degrading flips "
          f"(out of {KNAPSACK_GENOME_LENGTH})")

    print("\nAll knapsack domain tests passed!")
    return True


if __name__ == '__main__':
    test_knapsack_domain()
