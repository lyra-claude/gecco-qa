{-# LANGUAGE ScopedTypeVariables #-}

-- | 0/1 Knapsack evolution: select items to maximize value under weight capacity.
--
-- 50 items with deterministic weights and values (seed 42, range [1,99]).
-- Binary genome: 50 bits, one per item. Capacity = 50% of total weight.
-- Feasible solutions get value/max_value; overweight solutions are penalized.
--
-- == Cross-domain comparison
--
-- Another binary-genome combinatorial optimization problem, but with a
-- hard constraint (capacity) that creates a rugged, deceptive landscape.
-- The categorical pipeline handles this identically to OneMax or GraphColoring.
module Evolution.Examples.Knapsack
  ( -- * Problem instance
    ksNumItems
  , ksWeights
  , ksValues
  , ksCapacity
  , ksGenomeLength
    -- * GA integration
  , knapsackFitness
  , knapsackMutate
  , randomKnapsack
  ) where

import Control.Monad (replicateM)
import Data.Bits ((.&.))

import Evolution.Effects

-- ---------------------------------------------------------------------------
-- Deterministic 0/1 Knapsack instance (50 items, seed 42)
-- ---------------------------------------------------------------------------

-- | Number of items.
ksNumItems :: Int
ksNumItems = 50

-- | Genome length (one bit per item).
ksGenomeLength :: Int
ksGenomeLength = ksNumItems

-- | Deterministic LCG stream starting from seed 42.
-- Parameters: a=1664525, c=1013904223, m=2^32
lcgStream :: [Int]
lcgStream = iterate lcgNext 42
  where
    lcgNext s = (1664525 * s + 1013904223) .&. 0xFFFFFFFF

-- | Map an LCG output to range [1, 99].
toRange :: Int -> Int
toRange x = (abs x `mod` 99) + 1

-- | Item weights, deterministically generated.
ksWeights :: [Int]
ksWeights = map toRange $ take ksNumItems (drop 1 lcgStream)

-- | Item values, deterministically generated (offset stream by numItems).
ksValues :: [Int]
ksValues = map toRange $ take ksNumItems (drop (ksNumItems + 1) lcgStream)

-- | Knapsack capacity: 50% of total weight.
ksCapacity :: Int
ksCapacity = sum ksWeights `div` 2

-- | Maximum possible value (all items included, ignoring weight).
ksMaxValue :: Int
ksMaxValue = sum ksValues

-- ---------------------------------------------------------------------------
-- Fitness
-- ---------------------------------------------------------------------------

-- | Total weight of selected items.
totalWeight :: [Bool] -> Int
totalWeight genome = sum [ w | (True, w) <- zip genome ksWeights ]

-- | Total value of selected items.
totalValue :: [Bool] -> Int
totalValue genome = sum [ v | (True, v) <- zip genome ksValues ]

-- | Fitness: value ratio if feasible, penalized if overweight.
-- Feasible: totalValue / maxValue (in [0, 1])
-- Overweight: max(0, valueRatio - 2 * overflow / capacity)
knapsackFitness :: [Bool] -> Double
knapsackFitness genome =
  let w = totalWeight genome
      v = totalValue genome
      valueRatio = fromIntegral v / fromIntegral ksMaxValue
      overflow = w - ksCapacity
  in if overflow <= 0
     then valueRatio
     else max 0.0 (valueRatio - 2.0 * fromIntegral overflow / fromIntegral ksCapacity)

-- ---------------------------------------------------------------------------
-- GA integration
-- ---------------------------------------------------------------------------

-- | Mutation: flip a single bit (include/exclude item).
-- Called by 'pointMutate' which handles the mutation rate.
knapsackMutate :: Bool -> EvoM Bool
knapsackMutate b = return (not b)

-- | Generate a random knapsack genome (50 random bits).
-- Start with ~30% inclusion rate to avoid too many overweight individuals.
randomKnapsack :: EvoM [Bool]
randomKnapsack = replicateM ksGenomeLength $ do
  r <- randomDouble
  return (r < 0.3)
