#!/usr/bin/env python3
"""
Graph coloring domain for the multi-domain topology sweep.

Given an undirected Erdos-Renyi random graph (N=20, p=0.3, seed=42) and
k=4 colors, evolve a coloring that minimizes constraint violations
(adjacent vertices sharing the same color).

The generated graph has chromatic number 4 (contains a 4-clique), so
k=4 is the minimum number of colors needed for a valid coloring.

Genome encoding:
  - 2 bits per vertex to encode color (00=0, 01=1, 10=2, 11=3)
  - Genome length = 2 * 20 = 40 bits
  - Binary string, compatible with one-point crossover and bit-flip mutation

Fitness:
  fitness = 1.0 - (violations / total_edges)
  Range: [0.0, 1.0] where 1.0 = valid coloring (no violations)
"""

import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NUM_VERTICES = 20
NUM_COLORS = 4
BITS_PER_VERTEX = 2
GRAPH_COLORING_GENOME_LENGTH = BITS_PER_VERTEX * NUM_VERTICES  # 40
EDGE_PROBABILITY = 0.3
GRAPH_SEED = 42


# ---------------------------------------------------------------------------
# Generate fixed graph instance (Erdos-Renyi G(n, p) with seed 42)
# ---------------------------------------------------------------------------

def _generate_graph(n: int, p: float, seed: int) -> tuple:
    """Generate a reproducible Erdos-Renyi random graph.

    Returns:
        edges: list of (i, j) tuples with i < j
        adj:   list of lists, adj[v] = list of neighbors of v
    """
    rng = np.random.default_rng(seed)
    edges = []
    adj = [[] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                edges.append((i, j))
                adj[i].append(j)
                adj[j].append(i)

    return edges, adj


# Module-level constants: generated once at import time
EDGES, ADJ = _generate_graph(NUM_VERTICES, EDGE_PROBABILITY, GRAPH_SEED)
NUM_EDGES = len(EDGES)

# Pre-compute edge arrays for vectorized evaluation
_EDGE_U = np.array([e[0] for e in EDGES], dtype=np.int32)
_EDGE_V = np.array([e[1] for e in EDGES], dtype=np.int32)


# ---------------------------------------------------------------------------
# Genome decoding
# ---------------------------------------------------------------------------

def decode_colors(pop: np.ndarray) -> np.ndarray:
    """Decode population genomes to vertex colors.

    Each vertex uses 2 bits: bit_high * 2 + bit_low.
    All 4 values (0, 1, 2, 3) are valid colors.

    Args:
        pop: np.ndarray of shape (pop_size, 40), dtype int (0/1 binary)

    Returns:
        np.ndarray of shape (pop_size, 20), dtype int, values in {0, 1, 2, 3}
    """
    pop_size = pop.shape[0]
    # Reshape to (pop_size, 20, 2): pairs of bits per vertex
    pairs = pop.reshape(pop_size, NUM_VERTICES, BITS_PER_VERTEX)
    # Decode: high_bit * 2 + low_bit
    colors = pairs[:, :, 0] * 2 + pairs[:, :, 1]
    return colors


# ---------------------------------------------------------------------------
# Fitness evaluation
# ---------------------------------------------------------------------------

def evaluate_graph_coloring(pop: np.ndarray) -> np.ndarray:
    """Evaluate graph coloring fitness for entire population.

    Counts constraint violations (edges where both endpoints share a color)
    and returns fitness = 1.0 - (violations / total_edges).

    Args:
        pop: np.ndarray of shape (pop_size, 40), dtype int (0/1 binary)

    Returns:
        np.ndarray of shape (pop_size,), dtype float64
    """
    if NUM_EDGES == 0:
        # Degenerate case: no edges means every coloring is valid
        return np.ones(pop.shape[0], dtype=np.float64)

    colors = decode_colors(pop)  # (pop_size, 20)

    # Vectorized violation counting:
    # For each edge (u, v), check if colors[:, u] == colors[:, v]
    color_u = colors[:, _EDGE_U]  # (pop_size, num_edges)
    color_v = colors[:, _EDGE_V]  # (pop_size, num_edges)
    violations = np.sum(color_u == color_v, axis=1)  # (pop_size,)

    fitness = 1.0 - (violations.astype(np.float64) / NUM_EDGES)
    return fitness


# ---------------------------------------------------------------------------
# Population initialization
# ---------------------------------------------------------------------------

def random_graph_coloring_population(rng, pop_size,
                                     genome_length=GRAPH_COLORING_GENOME_LENGTH):
    """Generate random population for graph coloring.

    Args:
        rng: np.random.Generator
        pop_size: number of individuals
        genome_length: should be GRAPH_COLORING_GENOME_LENGTH (40)

    Returns:
        np.ndarray of shape (pop_size, genome_length), dtype int8
    """
    return rng.integers(0, 2, size=(pop_size, genome_length), dtype=np.int8)


# ---------------------------------------------------------------------------
# Greedy coloring (for testing / finding a valid coloring)
# ---------------------------------------------------------------------------

def greedy_coloring() -> np.ndarray:
    """Find a valid coloring using a greedy algorithm with multiple orderings.

    Tries the natural order first, then largest-degree-first, then random
    permutations until a valid k-coloring is found.

    Returns:
        np.ndarray of shape (40,), dtype int8 — a genome encoding a valid coloring,
        or None if no valid coloring found after all attempts.
    """
    def _try_ordering(order):
        colors = [-1] * NUM_VERTICES
        for v in order:
            used = set()
            for u in ADJ[v]:
                if colors[u] != -1:
                    used.add(colors[u])
            for c in range(NUM_COLORS):
                if c not in used:
                    colors[v] = c
                    break
            else:
                return None
        return colors

    # Try natural order
    result = _try_ordering(range(NUM_VERTICES))

    # Try largest-degree-first (Welsh-Powell)
    if result is None:
        order = sorted(range(NUM_VERTICES), key=lambda v: len(ADJ[v]), reverse=True)
        result = _try_ordering(order)

    # Try random permutations
    if result is None:
        rng = np.random.default_rng(0)
        for _ in range(1000):
            order = rng.permutation(NUM_VERTICES)
            result = _try_ordering(order)
            if result is not None:
                break

    if result is None:
        return None

    # Encode as genome
    genome = np.zeros(GRAPH_COLORING_GENOME_LENGTH, dtype=np.int8)
    for v in range(NUM_VERTICES):
        c = result[v]
        # Encode color c as 2 bits: high_bit = c // 2, low_bit = c % 2
        genome[v * 2] = c // 2
        genome[v * 2 + 1] = c % 2

    return genome


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def test_graph_coloring_domain():
    """Self-tests for the graph coloring domain."""
    print("=" * 60)
    print("Graph Coloring Domain — Self-Test")
    print("=" * 60)

    # Print graph statistics
    print(f"\nGraph: N={NUM_VERTICES} vertices, {NUM_EDGES} edges")
    print(f"Edge probability: p={EDGE_PROBABILITY}, seed={GRAPH_SEED}")
    print(f"Colors: k={NUM_COLORS}")
    print(f"Genome length: {GRAPH_COLORING_GENOME_LENGTH} bits")
    print(f"\nDegree distribution:")
    degrees = [len(ADJ[v]) for v in range(NUM_VERTICES)]
    print(f"  min={min(degrees)}, max={max(degrees)}, "
          f"mean={np.mean(degrees):.1f}, median={np.median(degrees):.1f}")
    print(f"\nEdge list ({NUM_EDGES} edges):")
    for i, (u, v) in enumerate(EDGES):
        end = "\n" if (i + 1) % 8 == 0 else "  "
        print(f"  ({u:2d},{v:2d})", end=end)
    if NUM_EDGES % 8 != 0:
        print()

    # Test 1: Random population evaluation
    print("\n--- Test 1: Random population ---")
    rng = np.random.default_rng(123)
    pop = random_graph_coloring_population(rng, 100)
    fitnesses = evaluate_graph_coloring(pop)
    assert fitnesses.dtype == np.float64, f"Expected float64, got {fitnesses.dtype}"
    assert len(fitnesses) == 100, f"Expected 100 fitnesses, got {len(fitnesses)}"
    assert np.all(fitnesses >= 0.0), f"Found negative fitness: {fitnesses.min()}"
    assert np.all(fitnesses <= 1.0), f"Found fitness > 1: {fitnesses.max()}"
    print(f"  100 random individuals: fitness range [{fitnesses.min():.4f}, {fitnesses.max():.4f}]")
    print(f"  Mean fitness: {fitnesses.mean():.4f}")
    print(f"  [PASS] All fitnesses in [0, 1]")

    # Test 2: Greedy valid coloring
    print("\n--- Test 2: Greedy valid coloring ---")
    valid_genome = greedy_coloring()
    if valid_genome is not None:
        valid_fitness = evaluate_graph_coloring(valid_genome.reshape(1, -1))
        colors = decode_colors(valid_genome.reshape(1, -1))[0]
        print(f"  Greedy coloring: {colors.tolist()}")
        print(f"  Fitness: {valid_fitness[0]:.4f}")
        assert valid_fitness[0] == 1.0, (
            f"Valid coloring should have fitness 1.0, got {valid_fitness[0]}"
        )
        print(f"  [PASS] Valid coloring achieves fitness 1.0")
    else:
        print(f"  [SKIP] Greedy coloring failed with k={NUM_COLORS} colors")

    # Test 3: All same color (worst case)
    print("\n--- Test 3: All same color (worst case) ---")
    # All vertices color 0: genome = all zeros
    mono_genome = np.zeros(GRAPH_COLORING_GENOME_LENGTH, dtype=np.int8)
    mono_fitness = evaluate_graph_coloring(mono_genome.reshape(1, -1))
    mono_colors = decode_colors(mono_genome.reshape(1, -1))[0]
    violations = NUM_EDGES  # every edge is violated when all same color
    expected_fitness = 1.0 - (violations / NUM_EDGES)
    print(f"  Monochromatic coloring (all color 0)")
    print(f"  Violations: {violations}/{NUM_EDGES} edges")
    print(f"  Fitness: {mono_fitness[0]:.4f} (expected {expected_fitness:.4f})")
    assert mono_fitness[0] == expected_fitness, (
        f"Expected fitness {expected_fitness}, got {mono_fitness[0]}"
    )
    print(f"  [PASS] Monochromatic coloring has fitness 0.0")

    # Test 4: Decode correctness
    print("\n--- Test 4: Decode correctness ---")
    # Manually encode: vertex 0=color 2 (bits 10), vertex 1=color 1 (bits 01)
    test_genome = np.zeros(GRAPH_COLORING_GENOME_LENGTH, dtype=np.int8)
    test_genome[0] = 1  # vertex 0 high bit
    test_genome[1] = 0  # vertex 0 low bit -> color 2
    test_genome[2] = 0  # vertex 1 high bit
    test_genome[3] = 1  # vertex 1 low bit -> color 1
    # Bit pattern 11 -> value 3 (valid color with k=4)
    test_genome[4] = 1  # vertex 2 high bit
    test_genome[5] = 1  # vertex 2 low bit -> color 3
    colors = decode_colors(test_genome.reshape(1, -1))[0]
    assert colors[0] == 2, f"Vertex 0: expected color 2, got {colors[0]}"
    assert colors[1] == 1, f"Vertex 1: expected color 1, got {colors[1]}"
    assert colors[2] == 3, f"Vertex 2: expected color 3, got {colors[2]}"
    print(f"  Vertex 0 (bits 10) -> color {colors[0]} (expected 2)")
    print(f"  Vertex 1 (bits 01) -> color {colors[1]} (expected 1)")
    print(f"  Vertex 2 (bits 11) -> color {colors[2]} (expected 3)")
    print(f"  [PASS] Color decoding correct")

    # Test 5: Population shape and dtype
    print("\n--- Test 5: Population generation ---")
    rng2 = np.random.default_rng(99)
    pop2 = random_graph_coloring_population(rng2, 50)
    assert pop2.shape == (50, GRAPH_COLORING_GENOME_LENGTH), (
        f"Expected shape (50, {GRAPH_COLORING_GENOME_LENGTH}), got {pop2.shape}"
    )
    assert pop2.dtype == np.int8, f"Expected dtype int8, got {pop2.dtype}"
    assert set(np.unique(pop2)).issubset({0, 1}), "Population should contain only 0s and 1s"
    print(f"  Shape: {pop2.shape}, dtype: {pop2.dtype}")
    print(f"  Values: {set(np.unique(pop2))}")
    print(f"  [PASS] Population generation correct")

    print("\n" + "=" * 60)
    print("All graph coloring domain tests passed!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    test_graph_coloring_domain()
