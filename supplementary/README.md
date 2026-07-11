# Supplementary Material: Composition Determines Diversity

## Contents

### `experiments/`
Raw CSV data and Python scripts for all experiments.

**Data** (5 topologies x 30 seeds x 100 generations each):

| File | Domain | Genome |
|------|--------|--------|
| `experiment_e_raw.csv` | OneMax | 50-bit binary |
| `experiment_e_maze.csv` | Maze (6x6) | 60-bit binary |
| `experiment_e_graph_coloring.csv` | Graph Coloring | 40-bit binary |
| `experiment_e_knapsack.csv` | Knapsack | 50-bit binary |
| `experiment_e_nothanks.csv` | No Thanks! | 13-float continuous |
| `experiment_e_checkers.csv` | Checkers | 64-bit binary |
| `experiment_e_sorting_network.csv` | Sorting Network | 28-bit binary |

CSV schema: `topology, seed, generation, hamming_diversity, population_divergence, best_fitness, ...`

**Domain sweep scripts** (generate the CSVs from scratch):
- `onemax_stats.py`, `maze_domain.py`, `graph_coloring_domain.py`, `knapsack_domain.py`, `nothanks_domain.py`, `checkers_domain.py`, `sorting_network_domain.py`

**Analysis scripts** (consume the CSVs):
- `multi_domain_analysis.py` -- Figure 1: topology ordering, Kendall's W, variance decomposition
- `strategy_fingerprints.py` -- Figure 2: diversity fingerprints (self-contained, no CSV needed)
- `plot_fingerprints.py`, `plot_multi_domain.py` -- Additional plots
- `coupling_onset_analysis.py`, `early_convergence_analysis.py` -- Coupling onset timing
- `test_onemax.py` -- Unit tests for OneMax GA operators

### `haskell-framework/`
The categorical evolution framework in Haskell (`categorical-evolution` library).

Key modules:
- `src/Evolution/Category.hs` -- Kleisli category and monad stack
- `src/Evolution/Operators.hs` -- GA operators as Kleisli morphisms
- `src/Evolution/Pipeline.hs` -- Pipeline composition (>>>:)
- `src/Evolution/Strategy.hs` -- Strategy combinators
- `src/Evolution/Island.hs` -- Island functor with migration topologies

## Reproducing Results

### Dependencies
```bash
pip install numpy scipy pandas matplotlib
```

### Figure 1: Topology ordering (uses pre-computed CSVs)
```bash
cd experiments
python3 multi_domain_analysis.py
```

### Figure 2: Strategy fingerprints (self-contained)
```bash
cd experiments
python3 strategy_fingerprints.py
```

### Re-running domain sweeps from scratch (~70 min total)
```bash
cd experiments
python3 onemax_stats.py          # ~5 min
python3 maze_domain.py           # ~10 min
python3 graph_coloring_domain.py # ~5 min
python3 knapsack_domain.py       # ~5 min
python3 nothanks_domain.py       # ~15 min
python3 checkers_domain.py       # ~30 min
```
