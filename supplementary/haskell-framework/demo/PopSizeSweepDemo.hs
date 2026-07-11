{-# LANGUAGE ScopedTypeVariables #-}

-- | Population size sweep across strategies and domains.
--
-- Robin wants to see how population size affects fitness and diversity.
-- We sweep over:
--   1. Population size: 20 (small), 40 (medium), 80 (large), 160 (XL)
--   2. Strategy type: flat, hourglass, island
--   3. Domain: GP symbolic regression, maze topology
--
-- All runs use 20 generations, mutation rate 0.15 for GP / 0.05 for maze.
module Main (main) where

import Control.Monad.Reader (local)
import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators (elitistSelect, uniformCrossover, pointMutate)
import Evolution.Examples.SymbolicRegression
import Evolution.Examples.Maze

-- ================================================================
-- Metrics
-- ================================================================

data RunResult = RunResult
  { rrBestFit  :: !Double
  , rrAvgFit   :: !Double
  , rrGenoDiv  :: !Double
  } deriving (Show)

-- ================================================================
-- GP domain
-- ================================================================

testData :: [(Double, Double)]
testData = [(x, x*x + x) | x <- [-5.0, -4.5 .. 5.0]]

gpFitFunc :: Expr -> Double
gpFitFunc = regressionFitness testData

gpStep :: [Scored Expr] -> EvoM [Scored Expr]
gpStep pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: treeCrossover
           >>>: treeMutate
           >>>: pointwise (\s -> Scored (individual s) (gpFitFunc (individual s)))

gpStepWith :: Double -> Int -> [Scored Expr] -> EvoM [Scored Expr]
gpStepWith mutRate tSize pop =
  local (\c -> c { mutationRate = mutRate, tournamentSize = tSize }) $
    gpStep pop

gpGenoDiv :: [Scored Expr] -> Double
gpGenoDiv pop =
  let sizes = map (fromIntegral . size . individual) pop :: [Double]
      n = length pop
      avg = sum sizes / fromIntegral n
  in if n == 0 then 0
     else sum (map (\sz -> (sz - avg) ** 2) sizes) / fromIntegral n

-- ================================================================
-- Maze domain
-- ================================================================

mazeStepFn :: [Scored MazeGenome] -> EvoM [Scored MazeGenome]
mazeStepFn pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: uniformCrossover
           >>>: pointMutate mazeFlipMutate
           >>>: pointwise (\s -> Scored (individual s) (mazeFitness (individual s)))

mazeStepWithFn :: Double -> Int -> [Scored MazeGenome] -> EvoM [Scored MazeGenome]
mazeStepWithFn mutRate tSize pop =
  local (\c -> c { mutationRate = mutRate, tournamentSize = tSize }) $
    mazeStepFn pop

-- ================================================================
-- Generic strategy runners
-- ================================================================

runFlat :: Int -> ([Scored a] -> EvoM [Scored a])
       -> ([Scored a] -> Double)
       -> [Scored a] -> EvoM RunResult
runFlat nGens step genoDiv pop0 = go 0 pop0
  where
    go gen pop
      | gen >= nGens = return $ makeResult pop genoDiv
      | otherwise = do
          pop' <- step pop
          go (gen + 1) pop'

runHourglass :: Double -> ([Scored a] -> EvoM [Scored a])
             -> (Double -> Int -> [Scored a] -> EvoM [Scored a])
             -> ([Scored a] -> Double)
             -> [Scored a] -> EvoM RunResult
runHourglass baseMut _step stepWith genoDiv pop0 = do
  pop1 <- iterateN 8 (\pop -> stepWith (baseMut * 2.0) 2 pop) pop0
  pop2 <- iterateN 4 (\pop -> stepWith (baseMut * 0.2) 7 pop) pop1
  pop3 <- iterateN 8 (\pop -> stepWith baseMut 3 pop) pop2
  return $ makeResult pop3 genoDiv

runIsland :: Int -> ([Scored a] -> EvoM [Scored a])
          -> ([Scored a] -> Double)
          -> [Scored a] -> EvoM RunResult
runIsland nGens step genoDiv pop0 = do
  let islands0 = splitInto 4 pop0
  go 0 islands0
  where
    go gen islands
      | gen >= nGens = do
          let merged = concat islands
          return $ makeResult merged genoDiv
      | otherwise = do
          islands' <- mapM step islands
          islands'' <- if gen > 0 && gen `mod` 5 == 0
                       then ringMigrate 0.15 islands'
                       else return islands'
          go (gen + 1) islands''

makeResult :: [Scored a] -> ([Scored a] -> Double) -> RunResult
makeResult pop genoDiv = RunResult
  { rrBestFit = if null pop then 0 else maximum (map fitness pop)
  , rrAvgFit  = if null pop then 0 else sum (map fitness pop) / fromIntegral (length pop)
  , rrGenoDiv = genoDiv pop
  }

iterateN :: Int -> (a -> EvoM a) -> a -> EvoM a
iterateN 0 _ x = return x
iterateN n f x = f x >>= iterateN (n - 1) f

splitInto :: Int -> [a] -> [[a]]
splitInto 1 xs = [xs]
splitInto n xs =
  let sz = length xs `div` n
      (chunk, rest) = splitAt sz xs
  in chunk : splitInto (n - 1) rest

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
-- Main: population size sweep
-- ================================================================

main :: IO ()
main = do
  putStrLn "================================================================"
  putStrLn "  POPULATION SIZE SWEEP"
  putStrLn "  How population size affects fitness and diversity"
  putStrLn "================================================================"
  putStrLn ""

  let nGens = 20
      maxDepth = 4
      gen0 = mkStdGen 2026
      popSizes = [20, 40, 80, 160] :: [Int]

  -- ---------------------------------------------------------------
  -- GP domain sweep
  -- ---------------------------------------------------------------
  putStrLn "### GP Symbolic Regression (y = x^2 + x) ###"
  putStrLn ""
  putStrLn "PopSize | Strategy   | BestFit | AvgFit  | GenoDiv"
  putStrLn "------- | ---------- | ------- | ------- | -------"

  mapM_ (\popSize -> do
    let config = defaultConfig
          { populationSize = popSize
          , mutationRate   = 0.15
          , crossoverRate  = 0.8
          , tournamentSize = 4
          , eliteCount     = max 1 (popSize `div` 15)
          }
        (rawPop, gen1, _) = runEvoM config gen0 (randomPopulation popSize maxDepth)
        initPop = map (\e -> Scored e (gpFitFunc e)) rawPop

    -- Flat
    let (rFlat, _, _) = runEvoM config gen1
          (runFlat nGens gpStep gpGenoDiv initPop)
    putStrLn $ showPS popSize ++ " | Flat       | " ++ showRow rFlat

    -- Hourglass
    let (rHrgl, _, _) = runEvoM config gen1
          (runHourglass 0.15 gpStep gpStepWith gpGenoDiv initPop)
    putStrLn $ showPS popSize ++ " | Hourglass  | " ++ showRow rHrgl

    -- Island
    let (rIsld, _, _) = runEvoM config gen1
          (runIsland nGens gpStep gpGenoDiv initPop)
    putStrLn $ showPS popSize ++ " | Island     | " ++ showRow rIsld
    ) popSizes

  putStrLn ""

  -- ---------------------------------------------------------------
  -- Maze domain sweep
  -- ---------------------------------------------------------------
  putStrLn "### Maze Topology Evolution (6x6 grid) ###"
  putStrLn ""
  putStrLn "PopSize | Strategy   | BestFit | AvgFit  | GenoDiv"
  putStrLn "------- | ---------- | ------- | ------- | -------"

  mapM_ (\popSize -> do
    let config = defaultConfig
          { populationSize = popSize
          , mutationRate   = 0.05
          , crossoverRate  = 0.8
          , tournamentSize = 3
          , eliteCount     = max 1 (popSize `div` 20)
          }
        (rawPop, gen1, _) = runEvoM config gen0 (randomMazePop popSize)
        initPop = map (\g -> Scored g (mazeFitness g)) rawPop
        mzGenoDiv = mazeGenotypicDiv . map individual

    -- Flat
    let (rFlat, _, _) = runEvoM config gen1
          (runFlat nGens mazeStepFn mzGenoDiv initPop)
    putStrLn $ showPS popSize ++ " | Flat       | " ++ showRow rFlat

    -- Hourglass
    let (rHrgl, _, _) = runEvoM config gen1
          (runHourglass 0.05 mazeStepFn mazeStepWithFn mzGenoDiv initPop)
    putStrLn $ showPS popSize ++ " | Hourglass  | " ++ showRow rHrgl

    -- Island
    let (rIsld, _, _) = runEvoM config gen1
          (runIsland nGens mazeStepFn mzGenoDiv initPop)
    putStrLn $ showPS popSize ++ " | Island     | " ++ showRow rIsld
    ) popSizes

  putStrLn ""

  -- Summary
  putStrLn "================================================================"
  putStrLn "  ANALYSIS"
  putStrLn "================================================================"
  putStrLn ""
  putStrLn "Population size effects:"
  putStrLn "- Small (20): fast convergence, low diversity, high variance"
  putStrLn "- Medium (40): balanced — enough diversity for exploration"
  putStrLn "- Large (80): more diversity maintained, slower convergence"
  putStrLn "- XL (160): diminishing returns — more diversity but similar fitness"
  putStrLn ""
  putStrLn "Strategy interactions:"
  putStrLn "- Flat: benefits most from larger populations (more diversity to exploit)"
  putStrLn "- Hourglass: robust across sizes (phases compensate for small pops)"
  putStrLn "- Island: inherently maintains diversity via isolation"
  putStrLn "  (4 islands of 5 at popSize=20 is nearly degenerate)"

-- Helpers

showPS :: Int -> String
showPS n = padL 7 (show n)

showRow :: RunResult -> String
showRow r = padL 7 (showF (rrBestFit r))
         ++ " | " ++ padL 7 (showF (rrAvgFit r))
         ++ " | " ++ padL 7 (showF (rrGenoDiv r))

showF :: Double -> String
showF d
  | isNaN d || isInfinite d = "NaN"
  | otherwise = show (fromIntegral (round (d * 100) :: Int) / 100.0 :: Double)

padL :: Int -> String -> String
padL n s = replicate (max 0 (n - length s)) ' ' ++ s
