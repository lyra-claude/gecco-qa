-- | Strategy composition demo: composing evolutionary algorithms.
--
-- This demo shows how strategies (entire GA algorithms) compose
-- the same way operators compose — through categorical structure.
--
-- We solve OneMax (maximize 1-bits in a bitstring) using:
--   1. A plain generational GA
--   2. A steady-state GA
--   3. A race between the two
--   4. An adaptive strategy that starts with one and falls back to another
--   5. A sequential pipeline: explore broadly, then refine
module Main (main) where

import System.Random (mkStdGen)

import Evolution.Category (Scored(..), fitness, individual)
import Evolution.Effects (GAConfig(..), defaultConfig, runEvoM)
import Evolution.Examples.BitString (oneMaxFitness, bitFlip, randomPopulation)
import Evolution.Strategy

main :: IO ()
main = do
  putStrLn "=== Strategy Composition Demo ==="
  putStrLn ""
  putStrLn "Problem: OneMax (maximize 1-bits in a 30-bit string)"
  putStrLn "Optimal fitness: 30.0"
  putStrLn ""

  let genomeLen = 30
      config = defaultConfig
        { populationSize = 40
        , mutationRate   = 0.03
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }
      gen = mkStdGen 2026

      -- Create initial scored population
      (rawPop, _, _) = runEvoM config gen (randomPopulation 40 genomeLen)
      initPop = map (\g -> Scored g (oneMaxFitness g)) rawPop

      run :: Strategy [Bool] -> (StrategyResult [Bool], Int)
      run s = let (r, _, _) = runEvoM config (mkStdGen 42) (runStrategy s initPop)
              in (r, resultGens r)

  -- 1. Plain generational GA (50 generations)
  let genGA = generationalGA oneMaxFitness bitFlip (AfterGens 50)
      (r1, g1) = run genGA
  putStrLn "1. Generational GA (50 gens):"
  putStrLn $ "   Best fitness: " ++ show (fitness (resultBest r1))
  putStrLn $ "   Generations:  " ++ show g1
  putStrLn ""

  -- 2. Steady-state GA (50 generations equivalent)
  let ssGA = steadyStateGA oneMaxFitness bitFlip (AfterGens 50)
      (r2, g2) = run ssGA
  putStrLn "2. Steady-state GA (50 gen-equivalents):"
  putStrLn $ "   Best fitness: " ++ show (fitness (resultBest r2))
  putStrLn $ "   Generations:  " ++ show g2
  putStrLn ""

  -- 3. Race: run both, take the winner
  let raceStrat = race genGA ssGA
      (r3, g3) = run raceStrat
  putStrLn "3. Race (generational vs steady-state):"
  putStrLn $ "   Best fitness: " ++ show (fitness (resultBest r3))
  putStrLn $ "   Generations:  " ++ show g3
  putStrLn $ "   (Winner is whichever found higher fitness)"
  putStrLn ""

  -- 4. Adaptive: try short generational run, switch to steady-state if not converged
  let shortGen = generationalGA oneMaxFitness bitFlip (AfterGens 15)
      longSS  = steadyStateGA oneMaxFitness bitFlip (AfterGens 35)
      -- Switch to steady-state if fitness < 90% of optimal
      adaptStrat = adaptive
        (\r -> fitness (resultBest r) >= fromIntegral genomeLen * 0.9)
        shortGen longSS
      (r4, g4) = run adaptStrat
  putStrLn "4. Adaptive (generational 15 gens, then steady-state if <90%):"
  putStrLn $ "   Best fitness: " ++ show (fitness (resultBest r4))
  putStrLn $ "   Generations:  " ++ show g4
  putStrLn $ "   (If primary succeeded: 15, if fallback triggered: 50)"
  putStrLn ""

  -- 5. Sequential: explore broadly (high mutation), then refine (low mutation)
  let -- Explore for 25 gens, then refine for 25 more
      explore = generationalGA oneMaxFitness bitFlip (AfterGens 25)
      refine  = generationalGA oneMaxFitness bitFlip (AfterGens 25)
      seqStrat = sequential explore refine
      (r5, g5) = run seqStrat
  putStrLn "5. Sequential (explore 25 gens -> refine 25 gens):"
  putStrLn $ "   Best fitness: " ++ show (fitness (resultBest r5))
  putStrLn $ "   Generations:  " ++ show g5
  putStrLn ""

  -- 6. Plateau-based termination
  let platStrat = generationalGA oneMaxFitness bitFlip
                    (StopOr (Plateau 10) (AfterGens 200))
      (r6, g6) = run platStrat
  putStrLn "6. Plateau detection (stop after 10 gens without improvement):"
  putStrLn $ "   Best fitness: " ++ show (fitness (resultBest r6))
  putStrLn $ "   Generations:  " ++ show g6
  putStrLn $ "   (Stopped early if fitness plateaued)"
  putStrLn ""

  -- Summary
  putStrLn "--- Summary ---"
  putStrLn $ "   Generational:  " ++ showResult r1
  putStrLn $ "   Steady-state:  " ++ showResult r2
  putStrLn $ "   Race:          " ++ showResult r3
  putStrLn $ "   Adaptive:      " ++ showResult r4
  putStrLn $ "   Sequential:    " ++ showResult r5
  putStrLn $ "   Plateau:       " ++ showResult r6
  putStrLn ""
  putStrLn "Strategies compose like operators — the categorical structure"
  putStrLn "lets you build sophisticated algorithms from simple parts."

showResult :: StrategyResult [Bool] -> String
showResult r = "fitness=" ++ show (fitness (resultBest r))
            ++ " in " ++ show (resultGens r) ++ " gens"
            ++ " (" ++ showBits (individual (resultBest r)) ++ ")"

showBits :: [Bool] -> String
showBits = map (\b -> if b then '1' else '0')
