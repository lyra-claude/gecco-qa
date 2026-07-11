{-# LANGUAGE ScopedTypeVariables #-}

-- | Fitness landscape analysis via random walk.
--
-- This module provides tools for characterizing fitness landscapes before
-- running evolution. The key insight: landscape structure determines which
-- evolutionary strategy will perform best.
--
-- A random walk through the landscape reveals:
--
--   * 'ruggedness' — how much fitness varies between neighbors (autocorrelation)
--   * 'correlationLen' — how far apart points can be and still have correlated fitness
--   * 'neutrality' — fraction of mutations that don't change fitness
--   * 'localOptima' — how many peaks the walk encounters
--
-- These metrics inform 'recommendStrategy', which auto-selects a strategy
-- from "Evolution.Strategy" based on the landscape profile. This closes the
-- loop: analyze → decide → execute, all composable.
--
-- == Connection to category theory
--
-- The landscape profile is a /functor/ from the category of fitness functions
-- to the category of strategies. Given a morphism @f : Genome -> Double@,
-- 'analyzeLandscape' produces a 'LandscapeProfile', and 'recommendStrategy'
-- maps that profile to a 'Strategy'. The composition
-- @recommendStrategy . analyzeLandscape@ is a functor from fitness functions
-- to algorithms.
module Evolution.Landscape
  ( -- * Landscape profile
    LandscapeProfile(..)
    -- * Analysis
  , analyzeLandscape
  , randomWalk
    -- * Mutation helpers
  , singlePointMutation
    -- * Strategy recommendation
  , recommendStrategy
  ) where

import Evolution.Effects
import Evolution.Strategy

-- | Profile of a fitness landscape computed via random walk.
data LandscapeProfile = LandscapeProfile
  { ruggedness     :: !Double  -- ^ 1 - autocorrelation(1). 0 = smooth, 1 = maximally rugged.
  , correlationLen :: !Double  -- ^ Correlation length: -1/ln(r1). Distance over which fitness
                               --   values remain correlated. Large = smooth, small = rugged.
  , neutrality     :: !Double  -- ^ Fraction of steps where |delta fitness| < 1% of range.
  , localOptima    :: !Int     -- ^ Number of local fitness peaks encountered in the walk.
  , fitnessRange   :: !Double  -- ^ Observed fitness range (max - min).
  } deriving (Show, Eq)

-- | Perform a random walk through the fitness landscape.
--
-- Starting from a given point, repeatedly apply the mutation function
-- and record the fitness at each step. Returns the fitness trace.
--
-- The mutation function should be a /single-step/ mutation (e.g., flip
-- one random bit). Use 'singlePointMutation' to lift a per-gene mutator
-- to a single-point genome mutator.
randomWalk :: forall a. (a -> Double)  -- ^ Fitness function
           -> (a -> EvoM a)           -- ^ Single-step genome mutation
           -> a                       -- ^ Starting point
           -> Int                     -- ^ Number of steps
           -> EvoM [Double]           -- ^ Fitness trace
randomWalk fitFunc mutFunc start steps = do
  let f0 = fitFunc start
  go steps start [f0]
  where
    go :: Int -> a -> [Double] -> EvoM [Double]
    go 0 _ acc = return (reverse acc)
    go n x acc = do
      x' <- mutFunc x
      let f = fitFunc x'
      go (n - 1) x' (f : acc)

-- | Analyze a fitness landscape via random walk.
--
-- Performs a random walk of the given length, then computes landscape
-- metrics from the fitness trace.
--
-- Recommended walk length: at least 200 steps for reliable statistics.
analyzeLandscape :: (a -> Double)  -- ^ Fitness function
                 -> (a -> EvoM a) -- ^ Single-step genome mutation
                 -> a             -- ^ Starting point
                 -> Int           -- ^ Walk length (>= 200 recommended)
                 -> EvoM LandscapeProfile
analyzeLandscape fitFunc mutFunc start steps = do
  trace <- randomWalk fitFunc mutFunc start steps
  return (computeProfile trace)

-- | Compute landscape profile from a fitness trace.
computeProfile :: [Double] -> LandscapeProfile
computeProfile trace
  | length trace < 3 = LandscapeProfile 0 100 0 0 0
  | otherwise =
  let n = length trace
      mean = sum trace / fromIntegral n
      variance = sum (map (\x -> (x - mean) ^ (2 :: Int)) trace) / fromIntegral n

      -- Lag-1 autocorrelation: measures fitness correlation between neighbors
      pairs = zip trace (Prelude.drop 1 trace)
      cov1 = sum (map (\(x, y) -> (x - mean) * (y - mean)) pairs)
             / fromIntegral (n - 1)
      r1 = if variance > 1e-12 then cov1 / variance else 1.0

      -- Ruggedness = 1 - autocorrelation(1)
      -- 0 = perfectly smooth (all neighbors correlated)
      -- 1 = maximally rugged (no correlation)
      rug = max 0 (min 1 (1 - r1))

      -- Correlation length: how far apart can points be and still correlate?
      -- τ = -1/ln(r1), but clamp for edge cases
      corLen = if r1 > 0.01 && r1 < 0.99
               then -1.0 / log r1
               else if r1 >= 0.99 then 100.0  -- very smooth
               else 0.1                       -- very rugged

      -- Neutrality: fraction of steps with negligible fitness change
      fMax = maximum trace
      fMin = minimum trace
      range' = fMax - fMin
      epsilon = if range' > 0 then range' * 0.01 else 0.001  -- 1% of range
      deltas = map (\(a, b) -> abs (b - a)) pairs
      neutralCount = length (filter (< epsilon) deltas)
      neutral = fromIntegral neutralCount / fromIntegral (length deltas)

      -- Local optima: count peaks in the fitness trace
      -- A peak is where f(i-1) < f(i) > f(i+1)
      triples = zip3 trace (Prelude.drop 1 trace) (Prelude.drop 2 trace)
      peaks = length $ filter (\(a, b, c) -> b > a && b > c) triples

  in LandscapeProfile rug corLen neutral peaks range'

-- | Single-point mutation: mutate exactly one random gene in a list-based genome.
--
-- Lifts a per-gene mutation function (like 'Evolution.Examples.BitString.bitFlip')
-- to a genome-level mutation that changes a single random position.
-- This is the right mutation for landscape analysis, where we want
-- minimal perturbation at each step.
singlePointMutation :: (a -> EvoM a) -> [a] -> EvoM [a]
singlePointMutation mutFunc genome = do
  let n = length genome
  i <- randomInt 0 (n - 1)
  let (before, rest) = splitAt i genome
  case rest of
    []     -> return genome  -- shouldn't happen if n > 0
    (x:xs) -> do
      x' <- mutFunc x
      return (before ++ (x' : xs))

-- | Recommend a strategy based on landscape analysis.
--
-- Maps landscape profile to strategy selection:
--
--   * Smooth landscape (ruggedness < 0.3): generational GA — gradient-like
--     search works well on smooth landscapes.
--
--   * Rugged landscape (ruggedness > 0.7): race generational vs steady-state —
--     hedge your bets on rugged terrain.
--
--   * Moderate ruggedness: steady-state GA — maintains more diversity,
--     better for multimodal landscapes.
--
--   * High neutrality (> 0.5): steady-state — neutral networks need
--     sustained exploration, not generational replacement.
recommendStrategy :: LandscapeProfile
                  -> ([a] -> Double)   -- ^ Fitness function (genome -> fitness)
                  -> (a -> EvoM a)     -- ^ Per-gene mutation
                  -> StopWhen          -- ^ Termination condition
                  -> Strategy [a]
recommendStrategy profile fitFunc mutFunc stop
  | neutrality profile > 0.5 =
      -- High neutrality: need sustained exploration
      steadyStateGA fitFunc mutFunc stop
  | ruggedness profile < 0.3 =
      -- Smooth: generational GA converges efficiently
      generationalGA fitFunc mutFunc stop
  | ruggedness profile > 0.7 =
      -- Very rugged: hedge with a race
      race (generationalGA fitFunc mutFunc stop)
           (steadyStateGA fitFunc mutFunc stop)
  | otherwise =
      -- Moderate: steady-state maintains diversity on multimodal landscapes
      steadyStateGA fitFunc mutFunc stop
