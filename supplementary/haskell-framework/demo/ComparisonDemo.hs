{-# LANGUAGE ScopedTypeVariables #-}

-- | Strategy comparison demo: three compositions on symbolic regression,
-- tracking diversity trajectories per generation.
--
-- Validates Claudius's predictions:
--   1. Hourglass shows "diversity dip" at bottleneck then re-expansion
--   2. Flat generational shows monotonic diversity decline
--   3. Different compositions produce qualitatively different dynamics
--
-- Three strategies on y = x^2 + x:
--   1. Flat generational GA (baseline)
--   2. Hourglass: explore(high mut) -> converge(low mut) -> diversify(med mut)
--   3. Island GA with 4 sub-populations and ring migration
module Main (main) where

import Control.Monad.Reader (local)
import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators (elitistSelect)
import Evolution.Examples.SymbolicRegression

-- | Per-generation metrics for comparison.
data GenMetrics = GenMetrics
  { mGen      :: !Int
  , mBestFit  :: !Double
  , mAvgFit   :: !Double
  , mGenoDiv  :: !Double   -- tree size variance
  , mPhenoDiv :: !Double   -- output variance across test points
  } deriving (Show)

-- | Test data: y = x^2 + x
testData :: [(Double, Double)]
testData = [(x, x*x + x) | x <- [-5.0, -4.5 .. 5.0]]

fitFunc :: Expr -> Double
fitFunc = regressionFitness testData

-- | Compute diversity metrics for a scored GP population.
computeMetrics :: Int -> [Scored Expr] -> GenMetrics
computeMetrics gen pop = GenMetrics
  { mGen      = gen
  , mBestFit  = if null pop then 0 else maximum (map fitness pop)
  , mAvgFit   = if null pop then 0 else s / fromIntegral n
  , mGenoDiv  = sizeVar
  , mPhenoDiv = phenoVar
  }
  where
    n = length pop
    s = sum (map fitness pop)
    -- Genotypic diversity: tree size variance
    sizes = map (fromIntegral . size . individual) pop :: [Double]
    avgSize = sum sizes / fromIntegral n
    sizeVar = sum (map (\sz -> (sz - avgSize) ** 2) sizes) / fromIntegral n
    -- Phenotypic diversity: average output variance across test points
    testXs = map fst testData
    phenoVar = avgOutputVariance testXs pop

-- | Average variance of predictions across the population, over test points.
avgOutputVariance :: [Double] -> [Scored Expr] -> Double
avgOutputVariance xs pop
  | null pop || null xs = 0
  | otherwise =
      let nPop = length pop
          -- For each test point, compute variance of predictions
          variances = map (\x ->
            let outputs = map (\s -> clamp (eval x (individual s))) pop
                mu = sum outputs / fromIntegral nPop
            in sum (map (\o -> (o - mu) ** 2) outputs) / fromIntegral nPop
            ) xs
      in sum variances / fromIntegral (length variances)
  where
    clamp v = if isNaN v || isInfinite v then 0 else max (-1e6) (min 1e6 v)

-- | One GP generation step: select -> crossover -> mutate -> evaluate.
gpStep :: [Scored Expr] -> EvoM [Scored Expr]
gpStep pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: treeCrossover
           >>>: treeMutate
           >>>: pointwise (\s -> Scored (individual s) (fitFunc (individual s)))

-- | GP step with overridden mutation rate and tournament size.
gpStepWith :: Double -> Int -> [Scored Expr] -> EvoM [Scored Expr]
gpStepWith mutRate tSize pop =
  local (\c -> c { mutationRate = mutRate, tournamentSize = tSize }) $
    gpStep pop

-- | Evolution loop with per-generation metric collection.
trackedLoop :: Int                                -- total generations
            -> (Int -> [Scored Expr] -> EvoM [Scored Expr])  -- step function
            -> [Scored Expr]                      -- initial population
            -> EvoM ([Scored Expr], [GenMetrics])
trackedLoop nGens step pop0 = go 0 pop0 [computeMetrics 0 pop0]
  where
    go gen pop acc
      | gen >= nGens = return (pop, reverse acc)
      | otherwise = do
          pop' <- step gen pop
          let m = computeMetrics (gen + 1) pop'
          go (gen + 1) pop' (m : acc)

-- ================================================================
-- Strategy 1: Flat generational GA (baseline)
-- ================================================================

runFlat :: Int -> [Scored Expr] -> EvoM ([Scored Expr], [GenMetrics])
runFlat nGens = trackedLoop nGens (\_ pop -> gpStep pop)

-- ================================================================
-- Strategy 2: Hourglass (explore -> converge -> diversify)
-- ================================================================

runHourglass :: Int -> Int -> Int -> [Scored Expr]
             -> EvoM ([Scored Expr], [GenMetrics])
runHourglass exploreN convergeN diversifyN pop0 = do
  -- Phase 1: Explore — high mutation, weak selection
  (pop1, m1) <- trackedLoop exploreN
    (\_ pop -> gpStepWith 0.30 2 pop) pop0
  -- Phase 2: Converge — low mutation, strong selection
  (pop2, m2) <- trackedLoop convergeN
    (\_ pop -> gpStepWith 0.02 7 pop) pop1
  -- Phase 3: Diversify — medium mutation, medium selection
  (pop3, m3) <- trackedLoop diversifyN
    (\_ pop -> gpStepWith 0.15 3 pop) pop2
  -- Renumber and concatenate metrics
  let offset1 = exploreN
      offset2 = exploreN + convergeN
      metrics = m1
             ++ map (\m -> m { mGen = mGen m + offset1 }) (tail m2)
             ++ map (\m -> m { mGen = mGen m + offset2 }) (tail m3)
  return (pop3, metrics)

-- ================================================================
-- Strategy 3: Island GA with ring migration
-- ================================================================

runIsland :: Int -> Int -> Int -> Double -> [Scored Expr]
          -> EvoM ([Scored Expr], [GenMetrics])
runIsland nGens nIslands migFreq migRate pop0 = do
  let islands0 = splitInto nIslands pop0
  go 0 islands0 [computeMetrics 0 pop0]
  where
    go gen islands acc
      | gen >= nGens = do
          let merged = concat islands
          return (merged, reverse acc)
      | otherwise = do
          -- Evolve each island independently
          islands' <- mapM gpStep islands
          -- Migrate if it's time
          islands'' <- if gen > 0 && gen `mod` migFreq == 0
                       then ringMigrate migRate islands'
                       else return islands'
          let merged = concat islands''
              m = computeMetrics (gen + 1) merged
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
-- Strategy 4: Adaptive switching (conditional composition / coproduct)
--
-- Start with exploratory GP (high mutation). If fitness plateaus for
-- 5 consecutive generations, switch to focused GP (low mutation,
-- strong selection). The composition boundary is EMERGENT — chosen
-- at runtime by inspecting population state.
-- ================================================================

runAdaptive :: Int -> [Scored Expr] -> EvoM ([Scored Expr], [GenMetrics])
runAdaptive totalGens pop0 = go 0 pop0 (fitness (bestOf pop0)) (0 :: Int) False [computeMetrics 0 pop0]
  where
    go gen pop bestSoFar noImprove switched acc
      | gen >= totalGens = return (pop, reverse acc)
      | otherwise = do
          -- Choose step based on whether we've switched
          pop' <- if switched
                  then gpStepWith 0.02 7 pop  -- Focused: low mutation, strong selection
                  else gpStepWith 0.25 2 pop  -- Exploratory: high mutation, weak selection
          let currentBest = fitness (bestOf pop')
              improved = currentBest > bestSoFar
              noImprove' = if improved then 0 else noImprove + 1
              -- Switch if plateaued for 5 gens and haven't switched yet
              switch = not switched && noImprove' >= 5
              m = computeMetrics (gen + 1) pop'
          go (gen + 1) pop' (max bestSoFar currentBest)
             (if switch then 0 else noImprove')
             (switched || switch) (m : acc)

-- ================================================================
-- Main: run all four and compare
-- ================================================================

main :: IO ()
main = do
  putStrLn "=== Strategy Composition Comparison ==="
  putStrLn "Problem: Symbolic regression y = x^2 + x"
  putStrLn ""

  let totalGens = 50
      popSize = 60
      maxDepth = 4
      config = defaultConfig
        { populationSize = popSize
        , mutationRate   = 0.15
        , crossoverRate  = 0.8
        , tournamentSize = 4
        , eliteCount     = 3
        }
      gen0 = mkStdGen 2026

  -- Generate initial population
  let (rawPop, gen1, _) = runEvoM config gen0 (randomPopulation popSize maxDepth)
      initPop = map (\e -> Scored e (fitFunc e)) rawPop

  putStrLn $ "Initial population: " ++ show popSize ++ " trees"
  putStrLn $ "Initial best fitness: " ++ showF (fitness (bestOf initPop))
  putStrLn ""

  -- 1. Flat generational GA
  let (_, gen2, _) = runEvoM config gen1 (return ())
      ((_pop1, metrics1), _, _) = runEvoM config gen2 (runFlat totalGens initPop)
  putStrLn "--- Strategy 1: Flat Generational GA (50 gens) ---"
  printTrajectory metrics1
  putStrLn ""

  -- 2. Hourglass: explore(15) -> converge(10) -> diversify(25)
  let ((_pop2, metrics2), _, _) = runEvoM config gen2
        (runHourglass 15 10 25 initPop)
  putStrLn "--- Strategy 2: Hourglass (explore 15 -> converge 10 -> diversify 25) ---"
  printTrajectory metrics2
  putStrLn ""

  -- 3. Island GA: 4 islands, ring migration every 5 gens
  let ((_pop3, metrics3), _, _) = runEvoM config gen2
        (runIsland totalGens 4 5 0.15 initPop)
  putStrLn "--- Strategy 3: Island GA (4 islands, ring migration every 5 gens) ---"
  putStrLn "  (Parametric coupling — composition via migration natural transformation)"
  printTrajectory metrics3
  putStrLn ""

  -- 4. Adaptive switching: explore until plateau, then focus
  let ((_pop4, metrics4), _, _) = runEvoM config gen2
        (runAdaptive totalGens initPop)
  putStrLn "--- Strategy 4: Adaptive (explore -> plateau detection -> focus) ---"
  putStrLn "  (Conditional composition — coproduct with runtime predicate)"
  printTrajectory metrics4
  putStrLn ""

  -- Summary comparison: genotypic diversity
  putStrLn "=== Genotypic Diversity (tree size variance) ==="
  putStrLn ""
  putStrLn "Gen  | Flat    | Hrglass | Island  | Adaptive"
  putStrLn "---- | ------- | ------- | ------- | --------"
  let sampleGens = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
  mapM_ (\g -> do
    let m1 = findGen g metrics1
        m2 = findGen g metrics2
        m3 = findGen g metrics3
        m4 = findGen g metrics4
    putStrLn $ padL 4 (show g)
            ++ " | " ++ padL 7 (showF (maybe 0 mGenoDiv m1))
            ++ " | " ++ padL 7 (showF (maybe 0 mGenoDiv m2))
            ++ " | " ++ padL 7 (showF (maybe 0 mGenoDiv m3))
            ++ " | " ++ padL 8 (showF (maybe 0 mGenoDiv m4))
    ) sampleGens
  putStrLn ""

  -- Summary comparison: phenotypic diversity
  putStrLn "=== Phenotypic Diversity (output variance) ==="
  putStrLn ""
  putStrLn "Gen  | Flat    | Hrglass | Island  | Adaptive"
  putStrLn "---- | ------- | ------- | ------- | --------"
  mapM_ (\g -> do
    let m1 = findGen g metrics1
        m2 = findGen g metrics2
        m3 = findGen g metrics3
        m4 = findGen g metrics4
    putStrLn $ padL 4 (show g)
            ++ " | " ++ padL 7 (showF (maybe 0 mPhenoDiv m1))
            ++ " | " ++ padL 7 (showF (maybe 0 mPhenoDiv m2))
            ++ " | " ++ padL 7 (showF (maybe 0 mPhenoDiv m3))
            ++ " | " ++ padL 8 (showF (maybe 0 mPhenoDiv m4))
    ) sampleGens
  putStrLn ""

  -- Final fitness comparison
  putStrLn "=== Final Results ==="
  let lastM1 = last metrics1
      lastM2 = last metrics2
      lastM3 = last metrics3
      lastM4 = last metrics4
  putStrLn $ "Flat:      best=" ++ showF (mBestFit lastM1)
          ++ "  avg=" ++ showF (mAvgFit lastM1)
          ++ "  genoDiv=" ++ showF (mGenoDiv lastM1)
          ++ "  phenoDiv=" ++ showF (mPhenoDiv lastM1)
  putStrLn $ "Hourglass: best=" ++ showF (mBestFit lastM2)
          ++ "  avg=" ++ showF (mAvgFit lastM2)
          ++ "  genoDiv=" ++ showF (mGenoDiv lastM2)
          ++ "  phenoDiv=" ++ showF (mPhenoDiv lastM2)
  putStrLn $ "Island:    best=" ++ showF (mBestFit lastM3)
          ++ "  avg=" ++ showF (mAvgFit lastM3)
          ++ "  genoDiv=" ++ showF (mGenoDiv lastM3)
          ++ "  phenoDiv=" ++ showF (mPhenoDiv lastM3)
  putStrLn $ "Adaptive:  best=" ++ showF (mBestFit lastM4)
          ++ "  avg=" ++ showF (mAvgFit lastM4)
          ++ "  genoDiv=" ++ showF (mGenoDiv lastM4)
          ++ "  phenoDiv=" ++ showF (mPhenoDiv lastM4)
  putStrLn ""

  -- Best expressions found
  let best1 = bestOf _pop1
      best2 = bestOf _pop2
      best3 = bestOf _pop3
      best4 = bestOf _pop4
  putStrLn "Best expressions found:"
  putStrLn $ "  Flat:      " ++ showExpr (individual best1)
          ++ "  (fitness " ++ showF (fitness best1) ++ ")"
  putStrLn $ "  Hourglass: " ++ showExpr (individual best2)
          ++ "  (fitness " ++ showF (fitness best2) ++ ")"
  putStrLn $ "  Island:    " ++ showExpr (individual best3)
          ++ "  (fitness " ++ showF (fitness best3) ++ ")"
  putStrLn $ "  Adaptive:  " ++ showExpr (individual best4)
          ++ "  (fitness " ++ showF (fitness best4) ++ ")"

-- Helpers

bestOf :: [Scored a] -> Scored a
bestOf = head . sortBy (comparing (Down . fitness))

findGen :: Int -> [GenMetrics] -> Maybe GenMetrics
findGen g = go
  where go [] = Nothing
        go (m:ms) = if mGen m == g then Just m else go ms

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
