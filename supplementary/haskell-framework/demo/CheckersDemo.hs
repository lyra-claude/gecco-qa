-- | Checkers GA demo: evolve evaluation function weights.
--
-- Demonstrates that the same categorical pipeline used for OneMax
-- (bitstring evolution) can evolve real-valued checkers strategy
-- weights. Only the genome type, fitness function, and mutation
-- operator change — the composition structure is identical.
module CheckersDemo (main, runCheckersDemo) where

import Evolution.Examples.Checkers (runCheckersGA)

main :: IO ()
main = runCheckersDemo

runCheckersDemo :: IO ()
runCheckersDemo = runCheckersGA
