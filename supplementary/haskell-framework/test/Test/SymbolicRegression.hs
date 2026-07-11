module Test.SymbolicRegression (runTests) where

import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators
import Evolution.Examples.SymbolicRegression

-- | Run symbolic regression tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Symbolic regression tests ---"
  failures <- sequence
    [ test "eval evaluates correctly"      testEval
    , test "size counts nodes"             testSize
    , test "depth measures correctly"      testDepth
    , test "subtreeAt/replaceAt roundtrip" testSubtreeRoundtrip
    , test "treeCrossover preserves count" testCrossoverCount
    , test "GP evolves toward target"      testGPEvolves
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

-- | eval produces correct results
testEval :: Bool
testEval =
  let expr = Add (Mul Var Var) Var  -- x^2 + x
  in eval 3.0 expr == 12.0    -- 9 + 3
     && eval 0.0 expr == 0.0
     && eval (-2.0) expr == 2.0  -- 4 + (-2)

-- | size counts all nodes
testSize :: Bool
testSize =
  let expr = Add (Mul Var Var) Var  -- 5 nodes
  in size expr == 5
     && size Var == 1
     && size (Const 42) == 1

-- | depth measures correctly
testDepth :: Bool
testDepth =
  let expr = Add (Mul Var Var) Var
  in depth expr == 3
     && depth Var == 1
     && depth (Neg (Neg Var)) == 3

-- | subtreeAt and replaceAt are consistent
testSubtreeRoundtrip :: Bool
testSubtreeRoundtrip =
  let expr = Add (Mul Var (Const 2)) (Sub Var (Const 1))
      -- subtreeAt 0 = whole tree
      -- subtreeAt 1 = Mul Var (Const 2)
      -- subtreeAt 2 = Var (left of Mul)
      -- subtreeAt 3 = Const 2
      -- subtreeAt 4 = Sub Var (Const 1)
      s0 = subtreeAt 0 expr
      s1 = subtreeAt 1 expr
      s2 = subtreeAt 2 expr
      s3 = subtreeAt 3 expr
  in s0 == expr
     && s1 == Mul Var (Const 2)
     && s2 == Var
     && s3 == Const 2
     -- Replacing root with itself is identity
     && replaceAt 0 expr expr == expr
     -- Replacing a subtree
     && replaceAt 2 (Const 5) expr == Add (Mul (Const 5) (Const 2)) (Sub Var (Const 1))

-- | Tree crossover preserves population size
testCrossoverCount :: Bool
testCrossoverCount =
  let cfg = defaultConfig
        { populationSize = 10
        , crossoverRate = 0.9
        }
      pop = replicate 10 (Scored (Add Var (Const 1)) 1.0)
      (result, _, _) = runEvoM cfg (mkStdGen 42) (runOp treeCrossover pop)
  in length result == 10

-- | GP should improve fitness over generations on y = x^2
testGPEvolves :: Bool
testGPEvolves =
  let dataPoints = [(x, x*x) | x <- [-3.0, -2.0 .. 3.0]]
      fitFunc = regressionFitness dataPoints
      cfg = defaultConfig
        { populationSize = 50
        , maxGenerations = 30
        , mutationRate   = 0.15
        , crossoverRate  = 0.8
        , tournamentSize = 5
        , eliteCount     = 2
        }
      gen = mkStdGen 42
      pipeline :: Int -> GeneticOp EvoM Expr Expr
      pipeline g =
        evaluate fitFunc
          >>>: logGeneration g
          >>>: elitistSelect
          >>>: treeCrossover
          >>>: treeMutate
          >>>: pointwise individual
      (initPop, gen', _) = runEvoM cfg gen $ randomPopulation 50 4
      (finalPop, _, _) = runEvoM cfg gen' $ go pipeline 0 30 initPop
      bestFit = maximum $ map fitFunc finalPop
  in bestFit > -1.0  -- Should get reasonably close to 0
  where
    go :: (Int -> GeneticOp EvoM Expr Expr) -> Int -> Int -> [Expr] -> EvoM [Expr]
    go _ g maxG pop | g >= maxG = return pop
    go pipe g maxG pop = do
      pop' <- runOp (pipe g) pop
      go pipe (g + 1) maxG pop'
