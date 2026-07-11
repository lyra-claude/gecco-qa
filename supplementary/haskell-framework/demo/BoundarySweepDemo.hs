{-# LANGUAGE ScopedTypeVariables #-}

-- | Hourglass boundary position sweep across GP and Maze domains.
--
-- Robin wants to see how the composition boundary position affects
-- fitness and diversity. We fix total generations at 20 and vary
-- where the explore→converge→diversify transitions occur.
--
-- Boundary configurations (total = 20 gens):
--   1. Early converge:  explore=4,  converge=4,  diversify=12
--   2. Balanced:        explore=6,  converge=4,  diversify=10
--   3. Late converge:   explore=10, converge=4,  diversify=6
--   4. Long converge:   explore=6,  converge=8,  diversify=6
--   5. No converge:     explore=10, converge=0,  diversify=10
module Main (main) where

import Control.Monad.Reader (local)
import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators (elitistSelect, uniformCrossover, pointMutate)
import Evolution.Examples.SymbolicRegression
import Evolution.Examples.Maze

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

-- | GP genotypic diversity (tree size variance).
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

mzStep :: [Scored MazeGenome] -> EvoM [Scored MazeGenome]
mzStep pop = runOp pipeline pop
  where
    pipeline = elitistSelect
           >>>: uniformCrossover
           >>>: pointMutate mazeFlipMutate
           >>>: pointwise (\s -> Scored (individual s) (mazeFitness (individual s)))

mzStepWith :: Double -> Int -> [Scored MazeGenome] -> EvoM [Scored MazeGenome]
mzStepWith mutRate tSize pop =
  local (\c -> c { mutationRate = mutRate, tournamentSize = tSize }) $
    mzStep pop

-- | Maze genotypic diversity.
mzGenoDiv :: [Scored MazeGenome] -> Double
mzGenoDiv = mazeGenotypicDiv . map individual

-- ================================================================
-- Generic hourglass runner
-- ================================================================

data HourglassResult = HourglassResult
  { hrBestFit  :: !Double
  , hrAvgFit   :: !Double
  , hrGenoDiv  :: !Double
  } deriving (Show)

-- | Run hourglass with given phase lengths.
runHourglass :: Double  -- base mutation rate
             -> ([Scored a] -> EvoM [Scored a])
             -> (Double -> Int -> [Scored a] -> EvoM [Scored a])
             -> ([Scored a] -> Double)
             -> Int -> Int -> Int  -- explore, converge, diversify lengths
             -> [Scored a]
             -> EvoM HourglassResult
runHourglass baseMut _step stepWith genoDiv exploreN convergeN diversifyN pop0 = do
  pop1 <- iterN exploreN  (\pop -> stepWith (baseMut * 2.0) 2 pop) pop0
  pop2 <- iterN convergeN (\pop -> stepWith (baseMut * 0.2) 7 pop) pop1
  pop3 <- iterN diversifyN (\pop -> stepWith baseMut 3 pop) pop2
  let n = length pop3
  return HourglassResult
    { hrBestFit = if null pop3 then 0 else maximum (map fitness pop3)
    , hrAvgFit  = if null pop3 then 0 else sum (map fitness pop3) / fromIntegral n
    , hrGenoDiv = genoDiv pop3
    }

iterN :: Int -> (a -> EvoM a) -> a -> EvoM a
iterN 0 _ x = return x
iterN n f x = f x >>= iterN (n - 1) f

main :: IO ()
main = do
  putStrLn "================================================================"
  putStrLn "  HOURGLASS BOUNDARY POSITION SWEEP"
  putStrLn "  How the composition transition point affects outcomes"
  putStrLn "================================================================"
  putStrLn ""

  let popSize = 40
      gen0 = mkStdGen 2026

  -- Boundary configurations
  let configs =
        [ ("Early converge  (4/4/12)",  4, 4, 12)
        , ("Balanced        (6/4/10)",  6, 4, 10)
        , ("Late converge  (10/4/6)",  10, 4,  6)
        , ("Long converge   (6/8/6)",   6, 8,  6)
        , ("No converge    (10/0/10)", 10, 0, 10)
        ]

  -- ---------------------------------------------------------------
  -- GP domain
  -- ---------------------------------------------------------------
  putStrLn "### GP Symbolic Regression (y = x^2 + x) ###"
  putStrLn ""
  let gpConfig = defaultConfig
        { populationSize = popSize
        , mutationRate   = 0.15
        , crossoverRate  = 0.8
        , tournamentSize = 4
        , eliteCount     = 3
        }
      (gpRawPop, gpGen1, _) = runEvoM gpConfig gen0
        (randomPopulation popSize 4)
      gpInitPop = map (\e -> Scored e (gpFitFunc e)) gpRawPop

  putStrLn "Config                    | BestFit | AvgFit  | GenoDiv"
  putStrLn "------------------------- | ------- | ------- | -------"

  mapM_ (\(name, e, c, d) -> do
    let (result, _, _) = runEvoM gpConfig gpGen1
          (runHourglass 0.15 gpStep gpStepWith gpGenoDiv e c d gpInitPop)
    putStrLn $ padR 25 name
            ++ " | " ++ padL 7 (showF (hrBestFit result))
            ++ " | " ++ padL 7 (showF (hrAvgFit result))
            ++ " | " ++ padL 7 (showF (hrGenoDiv result))
    ) configs
  putStrLn ""

  -- ---------------------------------------------------------------
  -- Maze domain
  -- ---------------------------------------------------------------
  putStrLn "### Maze Topology Evolution (6x6 grid) ###"
  putStrLn ""
  let mzConfig = defaultConfig
        { populationSize = popSize
        , mutationRate   = 0.05
        , crossoverRate  = 0.8
        , tournamentSize = 3
        , eliteCount     = 2
        }
      (mzRawPop, mzGen1, _) = runEvoM mzConfig gen0 (randomMazePop popSize)
      mzInitPop = map (\g -> Scored g (mazeFitness g)) mzRawPop

  putStrLn "Config                    | BestFit | AvgFit  | GenoDiv"
  putStrLn "------------------------- | ------- | ------- | -------"

  mapM_ (\(name, e, c, d) -> do
    let (result, _, _) = runEvoM mzConfig mzGen1
          (runHourglass 0.05 mzStep mzStepWith mzGenoDiv e c d mzInitPop)
    putStrLn $ padR 25 name
            ++ " | " ++ padL 7 (showF (hrBestFit result))
            ++ " | " ++ padL 7 (showF (hrAvgFit result))
            ++ " | " ++ padL 7 (showF (hrGenoDiv result))
    ) configs
  putStrLn ""

  putStrLn "=== ANALYSIS ==="
  putStrLn ""
  putStrLn "The composition boundary position controls the balance between:"
  putStrLn "- Exploration time (more → wider search, higher diversity)"
  putStrLn "- Convergence time (more → better exploitation, lower diversity)"
  putStrLn "- Diversification time (more → recovery of lost diversity)"
  putStrLn ""
  putStrLn "Expected: 'balanced' and 'late converge' should achieve best fitness,"
  putStrLn "while 'no converge' preserves diversity at the cost of convergence."

-- Helpers

showF :: Double -> String
showF d
  | isNaN d || isInfinite d = "NaN"
  | otherwise = show (fromIntegral (round (d * 100) :: Int) / 100.0 :: Double)

padL :: Int -> String -> String
padL n s = replicate (max 0 (n - length s)) ' ' ++ s

padR :: Int -> String -> String
padR n s = s ++ replicate (max 0 (n - length s)) ' '
