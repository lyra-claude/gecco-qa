module Main (main) where

import Evolution.Examples.BitString (runOneMax, runTarget)

main :: IO ()
main = do
  putStrLn "=== categorical-evolution demo ==="
  putStrLn ""
  runOneMax 20
  putStrLn ""
  runTarget (replicate 15 True ++ replicate 5 False)
