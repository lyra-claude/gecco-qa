{-# LANGUAGE FlexibleContexts #-}
{-# LANGUAGE ScopedTypeVariables #-}

-- | Genetic operators as categorical morphisms.
--
-- Each operator is a 'GeneticOp' — a morphism in the Kleisli category for
-- the evolution monad. They compose via '>>>:' to form pipelines:
--
-- @
--   evaluate fitnessFunc
--     >>>: select tournamentSelect
--     >>>: breed onePointCrossover
--     >>>: mutate bitFlip
-- @
--
-- This mirrors category-printf's composition of format specs:
--
-- @
--   "Hello, " . i . "! You are " . s . " years old."
-- @
--
-- In both cases, composition in a category accumulates structure:
-- format specs accumulate argument types, genetic operators accumulate effects.
module Evolution.Operators
  ( -- * Evaluation
    evaluate
    -- * Selection (MonadSelect-inspired)
  , tournamentSelect
  , rouletteSelect
  , elitistSelect
    -- * Crossover
  , onePointCrossover
  , uniformCrossover
    -- * Mutation
  , pointMutate
    -- * Logging
  , logGeneration
    -- * Composition helpers
  , withElitism
  ) where

import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import Control.Monad.Reader
import Control.Monad.Writer.Strict

import Evolution.Category
import Evolution.Effects

-- | Evaluate each individual against a fitness function.
-- Transforms an unscored population into a scored one.
--
-- @evaluate@ is the bridge between the problem domain and the GA domain.
evaluate :: (a -> Double) -> GeneticOp EvoM a (Scored a)
evaluate f = pointwise (\x -> Scored x (f x))

-- | Tournament selection. Picks n random individuals, keeps the best.
--
-- This is the categorical manifestation of mtl's 'MonadSelect':
-- @select :: ((a -> r) -> a) -> m a@
-- means "given a ranking function (a -> r), pick the best a."
-- Tournament selection does exactly this: it samples a subset and
-- picks the one with the highest ranking (fitness).
--
-- Repeated to fill the population.
tournamentSelect :: GeneticOp EvoM (Scored a) (Scored a)
tournamentSelect = liftMonadic $ \pop -> do
  cfg <- ask
  let n = populationSize cfg
      k = tournamentSize cfg
  replicateM n (tournament k pop)
  where
    tournament :: Int -> [Scored a] -> EvoM (Scored a)
    tournament k pop = do
      contestants <- replicateM k (randomChoice pop)
      return $ maximumByFitness contestants
    maximumByFitness = head . sortBy (comparing (Down . fitness))

-- | Roulette wheel (fitness-proportionate) selection.
-- Each individual's selection probability is proportional to its fitness.
rouletteSelect :: GeneticOp EvoM (Scored a) (Scored a)
rouletteSelect = liftMonadic $ \pop -> do
  cfg <- ask
  let n = populationSize cfg
      totalFit = sum (map fitness pop)
      -- Normalize to probabilities
      probs = if totalFit > 0
              then map (\s -> fitness s / totalFit) pop
              else map (const (1.0 / fromIntegral (length pop))) pop
      cumProbs = scanl1 (+) probs
  replicateM n (rouletteSpin cumProbs pop)
  where
    rouletteSpin :: [Double] -> [Scored a] -> EvoM (Scored a)
    rouletteSpin cumProbs pop = do
      r <- randomDouble
      let idx = length (takeWhile (< r) cumProbs)
          idx' = min idx (length pop - 1)
      return (pop !! idx')

-- | Elitist selection: keep the top n, fill the rest with tournament selection.
elitistSelect :: GeneticOp EvoM (Scored a) (Scored a)
elitistSelect = liftMonadic $ \pop -> do
  cfg <- ask
  let n = populationSize cfg
      elite = eliteCount cfg
      k = tournamentSize cfg
      sorted = sortBy (comparing (Down . fitness)) pop
      elites = take elite sorted
      remaining = n - elite
  selected <- replicateM remaining (tournament k pop)
  return (elites ++ selected)
  where
    tournament k pop = do
      contestants <- replicateM k (randomChoice pop)
      return $ head $ sortBy (comparing (Down . fitness)) contestants

-- | One-point crossover on list-based genomes.
-- Pairs up individuals and crosses them over at a random point.
onePointCrossover :: GeneticOp EvoM (Scored [a]) (Scored [a])
onePointCrossover = liftMonadic $ \pop -> do
  cfg <- ask
  let rate = crossoverRate cfg
  go rate pop
  where
    go _ [] = return []
    go _ [x] = return [x]
    go rate (p1:p2:rest) = do
      r <- randomDouble
      children <- if r < rate
        then do
          let g1 = individual p1
              g2 = individual p2
              len = min (length g1) (length g2)
          point <- randomInt 1 (max 1 (len - 1))
          let (h1, t1) = splitAt point g1
              (h2, t2) = splitAt point g2
              child1 = Scored (h1 ++ t2) 0  -- Fitness invalidated
              child2 = Scored (h2 ++ t1) 0
          return [child1, child2]
        else return [p1 { fitness = 0 }, p2 { fitness = 0 }]
      rest' <- go rate rest
      return (children ++ rest')

-- | Uniform crossover: each gene chosen from either parent with p=0.5.
uniformCrossover :: GeneticOp EvoM (Scored [a]) (Scored [a])
uniformCrossover = liftMonadic $ \pop -> do
  cfg <- ask
  let rate = crossoverRate cfg
  go rate pop
  where
    go _ [] = return []
    go _ [x] = return [x]
    go rate (p1:p2:rest) = do
      r <- randomDouble
      children <- if r < rate
        then do
          let g1 = individual p1
              g2 = individual p2
          -- For each gene position, flip a coin for each child
          pairs <- mapM (\(a, b) -> do
              coin <- randomDouble
              return (if coin < 0.5 then (a, b) else (b, a))
            ) (zip g1 g2)
          let child1 = map fst pairs
              child2 = map snd pairs
          return [Scored child1 0, Scored child2 0]
        else return [p1 { fitness = 0 }, p2 { fitness = 0 }]
      rest' <- go rate rest
      return (children ++ rest')

-- | Point mutation on list-based genomes.
-- Each gene has mutationRate probability of being replaced by the mutator function.
pointMutate :: (a -> EvoM a) -> GeneticOp EvoM (Scored [a]) (Scored [a])
pointMutate mutator = pointwiseM $ \scored -> do
  cfg <- ask
  let rate = mutationRate cfg
  genes' <- mapM (\gene -> do
      r <- randomDouble
      if r < rate then mutator gene else return gene
    ) (individual scored)
  return (scored { individual = genes', fitness = 0 })

-- | Log statistics for the current generation.
-- This is the MonadAccum/MonadWriter connection: each generation
-- /accumulates/ its statistics into the evolutionary log.
logGeneration :: Int -> GeneticOp EvoM (Scored a) (Scored a)
logGeneration gen = liftMonadic $ \pop -> do
  let fitnesses = map fitness pop
      best = maximum fitnesses
      worst = minimum fitnesses
      avg = sum fitnesses / fromIntegral (length fitnesses)
      -- Diversity: normalized standard deviation of fitness
      variance = sum (map (\f -> (f - avg)^(2::Int)) fitnesses)
                 / fromIntegral (length fitnesses)
      stddev = sqrt variance
      div' = if best > worst then stddev / (best - worst) else 0
  tell $ GALog [GenStats gen best avg worst div']
  return pop

-- | Wrap an operator pipeline with elitism: preserve the top n individuals
-- from the input population regardless of what the pipeline does.
--
-- This is a higher-order operator — a functor on GeneticOp's, in the
-- category-theoretic sense.
withElitism :: Int -> GeneticOp EvoM (Scored a) (Scored a)
           -> GeneticOp EvoM (Scored a) (Scored a)
withElitism n inner = liftMonadic $ \pop -> do
  let sorted = sortBy (comparing (Down . fitness)) pop
      elites = take n sorted
  result <- runOp inner pop
  -- Replace worst individuals with elites
  let resultSorted = sortBy (comparing fitness) result
      replaced = elites ++ drop n resultSorted
  return replaced
