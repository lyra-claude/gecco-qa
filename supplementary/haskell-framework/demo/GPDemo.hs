-- | Genetic Programming demo: discover y = x^2 + x from data points.
module Main (main) where

import Evolution.Examples.SymbolicRegression (runSymbolicRegression)

main :: IO ()
main = do
  -- Target function: y = x^2 + x
  -- (should discover something equivalent to (x * x) + x)
  let dataPoints = [(x, x*x + x) | x <- [-5.0, -4.5 .. 5.0]]
  runSymbolicRegression dataPoints
