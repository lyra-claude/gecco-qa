{-# LANGUAGE ScopedTypeVariables #-}

-- | BitString evolution: the "Hello World" of genetic algorithms.
--
-- We evolve binary strings to maximize the number of 1-bits (OneMax problem).
-- This example demonstrates the full categorical pipeline.
--
-- == Pipeline composition
--
-- @
--   evaluate oneMaxFitness
--     >>>: logGeneration gen
--     >>>: elitistSelect
--     >>>: onePointCrossover
--     >>>: pointMutate bitFlip
-- @
--
-- Each operator is a morphism in the Kleisli category for 'EvoM'.
-- The pipeline reads left to right, just like a sentence:
-- "evaluate, then select, then crossover, then mutate."
module Evolution.Examples.BitString
  ( -- * Fitness functions
    oneMaxFitness
  , targetFitness
    -- * Genome operations
  , bitFlip
  , randomBitString
  , randomPopulation
    -- * Running examples
  , runOneMax
  , runTarget
  ) where

import Control.Monad (replicateM)
import System.Random

import Evolution.Effects
import Evolution.Pipeline

-- | OneMax fitness: count the number of 1-bits.
-- Optimal solution for a genome of length n has fitness n.
oneMaxFitness :: [Bool] -> Double
oneMaxFitness = fromIntegral . length . filter id

-- | Target string fitness: count matching positions with target.
-- This is a generalization of OneMax where the target isn't all-True.
targetFitness :: [Bool] -> [Bool] -> Double
targetFitness target genome =
  fromIntegral $ length $ filter id $ zipWith (==) target genome

-- | Bit flip mutation: flip a single bit.
-- Used as the per-gene mutator in 'pointMutate'.
bitFlip :: Bool -> EvoM Bool
bitFlip b = return (not b)

-- | Generate a random bitstring of length n.
randomBitString :: Int -> EvoM [Bool]
randomBitString n = replicateM n (do
  r <- randomDouble
  return (r < 0.5))

-- | Generate a random initial population.
randomPopulation :: Int -> Int -> EvoM [[Bool]]
randomPopulation popSize genomeLen =
  replicateM popSize (randomBitString genomeLen)

-- | Run the OneMax example.
--
-- @runOneMax genomeLen@ evolves bitstrings of length @genomeLen@
-- to maximize the number of 1-bits.
runOneMax :: Int -> IO ()
runOneMax genomeLen = do
  gen <- newStdGen
  let config = defaultConfig { populationSize = 50, maxGenerations = 50 }
      (initPop, gen', _) = runEvoM config gen
                            (randomPopulation (populationSize config) genomeLen)
      result = evolve oneMaxFitness bitFlip config gen' initPop
  putStrLn $ "OneMax (genome length " ++ show genomeLen ++ ")"
  putStrLn $ "Best fitness: " ++ show (bestFitness' result)
            ++ " / " ++ show genomeLen
  putStrLn $ "Best genome:  " ++ showBits (bestIndividual result)
  putStrLn ""
  putStrLn "Fitness over generations:"
  mapM_ (\gs -> putStrLn $ "  Gen " ++ padLeft 3 (show (genNumber gs))
                         ++ ": best=" ++ showF (bestFitness gs)
                         ++ " avg=" ++ showF (avgFitness gs)
                         ++ " div=" ++ showF (diversity gs))
        (generations (evoLog result))
  where
    showBits = map (\b -> if b then '1' else '0')
    showF d = let s = show (fromIntegral (round (d * 100) :: Int) / 100.0 :: Double)
              in padLeft 6 s
    padLeft n s = replicate (n - length s) ' ' ++ s

-- | Run the target string example.
--
-- @runTarget target@ evolves bitstrings to match the given target.
runTarget :: [Bool] -> IO ()
runTarget target = do
  gen <- newStdGen
  let genomeLen = length target
      config = defaultConfig { populationSize = 50, maxGenerations = 100 }
      (initPop, gen', _) = runEvoM config gen
                            (randomPopulation (populationSize config) genomeLen)
      result = evolve (targetFitness target) bitFlip config gen' initPop
  putStrLn $ "Target matching (genome length " ++ show genomeLen ++ ")"
  putStrLn $ "Target:       " ++ showBits target
  putStrLn $ "Best found:   " ++ showBits (bestIndividual result)
  putStrLn $ "Best fitness: " ++ show (bestFitness' result)
            ++ " / " ++ show genomeLen
  where
    showBits = map (\b -> if b then '1' else '0')
