# Haskell Categorical Framework

Proof-of-concept implementation of GA operators as Kleisli morphisms over the evolution monad `T = Reader(Γ) × Writer(Λ) × State(S)`.

This code establishes that the categorical structure described in the paper is not just notation — Haskell's type system enforces it. The experimental validation (6 domains, 30 seeds each) was done in Python (`../experiments/`) for performance reasons.

## Building

```bash
cabal build
cabal run categorical-evolution -- --demo maze-migration-sweep
```

## Key Modules

| Module | Role |
|--------|------|
| `Evolution.Category` | Core: `GeneticOp` type, Kleisli composition `(>>>:)` |
| `Evolution.Effects` | `EvoM` monad stack |
| `Evolution.Operators` | Selection, crossover, mutation, evaluation |
| `Evolution.Island` | Island functor with topology-parameterized migration |
| `Evolution.Strategy` | Composable multi-phase strategies |
| `Evolution.Examples.*` | OneMax, Maze, Checkers, GraphColoring, Knapsack, SortingNetwork |
