{-# LANGUAGE ScopedTypeVariables #-}

-- | Competitive coevolution: two populations that evaluate against each other.
--
-- == Categorical interpretation
--
-- In standard evolution, fitness is a function @a -> Double@ — a morphism
-- from the genome type to the fitness type. In competitive coevolution,
-- fitness depends on the /other/ population: it's a functor from one
-- population's category to another's evaluation context.
--
-- Concretely:
--   * Population A's fitness depends on population B (and vice versa)
--   * @compete :: a -> b -> Double@ defines pairwise outcomes
--   * Each individual's fitness is computed by playing against a sample
--     from the opposing population
--
-- This is the same structure as our virtual-creatures arena tournaments:
-- creatures don't have intrinsic fitness, only /relative/ fitness against
-- opponents. Intransitive dynamics (A beats B, B beats C, C beats A) emerge
-- naturally from this structure.
--
-- == Type conventions
--
-- @evaluateAgainst@ and @roundRobin@ are generic over individual types.
-- @coevolve@ works specifically with list-based genomes @[a]@, @[b]@
-- so that crossover and mutation operators compose correctly.
module Evolution.Coevolution
  ( -- * Types
    CompetitiveResult(..)
  , CoevoConfig(..)
  , defaultCoevoConfig
    -- * Core
  , coevolve
  , evaluateAgainst
    -- * Utilities
  , roundRobin
  ) where

import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import System.Random

import Evolution.Category
import Evolution.Effects
import Evolution.Operators

-- | Configuration for coevolution.
data CoevoConfig = CoevoConfig
  { opponentSampleSize :: !Int    -- ^ How many opponents to evaluate against
  } deriving (Show, Eq)

-- | Sensible defaults.
defaultCoevoConfig :: CoevoConfig
defaultCoevoConfig = CoevoConfig
  { opponentSampleSize = 10
  }

-- | Result of a coevolutionary run.
data CompetitiveResult a b = CompetitiveResult
  { bestA        :: !a
  , bestAFitness :: !Double
  , bestB        :: !b
  , bestBFitness :: !Double
  , finalPopA    :: ![a]
  , finalPopB    :: ![b]
  , coevoLog     :: !GALog
  , coevoFinalGen :: !StdGen
  } deriving (Show)

-- | Evaluate a population against a sample from an opponent pool.
-- Each individual plays against 'opponentSampleSize' opponents.
-- Generic over individual types.
evaluateAgainst :: forall a b. (a -> b -> Double)  -- ^ How A scores against B
                -> [b]                              -- ^ Opponent pool
                -> CoevoConfig
                -> GeneticOp EvoM a (Scored a)
evaluateAgainst compete opponents coevoCfg = liftMonadic $ \popA -> do
  mapM (\indA -> do
      opps <- sampleOpponents (opponentSampleSize coevoCfg) opponents
      let scores = map (compete indA) opps
          avgScore = sum scores / fromIntegral (length scores)
      return (Scored indA avgScore)
    ) popA
  where
    sampleOpponents :: Int -> [b] -> EvoM [b]
    sampleOpponents n pool
      | n >= length pool = return pool
      | otherwise = do
          shuffled <- shuffle pool
          return (take n shuffled)

-- | Round-robin evaluation: every individual plays every opponent.
-- More expensive but more accurate than sampling.
roundRobin :: (a -> b -> Double) -> [b] -> GeneticOp EvoM a (Scored a)
roundRobin compete opponents = pointwiseM $ \indA -> do
  let scores = map (compete indA) opponents
      avgScore = sum scores / fromIntegral (length scores)
  return (Scored indA avgScore)

-- | Run competitive coevolution between two populations of list-based genomes.
--
-- Type parameters @a@ and @b@ are /gene/ types.
-- Genomes are @[a]@ and @[b]@; populations are @[[a]]@ and @[[b]]@.
--
-- Both populations evolve simultaneously, with fitness determined by
-- competition against the other population. This creates an evolutionary
-- arms race.
coevolve :: forall a b.
            ([a] -> [b] -> Double)  -- ^ How genome A scores against genome B
         -> ([b] -> [a] -> Double)  -- ^ How genome B scores against genome A
         -> (a -> EvoM a)           -- ^ Per-gene mutation for A
         -> (b -> EvoM b)           -- ^ Per-gene mutation for B
         -> CoevoConfig
         -> GAConfig
         -> StdGen
         -> [[a]]                   -- ^ Initial population A (list of genomes)
         -> [[b]]                   -- ^ Initial population B (list of genomes)
         -> CompetitiveResult [a] [b]
coevolve competeAB competeBA mutA mutB coevoCfg config gen0 initA initB =
  let maxGen = maxGenerations config
      (final, gen', log') = runEvoM config gen0 (go 0 maxGen initA initB)
      (finalA, finalB) = final
      -- Score final populations against each other
      scoredA = map (\a -> Scored a (avgAgainst competeAB a finalB)) finalA
      scoredB = map (\b -> Scored b (avgAgainst competeBA b finalA)) finalB
      bA = head $ sortBy (comparing (Down . fitness)) scoredA
      bB = head $ sortBy (comparing (Down . fitness)) scoredB
  in CompetitiveResult
      { bestA        = individual bA
      , bestAFitness = fitness bA
      , bestB        = individual bB
      , bestBFitness = fitness bB
      , finalPopA    = finalA
      , finalPopB    = finalB
      , coevoLog     = log'
      , coevoFinalGen = gen'
      }
  where
    avgAgainst :: (x -> y -> Double) -> x -> [y] -> Double
    avgAgainst f x ys = sum (map (f x) ys) / fromIntegral (length ys)

    go :: Int -> Int -> [[a]] -> [[b]] -> EvoM ([[a]], [[b]])
    go gen maxG popA popB
      | gen >= maxG = return (popA, popB)
      | otherwise = do
          -- Evaluate A against B, then select/crossover/mutate
          let evalA = evaluateAgainst competeAB popB coevoCfg
              pipeA = evalA
                        >>>: logGeneration gen
                        >>>: elitistSelect
                        >>>: onePointCrossover
                        >>>: pointMutate mutA
                        >>>: pointwise individual
          popA' <- runOp pipeA popA
          -- Evaluate B against the new A, then select/crossover/mutate
          let evalB = evaluateAgainst competeBA popA' coevoCfg
              pipeB = evalB
                        >>>: elitistSelect
                        >>>: onePointCrossover
                        >>>: pointMutate mutB
                        >>>: pointwise individual
          popB' <- runOp pipeB popB
          go (gen + 1) maxG popA' popB'
