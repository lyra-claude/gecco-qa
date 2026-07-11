{-# LANGUAGE ScopedTypeVariables #-}

-- | Graph coloring evolution: color vertices of a random graph with minimum conflicts.
--
-- An Erdos-Renyi graph G(20, 0.3) with seed 42. Each vertex gets one of 4 colors,
-- encoded as 2 bits per vertex (40-bit genome). Fitness is the fraction of edges
-- whose endpoints have different colors.
--
-- == Cross-domain comparison
--
-- Same binary genome structure as BitString/Maze, but fitness depends on
-- graph-theoretic constraint satisfaction rather than counting bits or
-- solving a maze. The categorical pipeline is identical.
module Evolution.Examples.GraphColoring
  ( -- * Graph
    gcGraph
  , gcNumVertices
  , gcNumEdges
  , gcGenomeLength
    -- * GA integration
  , graphColoringFitness
  , graphColoringMutate
  , randomGraphColoring
  ) where

import Control.Monad (replicateM)
import Data.Bits ((.&.))

import Evolution.Effects

-- ---------------------------------------------------------------------------
-- Deterministic Erdos-Renyi graph G(20, 0.3) with seed 42
-- ---------------------------------------------------------------------------

-- | Number of vertices.
gcNumVertices :: Int
gcNumVertices = 20

-- | The edge list for G(20, 0.3) with seed 42.
-- Generated deterministically using a linear congruential generator.
gcGraph :: [(Int, Int)]
gcGraph = filter edgePresent allPairs
  where
    allPairs = [(i, j) | i <- [0 .. gcNumVertices - 2], j <- [i + 1 .. gcNumVertices - 1]]

    -- Simple LCG for deterministic edge generation
    -- Parameters from Numerical Recipes: a=1664525, c=1013904223, m=2^32
    lcgStream :: [Int]
    lcgStream = iterate lcgNext 42

    lcgNext :: Int -> Int
    lcgNext s = (1664525 * s + 1013904223) .&. 0xFFFFFFFF

    -- One LCG value per potential edge
    edgePresent :: (Int, Int) -> Bool
    edgePresent (i, j) =
      let idx = edgeIndex i j
          val = lcgStream !! (idx + 1)  -- +1 to skip seed
          -- Threshold: 0.3 of the 32-bit range
          threshold = round (0.3 * 4294967296.0 :: Double) :: Int
      in val < threshold

    -- Map (i,j) pair to a sequential index
    edgeIndex :: Int -> Int -> Int
    edgeIndex i j = i * gcNumVertices - (i * (i + 1)) `div` 2 + j - i - 1

-- | Number of edges in the graph.
gcNumEdges :: Int
gcNumEdges = length gcGraph

-- | Genome length: 2 bits per vertex, 4 colors.
gcGenomeLength :: Int
gcGenomeLength = 2 * gcNumVertices  -- 40 bits

-- ---------------------------------------------------------------------------
-- Fitness
-- ---------------------------------------------------------------------------

-- | Decode vertex color from genome (2 bits -> 0..3).
vertexColor :: [Bool] -> Int -> Int
vertexColor genome v =
  let b1 = if genome !! (2 * v)     then 1 else 0
      b0 = if genome !! (2 * v + 1) then 2 else 0
  in b1 + b0

-- | Count the number of violated edges (endpoints with same color).
violations :: [Bool] -> Int
violations genome =
  length [ ()
         | (i, j) <- gcGraph
         , vertexColor genome i == vertexColor genome j
         ]

-- | Fitness: 1 - violations / total_edges.
-- Perfect coloring = 1.0, all edges violated = 0.0.
graphColoringFitness :: [Bool] -> Double
graphColoringFitness genome
  | gcNumEdges == 0 = 1.0
  | otherwise =
      1.0 - fromIntegral (violations genome) / fromIntegral gcNumEdges

-- ---------------------------------------------------------------------------
-- GA integration
-- ---------------------------------------------------------------------------

-- | Mutation: flip a single bit.
-- Called by 'pointMutate' which handles the mutation rate.
graphColoringMutate :: Bool -> EvoM Bool
graphColoringMutate b = return (not b)

-- | Generate a random graph coloring genome (40 random bits).
randomGraphColoring :: EvoM [Bool]
randomGraphColoring = replicateM gcGenomeLength $ do
  r <- randomDouble
  return (r < 0.5)
