-- | Landscape analysis demo: analyze → recommend → evolve.
--
-- Shows the complete pipeline: characterize a fitness landscape via
-- random walk, then auto-select and run the best strategy.
module Main (main) where

import System.Random (mkStdGen)

import Evolution.Category (Scored(..), fitness, individual)
import Evolution.Effects (GAConfig(..), EvoM, defaultConfig, runEvoM)
import Evolution.Examples.BitString (oneMaxFitness, bitFlip, randomPopulation)
import Evolution.Landscape
import Evolution.Strategy (runStrategy, resultBest, resultGens, StopWhen(..))

main :: IO ()
main = do
  putStrLn "=== Landscape Analysis Demo ==="
  putStrLn ""

  let config = defaultConfig
        { populationSize = 40
        , mutationRate   = 0.03
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }

  -- 1. Smooth landscape: OneMax
  putStrLn "--- Landscape 1: OneMax (smooth) ---"
  analyzeAndRun config oneMaxFitness bitFlip 30 "OneMax"

  -- 2. Rugged landscape: hash-like fitness
  let ruggedFitness :: [Bool] -> Double
      ruggedFitness bs =
        let vals = zipWith (\b i -> if b then i * 17 + 3 else i * 7 + 11)
                     bs ([1..] :: [Int])
        in fromIntegral (sum vals `mod` 97)
  putStrLn "--- Landscape 2: Hash-like (rugged) ---"
  analyzeAndRun config ruggedFitness bitFlip 30 "Hash-like"

  -- 3. Deceptive landscape: maximizing hamming distance from all-True,
  -- but with a narrow global optimum at all-True
  let deceptiveFitness :: [Bool] -> Double
      deceptiveFitness bs =
        let n = length bs
            trueCount = length (filter id bs)
        in if trueCount == n
           then fromIntegral n * 2.0  -- global optimum
           else fromIntegral (n - trueCount)  -- leads away from optimum
  putStrLn "--- Landscape 3: Deceptive (misleading gradient) ---"
  analyzeAndRun config deceptiveFitness bitFlip 30 "Deceptive"

  putStrLn "=== End of demo ==="

analyzeAndRun :: GAConfig
              -> ([Bool] -> Double)
              -> (Bool -> EvoM Bool)
              -> Int -> String -> IO ()
analyzeAndRun config fitFunc mutFunc genomeLen name = do
  let g = mkStdGen (length name * 37)
      start = replicate genomeLen False
      mutGenome = singlePointMutation mutFunc

      -- Step 1: Analyze the landscape
      (profile, g', _) = runEvoM config g
                           (analyzeLandscape fitFunc mutGenome start 500)

  putStrLn $ "  Ruggedness:       " ++ showF (ruggedness profile)
  putStrLn $ "  Correlation len:  " ++ showF (correlationLen profile)
  putStrLn $ "  Neutrality:       " ++ showF (neutrality profile)
  putStrLn $ "  Local optima:     " ++ show (localOptima profile)
  putStrLn $ "  Fitness range:    " ++ showF (fitnessRange profile)

  -- Step 2: Get recommended strategy
  let strat = recommendStrategy profile fitFunc mutFunc
                (StopOr (AfterGens 50) (Plateau 10))
      stratName
        | neutrality profile > 0.5 = "steady-state (high neutrality)"
        | ruggedness profile < 0.3 = "generational (smooth landscape)"
        | ruggedness profile > 0.7 = "race gen/ss (very rugged)"
        | otherwise                = "steady-state (moderate ruggedness)"

  putStrLn $ "  Recommended:      " ++ stratName

  -- Step 3: Create population and run
  let (rawPop, g'', _) = runEvoM config g' (randomPopulation 40 genomeLen)
      initPop = map (\genome -> Scored genome (fitFunc genome)) rawPop
      (result, _, _) = runEvoM config g'' (runStrategy strat initPop)
      initBest = maximum (map fitness initPop)

  putStrLn $ "  Initial best:     " ++ showF initBest
  putStrLn $ "  Final best:       " ++ showF (fitness (resultBest result))
  putStrLn $ "  Generations used: " ++ show (resultGens result)
  putStrLn $ "  Best genome:      " ++ showBits (individual (resultBest result))
  putStrLn ""
  where
    showF d = let s = show (fromIntegral (round (d * 1000) :: Int) / 1000.0 :: Double)
              in s
    showBits = map (\b -> if b then '1' else '0')
