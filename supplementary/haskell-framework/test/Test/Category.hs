module Test.Category (runTests) where

import Evolution.Category
import Evolution.Effects

import System.Random (mkStdGen)

-- | Run category law tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Category laws ---"
  failures <- sequence
    [ test "identity left"  testIdLeft
    , test "identity right" testIdRight
    , test "associativity"  testAssoc
    , test "pointwise map"  testPointwise
    , test "liftPure"       testLiftPure
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

-- Helper: run an EvoM operation and get the result
run :: EvoM a -> a
run m = let (a, _, _) = runEvoM defaultConfig (mkStdGen 42) m in a

-- | Left identity: idOp >>>: f == f
testIdLeft :: Bool
testIdLeft =
  let f = liftPure (map (* 2)) :: GeneticOp EvoM Int Int
      input = [1, 2, 3, 4, 5]
      result1 = run $ runOp (idOp >>>: f) input
      result2 = run $ runOp f input
  in result1 == result2

-- | Right identity: f >>>: idOp == f
testIdRight :: Bool
testIdRight =
  let f = liftPure (map (* 2)) :: GeneticOp EvoM Int Int
      input = [1, 2, 3, 4, 5]
      result1 = run $ runOp (f >>>: idOp) input
      result2 = run $ runOp f input
  in result1 == result2

-- | Associativity: (f >>>: g) >>>: h == f >>>: (g >>>: h)
testAssoc :: Bool
testAssoc =
  let f = liftPure (map (* 2))   :: GeneticOp EvoM Int Int
      g = liftPure (map (+ 10))  :: GeneticOp EvoM Int Int
      h = liftPure (filter even) :: GeneticOp EvoM Int Int
      input = [1, 2, 3, 4, 5]
      result1 = run $ runOp ((f >>>: g) >>>: h) input
      result2 = run $ runOp (f >>>: (g >>>: h)) input
  in result1 == result2

-- | Pointwise maps individual elements
testPointwise :: Bool
testPointwise =
  let op = pointwise (* 3) :: GeneticOp EvoM Int Int
      result = run $ runOp op [1, 2, 3]
  in result == [3, 6, 9]

-- | liftPure wraps a pure function
testLiftPure :: Bool
testLiftPure =
  let op = liftPure reverse :: GeneticOp EvoM Int Int
      result = run $ runOp op [1, 2, 3]
  in result == [3, 2, 1]
