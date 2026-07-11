#!/usr/bin/env python3
"""
Maze domain for the multi-domain topology sweep.

A 6x6 grid maze is encoded as a 60-bit genome:
  - Bits 0-29:  horizontal walls (connecting cells vertically)
  - Bits 30-59: vertical walls (connecting cells horizontally)

Fitness rewards mazes that are solvable, have long shortest paths,
a moderate density of dead ends (~30%), and branching factor near 2.0.

Wall indexing matches the Haskell implementation in
  src/Evolution/Examples/Maze.hs
"""

import numpy as np
from collections import deque


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAZE_SIZE = 6
NUM_CELLS = MAZE_SIZE * MAZE_SIZE  # 36
MAZE_GENOME_LENGTH = 2 * MAZE_SIZE * (MAZE_SIZE - 1)  # 60
START_CELL = 0
GOAL_CELL = NUM_CELLS - 1  # 35


# ---------------------------------------------------------------------------
# Maze decoding
# ---------------------------------------------------------------------------

def decode_maze(genome: np.ndarray) -> list:
    """Decode a 60-bit genome into an adjacency list for 36 cells.

    Wall indexing (matches Haskell):
    - Horizontal walls (indices 0-29): Wall at index k connects cell at
      (k // MAZE_SIZE, k % MAZE_SIZE) DOWNWARD to
      (k // MAZE_SIZE + 1, k % MAZE_SIZE).
      genome[k] == 0 means NO wall (passage exists).

    - Vertical walls (indices 30-59): Wall at offset k' (genome index 30+k')
      connects cell at (k' // (MAZE_SIZE-1), k' % (MAZE_SIZE-1)) RIGHTWARD to
      (k' // (MAZE_SIZE-1), k' % (MAZE_SIZE-1) + 1).
      genome[30+k'] == 0 means NO wall (passage exists).

    Returns: list of 36 lists, where neighbors[c] is a list of accessible
    neighbor cell indices.
    """
    neighbors = [[] for _ in range(NUM_CELLS)]

    # Horizontal walls: indices 0 to 29
    # k ranges from 0 to (MAZE_SIZE - 1) * MAZE_SIZE - 1 = 29
    num_h_walls = (MAZE_SIZE - 1) * MAZE_SIZE  # 30
    for k in range(num_h_walls):
        row = k // MAZE_SIZE
        col = k % MAZE_SIZE
        cell_above = row * MAZE_SIZE + col
        cell_below = (row + 1) * MAZE_SIZE + col
        if genome[k] == 0:  # no wall = passage
            neighbors[cell_above].append(cell_below)
            neighbors[cell_below].append(cell_above)

    # Vertical walls: indices 30 to 59
    # k' ranges from 0 to MAZE_SIZE * (MAZE_SIZE - 1) - 1 = 29
    num_v_walls = MAZE_SIZE * (MAZE_SIZE - 1)  # 30
    for kp in range(num_v_walls):
        row = kp // (MAZE_SIZE - 1)
        col = kp % (MAZE_SIZE - 1)
        cell_left = row * MAZE_SIZE + col
        cell_right = row * MAZE_SIZE + col + 1
        if genome[30 + kp] == 0:  # no wall = passage
            neighbors[cell_left].append(cell_right)
            neighbors[cell_right].append(cell_left)

    return neighbors


# ---------------------------------------------------------------------------
# BFS solver
# ---------------------------------------------------------------------------

def bfs_solve(neighbors: list, start: int, goal: int) -> int | None:
    """Standard BFS. Returns shortest path length (edges) or None if unreachable."""
    if start == goal:
        return 0

    visited = set()
    visited.add(start)
    queue = deque()
    queue.append((start, 0))

    while queue:
        cell, dist = queue.popleft()
        for nb in neighbors[cell]:
            if nb == goal:
                return dist + 1
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, dist + 1))

    return None


# ---------------------------------------------------------------------------
# Fitness
# ---------------------------------------------------------------------------

def maze_fitness(genome: np.ndarray) -> float:
    """Three-component fitness for maze quality.

    fitness = 0.5 * sol_score + 0.3 * max(0, dead_end_score) + 0.2 * max(0, branch_score)

    Where:
    - sol_score = path_length / (NUM_CELLS - 1)  -- longer paths are better
    - dead_end_score = 1.0 - abs(dead_end_ratio - 0.3) * 2.0  -- peak at 30% dead ends
    - branch_score = 1.0 - abs(avg_branching - 2.0) / 2.0  -- peak at 2.0 avg neighbors
    """
    neighbors = decode_maze(genome)

    # Solvability and path length
    path_length = bfs_solve(neighbors, START_CELL, GOAL_CELL)
    if path_length is None:
        return 0.0

    sol_score = path_length / (NUM_CELLS - 1)  # max possible = 35

    # Dead ends: cells with exactly 1 neighbor
    num_dead_ends = sum(1 for c in range(NUM_CELLS) if len(neighbors[c]) == 1)
    dead_end_ratio = num_dead_ends / NUM_CELLS
    dead_end_score = 1.0 - abs(dead_end_ratio - 0.3) * 2.0

    # Branching factor: average number of neighbors
    total_neighbors = sum(len(neighbors[c]) for c in range(NUM_CELLS))
    avg_branching = total_neighbors / NUM_CELLS
    branch_score = 1.0 - abs(avg_branching - 2.0) / 2.0

    fitness = (0.5 * sol_score
               + 0.3 * max(0.0, dead_end_score)
               + 0.2 * max(0.0, branch_score))
    return float(fitness)


# ---------------------------------------------------------------------------
# Population-level functions
# ---------------------------------------------------------------------------

def evaluate_maze(pop: np.ndarray) -> np.ndarray:
    """Evaluate maze fitness for entire population. Returns 1D array of fitnesses."""
    return np.array([maze_fitness(pop[i]) for i in range(len(pop))])


def random_maze_population(rng, pop_size, genome_length=MAZE_GENOME_LENGTH):
    """Generate random maze population with 40% wall probability.

    A wall probability of 0.4 means ~60% of potential passages are open,
    producing mazes that are usually solvable but not trivially so.
    """
    return (rng.random(size=(pop_size, genome_length)) < 0.4).astype(np.int8)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_maze_domain():
    """Self-tests for the maze domain."""
    print("Running maze domain tests...")

    # Test 1: All zeros = no walls = fully open grid
    genome_open = np.zeros(MAZE_GENOME_LENGTH, dtype=np.int8)
    neighbors = decode_maze(genome_open)

    # Every interior cell should have 4 neighbors, edge cells 3, corners 2
    for r in range(MAZE_SIZE):
        for c in range(MAZE_SIZE):
            cell = r * MAZE_SIZE + c
            expected_neighbors = set()
            if r > 0:
                expected_neighbors.add((r - 1) * MAZE_SIZE + c)
            if r < MAZE_SIZE - 1:
                expected_neighbors.add((r + 1) * MAZE_SIZE + c)
            if c > 0:
                expected_neighbors.add(r * MAZE_SIZE + c - 1)
            if c < MAZE_SIZE - 1:
                expected_neighbors.add(r * MAZE_SIZE + c + 1)
            actual = set(neighbors[cell])
            assert actual == expected_neighbors, (
                f"Cell ({r},{c})={cell}: expected neighbors {expected_neighbors}, "
                f"got {actual}"
            )
    print("  [PASS] Test 1: All-zeros genome produces fully open grid")

    # Test 2: BFS on fully open grid
    # Shortest path from (0,0) to (5,5) = 5 + 5 = 10 edges
    path_len = bfs_solve(neighbors, START_CELL, GOAL_CELL)
    expected_path = (MAZE_SIZE - 1) + (MAZE_SIZE - 1)  # 10
    assert path_len == expected_path, (
        f"BFS on open grid: expected {expected_path}, got {path_len}"
    )
    print(f"  [PASS] Test 2: BFS on open grid = {path_len} (expected {expected_path})")

    # Test 3: All walls = unreachable = fitness 0
    genome_walls = np.ones(MAZE_GENOME_LENGTH, dtype=np.int8)
    fitness_walls = maze_fitness(genome_walls)
    assert fitness_walls == 0.0, (
        f"All-walls fitness: expected 0.0, got {fitness_walls}"
    )
    print(f"  [PASS] Test 3: All-walls fitness = {fitness_walls}")

    # Test 4: evaluate_maze on random population
    rng = np.random.default_rng(42)
    pop = random_maze_population(rng, 50)
    fitnesses = evaluate_maze(pop)
    assert fitnesses.dtype == np.float64, f"Expected float64, got {fitnesses.dtype}"
    assert len(fitnesses) == 50, f"Expected 50 fitnesses, got {len(fitnesses)}"
    assert np.all(fitnesses >= 0.0), f"Found negative fitness: {fitnesses.min()}"
    assert np.all(fitnesses <= 1.0), f"Found fitness > 1: {fitnesses.max()}"
    num_solvable = np.sum(fitnesses > 0.0)
    print(f"  [PASS] Test 4: evaluate_maze on 50 random mazes, "
          f"all in [0,1], {num_solvable}/50 solvable")

    # Test 5: Open maze fitness should be > 0
    fitness_open = maze_fitness(genome_open)
    assert fitness_open > 0.0, f"Open maze fitness should be > 0, got {fitness_open}"
    print(f"  [PASS] Test 5: Open maze fitness = {fitness_open:.4f}")

    print("\nAll maze domain tests passed!")
    return True


if __name__ == '__main__':
    test_maze_domain()
