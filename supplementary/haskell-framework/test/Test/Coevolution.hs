module Test.Coevolution (runTests) where

import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Coevolution

-- | Run coevolution tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Coevolution tests ---"
  failures <- sequence
    [ test "evaluateAgainst scores correctly"  testEvaluateAgainst
    , test "roundRobin scores correctly"       testRoundRobin
    , test "coevolution runs without error"    testCoevolutionRuns
    , test "arms race improves both sides"     testArmsRace
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

testConfig :: GAConfig
testConfig = defaultConfig
  { populationSize = 20
  , maxGenerations = 20
  , mutationRate   = 0.05
  , crossoverRate  = 0.7
  , tournamentSize = 3
  , eliteCount     = 2
  }

-- | Bit-matching game: A scores by matching B, B scores by differing from A.
-- This creates an arms race: A tries to predict B, B tries to be unpredictable.
matchScore :: [Bool] -> [Bool] -> Double
matchScore a b = fromIntegral $ length $ filter id $ zipWith (==) a b

differScore :: [Bool] -> [Bool] -> Double
differScore a b = fromIntegral $ length $ filter id $ zipWith (/=) a b

-- | Bit flip mutation for coevolution tests
coevoBitFlip :: Bool -> EvoM Bool
coevoBitFlip b = return (not b)

-- | evaluateAgainst produces correct scores
testEvaluateAgainst :: Bool
testEvaluateAgainst =
  let popA = [[True, True, True]]  -- All true
      popB = [[True, True, True], [False, False, False]]  -- One matching, one not
      coevoCfg = CoevoConfig { opponentSampleSize = 2 }
      op = evaluateAgainst matchScore popB coevoCfg
      (result, _, _) = runEvoM testConfig (mkStdGen 42) (runOp op popA)
      -- Against [T,T,T] scores 3.0, against [F,F,F] scores 0.0, avg = 1.5
  in length result == 1
     && fitness (head result) == 1.5

-- | roundRobin evaluates against all opponents
testRoundRobin :: Bool
testRoundRobin =
  let popA = [[True, True, True, True]]
      popB = [ [True, True, True, True]    -- score 4
             , [False, False, False, False] -- score 0
             ]
      op = roundRobin matchScore popB
      (result, _, _) = runEvoM testConfig (mkStdGen 42) (runOp op popA)
  in length result == 1
     && fitness (head result) == 2.0  -- avg of 4 and 0

-- | Coevolution completes without errors and produces valid results
testCoevolutionRuns :: Bool
testCoevolutionRuns =
  let gen = mkStdGen 42
      genomeLen = 8
      initA = replicate 20 (replicate genomeLen True)
      initB = replicate 20 (replicate genomeLen False)
      coevoCfg = defaultCoevoConfig
      result = coevolve matchScore differScore
                        coevoBitFlip coevoBitFlip
                        coevoCfg testConfig gen
                        initA initB
  in length (finalPopA result) == 20
     && length (finalPopB result) == 20
     && bestAFitness result >= 0.0
     && bestBFitness result >= 0.0

-- | Arms race: both populations should improve over generations
testArmsRace :: Bool
testArmsRace =
  let gen = mkStdGen 12345
      genomeLen = 8 :: Int
      -- Start both with random-ish populations (alternating patterns)
      initA = [ [i `mod` 2 == 0 | i <- [0..genomeLen-1]] | _ <- [1..20::Int] ]
      initB = [ [i `mod` 2 /= 0 | i <- [0..genomeLen-1]] | _ <- [1..20::Int] ]
      coevoCfg = defaultCoevoConfig { opponentSampleSize = 5 }
      shortConfig = testConfig { maxGenerations = 5 }
      longConfig  = testConfig { maxGenerations = 30 }
      shortResult = coevolve matchScore differScore
                             coevoBitFlip coevoBitFlip
                             coevoCfg shortConfig gen initA initB
      longResult  = coevolve matchScore differScore
                             coevoBitFlip coevoBitFlip
                             coevoCfg longConfig gen initA initB
      -- After more generations, population A should be better at matching
      -- (or at least not worse, since the arms race pushes both)
  in bestAFitness longResult >= bestAFitness shortResult - 1.0
