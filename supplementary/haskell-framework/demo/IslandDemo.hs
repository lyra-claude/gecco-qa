-- | Island model demo: OneMax with 4 islands and ring migration.
--
-- Compares single-population evolution against the island model.
-- Islands maintain diversity by evolving independently, then share
-- good solutions via periodic migration.
module Main (main) where

import System.Random (mkStdGen)

import Evolution.Effects
import Evolution.Pipeline
import Evolution.Island
import Evolution.Examples.BitString

main :: IO ()
main = do
  putStrLn "=== Island Model Demo: OneMax ==="
  putStrLn ""

  let genomeLen = 30
      totalPop  = 60
      nGens     = 60
      nIslands  = 4
      perIsland = totalPop `div` nIslands
      gen       = mkStdGen 42

      -- Single population config
      singleConfig = defaultConfig
        { populationSize = totalPop
        , maxGenerations = nGens
        , mutationRate   = 0.03
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }

      -- Island config (smaller populations per island)
      islandConfig = defaultConfig
        { populationSize = perIsland
        , maxGenerations = nGens
        , mutationRate   = 0.03
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 1
        }

      model = IslandModel
        { numIslands    = nIslands
        , migrationRate = 0.15
        , migrationFreq = 8
        , topology      = Ring
        }

      -- Run single population
      (singlePop, gen1, _) = runEvoM singleConfig gen $
        randomPopulation totalPop genomeLen
      singleResult = evolve oneMaxFitness bitFlip singleConfig gen1 singlePop

      -- Run island model
      (islandPops, gen2, _) = runEvoM islandConfig gen $
        mapM (\_ -> randomPopulation perIsland genomeLen) [1..nIslands]
      islands = uniformIslands oneMaxFitness bitFlip islandPops
      islandResult = evolveIslands model oneMaxFitness islandConfig gen2 islands

  putStrLn $ "Genome length: " ++ show genomeLen
  putStrLn $ "Total population: " ++ show totalPop
  putStrLn $ "Generations: " ++ show nGens
  putStrLn ""

  putStrLn "--- Single Population ---"
  putStrLn $ "Best fitness: " ++ show (bestFitness' singleResult)
                              ++ " / " ++ show genomeLen
  putStrLn $ "Best genome:  " ++ showBits (bestIndividual singleResult)
  let singleStats = generations (evoLog singleResult)
  putStrLn $ "Fitness trajectory: "
    ++ showTrajectory (map bestFitness singleStats)
  putStrLn ""

  putStrLn $ "--- Island Model (" ++ show nIslands
    ++ " islands, ring migration every "
    ++ show (migrationFreq model) ++ " gens) ---"
  putStrLn $ "Best fitness: " ++ show (bestIslandFitness islandResult)
                              ++ " / " ++ show genomeLen
  putStrLn $ "Best genome:  " ++ showBits (bestIslandIndividual islandResult)
  let islandStats = generations (islandLog islandResult)
  putStrLn $ "Fitness trajectory: "
    ++ showTrajectory (map bestFitness islandStats)
  putStrLn ""

  -- Show per-island diversity
  putStrLn "Per-island best fitness:"
  let islandBests = map (\pop ->
          maximum (map oneMaxFitness pop)
        ) (allIslandPops islandResult)
  mapM_ (\(i, b) -> putStrLn $ "  Island " ++ show i
                              ++ ": " ++ show b
                              ++ " / " ++ show genomeLen
    ) (zip [1::Int ..] islandBests)

showBits :: [Bool] -> String
showBits = map (\b -> if b then '1' else '0')

-- | Show a sampled trajectory (every 5th value)
showTrajectory :: [Double] -> String
showTrajectory xs =
  let sampled = [xs !! i | i <- [0, 5 .. length xs - 1]]
  in unwords (map showF sampled)

showF :: Double -> String
showF d = show (round d :: Int)
