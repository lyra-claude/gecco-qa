module Test.Landscape (runTests) where

import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Examples.BitString (oneMaxFitness, bitFlip, randomPopulation)
import Evolution.Landscape
import Evolution.Strategy (runStrategy, resultBest, StrategyResult(..), StopWhen(..))

-- | Run landscape analysis tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Landscape analysis tests ---"
  failures <- sequence
    [ test "random walk returns correct length"       testRandomWalkLength
    , test "smooth landscape has low ruggedness"       testSmoothLandscape
    , test "rugged landscape has high ruggedness"      testRuggedLandscape
    , test "singlePointMutation changes one gene"      testSinglePointMutation
    , test "recommendStrategy returns a working strategy" testRecommendStrategy
    , test "neutrality detected on flat landscape"     testNeutralLandscape
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

-- | Random walk should return (steps + 1) fitness values (including start)
testRandomWalkLength :: Bool
testRandomWalkLength =
  let config = defaultConfig { mutationRate = 0.1 }
      g = mkStdGen 42
      start = replicate 20 True  -- 20-bit genome
      mutGenome = singlePointMutation bitFlip
      (trace, _, _) = runEvoM config g
                        (randomWalk oneMaxFitness mutGenome start 100)
  in length trace == 101  -- 100 steps + initial point

-- | A smooth landscape (OneMax) should have low ruggedness
-- OneMax with single-bit flip: changing one bit changes fitness by exactly 1
-- This is moderately smooth — autocorrelation should be high
testSmoothLandscape :: Bool
testSmoothLandscape =
  let config = defaultConfig { mutationRate = 0.1 }
      g = mkStdGen 123
      start = replicate 30 True
      mutGenome = singlePointMutation bitFlip
      (profile, _, _) = runEvoM config g
                          (analyzeLandscape oneMaxFitness mutGenome start 500)
  in ruggedness profile < 0.5  -- OneMax is relatively smooth

-- | A "random" fitness function should produce a rugged landscape
testRuggedLandscape :: Bool
testRuggedLandscape =
  let -- Fitness = hash-like function (pseudorandom based on genome)
      ruggedFitness :: [Bool] -> Double
      ruggedFitness bs =
        let vals = zipWith (\b i -> if b then i * 17 + 3 else i * 7 + 11)
                     bs ([1..] :: [Int])
            h = fromIntegral (sum vals `mod` 97) :: Double
        in h
      config = defaultConfig { mutationRate = 0.1 }
      g = mkStdGen 456
      start = replicate 30 False
      mutGenome = singlePointMutation bitFlip
      (profile, _, _) = runEvoM config g
                          (analyzeLandscape ruggedFitness mutGenome start 500)
  in ruggedness profile > 0.3  -- Should be noticeably rugged

-- | singlePointMutation should change exactly one gene
testSinglePointMutation :: Bool
testSinglePointMutation =
  let config = defaultConfig { mutationRate = 0.1 }
      g = mkStdGen 789
      genome = [True, True, True, True, True, True, True, True]
      (mutated, _, _) = runEvoM config g (singlePointMutation bitFlip genome)
      diffs = length $ filter id $ zipWith (/=) genome mutated
  in diffs == 1  -- exactly one gene changed

-- | recommendStrategy should return a strategy that actually runs and improves fitness
testRecommendStrategy :: Bool
testRecommendStrategy =
  let config = defaultConfig
        { populationSize = 30
        , mutationRate   = 0.05
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }
      g = mkStdGen 111
      -- Analyze landscape
      start = replicate 20 False
      mutGenome = singlePointMutation bitFlip
      (profile, g', _) = runEvoM config g
                           (analyzeLandscape oneMaxFitness mutGenome start 200)
      -- Get recommended strategy
      strat = recommendStrategy profile oneMaxFitness bitFlip (AfterGens 30)
      -- Create initial population and run
      (rawPop, g'', _) = runEvoM config g'
                           (randomPopulation 30 20)
      initPop = map (\genome -> Scored genome (oneMaxFitness genome)) rawPop
      (result, _, _) = runEvoM config g'' (runStrategy strat initPop)
      initBest = maximum (map fitness initPop)
  in fitness (resultBest result) > initBest

-- | A perfectly flat landscape should have high neutrality
testNeutralLandscape :: Bool
testNeutralLandscape =
  let flatFitness :: [Bool] -> Double
      flatFitness _ = 42.0  -- constant fitness
      config = defaultConfig { mutationRate = 0.1 }
      g = mkStdGen 222
      start = replicate 20 True
      mutGenome = singlePointMutation bitFlip
      (profile, _, _) = runEvoM config g
                          (analyzeLandscape flatFitness mutGenome start 200)
  in neutrality profile > 0.9  -- Nearly all steps are neutral on a flat landscape
