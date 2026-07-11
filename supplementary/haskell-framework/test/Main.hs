module Main (main) where

import System.Exit (exitFailure, exitSuccess)
import Test.Category
import Test.Operators
import Test.Pipeline
import Test.Island
import Test.Coevolution
import Test.SymbolicRegression
import Test.Strategy
import Test.Landscape
import Test.Checkers
import Test.Maze

main :: IO ()
main = do
  putStrLn "=== categorical-evolution test suite ==="
  putStrLn ""
  r1  <- Test.Category.runTests
  r2  <- Test.Operators.runTests
  r3  <- Test.Pipeline.runTests
  r4  <- Test.Island.runTests
  r5  <- Test.Coevolution.runTests
  r6  <- Test.SymbolicRegression.runTests
  r7  <- Test.Strategy.runTests
  r8  <- Test.Landscape.runTests
  r9  <- Test.Checkers.runTests
  r10 <- Test.Maze.runTests
  putStrLn ""
  let total = r1 + r2 + r3 + r4 + r5 + r6 + r7 + r8 + r9 + r10
  if total == 0
    then putStrLn "All tests passed!" >> exitSuccess
    else putStrLn (show total ++ " test(s) failed.") >> exitFailure
