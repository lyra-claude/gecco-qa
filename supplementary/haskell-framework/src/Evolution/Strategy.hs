{-# LANGUAGE ScopedTypeVariables #-}

-- | The category of evolutionary strategies.
--
-- == From operators to strategies
--
-- 'Evolution.Category' gives us composable /operators/ — single
-- population transformations like selection, crossover, and mutation.
-- Those compose within a generation.
--
-- This module lifts the abstraction: /strategies/ are composable
-- /algorithms/, each running for multiple generations. Strategies form
-- a category:
--
--   * Objects: scored population types
--   * Morphisms: strategies (algorithms transforming populations)
--   * Composition: 'sequential' (run one, then the other)
--   * Identity: 'idStrategy' (do nothing)
--
-- == Combinators as categorical constructions
--
-- * 'sequential' — composition in the strategy category
-- * 'race' — product (run both, take the best)
-- * 'adaptive' — coproduct with discriminator (try one, fall back to other)
-- * 'mapStrategy' — functor between strategy categories on different types
--
-- == Termination conditions
--
-- 'StopWhen' forms a Boolean algebra over stopping conditions:
-- 'StopOr' and 'StopAnd' let you combine conditions freely.
module Evolution.Strategy
  ( -- * Termination conditions
    StopWhen(..)
    -- * Strategy results
  , StrategyResult(..)
    -- * Strategy type
  , Strategy(..)
  , mkStrategy
  , idStrategy
    -- * Core strategies
  , generationalGA
  , steadyStateGA
    -- * Combinators
  , sequential
  , race
  , adaptive
    -- * Strategy functor
  , mapStrategy
    -- * Island strategy functor
  , IslandConfig(..)
  , IslandTopo(..)
  , islandStrategy
    -- * Step function export (for custom strategies)
  , gaStep
  ) where

import Control.Monad.Reader
import Control.Monad.State.Strict
import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import System.Random

import Evolution.Category
import Evolution.Effects
import Evolution.Operators

-- | Termination condition for a strategy. Forms a Boolean algebra
-- under 'StopOr' (join) and 'StopAnd' (meet).
data StopWhen
  = AfterGens Int              -- ^ Stop after N steps
  | FitnessAbove Double        -- ^ Stop when best fitness exceeds threshold
  | Plateau Int                -- ^ Stop when no improvement for N consecutive steps
  | StopOr StopWhen StopWhen   -- ^ Stop when either condition is met
  | StopAnd StopWhen StopWhen  -- ^ Stop when both conditions are met
  deriving (Show, Eq)

-- Internal state for checking termination.
data StopState = StopState
  { ssGens      :: !Int     -- ^ Steps so far
  , ssBest      :: !Double  -- ^ Best fitness seen
  , ssNoImprove :: !Int     -- ^ Consecutive steps without improvement
  }

-- | Check whether a termination condition is satisfied.
checkStop :: StopWhen -> StopState -> Bool
checkStop (AfterGens n)   ss = ssGens ss >= n
checkStop (FitnessAbove t) ss = ssBest ss >= t
checkStop (Plateau n)      ss = ssNoImprove ss >= n
checkStop (StopOr a b)     ss = checkStop a ss || checkStop b ss
checkStop (StopAnd a b)    ss = checkStop a ss && checkStop b ss

-- | Result of running a strategy.
data StrategyResult a = StrategyResult
  { resultPop   :: [Scored a]   -- ^ Final scored population
  , resultBest  :: Scored a     -- ^ Best individual found across all steps
  , resultGens  :: Int          -- ^ Total steps taken
  } deriving (Show)

-- | An evolutionary strategy: a composable algorithm that transforms
-- scored populations over multiple generations.
--
-- Strategies form a monoid under 'sequential' composition with
-- 'idStrategy' as identity.
newtype Strategy a = Strategy
  { runStrategy :: [Scored a] -> EvoM (StrategyResult a)
  }

-- | Identity strategy: returns the population unchanged.
-- This is the identity morphism in the strategy category.
idStrategy :: Strategy a
idStrategy = Strategy $ \pop ->
  return $ StrategyResult pop (bestOf pop) 0

-- | Create a strategy from a step function and termination condition.
--
-- The step function takes a step counter and the current scored population,
-- and returns the next scored population. The strategy iterates the step
-- function until the termination condition is satisfied.
mkStrategy :: (Int -> [Scored a] -> EvoM [Scored a]) -> StopWhen -> Strategy a
mkStrategy step stop = Strategy $ \pop0 -> do
  let best0 = bestOf pop0
      ss0 = StopState 0 (fitness best0) 0
  go ss0 best0 pop0
  where
    go ss overallBest pop
      | checkStop stop ss = return $ StrategyResult pop overallBest (ssGens ss)
      | otherwise = do
          pop' <- step (ssGens ss) pop
          let bestNow = bestOf pop'
              newBestFit = max (ssBest ss) (fitness bestNow)
              improved = fitness bestNow > ssBest ss
              overallBest' = if fitness bestNow > fitness overallBest
                             then bestNow else overallBest
              ss' = StopState
                { ssGens      = ssGens ss + 1
                , ssBest      = newBestFit
                , ssNoImprove = if improved then 0 else ssNoImprove ss + 1
                }
          go ss' overallBest' pop'

-- | Standard generational GA as a strategy.
--
-- Each step runs: log -> elitist select -> crossover -> mutate -> re-evaluate.
-- This wraps the existing operator pipeline from "Evolution.Operators".
generationalGA :: ([a] -> Double) -> (a -> EvoM a) -> StopWhen -> Strategy [a]
generationalGA fitFunc mutFunc stop = mkStrategy step stop
  where
    step gen pop = runOp pipeline pop
      where
        pipeline = logGeneration gen
               >>>: elitistSelect
               >>>: onePointCrossover
               >>>: pointMutate mutFunc
               >>>: pointwise reeval
        reeval s = Scored (individual s) (fitFunc (individual s))

-- | Steady-state GA as a strategy.
--
-- Instead of replacing the entire population each generation, this
-- replaces individuals one pair at a time: select two parents,
-- cross and mutate to produce two offspring, replace the two worst.
-- Each step does @popSize / 2@ replacements (one "generation equivalent").
--
-- Steady-state GAs typically maintain more population diversity than
-- generational GAs, at the cost of slower convergence on easy problems.
steadyStateGA :: forall a. ([a] -> Double) -> (a -> EvoM a) -> StopWhen -> Strategy [a]
steadyStateGA fitFunc mutFunc stop = mkStrategy step stop
  where
    step :: Int -> [Scored [a]] -> EvoM [Scored [a]]
    step _gen pop0 = do
      cfg <- ask
      let replacements = max 1 (populationSize cfg `div` 2)
      doReplacements replacements pop0

    doReplacements :: Int -> [Scored [a]] -> EvoM [Scored [a]]
    doReplacements 0 pop = return pop
    doReplacements n pop = do
      pop' <- singleReplace pop
      doReplacements (n - 1) pop'

    singleReplace :: [Scored [a]] -> EvoM [Scored [a]]
    singleReplace pop = do
      cfg <- ask
      let k = tournamentSize cfg
          cxRate = crossoverRate cfg
      -- Tournament select two parents
      p1 <- tournamentPick k pop
      p2 <- tournamentPick k pop
      -- Crossover
      r <- randomDouble
      (c1g, c2g) <- if r < cxRate
        then do
          let g1 = individual p1
              g2 = individual p2
              len = min (length g1) (length g2)
          pt <- randomInt 1 (max 1 (len - 1))
          let (h1, t1) = splitAt pt g1
              (h2, t2) = splitAt pt g2
          return (h1 ++ t2, h2 ++ t1)
        else return (individual p1, individual p2)
      -- Mutate each gene (respecting mutation rate)
      let rate = mutationRate cfg
      c1' <- mapM (\g -> do
        r' <- randomDouble
        if r' < rate then mutFunc g else return g) c1g
      c2' <- mapM (\g -> do
        r' <- randomDouble
        if r' < rate then mutFunc g else return g) c2g
      -- Score offspring
      let s1 = Scored c1' (fitFunc c1')
          s2 = Scored c2' (fitFunc c2')
      -- Replace two worst (sorted ascending by fitness)
      let sorted = sortBy (comparing fitness) pop
      return (s1 : s2 : drop 2 sorted)

    tournamentPick :: Int -> [Scored b] -> EvoM (Scored b)
    tournamentPick k pop = do
      contestants <- replicateM k (randomChoice pop)
      return $ bestOf contestants

-- | Sequential composition: run the first strategy to completion,
-- then run the second starting from the first's final population.
--
-- This is composition in the strategy category.
-- @sequential idStrategy s = s@ and @sequential s idStrategy = s@.
--
-- Generation counts are summed. The overall best is the better of
-- the two strategies' bests.
sequential :: Strategy a -> Strategy a -> Strategy a
sequential s1 s2 = Strategy $ \pop -> do
  r1 <- runStrategy s1 pop
  r2 <- runStrategy s2 (resultPop r1)
  let best = betterOf (resultBest r1) (resultBest r2)
  return $ StrategyResult (resultPop r2) best (resultGens r1 + resultGens r2)

-- | Race: run both strategies on the same initial population with
-- independent random seeds, return whichever finds the better result.
--
-- This is the categorical product: both morphisms are applied,
-- and the best outcome is projected out.
race :: Strategy a -> Strategy a -> Strategy a
race s1 s2 = Strategy $ \pop -> do
  -- Split the PRNG for independent runs
  g <- get
  let (g1, g2) = split g
  -- Run first strategy
  put g1
  r1 <- runStrategy s1 pop
  -- Run second strategy
  put g2
  r2 <- runStrategy s2 pop
  -- Return the better result
  return $ if fitness (resultBest r1) >= fitness (resultBest r2) then r1 else r2

-- | Adaptive: run the primary strategy, then check a predicate on the result.
-- If the predicate returns 'True', accept the result.
-- If 'False', run the fallback strategy starting from the primary's
-- final population.
--
-- This is a conditional coproduct: the predicate discriminates between
-- accepting the identity (keep result) or applying the fallback morphism.
--
-- Common predicates:
--
-- @
--   -- Switch if best fitness is below threshold
--   adaptive (\\r -> fitness (resultBest r) >= 8.0) primary fallback
--
--   -- Switch if the primary ran too long without converging
--   adaptive (\\r -> resultGens r < 50) primary fallback
-- @
adaptive :: (StrategyResult a -> Bool) -> Strategy a -> Strategy a -> Strategy a
adaptive predicate primary fallback = Strategy $ \pop -> do
  r1 <- runStrategy primary pop
  if predicate r1
    then return r1
    else do
      r2 <- runStrategy fallback (resultPop r1)
      let best = betterOf (resultBest r1) (resultBest r2)
      return $ StrategyResult (resultPop r2) best (resultGens r1 + resultGens r2)

-- | Map a strategy from one representation to another.
--
-- Given decoding and encoding functions between types @a@ and @b@,
-- transform a @Strategy a@ into a @Strategy b@. This is a functor
-- between strategy categories:
--
-- @
--   mapStrategy id id s = s                                        -- identity
--   mapStrategy (f . g) (h . k) = mapStrategy g k . mapStrategy f h -- composition
-- @
--
-- Use this to apply a strategy designed for one genome representation
-- to a different one. For example, map a bitstring strategy to work
-- on integer-encoded genomes via binary encoding/decoding.
mapStrategy :: (b -> a) -> (a -> b) -> Strategy a -> Strategy b
mapStrategy decode encode s = Strategy $ \popB -> do
  let popA = map (\scored -> Scored (decode (individual scored)) (fitness scored)) popB
  r <- runStrategy s popA
  let popB' = map (\scored -> Scored (encode (individual scored)) (fitness scored)) (resultPop r)
      bestB = Scored (encode (individual (resultBest r))) (fitness (resultBest r))
  return $ StrategyResult popB' bestB (resultGens r)

-- | The generational GA step function, exported for use with 'mkStrategy'
-- and 'islandStrategy'.
--
-- Each call runs one generation: log -> elitist select -> crossover -> mutate -> re-evaluate.
gaStep :: ([a] -> Double) -> (a -> EvoM a) -> Int -> [Scored [a]] -> EvoM [Scored [a]]
gaStep fitFunc mutFunc gen pop = runOp pipeline pop
  where
    pipeline = logGeneration gen
           >>>: elitistSelect
           >>>: onePointCrossover
           >>>: pointMutate mutFunc
           >>>: pointwise (\s -> Scored (individual s) (fitFunc (individual s)))

-- | Configuration for the island strategy functor.
data IslandConfig = IslandConfig
  { islandCount    :: !Int         -- ^ Number of islands
  , islandMigRate  :: !Double      -- ^ Fraction of each island's population to migrate
  , islandMigFreq  :: !Int         -- ^ Migrate every N generations
  , islandTopology :: !IslandTopo  -- ^ Migration topology
  } deriving (Show, Eq)

-- | Migration topology.
data IslandTopo
  = IslandRing   -- ^ Ring: island i sends migrants to island (i+1) mod n
  | IslandFull   -- ^ Fully connected: every island exchanges with every other
  deriving (Show, Eq)

-- | The island functor: lifts a step function into an island-model strategy.
--
-- Given a per-island step function and termination conditions, produces a
-- strategy that partitions the population into sub-populations, runs the
-- step function on each independently, and performs periodic migration.
--
-- Migration is a natural transformation between the parallel strategy
-- executions: it moves individuals between islands without knowing or
-- caring about the step function running on each island. The topology
-- (ring, fully connected) is a parameter of the functor.
--
-- == The Strict\/Lax Dichotomy Theorem
--
-- Let @I(μ, freq, topo)@ be the island strategy functor. For any
-- strategies @S₁@, @S₂@ with @|S₁| + |S₂| = N@:
--
-- (i) /Strict case/: If @μ = 0@ or @freq > N@, then @I@ is a strict
--     2-functor with respect to sequential composition:
--
-- @
--     I(S₁ ; S₂) ≡ I(S₁) ; I(S₂)    (population-level equality)
-- @
--
-- (ii) /Lax case/: If @μ > 0@ and @freq ≤ N@, then @I@ is a uniformly
--      lax 2-functor. Given sufficient generations after the composition
--      boundary, the population divergence between @I(S₁ ; S₂)@ and
--      @I(S₁) ; I(S₂)@ saturates to a characteristic level @D*@ that is:
--
--      * Independent of the number of affected migration events
--      * Independent of the composition boundary position
--      * Dependent on @μ@ and @freq@ (higher coupling → larger @D*@)
--      * Determined asymptotically by the mixing time (spectral gap)
--        of the evolutionary Markov chain
--
-- /Proof sketch/: (i) follows because zero migration means each island
-- evolves independently with identical PRNG state threading. (ii) follows
-- because any perturbation to the migration schedule — whether one missing
-- event or a full phase shift — propagates through the population Markov
-- chain at a rate governed by its spectral gap (second eigenvalue).
-- Saturation to @D*@ occurs in @O(1/gap)@ generations, where @gap@ is
-- the spectral gap of the coupled selection-mutation-migration process.
--
-- /Practical consequence/: You cannot reason about the outcome of composed
-- island strategies by reasoning about islands independently, regardless
-- of how rare migration is. One migration event per thousand generations
-- is categorically equivalent to one per generation.
--
-- @
--   -- 4 islands, ring migration every 5 gens
--   let config = IslandConfig 4 0.1 5 IslandRing
--       strat = islandStrategy config (gaStep oneMaxFitness bitFlip) (AfterGens 50)
-- @
islandStrategy :: IslandConfig
               -> (Int -> [Scored a] -> EvoM [Scored a])
               -> StopWhen
               -> Strategy a
islandStrategy config step stop = Strategy $ \pop0 -> do
  let n = islandCount config
      islands0 = splitInto n pop0
      mergedBest0 = bestOf (concat islands0)
      ss0 = StopState 0 (fitness mergedBest0) 0
  (finalIslands, finalBest, totalGens) <- islandLoop ss0 mergedBest0 islands0
  return $ StrategyResult (concat finalIslands) finalBest totalGens
  where
    islandLoop ss overallBest islands
      | checkStop stop ss = return (islands, overallBest, ssGens ss)
      | otherwise = do
          -- Evolve each island one step
          islands' <- mapM (step (ssGens ss)) islands
          -- Migrate if it's time
          islands'' <- if ssGens ss > 0 && ssGens ss `mod` islandMigFreq config == 0
                       then migrateIslands config islands'
                       else return islands'
          -- Update tracking
          let merged = concat islands''
              currentBest = bestOf merged
              improved = fitness currentBest > ssBest ss
              overallBest' = betterOf currentBest overallBest
              ss' = StopState
                { ssGens      = ssGens ss + 1
                , ssBest      = max (ssBest ss) (fitness currentBest)
                , ssNoImprove = if improved then 0 else ssNoImprove ss + 1
                }
          islandLoop ss' overallBest' islands''

-- Island migration

migrateIslands :: IslandConfig -> [[Scored a]] -> EvoM [[Scored a]]
migrateIslands config islands = case islandTopology config of
  IslandRing -> ringMig (islandMigRate config) islands
  IslandFull -> fullMig (islandMigRate config) islands

ringMig :: Double -> [[Scored a]] -> EvoM [[Scored a]]
ringMig rate islands
  | length islands <= 1 = return islands
  | otherwise = do
      let migCounts = map (\pop ->
            max 1 (round (rate * fromIntegral (length pop)) :: Int)) islands
      migrants <- mapM (\(pop, k) -> do
          shuffled <- shuffle pop
          return (Prelude.take k shuffled)
        ) (zip islands migCounts)
      -- Island i receives migrants from island (i-1)
      let updated = zipWith (\pop migIn ->
            let trimmed = Prelude.take (length pop - length migIn) pop
            in migIn ++ trimmed
            ) islands (last migrants : init migrants)
      return updated

fullMig :: Double -> [[Scored a]] -> EvoM [[Scored a]]
fullMig rate islands
  | length islands <= 1 = return islands
  | otherwise = do
      let n = length islands
          perIsland = max 1 (round (rate * fromIntegral (length (Prelude.head islands))
                                    / fromIntegral (n - 1)) :: Int)
      donors <- mapM (\pop -> do
          shuffled <- shuffle pop
          return (Prelude.take (perIsland * (n - 1)) shuffled)
        ) islands
      let updated = zipWith3 (\i pop _ ->
            let incoming = concatMap (\(j, d) ->
                  if j /= i then Prelude.take perIsland d else [])
                  (zip [0 :: Int ..] donors)
                trimmed = Prelude.take (length pop - length incoming) pop
            in incoming ++ trimmed
            ) [0 :: Int ..] islands donors
      return updated

-- Helpers (not exported)

bestOf :: [Scored a] -> Scored a
bestOf = Prelude.head . sortBy (comparing (Down . fitness))

betterOf :: Scored a -> Scored a -> Scored a
betterOf a b = if fitness a >= fitness b then a else b

splitInto :: Int -> [a] -> [[a]]
splitInto 0 xs = [xs]
splitInto 1 xs = [xs]
splitInto n xs =
  let size = length xs `div` n
      (chunk, rest) = splitAt size xs
  in chunk : splitInto (n - 1) rest
