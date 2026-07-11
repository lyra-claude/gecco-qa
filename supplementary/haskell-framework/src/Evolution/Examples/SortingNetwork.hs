{-# LANGUAGE ScopedTypeVariables #-}

-- | Sorting network evolution: discover networks that correctly sort 8 inputs.
--
-- A sorting network for n inputs is a sequence of comparators. Each comparator
-- takes two wires and swaps them if they are out of order. We use all C(8,2) = 28
-- potential comparator positions as a binary genome: bit i = 1 means comparator i
-- is active.
--
-- Fitness is the fraction of all 2^8 = 256 binary input patterns (0/1 on each wire)
-- that are correctly sorted by the network. By the 0-1 principle, a network that
-- sorts all binary sequences sorts all sequences.
--
-- == Cross-domain comparison
--
-- Another binary genome, but the fitness landscape is highly epistatic: the
-- contribution of each comparator depends on which others are present.
-- The categorical pipeline handles this identically to BitString or Knapsack.
module Evolution.Examples.SortingNetwork
  ( -- * Network parameters
    snNumInputs
  , snNumComparators
  , snGenomeLength
  , snComparatorPairs
    -- * GA integration
  , sortingNetworkFitness
  , sortingNetworkMutate
  , randomSortingNetwork
  ) where

import Control.Monad (replicateM)
import Data.Bits (testBit)
import Evolution.Effects

-- ---------------------------------------------------------------------------
-- Sorting network for 8 inputs
-- ---------------------------------------------------------------------------

-- | Number of input wires.
snNumInputs :: Int
snNumInputs = 8

-- | All C(8,2) = 28 possible comparator positions.
snComparatorPairs :: [(Int, Int)]
snComparatorPairs = [(i, j) | i <- [0 .. snNumInputs - 2], j <- [i + 1 .. snNumInputs - 1]]

-- | Number of comparators (genome length).
snNumComparators :: Int
snNumComparators = length snComparatorPairs  -- 28

-- | Genome length: one bit per comparator.
snGenomeLength :: Int
snGenomeLength = snNumComparators

-- ---------------------------------------------------------------------------
-- Network simulation
-- ---------------------------------------------------------------------------

-- | Apply a single comparator to a list of wires.
-- Swaps wires[i] and wires[j] if wires[i] > wires[j].
applyComparator :: (Int, Int) -> [Int] -> [Int]
applyComparator (i, j) wires
  | wi > wj   = setAt j wi (setAt i wj wires)
  | otherwise  = wires
  where
    wi = wires !! i
    wj = wires !! j

-- | Set element at index.
setAt :: Int -> a -> [a] -> [a]
setAt idx val xs = take idx xs ++ [val] ++ drop (idx + 1) xs

-- | Run a sorting network on an input sequence.
-- The genome determines which comparators are active.
runNetwork :: [Bool] -> [Int] -> [Int]
runNetwork genome input = foldl applyComp input activeComparators
  where
    activeComparators = [ pair
                        | (active, pair) <- zip genome snComparatorPairs
                        , active
                        ]
    applyComp wires pair = applyComparator pair wires

-- | Check if a list is sorted (non-decreasing).
isSorted :: [Int] -> Bool
isSorted [] = True
isSorted [_] = True
isSorted (x:y:rest) = x <= y && isSorted (y:rest)

-- ---------------------------------------------------------------------------
-- Fitness
-- ---------------------------------------------------------------------------

-- | All 256 binary input patterns for 8 wires.
allBinaryInputs :: [[Int]]
allBinaryInputs =
  [ [ if testBit n b then 1 else 0 | b <- [0 .. snNumInputs - 1] ]
  | n <- [0 .. (2 ^ snNumInputs - 1) :: Int]
  ]

-- | Fitness: fraction of all 2^8 binary inputs correctly sorted.
-- By the 0-1 principle, a network that sorts all binary sequences sorts everything.
sortingNetworkFitness :: [Bool] -> Double
sortingNetworkFitness genome =
  let results = map (isSorted . runNetwork genome) allBinaryInputs
      correct = length (filter id results)
      total = length allBinaryInputs  -- 256
  in fromIntegral correct / fromIntegral total

-- ---------------------------------------------------------------------------
-- GA integration
-- ---------------------------------------------------------------------------

-- | Mutation: flip a single bit (activate/deactivate comparator).
-- Called by 'pointMutate' which handles the mutation rate.
sortingNetworkMutate :: Bool -> EvoM Bool
sortingNetworkMutate b = return (not b)

-- | Generate a random sorting network genome (28 random bits).
-- Start with ~50% comparators active.
randomSortingNetwork :: EvoM [Bool]
randomSortingNetwork = replicateM snGenomeLength $ do
  r <- randomDouble
  return (r < 0.5)
