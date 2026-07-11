{-# LANGUAGE ScopedTypeVariables #-}

-- | Migration frequency sweep for maze domain.
--
-- Replicates the GP lax functor experiment (session 10) on maze topology.
-- Tests whether the island functor strict/lax dichotomy holds across domains.
--
-- Sweeps migration frequency from 2 to 40 and measures:
--   - Divergence: population difference between sequential(20,20) and single(40)
--   - Whether composition is strict (divergence = 0) or lax (divergence > 0)
module Main (main) where

import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators (elitistSelect, uniformCrossover, pointMutate)
import Evolution.Examples.Maze

-- | Maze step function.
mzStep :: [Scored MazeGenome] -> EvoM [Scored MazeGenome]
mzStep pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: uniformCrossover
           >>>: pointMutate mazeFlipMutate
           >>>: pointwise (\s -> Scored (individual s) (mazeFitness (individual s)))

-- | Split a list into n chunks.
splitInto :: Int -> [a] -> [[a]]
splitInto 1 xs = [xs]
splitInto n xs =
  let sz = length xs `div` n
      (chunk, rest) = splitAt sz xs
  in chunk : splitInto (n - 1) rest

-- | Ring migration.
ringMigrate :: Double -> [[Scored a]] -> EvoM [[Scored a]]
ringMigrate _ [] = return []
ringMigrate _ [x] = return [x]
ringMigrate rate islands = do
  let migCounts = map (\pop ->
        max 1 (round (rate * fromIntegral (length pop)) :: Int)) islands
  migrants <- mapM (\(pop, k) -> do
      shuffled <- shuffle pop
      return (take k shuffled)
    ) (zip islands migCounts)
  let updated = zipWith (\pop migIn ->
        let trimmed = take (length pop - length migIn) pop
        in migIn ++ trimmed
        ) islands (last migrants : init migrants)
  return updated

-- | Run island GA for n generations with migration every migFreq gens.
runIslandGA :: Int -> Int -> Double -> Int -> [Scored MazeGenome]
            -> EvoM [Scored MazeGenome]
runIslandGA nGens migFreq migRate nIslands pop0 = do
  let islands0 = splitInto nIslands pop0
  go 0 islands0
  where
    go gen islands
      | gen >= nGens = return (concat islands)
      | otherwise = do
          islands' <- mapM mzStep islands
          islands'' <- if migFreq > 0 && gen > 0 && gen `mod` migFreq == 0
                       then ringMigrate migRate islands'
                       else return islands'
          go (gen + 1) islands''

-- | Population divergence: average pairwise Hamming distance between
-- final populations of two runs, normalized by genome length.
popDivergence :: [Scored MazeGenome] -> [Scored MazeGenome] -> Double
popDivergence pop1 pop2 =
  let genomes1 = map individual pop1
      genomes2 = map individual pop2
      n = min (length genomes1) (length genomes2)
      pairs = zip (take n genomes1) (take n genomes2)
      dists = map (\(a, b) -> hammingDist a b) pairs
  in if null dists then 0 else sum dists / fromIntegral (length dists)
  where
    hammingDist a b = fromIntegral (length (filter id (zipWith (/=) a b)))
                    / fromIntegral genomeLength

main :: IO ()
main = do
  putStrLn "================================================================"
  putStrLn "  MIGRATION FREQUENCY SWEEP — MAZE DOMAIN"
  putStrLn "  Testing strict/lax dichotomy across genome types"
  putStrLn "================================================================"
  putStrLn ""

  let totalGens = 40
      popSize = 40
      nIslands = 4
      migRate = 0.15
      config = defaultConfig
        { populationSize = popSize
        , mutationRate   = 0.05
        , crossoverRate  = 0.8
        , tournamentSize = 3
        , eliteCount     = 2
        }
      gen0 = mkStdGen 2026

  -- Generate initial population
  let (rawPop, gen1, _) = runEvoM config gen0 (randomMazePop popSize)
      initPop = map (\g -> Scored g (mazeFitness g)) rawPop

  putStrLn "Setup: 4 islands, ring migration, rate=0.15, pop=40"
  putStrLn "Comparison: single run (40 gens) vs sequential (20+20 gens)"
  putStrLn ""
  putStrLn "MigFreq | Single BestFit | Seq BestFit | Divergence | Strict/Lax"
  putStrLn "------- | -------------- | ----------- | ---------- | ----------"

  -- No migration (control — should be strict)
  let (singlePop0, _, _) = runEvoM config gen1
        (runIslandGA totalGens 0 migRate nIslands initPop)
      (seqPop0a, gen2a, _) = runEvoM config gen1
        (runIslandGA 20 0 migRate nIslands initPop)
      (seqPop0, _, _) = runEvoM config gen2a
        (runIslandGA 20 0 migRate nIslands seqPop0a)
      div0 = popDivergence singlePop0 seqPop0
  putStrLn $ "   none | " ++ padL 14 (showF (bestFitOf singlePop0))
          ++ " | " ++ padL 11 (showF (bestFitOf seqPop0))
          ++ " | " ++ padL 10 (showF div0)
          ++ " | " ++ classifyLax div0

  -- Sweep migration frequencies
  let freqs = [2, 5, 10, 20, 40]
  mapM_ (\freq -> do
    let (singlePop, _, _) = runEvoM config gen1
          (runIslandGA totalGens freq migRate nIslands initPop)
        (seqPopA, genA, _) = runEvoM config gen1
          (runIslandGA 20 freq migRate nIslands initPop)
        (seqPop, _, _) = runEvoM config genA
          (runIslandGA 20 freq migRate nIslands seqPopA)
        divVal = popDivergence singlePop seqPop
    putStrLn $ padL 7 (show freq)
            ++ " | " ++ padL 14 (showF (bestFitOf singlePop))
            ++ " | " ++ padL 11 (showF (bestFitOf seqPop))
            ++ " | " ++ padL 10 (showF divVal)
            ++ " | " ++ classifyLax divVal
    ) freqs

  putStrLn ""
  putStrLn "=== ANALYSIS ==="
  putStrLn ""
  putStrLn "If the GP result (strict/lax dichotomy) replicates across domains:"
  putStrLn "- No migration: divergence should be 0 (strict functor)"
  putStrLn "- Any migration: divergence should be > 0 and roughly uniform (lax functor)"
  putStrLn "- This confirms the dichotomy theorem is domain-independent"

-- Helpers

bestFitOf :: [Scored a] -> Double
bestFitOf pop = if null pop then 0 else maximum (map fitness pop)

classifyLax :: Double -> String
classifyLax d
  | d < 0.01  = "STRICT"
  | otherwise = "LAX (d=" ++ showF d ++ ")"

showF :: Double -> String
showF d
  | isNaN d || isInfinite d = "NaN"
  | otherwise = show (fromIntegral (round (d * 1000) :: Int) / 1000.0 :: Double)

padL :: Int -> String -> String
padL n s = replicate (max 0 (n - length s)) ' ' ++ s
