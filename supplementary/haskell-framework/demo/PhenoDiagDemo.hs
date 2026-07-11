{-# LANGUAGE ScopedTypeVariables #-}

-- | Phenotypic diversity diagnostics for GP experiments.
--
-- Robin's directive: rule out neutral bloat inflating diversity trajectories.
--
-- The concern: genotypic diversity (tree size variance) might increase during
-- the "diversify" phase of hourglass, but this could be neutral bloat —
-- larger trees that compute the same function. If phenotypic diversity
-- (output variance) doesn't track genotypic diversity, the diversity
-- story is weaker.
--
-- Diagnostics:
--   1. Genotypic vs phenotypic diversity correlation per generation
--   2. Tree size distribution at key phase transitions
--   3. Semantic uniqueness: how many distinct outputs does the population have?
--   4. Effective population size: individuals with distinct behavior
module Main (main) where

import Control.Monad.Reader (local)
import Data.List (nub)
import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators (elitistSelect)
import Evolution.Examples.SymbolicRegression

-- | Test data: y = x^2 + x
testData :: [(Double, Double)]
testData = [(x, x*x + x) | x <- [-5.0, -4.5 .. 5.0]]

fitFunc :: Expr -> Double
fitFunc = regressionFitness testData

-- | Comprehensive per-generation metrics.
data DiagMetrics = DiagMetrics
  { dGen         :: !Int
  , dBestFit     :: !Double
  , dAvgFit      :: !Double
  , dGenoDiv     :: !Double   -- tree size variance
  , dPhenoDiv    :: !Double   -- output variance across test points
  , dAvgSize     :: !Double   -- average tree size
  , dMinSize     :: !Int      -- smallest tree
  , dMaxSize     :: !Int      -- largest tree
  , dSemanticUni :: !Int      -- number of semantically distinct individuals
  , dEffPopSize  :: !Int      -- individuals with unique output signatures
  , dBloatRatio  :: !Double   -- avg size / min size that achieves same best fitness
  } deriving (Show)

-- | Compute diagnostic metrics.
computeDiag :: Int -> [Scored Expr] -> DiagMetrics
computeDiag gen pop = DiagMetrics
  { dGen         = gen
  , dBestFit     = if null pop then 0 else maximum (map fitness pop)
  , dAvgFit      = if null pop then 0 else sum (map fitness pop) / fromIntegral n
  , dGenoDiv     = sizeVar
  , dPhenoDiv    = phenoVar
  , dAvgSize     = avgSize
  , dMinSize     = if null sizes' then 0 else minimum sizes'
  , dMaxSize     = if null sizes' then 0 else maximum sizes'
  , dSemanticUni = semanticUnique
  , dEffPopSize  = effectivePopSize
  , dBloatRatio  = bloatR
  }
  where
    n = length pop
    sizes' = map (size . individual) pop
    sizes = map fromIntegral sizes' :: [Double]
    avgSize = if n == 0 then 0 else sum sizes / fromIntegral n

    -- Genotypic diversity: tree size variance
    sizeVar = if n == 0 then 0
              else sum (map (\sz -> (sz - avgSize) ** 2) sizes) / fromIntegral n

    -- Phenotypic diversity: output variance across test points
    testXs = map fst testData
    phenoVar = avgOutputVariance testXs pop

    -- Semantic uniqueness: discretize outputs and count distinct signatures
    outputSigs = map (outputSignature testXs) pop
    semanticUnique = length (nub outputSigs)

    -- Effective population size (same as semantic uniqueness here)
    effectivePopSize = semanticUnique

    -- Bloat ratio: average size / size of best-fit individual
    bestSize = case filter (\s -> fitness s == maximum (map fitness pop)) pop of
                 (s:_) -> fromIntegral (size (individual s))
                 []    -> 1.0
    bloatR = if bestSize > 0 then avgSize / bestSize else 1.0

-- | Output signature: discretized evaluation at test points.
-- Two trees with the same signature are semantically equivalent.
outputSignature :: [Double] -> Scored Expr -> [Int]
outputSignature xs scored =
  map (\x -> discretize (clamp (eval x (individual scored)))) xs
  where
    discretize v = round (v * 10) :: Int  -- 0.1 precision
    clamp v = if isNaN v || isInfinite v then 0 else max (-1e6) (min 1e6 v)

-- | Average variance of predictions across the population.
avgOutputVariance :: [Double] -> [Scored Expr] -> Double
avgOutputVariance xs pop
  | null pop || null xs = 0
  | otherwise =
      let nPop = length pop
          variances = map (\x ->
            let outputs = map (\s -> clamp (eval x (individual s))) pop
                mu = sum outputs / fromIntegral nPop
            in sum (map (\o -> (o - mu) ** 2) outputs) / fromIntegral nPop
            ) xs
      in sum variances / fromIntegral (length variances)
  where
    clamp v = if isNaN v || isInfinite v then 0 else max (-1e6) (min 1e6 v)

-- | GP step function.
gpStep :: [Scored Expr] -> EvoM [Scored Expr]
gpStep pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: treeCrossover
           >>>: treeMutate
           >>>: pointwise (\s -> Scored (individual s) (fitFunc (individual s)))

-- | GP step with overridden parameters.
gpStepWith :: Double -> Int -> [Scored Expr] -> EvoM [Scored Expr]
gpStepWith mutRate tSize pop =
  local (\c -> c { mutationRate = mutRate, tournamentSize = tSize }) $
    gpStep pop

-- | Tracked evolution loop with diagnostic metrics.
trackedDiag :: Int -> (Int -> [Scored Expr] -> EvoM [Scored Expr])
            -> [Scored Expr] -> EvoM ([Scored Expr], [DiagMetrics])
trackedDiag nGens step pop0 = go 0 pop0 [computeDiag 0 pop0]
  where
    go gen pop acc
      | gen >= nGens = return (pop, reverse acc)
      | otherwise = do
          pop' <- step gen pop
          let m = computeDiag (gen + 1) pop'
          go (gen + 1) pop' (m : acc)

-- | Hourglass with diagnostics.
runHourglassDiag :: Int -> Int -> Int -> [Scored Expr]
                 -> EvoM ([Scored Expr], [DiagMetrics])
runHourglassDiag exploreN convergeN diversifyN pop0 = do
  (pop1, m1) <- trackedDiag exploreN (\_ pop -> gpStepWith 0.30 2 pop) pop0
  (pop2, m2) <- trackedDiag convergeN (\_ pop -> gpStepWith 0.02 7 pop) pop1
  (pop3, m3) <- trackedDiag diversifyN (\_ pop -> gpStepWith 0.15 3 pop) pop2
  let offset1 = exploreN
      offset2 = exploreN + convergeN
      metrics = m1
             ++ map (\m -> m { dGen = dGen m + offset1 }) (tail m2)
             ++ map (\m -> m { dGen = dGen m + offset2 }) (tail m3)
  return (pop3, metrics)

-- | Flat GA with diagnostics.
runFlatDiag :: Int -> [Scored Expr] -> EvoM ([Scored Expr], [DiagMetrics])
runFlatDiag nGens = trackedDiag nGens (\_ pop -> gpStep pop)

main :: IO ()
main = do
  putStrLn "================================================================"
  putStrLn "  PHENOTYPIC DIVERSITY DIAGNOSTICS"
  putStrLn "  Ruling out neutral bloat in GP diversity trajectories"
  putStrLn "================================================================"
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
  putStrLn ""

  -- Run hourglass
  let ((_hPop, hMetrics), _, _) = runEvoM config gen1
        (runHourglassDiag 15 10 25 initPop)

  putStrLn "=== HOURGLASS (explore 15 -> converge 10 -> diversify 25) ==="
  putStrLn ""
  putStrLn "Gen  | GenoDiv  PhenoDiv | AvgSize Min Max | SemUniq EffPop | BloatR"
  putStrLn "---- | -------- -------- | ------- --- --- | ------- ------ | ------"
  mapM_ (\m ->
    putStrLn $ padL 4 (show (dGen m))
            ++ " | " ++ padL 8 (showF (dGenoDiv m))
            ++ " " ++ padL 8 (showF (dPhenoDiv m))
            ++ " | " ++ padL 7 (showF (dAvgSize m))
            ++ " " ++ padL 3 (show (dMinSize m))
            ++ " " ++ padL 3 (show (dMaxSize m))
            ++ " | " ++ padL 7 (show (dSemanticUni m))
            ++ " " ++ padL 6 (show (dEffPopSize m))
            ++ " | " ++ padL 6 (showF (dBloatRatio m))
    ) (every 5 hMetrics)
  putStrLn ""

  -- Run flat for comparison
  let ((_fPop, fMetrics), _, _) = runEvoM config gen1
        (runFlatDiag totalGens initPop)

  putStrLn "=== FLAT GENERATIONAL (50 gens, baseline) ==="
  putStrLn ""
  putStrLn "Gen  | GenoDiv  PhenoDiv | AvgSize Min Max | SemUniq EffPop | BloatR"
  putStrLn "---- | -------- -------- | ------- --- --- | ------- ------ | ------"
  mapM_ (\m ->
    putStrLn $ padL 4 (show (dGen m))
            ++ " | " ++ padL 8 (showF (dGenoDiv m))
            ++ " " ++ padL 8 (showF (dPhenoDiv m))
            ++ " | " ++ padL 7 (showF (dAvgSize m))
            ++ " " ++ padL 3 (show (dMinSize m))
            ++ " " ++ padL 3 (show (dMaxSize m))
            ++ " | " ++ padL 7 (show (dSemanticUni m))
            ++ " " ++ padL 6 (show (dEffPopSize m))
            ++ " | " ++ padL 6 (showF (dBloatRatio m))
    ) (every 5 fMetrics)
  putStrLn ""

  -- Key diagnostic: correlation between genotypic and phenotypic diversity
  putStrLn "=== DIAGNOSTIC: Genotypic vs Phenotypic Correlation ==="
  putStrLn ""
  putStrLn "If bloat inflates genotypic diversity without phenotypic change,"
  putStrLn "we'd see genotypic diversity rise while semantic uniqueness stays flat."
  putStrLn ""

  -- Phase analysis for hourglass
  let exploreMetrics = filter (\m -> dGen m >= 0 && dGen m <= 15) hMetrics
      convergeMetrics = filter (\m -> dGen m > 15 && dGen m <= 25) hMetrics
      diversifyMetrics = filter (\m -> dGen m > 25) hMetrics

      avgGenoDiv ms = if null ms then 0 else sum (map dGenoDiv ms) / fromIntegral (length ms)
      avgPhenoDiv ms = if null ms then 0 else sum (map dPhenoDiv ms) / fromIntegral (length ms)
      avgSemUniq ms = if null ms then 0 else sum (map (fromIntegral . dSemanticUni) ms) / fromIntegral (length ms) :: Double
      avgBloat ms = if null ms then 0 else sum (map dBloatRatio ms) / fromIntegral (length ms)

  putStrLn "Phase      | AvgGenoDiv | AvgPhenoDiv | AvgSemUniq | AvgBloat"
  putStrLn "---------- | ---------- | ----------- | ---------- | --------"
  putStrLn $ "Explore    | " ++ padL 10 (showF (avgGenoDiv exploreMetrics))
          ++ " | " ++ padL 11 (showF (avgPhenoDiv exploreMetrics))
          ++ " | " ++ padL 10 (showF (avgSemUniq exploreMetrics))
          ++ " | " ++ padL 8 (showF (avgBloat exploreMetrics))
  putStrLn $ "Converge   | " ++ padL 10 (showF (avgGenoDiv convergeMetrics))
          ++ " | " ++ padL 11 (showF (avgPhenoDiv convergeMetrics))
          ++ " | " ++ padL 10 (showF (avgSemUniq convergeMetrics))
          ++ " | " ++ padL 8 (showF (avgBloat convergeMetrics))
  putStrLn $ "Diversify  | " ++ padL 10 (showF (avgGenoDiv diversifyMetrics))
          ++ " | " ++ padL 11 (showF (avgPhenoDiv diversifyMetrics))
          ++ " | " ++ padL 10 (showF (avgSemUniq diversifyMetrics))
          ++ " | " ++ padL 8 (showF (avgBloat diversifyMetrics))
  putStrLn ""

  -- Verdict
  let diversifyGeno = avgGenoDiv diversifyMetrics
      diversifySem = avgSemUniq diversifyMetrics
      genoRebounds = diversifyGeno > avgGenoDiv convergeMetrics
      semRebounds = diversifySem > avgSemUniq convergeMetrics
  putStrLn "=== VERDICT ==="
  putStrLn $ "Genotypic diversity rebounds in diversify phase: " ++ show genoRebounds
  putStrLn $ "Semantic uniqueness rebounds in diversify phase: " ++ show semRebounds
  if genoRebounds && semRebounds
    then putStrLn "CONCLUSION: Diversity rebound is GENUINE (not neutral bloat)"
    else if genoRebounds && not semRebounds
      then putStrLn "CONCLUSION: Diversity rebound is BLOAT (genotypic without semantic)"
      else putStrLn "CONCLUSION: No clear rebound detected"

-- Helpers

every :: Int -> [a] -> [a]
every _ [] = []
every n (x:xs) = x : every n (drop (n - 1) xs)

showF :: Double -> String
showF d
  | isNaN d || isInfinite d = "NaN"
  | otherwise = show (fromIntegral (round (d * 100) :: Int) / 100.0 :: Double)

padL :: Int -> String -> String
padL n s = replicate (max 0 (n - length s)) ' ' ++ s
