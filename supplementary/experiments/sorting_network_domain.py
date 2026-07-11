#!/usr/bin/env python3
"""
Sorting network domain for the multi-domain topology sweep.

A sorting network for N=8 inputs is a fixed sequence of compare-and-swap
operations. Each comparator (i,j) compares elements at positions i and j,
swapping them if out of order. A valid sorting network correctly sorts ALL
possible input permutations.

Genome encoding:
  - N = 8 inputs (standard benchmark size)
  - All C(8,2) = 28 possible comparator pairs, enumerated in a fixed order:
    (0,1), (0,2), ..., (0,7), (1,2), ..., (6,7)
  - Genome = binary string of length 28. Each bit indicates whether that
    comparator is active.

Fitness:
  - Test against all 2^8 = 256 possible binary input sequences (0/1 values)
  - For each input, apply all active comparators in order
  - Fitness = fraction of inputs correctly sorted (non-decreasing order)
  - Range: [0.0, 1.0] where 1.0 = perfect sorting network
"""

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_INPUTS = 8
SORTING_NETWORK_GENOME_LENGTH = N_INPUTS * (N_INPUTS - 1) // 2  # C(8,2) = 28

# Pre-compute the 28 comparator pairs in canonical order:
# (0,1), (0,2), ..., (0,7), (1,2), (1,3), ..., (6,7)
COMPARATOR_PAIRS = []
for i in range(N_INPUTS):
    for j in range(i + 1, N_INPUTS):
        COMPARATOR_PAIRS.append((i, j))
COMPARATOR_PAIRS = np.array(COMPARATOR_PAIRS, dtype=np.int32)  # shape (28, 2)

# Pre-compute all 2^8 = 256 test inputs as binary vectors
# Each row is one input sequence of 8 elements (0s and 1s)
NUM_TEST_INPUTS = 2 ** N_INPUTS  # 256
TEST_INPUTS = np.array(
    [[(v >> (N_INPUTS - 1 - bit)) & 1 for bit in range(N_INPUTS)]
     for v in range(NUM_TEST_INPUTS)],
    dtype=np.int8
)  # shape (256, 8)


# ---------------------------------------------------------------------------
# Core evaluation (vectorized)
# ---------------------------------------------------------------------------

def _apply_network_batch(test_inputs: np.ndarray, active_mask: np.ndarray) -> np.ndarray:
    """Apply a single sorting network to all test inputs.

    Args:
        test_inputs: shape (256, 8), dtype int8 — the 256 binary test vectors
        active_mask: shape (28,), dtype bool — which comparators are active

    Returns:
        outputs: shape (256, 8), dtype int8 — results after applying network
    """
    outputs = test_inputs.copy()
    # Get indices of active comparators
    active_indices = np.where(active_mask)[0]

    for idx in active_indices:
        i, j = COMPARATOR_PAIRS[idx]
        # Compare-and-swap: if outputs[:, i] > outputs[:, j], swap them
        # For binary values, swap when left=1 and right=0
        need_swap = outputs[:, i] > outputs[:, j]
        # Swap: use temporary to avoid aliasing
        tmp = outputs[need_swap, i].copy()
        outputs[need_swap, i] = outputs[need_swap, j]
        outputs[need_swap, j] = tmp

    return outputs


def _is_sorted_batch(outputs: np.ndarray) -> np.ndarray:
    """Check which outputs are in non-decreasing order.

    Args:
        outputs: shape (256, 8), dtype int8

    Returns:
        sorted_mask: shape (256,), dtype bool — True if that row is sorted
    """
    # Non-decreasing: outputs[:, k] <= outputs[:, k+1] for all k
    # Check all consecutive pairs at once
    diffs = outputs[:, 1:] - outputs[:, :-1]  # shape (256, 7)
    # Sorted if no negative diffs
    return np.all(diffs >= 0, axis=1)


def evaluate_sorting_network(pop: np.ndarray) -> np.ndarray:
    """Evaluate sorting network fitness for entire population.

    Args:
        pop: np.ndarray of shape (pop_size, 28), dtype int (0/1 binary)

    Returns:
        np.ndarray of shape (pop_size,), dtype float64
        Each value is the fraction of 256 test inputs correctly sorted.
    """
    pop_size = len(pop)
    fitnesses = np.empty(pop_size, dtype=np.float64)

    for ind_idx in range(pop_size):
        active_mask = pop[ind_idx].astype(bool)
        outputs = _apply_network_batch(TEST_INPUTS, active_mask)
        sorted_mask = _is_sorted_batch(outputs)
        fitnesses[ind_idx] = np.sum(sorted_mask) / NUM_TEST_INPUTS

    return fitnesses


# ---------------------------------------------------------------------------
# Population initialization
# ---------------------------------------------------------------------------

def random_sorting_network_population(rng, pop_size, genome_length=SORTING_NETWORK_GENOME_LENGTH):
    """Generate random population of sorting networks.

    Each individual is a binary vector of length 28 (one bit per comparator).
    Uses 50% activation probability — roughly half the comparators active.

    Args:
        rng: np.random.Generator
        pop_size: number of individuals
        genome_length: should be 28 (parameter for framework compatibility)

    Returns:
        np.ndarray of shape (pop_size, genome_length), dtype int8
    """
    return rng.integers(0, 2, size=(pop_size, genome_length), dtype=np.int8)


# ---------------------------------------------------------------------------
# Notes on encoding
# ---------------------------------------------------------------------------
#
# Our genome encoding activates a SUBSET of the 28 possible comparator pairs,
# applied in the fixed canonical order: (0,1), (0,2), ..., (0,7), (1,2), ..., (6,7).
#
# This canonical order is equivalent to SELECTION SORT:
#   - Pairs (0,1)...(0,7) bubble the global minimum to position 0
#   - Pairs (1,2)...(1,7) bubble the 2nd-smallest to position 1
#   - etc.
#
# With all 28 pairs active, the network sorts all inputs correctly (fitness 1.0).
# Each comparator is essential — removing any single one breaks correctness.
# This makes the fitness landscape non-trivial: the GA must discover that
# nearly all comparators need to be active, creating a "needle in haystack"
# pressure balanced by the many partial-credit inputs.


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_sorting_network_domain():
    """Self-tests for the sorting network domain."""
    print("Running sorting network domain tests...")

    # Test 1: Constants sanity
    assert SORTING_NETWORK_GENOME_LENGTH == 28, (
        f"Expected genome length 28, got {SORTING_NETWORK_GENOME_LENGTH}")
    assert len(COMPARATOR_PAIRS) == 28, (
        f"Expected 28 comparator pairs, got {len(COMPARATOR_PAIRS)}")
    assert TEST_INPUTS.shape == (256, 8), (
        f"Expected test inputs shape (256, 8), got {TEST_INPUTS.shape}")
    print("  [PASS] Test 1: Constants are correct (28 pairs, 256 test inputs)")

    # Test 2: Comparator pair ordering
    expected_first = (0, 1)
    expected_last = (6, 7)
    actual_first = tuple(COMPARATOR_PAIRS[0])
    actual_last = tuple(COMPARATOR_PAIRS[-1])
    assert actual_first == expected_first, (
        f"Expected first pair {expected_first}, got {actual_first}")
    assert actual_last == expected_last, (
        f"Expected last pair {expected_last}, got {actual_last}")
    print("  [PASS] Test 2: Comparator pair ordering is correct")

    # Test 3: Empty network (all zeros) — only sorted inputs should pass
    genome_empty = np.zeros(SORTING_NETWORK_GENOME_LENGTH, dtype=np.int8)
    pop_empty = genome_empty.reshape(1, -1)
    fit_empty = evaluate_sorting_network(pop_empty)
    # For binary inputs with 8 elements, number of already-sorted inputs:
    # A binary sequence is non-decreasing iff it's 0...01...1 (all 0s then all 1s)
    # That's 9 patterns: 00000000, 00000001, 00000011, ..., 01111111, 11111111
    expected_sorted_count = N_INPUTS + 1  # 9
    expected_empty_fitness = expected_sorted_count / NUM_TEST_INPUTS  # 9/256
    assert abs(fit_empty[0] - expected_empty_fitness) < 1e-10, (
        f"Empty network fitness: expected {expected_empty_fitness:.6f}, "
        f"got {fit_empty[0]:.6f}")
    print(f"  [PASS] Test 3: Empty network fitness = {fit_empty[0]:.6f} "
          f"(expected {expected_empty_fitness:.6f} = {expected_sorted_count}/256)")

    # Test 4: Selection sort network (all 28 pairs) — should sort perfectly
    genome_all_pairs = np.ones(SORTING_NETWORK_GENOME_LENGTH, dtype=np.int8)
    pop_all_pairs = genome_all_pairs.reshape(1, -1)
    fit_all_pairs = evaluate_sorting_network(pop_all_pairs)
    assert fit_all_pairs[0] == 1.0, (
        f"Selection sort (all pairs) fitness: expected 1.0, got {fit_all_pairs[0]:.6f}")
    print(f"  [PASS] Test 4: Selection sort (all 28 pairs) fitness = 1.0")

    # Test 5: Single comparator — should do better than empty
    genome_single = np.zeros(SORTING_NETWORK_GENOME_LENGTH, dtype=np.int8)
    genome_single[0] = 1  # activate comparator (0,1)
    pop_single = genome_single.reshape(1, -1)
    fit_single = evaluate_sorting_network(pop_single)
    assert fit_single[0] > fit_empty[0], (
        f"Single comparator ({fit_single[0]:.6f}) should beat "
        f"empty network ({fit_empty[0]:.6f})")
    print(f"  [PASS] Test 5: Single comparator (0,1) fitness = {fit_single[0]:.6f} "
          f"> empty {fit_empty[0]:.6f}")

    # Test 6: Removing any single comparator from all-28 breaks correctness
    # This validates the "every pair is essential" property of selection sort
    genome_full = np.ones(SORTING_NETWORK_GENOME_LENGTH, dtype=np.int8)
    all_essential = True
    for drop_idx in range(SORTING_NETWORK_GENOME_LENGTH):
        genome_dropped = genome_full.copy()
        genome_dropped[drop_idx] = 0
        pop_dropped = genome_dropped.reshape(1, -1)
        fit_dropped = evaluate_sorting_network(pop_dropped)
        if fit_dropped[0] == 1.0:
            all_essential = False
            break
    assert all_essential, (
        f"Comparator {drop_idx} is NOT essential — removing it still sorts all inputs")
    print(f"  [PASS] Test 6: All 28 comparators are essential (removing any one breaks sort)")

    # Test 7: Population evaluation
    rng = np.random.default_rng(42)
    pop = random_sorting_network_population(rng, 50)
    fitnesses = evaluate_sorting_network(pop)
    assert fitnesses.dtype == np.float64, f"Expected float64, got {fitnesses.dtype}"
    assert len(fitnesses) == 50, f"Expected 50 fitnesses, got {len(fitnesses)}"
    assert np.all(fitnesses >= 0.0), f"Found negative fitness: {fitnesses.min()}"
    assert np.all(fitnesses <= 1.0), f"Found fitness > 1: {fitnesses.max()}"
    mean_fit = float(np.mean(fitnesses))
    max_fit = float(np.max(fitnesses))
    print(f"  [PASS] Test 7: 50 random networks — mean fitness = {mean_fit:.4f}, "
          f"max = {max_fit:.4f}, all in [0,1]")

    # Test 8: Compare-and-swap correctness on a specific case
    # Network with only comparator (0,7): should swap if pos[0] > pos[7]
    genome_07 = np.zeros(SORTING_NETWORK_GENOME_LENGTH, dtype=np.int8)
    # (0,7) is the 7th comparator (index 6): (0,1)=0, (0,2)=1, ..., (0,7)=6
    genome_07[6] = 1
    pop_07 = genome_07.reshape(1, -1)
    # Input: 10000000 (decimal 128) -> after (0,7) swap: 00000001
    # That input is index 128 in TEST_INPUTS
    test_input = TEST_INPUTS[128].copy()  # should be [1,0,0,0,0,0,0,0]
    assert list(test_input) == [1, 0, 0, 0, 0, 0, 0, 0], (
        f"Expected [1,0,0,0,0,0,0,0], got {list(test_input)}")
    output = _apply_network_batch(test_input.reshape(1, -1), genome_07.astype(bool))
    assert list(output[0]) == [0, 0, 0, 0, 0, 0, 0, 1], (
        f"After (0,7) swap on [1,0,0,0,0,0,0,0]: expected [0,0,0,0,0,0,0,1], "
        f"got {list(output[0])}")
    print("  [PASS] Test 8: Compare-and-swap (0,7) on [1,0,0,0,0,0,0,0] = "
          "[0,0,0,0,0,0,0,1]")

    # Test 9: Performance benchmark
    import time
    rng2 = np.random.default_rng(99)
    pop_bench = random_sorting_network_population(rng2, 80)
    t0 = time.time()
    for _ in range(10):
        evaluate_sorting_network(pop_bench)
    t1 = time.time()
    eval_time = (t1 - t0) / 10
    evals_per_sec = 80 / eval_time
    print(f"  [INFO] Test 9: 80 individuals evaluated in {eval_time*1000:.1f}ms "
          f"({evals_per_sec:.0f} evals/sec)")

    print("\nAll sorting network domain tests passed!")
    return True


if __name__ == '__main__':
    test_sorting_network_domain()
