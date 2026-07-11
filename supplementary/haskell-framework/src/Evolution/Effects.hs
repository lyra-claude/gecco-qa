{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE GeneralizedNewtypeDeriving #-}
{-# OPTIONS_GHC -Wno-unused-top-binds #-}

-- | MTL effect stack for genetic algorithms.
--
-- This module defines the monadic context in which genetic operators execute.
-- Each effect corresponds to a capability that GA operators need:
--
--   * 'MonadReader' 'GAConfig' — read-only access to GA parameters
--   * 'MonadState'  'StdGen'   — randomness (state-threaded PRNG)
--   * 'MonadWriter' 'GALog'    — logging fitness statistics, diversity metrics
--
-- The connection to mtl's 'MonadSelect': selection in a GA is exactly
-- backtracking search with a ranking function (fitness). We implement
-- tournament selection, roulette selection, etc. as concrete instances of
-- the "choose the best according to a ranking" pattern.
--
-- The connection to mtl's 'MonadAccum': evolutionary history is accumulated
-- monoidal data — each generation appends its statistics to a running log.
-- 'MonadAccum' captures this pattern exactly: you can 'look' at history so
-- far and 'add' new entries.
module Evolution.Effects
  ( -- * Configuration
    GAConfig(..)
  , defaultConfig
    -- * Logging
  , GALog(..)
  , GenStats(..)
  , emptyLog
    -- * The evolution monad
  , EvoM
  , runEvoM
    -- * Random utilities
  , randomDouble
  , randomInt
  , shuffle
  , randomChoice
  ) where

import Control.Monad.Reader
import Control.Monad.State.Strict
import Control.Monad.Writer.Strict
import System.Random

-- | GA configuration parameters. Read-only during a run.
data GAConfig = GAConfig
  { populationSize   :: !Int      -- ^ Number of individuals
  , mutationRate     :: !Double   -- ^ Per-gene mutation probability
  , crossoverRate    :: !Double   -- ^ Probability of crossover vs cloning
  , tournamentSize   :: !Int      -- ^ Tournament selection pool size
  , eliteCount       :: !Int      -- ^ Number of elites preserved each generation
  , maxGenerations   :: !Int      -- ^ Maximum number of generations
  } deriving (Show, Eq)

-- | Sensible defaults.
defaultConfig :: GAConfig
defaultConfig = GAConfig
  { populationSize = 100
  , mutationRate   = 0.01
  , crossoverRate  = 0.7
  , tournamentSize = 3
  , eliteCount     = 2
  , maxGenerations = 100
  }

-- | Statistics for a single generation.
data GenStats = GenStats
  { genNumber    :: !Int
  , bestFitness  :: !Double
  , avgFitness   :: !Double
  , worstFitness :: !Double
  , diversity    :: !Double   -- ^ Population diversity (0-1)
  } deriving (Show, Eq)

-- | Accumulated log of evolutionary history.
-- A monoid: we accumulate generation stats over time.
newtype GALog = GALog { generations :: [GenStats] }
  deriving (Show, Eq)

instance Semigroup GALog where
  GALog a <> GALog b = GALog (a <> b)

instance Monoid GALog where
  mempty = GALog []

-- | An empty log.
emptyLog :: GALog
emptyLog = mempty

-- | The evolution monad: Reader for config, State for PRNG, Writer for logging.
--
-- This is the concrete monad stack that GeneticOp's execute in.
-- The stack order matters:
--   ReaderT config (StateT prng (Writer log)) a
-- Config is outermost (read-only), PRNG is threaded, log accumulates.
newtype EvoM a = EvoM
  { unEvoM :: ReaderT GAConfig (StateT StdGen (Writer GALog)) a
  } deriving (Functor, Applicative, Monad,
              MonadReader GAConfig,
              MonadState StdGen,
              MonadWriter GALog)

-- | Run an evolution computation.
runEvoM :: GAConfig -> StdGen -> EvoM a -> (a, StdGen, GALog)
runEvoM config gen (EvoM m) =
  let ((a, gen'), log') = runWriter (runStateT (runReaderT m config) gen)
  in (a, gen', log')

-- | Generate a random Double in [0, 1).
randomDouble :: EvoM Double
randomDouble = state (uniformR (0.0, 1.0))

-- | Generate a random Int in [lo, hi].
randomInt :: Int -> Int -> EvoM Int
randomInt lo hi = state (uniformR (lo, hi))

-- | Fisher-Yates shuffle.
shuffle :: [a] -> EvoM [a]
shuffle [] = return []
shuffle [x] = return [x]
shuffle xs = go (length xs - 1) xs
  where
    go 0 ys = return ys
    go i ys = do
      j <- randomInt 0 i
      let ys' = swapAt i j ys
      go (i - 1) ys'
    swapAt i j ys
      | i == j    = ys
      | otherwise =
          let vi = ys !! i
              vj = ys !! j
          in [ if k == i then vj
               else if k == j then vi
               else y
             | (k, y) <- zip [0..] ys
             ]

-- | Choose a random element from a list.
randomChoice :: [a] -> EvoM a
randomChoice [] = error "randomChoice: empty list"
randomChoice xs = do
  i <- randomInt 0 (length xs - 1)
  return (xs !! i)
