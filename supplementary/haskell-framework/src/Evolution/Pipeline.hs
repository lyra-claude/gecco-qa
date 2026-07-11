{-# LANGUAGE ScopedTypeVariables #-}

-- | Composable evolutionary pipelines.
--
-- This module provides the high-level interface for building and running
-- genetic algorithms by composing operators.
--
-- == The category-printf analogy
--
-- In category-printf:
--
-- @
--   let fmt = "Hello, " . i . "! You are " . s . " years old."
--   sprintf fmt "Alice" 30  -- "Hello, Alice! You are 30 years old."
-- @
--
-- Each piece (@"Hello, "@, @i@, @s@) is a morphism in the co-Kleisli category.
-- Composition (@.@) accumulates argument types: the final format spec
-- demands a String and an Int.
--
-- In categorical-evolution:
--
-- @
--   let pipeline = evaluate fitnessFunc
--                    >>>: elitistSelect
--                    >>>: onePointCrossover
--                    >>>: pointMutate bitFlip
--                    >>>: evaluate fitnessFunc
--   evolve pipeline config gen0 initialPop
-- @
--
-- Each piece is a morphism in the Kleisli category for 'EvoM'.
-- Composition (@>>>:@) accumulates effects: randomness, logging, selection.
-- The final pipeline is itself a single 'GeneticOp' — a closed morphism
-- that can be iterated.
module Evolution.Pipeline
  ( -- * Pipeline construction
    generationStep
    -- * Running evolution
  , evolve
  , evolveN
    -- * Result types
  , EvoResult(..)
  ) where

import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import System.Random

import Evolution.Category
import Evolution.Effects
import Evolution.Operators

-- | The result of an evolutionary run.
data EvoResult a = EvoResult
  { bestIndividual :: !a
  , bestFitness'   :: !Double
  , finalPop       :: ![Scored a]
  , evoLog         :: !GALog
  , finalGen       :: !StdGen
  } deriving (Show)

-- | Build a single generation step from a fitness function and a mutation operator.
--
-- This is the "default pipeline" — the most common configuration.
-- For custom pipelines, compose operators directly with '>>>:'.
generationStep :: ([a] -> Double)          -- ^ Fitness function (genome -> fitness)
               -> (a -> EvoM a)           -- ^ Per-gene mutation function
               -> Int                     -- ^ Generation number (for logging)
               -> GeneticOp EvoM [a] [a]  -- ^ One generation: [genome] -> [genome]
generationStep fitFunc mutFunc gen =
  -- Wrap genomes: [a] -> [Scored [a]]
  evaluate fitFunc
    >>>: logGeneration gen
    >>>: elitistSelect
    >>>: onePointCrossover
    >>>: pointMutate mutFunc
    -- Unwrap: [Scored [a]] -> [[a]]
    >>>: pointwise individual

-- | Run evolution for the configured number of generations.
evolve :: forall a. ([a] -> Double)      -- ^ Fitness function (genome -> fitness)
       -> (a -> EvoM a)                  -- ^ Per-gene mutation function
       -> GAConfig                       -- ^ Configuration
       -> StdGen                         -- ^ Initial PRNG
       -> [[a]]                          -- ^ Initial population (list of genomes)
       -> EvoResult [a]
evolve fitFunc mutFunc config gen0 initPop =
  let maxGen = maxGenerations config
      (result, gen', log') = runEvoM config gen0 $ go 0 maxGen initPop
      sorted = sortBy (comparing (Down . fitness)) (map (\g -> Scored g (fitFunc g)) result)
      best = head sorted
  in EvoResult
      { bestIndividual = individual best
      , bestFitness'   = fitness best
      , finalPop       = sorted
      , evoLog         = log'
      , finalGen       = gen'
      }
  where
    go :: Int -> Int -> [[a]] -> EvoM [[a]]
    go gen maxG pop
      | gen >= maxG = return pop
      | otherwise = do
          pop' <- runOp (generationStep fitFunc mutFunc gen) pop
          go (gen + 1) maxG pop'

-- | Run evolution for exactly n generations (ignoring maxGenerations in config).
evolveN :: forall a. Int                 -- ^ Number of generations
        -> ([a] -> Double)               -- ^ Fitness function (genome -> fitness)
        -> (a -> EvoM a)                 -- ^ Per-gene mutation function
        -> GAConfig                      -- ^ Configuration
        -> StdGen                        -- ^ Initial PRNG
        -> [[a]]                         -- ^ Initial population
        -> EvoResult [a]
evolveN n fitFunc mutFunc config gen0 initPop =
  let (result, gen', log') = runEvoM config gen0 $ go 0 n initPop
      sorted = sortBy (comparing (Down . fitness)) (map (\g -> Scored g (fitFunc g)) result)
      best = head sorted
  in EvoResult
      { bestIndividual = individual best
      , bestFitness'   = fitness best
      , finalPop       = sorted
      , evoLog         = log'
      , finalGen       = gen'
      }
  where
    go :: Int -> Int -> [[a]] -> EvoM [[a]]
    go gen maxG pop
      | gen >= maxG = return pop
      | otherwise = do
          pop' <- runOp (generationStep fitFunc mutFunc gen) pop
          go (gen + 1) maxG pop'
