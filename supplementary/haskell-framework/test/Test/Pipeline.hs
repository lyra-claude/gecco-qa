module Test.Pipeline (runTests) where

import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Pipeline
import Evolution.Examples.BitString

-- | Run pipeline integration tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Pipeline tests ---"
  failures <- sequence
    [ test "evolveN improves fitness"   testEvolutionImproves
    , test "onemax converges"           testOneMaxConverges
    , test "log has correct length"     testLogLength
    , test "custom pipeline composes"   testCustomPipeline
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

-- | Evolution should improve fitness over generations
testEvolutionImproves :: Bool
testEvolutionImproves =
  let config = defaultConfig
        { populationSize = 20
        , maxGenerations = 10
        , mutationRate   = 0.05
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }
      gen = mkStdGen 12345
      genomeLen = 20
      (initPop, gen', _) = runEvoM config gen
                            (randomPopulation (populationSize config) genomeLen)
      result = evolve oneMaxFitness bitFlip config gen' initPop
      stats = generations (evoLog result)
      firstBest = bestFitness (Prelude.head stats)
      lastBest  = bestFitness (last stats)
  in lastBest >= firstBest

-- | OneMax with enough generations should get close to optimal
testOneMaxConverges :: Bool
testOneMaxConverges =
  let genomeLen = 10
      config = defaultConfig
        { populationSize = 30
        , maxGenerations = 50
        , mutationRate   = 0.02
        , crossoverRate  = 0.8
        , tournamentSize = 3
        , eliteCount     = 2
        }
      gen = mkStdGen 42
      (initPop, gen', _) = runEvoM config gen
                            (randomPopulation (populationSize config) genomeLen)
      result = evolve oneMaxFitness bitFlip config gen' initPop
  in bestFitness' result >= fromIntegral genomeLen * 0.8  -- At least 80%

-- | Log should have one entry per generation
testLogLength :: Bool
testLogLength =
  let nGens = 15
      config = defaultConfig
        { populationSize = 10
        , maxGenerations = nGens
        , mutationRate   = 0.05
        , tournamentSize = 2
        , eliteCount     = 1
        }
      gen = mkStdGen 99
      (initPop, gen', _) = runEvoM config gen
                            (randomPopulation (populationSize config) 8)
      result = evolve oneMaxFitness bitFlip config gen' initPop
  in length (generations (evoLog result)) == nGens

-- | Custom pipeline via >>>: should compose correctly
testCustomPipeline :: Bool
testCustomPipeline =
  let -- A simple pipeline: double every element, then keep only positives
      op = liftPure (map (* 2))    -- [Int] -> [Int]
           >>>: liftPure (filter (> 0))   -- [Int] -> [Int]
           :: GeneticOp EvoM Int Int
      input = [-3, -1, 0, 2, 5]
      (result, _, _) = runEvoM defaultConfig (mkStdGen 0) (runOp op input)
  in result == [4, 10]
