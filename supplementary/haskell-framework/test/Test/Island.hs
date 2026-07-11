module Test.Island (runTests) where

import System.Random (mkStdGen)

import Evolution.Effects
import Evolution.Pipeline
import Evolution.Island
import Evolution.Examples.BitString

-- | Run island model tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Island model tests ---"
  failures <- sequence
    [ test "uniform islands created correctly" testUniformIslands
    , test "ring migration moves individuals"  testRingMigration
    , test "island model improves fitness"     testIslandModelImproves
    , test "multiple islands beat single"      testIslandsBeatSingle
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

testConfig :: GAConfig
testConfig = defaultConfig
  { populationSize = 20
  , maxGenerations = 30
  , mutationRate   = 0.03
  , crossoverRate  = 0.7
  , tournamentSize = 3
  , eliteCount     = 2
  }

-- | uniformIslands creates the right number of islands
testUniformIslands :: Bool
testUniformIslands =
  let gen = mkStdGen 42
      genomeLen = 10
      nIslands = 3
      (pops, _, _) = runEvoM testConfig gen $ do
        mapM (\_ -> randomPopulation (populationSize testConfig) genomeLen)
             [1..nIslands]
      islands = uniformIslands oneMaxFitness bitFlip pops
  in length islands == nIslands
     && all (\isl -> length (islandPop isl) == populationSize testConfig) islands

-- | Ring migration changes island populations
testRingMigration :: Bool
testRingMigration =
  let gen = mkStdGen 42
      -- Create 3 islands with distinct populations
      pop1 = replicate 10 (replicate 10 True)   -- All 1s
      pop2 = replicate 10 (replicate 10 False)  -- All 0s
      pop3 = replicate 10 ([True, False, True, False, True, False, True, False, True, False])
      islands = [ Island pop1 (generationStep oneMaxFitness bitFlip)
                , Island pop2 (generationStep oneMaxFitness bitFlip)
                , Island pop3 (generationStep oneMaxFitness bitFlip)
                ]
      (migrated, _, _) = runEvoM testConfig gen (ringMigrate 0.2 islands)
      -- After migration, island 2 should have some individuals from island 1
      -- (ring sends i → i+1 mod n, so island 0 → island 1)
      pop2After = islandPop (migrated !! 1)
      -- At least one all-True genome should now be in island 2
      hasAllTrue = any (all (== True)) pop2After
  in hasAllTrue

-- | Island model evolution should improve fitness
testIslandModelImproves :: Bool
testIslandModelImproves =
  let gen = mkStdGen 12345
      genomeLen = 15
      nIslands = 3
      model = IslandModel
        { numIslands    = nIslands
        , migrationRate = 0.1
        , migrationFreq = 5
        , topology      = Ring
        }
      (pops, gen', _) = runEvoM testConfig gen $ do
        mapM (\_ -> randomPopulation (populationSize testConfig) genomeLen)
             [1..nIslands]
      islands = uniformIslands oneMaxFitness bitFlip pops
      result = evolveIslands model oneMaxFitness testConfig gen' islands
  in bestIslandFitness result >= fromIntegral genomeLen * 0.7

-- | Multiple islands should find better solutions than a single population
-- (on average, by exploring more of the search space)
testIslandsBeatSingle :: Bool
testIslandsBeatSingle =
  let gen = mkStdGen 999
      genomeLen = 20
      nIslands = 4
      totalPop = 40  -- Same total population as single
      perIsland = totalPop `div` nIslands
      islandConfig = testConfig
        { populationSize = perIsland
        , maxGenerations = 40
        }
      singleConfig = testConfig
        { populationSize = totalPop
        , maxGenerations = 40
        }
      model = IslandModel
        { numIslands    = nIslands
        , migrationRate = 0.1
        , migrationFreq = 5
        , topology      = Ring
        }
      -- Single population run
      (singlePop, gen1, _) = runEvoM singleConfig gen $
        randomPopulation totalPop genomeLen
      singleResult = evolve oneMaxFitness bitFlip singleConfig gen1 singlePop
      -- Island model run
      (islandPops, gen2, _) = runEvoM islandConfig gen $ do
        mapM (\_ -> randomPopulation perIsland genomeLen) [1..nIslands]
      islands = uniformIslands oneMaxFitness bitFlip islandPops
      islandResult = evolveIslands model oneMaxFitness islandConfig gen2 islands
      -- Island model should do at least as well (with some margin for randomness)
  in bestIslandFitness islandResult >= bestFitness' singleResult - 2.0
