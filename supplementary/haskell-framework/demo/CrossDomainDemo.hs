{-# LANGUAGE ScopedTypeVariables #-}

-- | Cross-domain comparison: same three strategy compositions applied to
-- structurally different genome types.
--
-- Domain 1: Checkers weight evolution (10 real-valued weights)
-- Domain 2: Maze topology evolution (60-bit binary wall vector)
--
-- Robin's directive: "DO IT" — run hourglass, island, flat on both domains,
-- show the framework applies across genotype spaces.
--
-- For each domain we track:
--   * Genotypic diversity (domain-specific)
--   * Phenotypic diversity (domain-specific)
--   * Best fitness per generation
--   * Average fitness per generation
module Main (main) where

import Control.Monad.Reader (local)
import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators (elitistSelect, uniformCrossover, pointMutate)
import Evolution.Examples.Checkers
import Evolution.Examples.Maze

-- ================================================================
-- Generic per-generation metrics
-- ================================================================

data GenMetrics = GenMetrics
  { mGen      :: !Int
  , mBestFit  :: !Double
  , mAvgFit   :: !Double
  , mGenoDiv  :: !Double
  , mPhenoDiv :: !Double
  } deriving (Show)

-- ================================================================
-- Checkers domain
-- ================================================================

-- | Opponents with diverse play styles for checkers fitness evaluation.
-- Default weights + strategic variants (material-heavy, king-heavy, positional).
checkersOpponents :: ([[Double]])
checkersOpponents =
  [ defaultWeights                                          -- balanced
  , [2.0, 1.0, 0.3, 0.1, 0.1, 0.05, 0.15, 0.1, 0.3, 0.05]  -- material-heavy
  , [0.5, 3.0, 0.3, 0.1, 0.1, 0.05, 0.15, 0.1, 1.0, 0.05]  -- king-focused
  , [0.3, 0.3, 1.0, 1.0, 0.5, 0.5, 0.3, 0.5, 0.3, 0.3]     -- positional
  ]

-- | Checkers fitness: win rate against opponent pool.
checkersFit :: [[Double]] -> WeightGenome -> Double
checkersFit opponents = weightFitness opponents 2

-- | Checkers step function: select -> crossover -> mutate -> evaluate.
checkersStep :: (WeightGenome -> Double)
             -> [Scored WeightGenome] -> EvoM [Scored WeightGenome]
checkersStep fitFunc pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: uniformCrossover
           >>>: pointMutate gaussianPerturb
           >>>: pointwise (\s -> Scored (individual s) (fitFunc (individual s)))

-- | Checkers step with overridden parameters.
checkersStepWith :: Double -> Int
                 -> (WeightGenome -> Double)
                 -> [Scored WeightGenome] -> EvoM [Scored WeightGenome]
checkersStepWith mutRate tSize fitFunc pop =
  local (\c -> c { mutationRate = mutRate, tournamentSize = tSize }) $
    checkersStep fitFunc pop

-- | Checkers genotypic diversity: variance of weight values across population.
checkersGenoDiv :: [WeightGenome] -> Double
checkersGenoDiv [] = 0
checkersGenoDiv genomes =
  let n = length genomes
      nWeights = 10 :: Int
      -- Average pairwise L2 distance (sampled)
      pairs = take 20 [(i, j) | i <- [0..n-2], j <- [i+1..n-1]]
      dists = map (\(i, j) ->
        let a = genomes !! i
            b = genomes !! j
        in sqrt (sum (zipWith (\x y -> (x - y) ** 2) a b))
           / fromIntegral nWeights
        ) pairs
  in if null dists then 0 else sum dists / fromIntegral (length dists)

-- | Checkers phenotypic diversity: variance of fitness values.
checkersPhenoDiv :: (WeightGenome -> Double) -> [WeightGenome] -> Double
checkersPhenoDiv fitFunc genomes =
  let fits = map fitFunc genomes
      n = length fits
      mu = sum fits / fromIntegral n
  in if n == 0 then 0
     else sum (map (\x -> (x - mu) ** 2) fits) / fromIntegral n

-- | Compute metrics for checkers population.
checkersMetrics :: (WeightGenome -> Double) -> Int -> [Scored WeightGenome] -> GenMetrics
checkersMetrics fitFunc gen pop = GenMetrics
  { mGen      = gen
  , mBestFit  = if null pop then 0 else maximum (map fitness pop)
  , mAvgFit   = if null pop then 0 else sum (map fitness pop) / fromIntegral (length pop)
  , mGenoDiv  = checkersGenoDiv (map individual pop)
  , mPhenoDiv = checkersPhenoDiv fitFunc (map individual pop)
  }

-- ================================================================
-- Maze domain
-- ================================================================

-- | Maze step function: select -> crossover -> mutate -> evaluate.
mazeStep :: [Scored MazeGenome] -> EvoM [Scored MazeGenome]
mazeStep pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: uniformCrossover
           >>>: pointMutate mazeFlipMutate
           >>>: pointwise (\s -> Scored (individual s) (mazeFitness (individual s)))

-- | Maze step with overridden parameters.
mazeStepWith :: Double -> Int -> [Scored MazeGenome] -> EvoM [Scored MazeGenome]
mazeStepWith mutRate tSize pop =
  local (\c -> c { mutationRate = mutRate, tournamentSize = tSize }) $
    mazeStep pop

-- | Compute metrics for maze population.
mazeMetrics :: Int -> [Scored MazeGenome] -> GenMetrics
mazeMetrics gen pop = GenMetrics
  { mGen      = gen
  , mBestFit  = if null pop then 0 else maximum (map fitness pop)
  , mAvgFit   = if null pop then 0 else sum (map fitness pop) / fromIntegral (length pop)
  , mGenoDiv  = mazeGenotypicDiv (map individual pop)
  , mPhenoDiv = mazePhenotypicDiv (map individual pop)
  }

-- ================================================================
-- Generic tracked evolution loop
-- ================================================================

-- | Evolution loop with per-generation metric collection.
-- Generic over genome type via the metrics function.
trackedLoop :: (Int -> [Scored a] -> GenMetrics)   -- compute metrics
            -> Int                                 -- total generations
            -> (Int -> [Scored a] -> EvoM [Scored a])  -- step function
            -> [Scored a]                          -- initial population
            -> EvoM ([Scored a], [GenMetrics])
trackedLoop computeM nGens step pop0 = go 0 pop0 [computeM 0 pop0]
  where
    go gen pop acc
      | gen >= nGens = return (pop, reverse acc)
      | otherwise = do
          pop' <- step gen pop
          let m = computeM (gen + 1) pop'
          go (gen + 1) pop' (m : acc)

-- ================================================================
-- Three strategy compositions
-- ================================================================

-- | Strategy 1: Flat generational GA (baseline).
runFlat :: (Int -> [Scored a] -> GenMetrics)
        -> ([Scored a] -> EvoM [Scored a])
        -> Int -> [Scored a]
        -> EvoM ([Scored a], [GenMetrics])
runFlat computeM step nGens = trackedLoop computeM nGens (\_ pop -> step pop)

-- | Strategy 2: Hourglass (explore -> converge -> diversify).
runHourglass :: (Int -> [Scored a] -> GenMetrics)
             -> (Double -> Int -> [Scored a] -> EvoM [Scored a])  -- step with params
             -> Int -> Int -> Int -> [Scored a]
             -> EvoM ([Scored a], [GenMetrics])
runHourglass computeM stepWith exploreN convergeN diversifyN pop0 = do
  -- Phase 1: Explore — high mutation, weak selection
  (pop1, m1) <- trackedLoop computeM exploreN
    (\_ pop -> stepWith 0.30 2 pop) pop0
  -- Phase 2: Converge — low mutation, strong selection
  (pop2, m2) <- trackedLoop computeM convergeN
    (\_ pop -> stepWith 0.02 7 pop) pop1
  -- Phase 3: Diversify — medium mutation, medium selection
  (pop3, m3) <- trackedLoop computeM diversifyN
    (\_ pop -> stepWith 0.15 3 pop) pop2
  -- Renumber and concatenate metrics
  let offset1 = exploreN
      offset2 = exploreN + convergeN
      metrics = m1
             ++ map (\m -> m { mGen = mGen m + offset1 }) (tail m2)
             ++ map (\m -> m { mGen = mGen m + offset2 }) (tail m3)
  return (pop3, metrics)

-- | Strategy 3: Island GA with ring migration.
runIsland :: (Int -> [Scored a] -> GenMetrics)
          -> ([Scored a] -> EvoM [Scored a])
          -> Int -> Int -> Int -> Double -> [Scored a]
          -> EvoM ([Scored a], [GenMetrics])
runIsland computeM step nGens nIslands migFreq migRate pop0 = do
  let islands0 = splitInto nIslands pop0
  go 0 islands0 [computeM 0 pop0]
  where
    go gen islands acc
      | gen >= nGens = do
          let merged = concat islands
          return (merged, reverse acc)
      | otherwise = do
          -- Evolve each island independently
          islands' <- mapM step islands
          -- Migrate if it's time
          islands'' <- if gen > 0 && gen `mod` migFreq == 0
                       then ringMigrate migRate islands'
                       else return islands'
          let merged = concat islands''
              m = computeM (gen + 1) merged
          go (gen + 1) islands'' (m : acc)

-- | Split a list into n roughly equal chunks.
splitInto :: Int -> [a] -> [[a]]
splitInto 1 xs = [xs]
splitInto n xs =
  let sz = length xs `div` n
      (chunk, rest) = splitAt sz xs
  in chunk : splitInto (n - 1) rest

-- | Ring migration: island i sends top migrants to island (i+1) mod n.
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

-- ================================================================
-- Main: run all three on both domains
-- ================================================================

main :: IO ()
main = do
  putStrLn "================================================================"
  putStrLn "  CROSS-DOMAIN STRATEGY COMPARISON"
  putStrLn "  Same categorical compositions, different genome spaces"
  putStrLn "================================================================"
  putStrLn ""

  let totalGens = 20
      popSize = 20
      gen0 = mkStdGen 2026

  -- ---------------------------------------------------------------
  -- Domain 1: Checkers weight evolution
  -- ---------------------------------------------------------------
  putStrLn "### Domain 1: Checkers Weight Evolution ###"
  putStrLn "Genome: 10 real-valued weights in [-5, 5]"
  putStrLn "Fitness: win rate against 2 opponents (2 games each)"
  putStrLn ""

  let checkersConfig = defaultConfig
        { populationSize = popSize
        , mutationRate   = 0.20
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }
      opps = checkersOpponents
      cFitFunc = checkersFit opps
      cMetrics = checkersMetrics cFitFunc

  -- Generate initial population
  let (cInitRaw, gen2, _) = runEvoM checkersConfig gen0 (randomWeightPop popSize)
      cInitPop = map (\g -> Scored g (cFitFunc g)) cInitRaw

  putStrLn $ "Initial best fitness: " ++ showF (maximum (map fitness cInitPop))
  putStrLn ""

  -- 1a. Flat generational
  let ((_cPop1, cM1), gen3, _) = runEvoM checkersConfig gen2
        (runFlat cMetrics (checkersStep cFitFunc) totalGens cInitPop)
  putStrLn "--- Checkers: Flat Generational (40 gens) ---"
  printTrajectory cM1
  putStrLn ""

  -- 1b. Hourglass: explore(12) -> converge(8) -> diversify(20)
  let ((cPop2, cM2), _, _) = runEvoM checkersConfig gen2
        (runHourglass cMetrics (checkersStepWith' cFitFunc) 6 4 10 cInitPop)
  putStrLn "--- Checkers: Hourglass (explore 6 -> converge 4 -> diversify 10) ---"
  printTrajectory cM2
  putStrLn ""

  -- 1c. Island GA: 4 islands, ring migration every 5 gens
  let ((_cPop3, cM3), _, _) = runEvoM checkersConfig gen2
        (runIsland cMetrics (checkersStep cFitFunc) totalGens 4 5 0.15 cInitPop)
  putStrLn "--- Checkers: Island GA (4 islands, ring every 5 gens) ---"
  printTrajectory cM3
  putStrLn ""

  -- ---------------------------------------------------------------
  -- Domain 2: Maze topology evolution
  -- ---------------------------------------------------------------
  putStrLn "### Domain 2: Maze Topology Evolution ###"
  putStrLn $ "Genome: " ++ show genomeLength ++ "-bit binary wall vector (" ++ show mazeSize ++ "x" ++ show mazeSize ++ " grid)"
  putStrLn "Fitness: solution length + dead-end ratio + branching factor"
  putStrLn ""

  let mazeConfig = defaultConfig
        { populationSize = popSize
        , mutationRate   = 0.05  -- Lower for binary genomes
        , crossoverRate  = 0.8
        , tournamentSize = 3
        , eliteCount     = 2
        }

  -- Generate initial population
  let (mInitRaw, gen4, _) = runEvoM mazeConfig gen3 (randomMazePop popSize)
      mInitPop = map (\g -> Scored g (mazeFitness g)) mInitRaw

  putStrLn $ "Initial best fitness: " ++ showF (maximum (map fitness mInitPop))
  putStrLn ""

  -- 2a. Flat generational
  let ((_mPop1, mM1), _, _) = runEvoM mazeConfig gen4
        (runFlat mazeMetrics mazeStep totalGens mInitPop)
  putStrLn "--- Maze: Flat Generational (40 gens) ---"
  printTrajectory mM1
  putStrLn ""

  -- 2b. Hourglass
  let ((mPop2, mM2), _, _) = runEvoM mazeConfig gen4
        (runHourglass mazeMetrics mazeStepWith 6 4 10 mInitPop)
  putStrLn "--- Maze: Hourglass (explore 6 -> converge 4 -> diversify 10) ---"
  printTrajectory mM2
  putStrLn ""

  -- 2c. Island GA
  let ((_mPop3, mM3), _, _) = runEvoM mazeConfig gen4
        (runIsland mazeMetrics mazeStep totalGens 4 5 0.15 mInitPop)
  putStrLn "--- Maze: Island GA (4 islands, ring every 5 gens) ---"
  printTrajectory mM3
  putStrLn ""

  -- ---------------------------------------------------------------
  -- Cross-domain comparison tables
  -- ---------------------------------------------------------------
  putStrLn "================================================================"
  putStrLn "  CROSS-DOMAIN GENOTYPIC DIVERSITY COMPARISON"
  putStrLn "================================================================"
  putStrLn ""
  putStrLn "Gen  | C:Flat  C:Hrgl  C:Isld | M:Flat  M:Hrgl  M:Isld"
  putStrLn "---- | ------  ------  ------ | ------  ------  ------"
  let sampleGens = [0, 5, 10, 15, 20]
  mapM_ (\g -> do
    let findG ms = findGen g ms
        c1 = maybe 0 mGenoDiv (findG cM1)
        c2 = maybe 0 mGenoDiv (findG cM2)
        c3 = maybe 0 mGenoDiv (findG cM3)
        m1 = maybe 0 mGenoDiv (findG mM1)
        m2 = maybe 0 mGenoDiv (findG mM2)
        m3 = maybe 0 mGenoDiv (findG mM3)
    putStrLn $ padL 4 (show g)
            ++ " | " ++ padL 6 (showF c1) ++ "  " ++ padL 6 (showF c2) ++ "  " ++ padL 6 (showF c3)
            ++ " | " ++ padL 6 (showF m1) ++ "  " ++ padL 6 (showF m2) ++ "  " ++ padL 6 (showF m3)
    ) sampleGens
  putStrLn ""

  putStrLn "================================================================"
  putStrLn "  CROSS-DOMAIN PHENOTYPIC DIVERSITY COMPARISON"
  putStrLn "================================================================"
  putStrLn ""
  putStrLn "Gen  | C:Flat  C:Hrgl  C:Isld | M:Flat  M:Hrgl  M:Isld"
  putStrLn "---- | ------  ------  ------ | ------  ------  ------"
  mapM_ (\g -> do
    let findG ms = findGen g ms
        c1 = maybe 0 mPhenoDiv (findG cM1)
        c2 = maybe 0 mPhenoDiv (findG cM2)
        c3 = maybe 0 mPhenoDiv (findG cM3)
        m1 = maybe 0 mPhenoDiv (findG mM1)
        m2 = maybe 0 mPhenoDiv (findG mM2)
        m3 = maybe 0 mPhenoDiv (findG mM3)
    putStrLn $ padL 4 (show g)
            ++ " | " ++ padL 6 (showF c1) ++ "  " ++ padL 6 (showF c2) ++ "  " ++ padL 6 (showF c3)
            ++ " | " ++ padL 6 (showF m1) ++ "  " ++ padL 6 (showF m2) ++ "  " ++ padL 6 (showF m3)
    ) sampleGens
  putStrLn ""

  -- ---------------------------------------------------------------
  -- Final fitness comparison
  -- ---------------------------------------------------------------
  putStrLn "================================================================"
  putStrLn "  FINAL RESULTS"
  putStrLn "================================================================"
  putStrLn ""
  let lastCM1 = last cM1; lastCM2 = last cM2; lastCM3 = last cM3
      lastMM1 = last mM1; lastMM2 = last mM2; lastMM3 = last mM3
  putStrLn "Domain    | Strategy   | BestFit | AvgFit  | GenoDiv | PhenoDiv"
  putStrLn "--------- | ---------- | ------- | ------- | ------- | --------"
  putStrLn $ "Checkers  | Flat       | " ++ row lastCM1
  putStrLn $ "Checkers  | Hourglass  | " ++ row lastCM2
  putStrLn $ "Checkers  | Island     | " ++ row lastCM3
  putStrLn $ "Maze      | Flat       | " ++ row lastMM1
  putStrLn $ "Maze      | Hourglass  | " ++ row lastMM2
  putStrLn $ "Maze      | Island     | " ++ row lastMM3
  putStrLn ""

  -- Show best maze
  putStrLn "Best maze found (Hourglass strategy):"
  putStrLn $ showMaze (individual (bestOf mPop2))

  -- Show best checkers weights
  let bestW = individual (bestOf cPop2)
  putStrLn "Best checkers weights (Hourglass strategy):"
  mapM_ (\(name, w) ->
    putStrLn $ "  " ++ padR 14 name ++ showF w
    ) (zip featureNames bestW)
  putStrLn ""

  -- Match: evolved vs default
  let (winRate, _) = playMatch bestW defaultWeights 20 gen4
  putStrLn $ "Evolved vs default (20 games): win rate = " ++ showF winRate

  where
    checkersStepWith' fitFunc mutRate tSize pop =
      checkersStepWith mutRate tSize fitFunc pop

-- ================================================================
-- Helpers
-- ================================================================

bestOf :: [Scored a] -> Scored a
bestOf = head . sortBy (comparing (Down . fitness))

findGen :: Int -> [GenMetrics] -> Maybe GenMetrics
findGen g = go
  where go [] = Nothing
        go (m:ms) = if mGen m == g then Just m else go ms

row :: GenMetrics -> String
row m = padL 7 (showF (mBestFit m))
     ++ " | " ++ padL 7 (showF (mAvgFit m))
     ++ " | " ++ padL 7 (showF (mGenoDiv m))
     ++ " | " ++ padL 8 (showF (mPhenoDiv m))

printTrajectory :: [GenMetrics] -> IO ()
printTrajectory ms = do
  putStrLn "  Gen  BestFit    AvgFit     GenoDiv    PhenoDiv"
  mapM_ (\m ->
    putStrLn $ "  " ++ padL 4 (show (mGen m))
            ++ "  " ++ padL 9 (showF (mBestFit m))
            ++ "  " ++ padL 9 (showF (mAvgFit m))
            ++ "  " ++ padL 9 (showF (mGenoDiv m))
            ++ "  " ++ padL 9 (showF (mPhenoDiv m))
    ) (every 5 ms)

every :: Int -> [a] -> [a]
every _ [] = []
every n (x:xs) = x : every n (drop (n - 1) xs)

showF :: Double -> String
showF d
  | isNaN d || isInfinite d = "NaN"
  | otherwise = show (fromIntegral (round (d * 100) :: Int) / 100.0 :: Double)

padL :: Int -> String -> String
padL n s = replicate (max 0 (n - length s)) ' ' ++ s

padR :: Int -> String -> String
padR n s = s ++ replicate (max 0 (n - length s)) ' '
