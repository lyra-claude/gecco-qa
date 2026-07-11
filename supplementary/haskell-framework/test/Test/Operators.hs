module Test.Operators (runTests) where

import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators

-- | Run operator tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Operator tests ---"
  failures <- sequence
    [ test "evaluate scores correctly"   testEvaluate
    , test "tournament preserves count"  testTournamentCount
    , test "elitist preserves best"      testElitistBest
    , test "mutation can flip bits"      testMutation
    , test "logging records stats"       testLogging
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

run :: EvoM a -> a
run m = let (a, _, _) = runEvoM testConfig (mkStdGen 42) m in a

runWithLog :: EvoM a -> (a, GALog)
runWithLog m = let (a, _, l) = runEvoM testConfig (mkStdGen 42) m in (a, l)

testConfig :: GAConfig
testConfig = defaultConfig
  { populationSize = 10
  , tournamentSize = 3
  , eliteCount     = 2
  , mutationRate   = 0.5
  , crossoverRate  = 0.7
  }

-- | Evaluate assigns correct fitness values
testEvaluate :: Bool
testEvaluate =
  let pop = [[True, False, True], [False, False, False], [True, True, True]]
      fitFunc = fromIntegral . length . filter id
      result = run $ runOp (evaluate fitFunc) pop
  in map fitness result == [2.0, 0.0, 3.0]

-- | Tournament selection preserves population size
testTournamentCount :: Bool
testTournamentCount =
  let pop = [ Scored [True, False] 1.0
            , Scored [False, True] 2.0
            , Scored [True, True]  3.0
            , Scored [False, False] 0.0
            ] ++ replicate 6 (Scored [True, False] 1.5)
      result = run $ runOp tournamentSelect pop
  in length result == populationSize testConfig

-- | Elitist selection preserves the best individual
testElitistBest :: Bool
testElitistBest =
  let best = Scored [True, True, True] 10.0
      pop = best : replicate 9 (Scored [False, False, False] 1.0)
      result = run $ runOp elitistSelect pop
      bestResult = maximum (map fitness result)
  in bestResult == 10.0

-- | Point mutation with high rate can flip bits
testMutation :: Bool
testMutation =
  let pop = [Scored [True, True, True, True, True] 0]
      highMutConfig = testConfig { mutationRate = 1.0 }
      (result, _, _) = runEvoM highMutConfig (mkStdGen 42)
                         (runOp (pointMutate bitFlip) pop)
      -- With rate=1.0, all bits should be flipped
      flipped = individual (Prelude.head result)
  in all (== False) flipped
  where
    bitFlip b = return (not b)

-- | Logging records generation statistics
testLogging :: Bool
testLogging =
  let pop = [ Scored () 1.0, Scored () 5.0, Scored () 3.0
            , Scored () 2.0, Scored () 4.0 ]
      (_, log') = runWithLog $ runOp (logGeneration 0) pop
      stats = generations log'
  in length stats == 1
     && bestFitness (Prelude.head stats) == 5.0
     && worstFitness (Prelude.head stats) == 1.0
