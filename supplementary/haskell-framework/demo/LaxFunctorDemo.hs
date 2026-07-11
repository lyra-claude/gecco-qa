{-# LANGUAGE ScopedTypeVariables #-}

-- | Lax functor experiment: migration frequency sweep.
--
-- Tests Claudius's prediction that the island functor is lax with respect
-- to sequential composition. The laxator has periodic structure tied to
-- migration frequency:
--
--   * Trivial (identity) when composition boundary falls between migration events
--   * Non-trivial when it coincides with a migration event
--
-- Experiment: compare I(f)(S_40) vs I(f)(S_20);I(f)(S_20) at various
-- migration frequencies. Plot population-level divergence vs frequency.
--
-- Prediction: divergence ~ freq / composition_length
module Main (main) where

import Data.List (sortBy)
import Data.Ord (comparing)
import System.Random (mkStdGen)

import Evolution.Category (Scored(..), fitness, individual)
import Evolution.Effects (GAConfig(..), defaultConfig, runEvoM)
import Evolution.Examples.BitString (oneMaxFitness, bitFlip, randomPopulation)
import Evolution.Strategy

main :: IO ()
main = do
  putStrLn "=== Lax Functor Experiment: Migration Frequency Sweep ==="
  putStrLn ""
  putStrLn "Comparing I(f)(S_40) vs I(f)(S_20);I(f)(S_20)"
  putStrLn "at different migration frequencies."
  putStrLn ""
  putStrLn "Claudius's prediction: divergence scales with freq/composition_length"
  putStrLn "because the laxator is non-trivial only when a composition boundary"
  putStrLn "coincides with a migration event."
  putStrLn ""

  let config = defaultConfig
        { populationSize = 40
        , mutationRate   = 0.05
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }
      gen0 = mkStdGen 2026
      genomeLen = 20
      (rawPop, _, _) = runEvoM config gen0 (randomPopulation 40 genomeLen)
      initPop = map (\g -> Scored g (oneMaxFitness g)) rawPop

      frequencies = [2, 3, 4, 5, 7, 10, 13, 20, 40]

  putStrLn "Freq | Sched diff | Pop divergence | Hamming div    | Fitness diff | Best (single) | Best (composed)"
  putStrLn "---- | ---------- | -------------- | -------------- | ------------ | ------------- | ---------------"

  mapM_ (\freq -> do
    let iConfig = IslandConfig
          { islandCount    = 4
          , islandMigRate  = 0.1
          , islandMigFreq  = freq
          , islandTopology = IslandRing
          }
        -- Single 40-gen run
        single = islandStrategy iConfig (gaStep oneMaxFitness bitFlip) (AfterGens 40)
        -- Sequential 20+20
        composed = sequential
          (islandStrategy iConfig (gaStep oneMaxFitness bitFlip) (AfterGens 20))
          (islandStrategy iConfig (gaStep oneMaxFitness bitFlip) (AfterGens 20))

        (rSingle, _, _)   = runEvoM config (mkStdGen 42) (runStrategy single initPop)
        (rComposed, _, _) = runEvoM config (mkStdGen 42) (runStrategy composed initPop)

        -- Compare populations (sort by genome for deterministic comparison)
        sortByGenome = sortBy (comparing individual)
        singlePop   = map individual (sortByGenome (resultPop rSingle))
        composedPop = map individual (sortByGenome (resultPop rComposed))

        -- Compute divergence: fraction of individuals that differ
        divergence = fromIntegral (length (filter id (zipWith (/=) singlePop composedPop)))
                   / fromIntegral (length singlePop) :: Double

        -- Hamming-like divergence: average per-gene difference
        hammingDiv = if null singlePop then 0 else
          let dists = zipWith (\a b -> fromIntegral (length (filter id (zipWith (/=) a b)))
                                      / fromIntegral genomeLen :: Double)
                              singlePop composedPop
          in sum dists / fromIntegral (length dists)

        fitDiff = abs (fitness (resultBest rSingle) - fitness (resultBest rComposed))

        -- Number of migration events that differ between single and composed
        singleMigs = [g | g <- [1..39], g `mod` freq == 0]
        comp1Migs  = [g | g <- [1..19], g `mod` freq == 0]
        comp2Migs  = [20 + g | g <- [1..19], g `mod` freq == 0]
        composedMigs = comp1Migs ++ comp2Migs
        missingMigs = length [g | g <- singleMigs, g `notElem` composedMigs]
        extraMigs   = length [g | g <- composedMigs, g `notElem` singleMigs]
        schedDiff = missingMigs + extraMigs

    putStrLn $ padL 4 (show freq)
            ++ " | " ++ padL 10 (show schedDiff)
            ++ " | " ++ padL 14 (showF divergence)
            ++ " | " ++ padL 14 (showF hammingDiv)
            ++ " | " ++ padL 12 (showF fitDiff)
            ++ " | " ++ padL 13 (showF (fitness (resultBest rSingle)))
            ++ " | " ++ padL 15 (showF (fitness (resultBest rComposed)))
    ) frequencies

  putStrLn ""

  -- Part 2: Boundary position sweep (Claudius's Bernoulli trial prediction)
  putStrLn "=== Part 2: Boundary Position Sweep ==="
  putStrLn ""
  putStrLn "Fixed freq=5, total=40 gens. Vary composition boundary from 15 to 25."
  putStrLn "Migration events for single 40-gen run: {5,10,15,20,25,30,35}"
  putStrLn "Claudius predicts: divergence clusters near zero (boundary misses migration)"
  putStrLn "or jumps to characteristic magnitude (boundary hits migration)."
  putStrLn ""
  putStrLn "Boundary | Hits mig? | Sched diff | Pop divergence | Hamming div"
  putStrLn "-------- | --------- | ---------- | -------------- | -----------"

  let boundaries = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
      fixedFreq = 5

  mapM_ (\boundary -> do
    let iConfig = IslandConfig
          { islandCount    = 4
          , islandMigRate  = 0.1
          , islandMigFreq  = fixedFreq
          , islandTopology = IslandRing
          }
        totalG = 40
        -- Single run
        single = islandStrategy iConfig (gaStep oneMaxFitness bitFlip) (AfterGens totalG)
        -- Composed: boundary gens + (totalG - boundary) gens
        composed = sequential
          (islandStrategy iConfig (gaStep oneMaxFitness bitFlip) (AfterGens boundary))
          (islandStrategy iConfig (gaStep oneMaxFitness bitFlip) (AfterGens (totalG - boundary)))

        (rSingle, _, _)   = runEvoM config (mkStdGen 42) (runStrategy single initPop)
        (rComposed, _, _) = runEvoM config (mkStdGen 42) (runStrategy composed initPop)

        sortByGenome = sortBy (comparing individual)
        singlePop   = map individual (sortByGenome (resultPop rSingle))
        composedPop = map individual (sortByGenome (resultPop rComposed))

        divergence = fromIntegral (length (filter id (zipWith (/=) singlePop composedPop)))
                   / fromIntegral (length singlePop) :: Double

        hammingDiv = if null singlePop then 0 else
          let dists = zipWith (\a b -> fromIntegral (length (filter id (zipWith (/=) a b)))
                                      / fromIntegral genomeLen :: Double)
                              singlePop composedPop
          in sum dists / fromIntegral (length dists)

        -- Schedule analysis
        singleMigs = [g | g <- [1..totalG-1], g `mod` fixedFreq == 0]
        comp1Migs  = [g | g <- [1..boundary-1], g `mod` fixedFreq == 0]
        comp2Migs  = [boundary + g | g <- [1..totalG-boundary-1], g `mod` fixedFreq == 0]
        composedMigs = comp1Migs ++ comp2Migs
        missingMigs = length [g | g <- singleMigs, g `notElem` composedMigs]
        extraMigs   = length [g | g <- composedMigs, g `notElem` singleMigs]
        schedDiff = missingMigs + extraMigs

        hitsM = boundary `mod` fixedFreq == 0

    putStrLn $ padL 8 (show boundary)
            ++ " | " ++ padL 9 (if hitsM then "YES" else "no")
            ++ " | " ++ padL 10 (show schedDiff)
            ++ " | " ++ padL 14 (showF divergence)
            ++ " | " ++ padL 11 (showF hammingDiv)
    ) boundaries

  putStrLn ""
  putStrLn "Key observations:"
  putStrLn "  Part 1: At freq=40 (no migration): STRICT functor — populations identical"
  putStrLn "          At all other frequencies: LAX functor — populations diverge"
  putStrLn "  Part 2: Bernoulli trial structure — divergence depends on whether"
  putStrLn "          the composition boundary hits a migration event"

showF :: Double -> String
showF d
  | isNaN d || isInfinite d = "NaN"
  | otherwise = show (fromIntegral (round (d * 1000) :: Int) / 1000.0 :: Double)

padL :: Int -> String -> String
padL n s = replicate (max 0 (n - length s)) ' ' ++ s
