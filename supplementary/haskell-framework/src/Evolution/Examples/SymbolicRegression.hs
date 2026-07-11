{-# LANGUAGE ScopedTypeVariables #-}

-- | Genetic Programming: symbolic regression with expression trees.
--
-- This example goes beyond flat bitstring genomes. Here, individuals are
-- expression trees, and the genetic operators (crossover, mutation) work
-- on tree structure rather than linear sequences.
--
-- Since our 'GeneticOp' type is generic over individual types, we can
-- use exactly the same categorical composition for tree-based GP as for
-- bitstring GA. The category doesn't care about the representation —
-- only that operators compose.
--
-- == The GP pipeline
--
-- @
--   evaluate fitFunc >>>: tournamentSelect >>>: treeCrossover >>>: treeMutate
-- @
--
-- Same structure as the bitstring pipeline, but the operators know how to
-- manipulate trees instead of lists.
module Evolution.Examples.SymbolicRegression
  ( -- * Expression trees
    Expr(..)
  , eval
  , showExpr
  , depth
  , size
    -- * Random generation
  , randomExpr
  , randomPopulation
    -- * Genetic operators
  , treeCrossover
  , treeMutate
    -- * Tree operations
  , subtreeAt
  , replaceAt
    -- * Fitness
  , regressionFitness
    -- * Running
  , runSymbolicRegression
  ) where

import Data.List (sortBy)
import Control.Monad.Reader (ask)
import System.Random (mkStdGen)

import Evolution.Category
import Evolution.Effects
import Evolution.Operators

-- | Expression tree for symbolic regression.
-- Supports basic arithmetic over a single variable x.
data Expr
  = Var                    -- ^ The variable x
  | Const !Double          -- ^ A constant
  | Add !Expr !Expr        -- ^ Addition
  | Mul !Expr !Expr        -- ^ Multiplication
  | Sub !Expr !Expr        -- ^ Subtraction
  | Neg !Expr              -- ^ Negation
  deriving (Show, Eq)

-- | Evaluate an expression at a given x value.
eval :: Double -> Expr -> Double
eval x Var         = x
eval _ (Const c)   = c
eval x (Add a b)   = eval x a + eval x b
eval x (Mul a b)   = eval x a * eval x b
eval x (Sub a b)   = eval x a - eval x b
eval x (Neg a)     = negate (eval x a)

-- | Pretty-print an expression.
showExpr :: Expr -> String
showExpr Var         = "x"
showExpr (Const c)
  | c == fromIntegral (round c :: Int) = show (round c :: Int)
  | otherwise = show c
showExpr (Add a b)   = "(" ++ showExpr a ++ " + " ++ showExpr b ++ ")"
showExpr (Mul a b)   = "(" ++ showExpr a ++ " * " ++ showExpr b ++ ")"
showExpr (Sub a b)   = "(" ++ showExpr a ++ " - " ++ showExpr b ++ ")"
showExpr (Neg a)     = "(-" ++ showExpr a ++ ")"

-- | Tree depth.
depth :: Expr -> Int
depth Var       = 1
depth (Const _) = 1
depth (Add a b) = 1 + max (depth a) (depth b)
depth (Mul a b) = 1 + max (depth a) (depth b)
depth (Sub a b) = 1 + max (depth a) (depth b)
depth (Neg a)   = 1 + depth a

-- | Tree size (number of nodes).
size :: Expr -> Int
size Var       = 1
size (Const _) = 1
size (Add a b) = 1 + size a + size b
size (Mul a b) = 1 + size a + size b
size (Sub a b) = 1 + size a + size b
size (Neg a)   = 1 + size a

-- | Generate a random expression tree of bounded depth.
randomExpr :: Int -> EvoM Expr
randomExpr maxD
  | maxD <= 1 = do
      r <- randomDouble
      if r < 0.5
        then return Var
        else do
          c <- randomDouble
          let c' = (c - 0.5) * 10
          return (Const (fromIntegral (round c' :: Int)))
  | otherwise = do
      r <- randomDouble
      if r < 0.3
        then do
          r2 <- randomDouble
          if r2 < 0.5 then return Var
          else do
            c <- randomDouble
            return (Const (fromIntegral (round ((c - 0.5) * 10) :: Int)))
        else do
          r2 <- randomDouble
          if r2 < 0.1
            then Neg <$> randomExpr (maxD - 1)
            else do
              left  <- randomExpr (maxD - 1)
              right <- randomExpr (maxD - 1)
              r3 <- randomDouble
              return $ if r3 < 0.33 then Add left right
                       else if r3 < 0.66 then Mul left right
                       else Sub left right

-- | Generate a random population of expression trees.
randomPopulation :: Int -> Int -> EvoM [Expr]
randomPopulation popSize maxDepth =
  mapM (\_ -> randomExpr maxDepth) [1..popSize]

-- | Tree crossover: swap random subtrees between two parents.
treeCrossover :: GeneticOp EvoM (Scored Expr) (Scored Expr)
treeCrossover = liftMonadic $ \pop -> do
  cfg <- ask
  let rate = crossoverRate cfg
  go rate pop
  where
    go :: Double -> [Scored Expr] -> EvoM [Scored Expr]
    go _ [] = return []
    go _ [x] = return [x]
    go rate (p1:p2:rest) = do
      r <- randomDouble
      children <- if r < rate
        then do
          let t1 = individual p1
              t2 = individual p2
              s1 = size t1
              s2 = size t2
          pos1 <- randomInt 0 (s1 - 1)
          pos2 <- randomInt 0 (s2 - 1)
          let sub1 = subtreeAt pos1 t1
              sub2 = subtreeAt pos2 t2
              child1 = replaceAt pos1 sub2 t1
              child2 = replaceAt pos2 sub1 t2
          return [Scored child1 0, Scored child2 0]
        else return [p1 { fitness = 0 }, p2 { fitness = 0 }]
      rest' <- go rate rest
      return (children ++ rest')

-- | Tree mutation: replace a random subtree with a new random tree.
treeMutate :: GeneticOp EvoM (Scored Expr) (Scored Expr)
treeMutate = pointwiseM $ \scored -> do
  cfg <- ask
  let rate = mutationRate cfg
  r <- randomDouble
  if r < rate
    then do
      let t = individual scored
          s = size t
      pos <- randomInt 0 (s - 1)
      newSub <- randomExpr 3
      let t' = replaceAt pos newSub t
      return (Scored t' 0)
    else return scored

-- | Get the subtree at a given position (pre-order traversal index).
subtreeAt :: Int -> Expr -> Expr
subtreeAt 0 e = e
subtreeAt n (Add a b)
  | n <= size a = subtreeAt (n - 1) a
  | otherwise   = subtreeAt (n - 1 - size a) b
subtreeAt n (Mul a b)
  | n <= size a = subtreeAt (n - 1) a
  | otherwise   = subtreeAt (n - 1 - size a) b
subtreeAt n (Sub a b)
  | n <= size a = subtreeAt (n - 1) a
  | otherwise   = subtreeAt (n - 1 - size a) b
subtreeAt n (Neg a) = subtreeAt (n - 1) a
subtreeAt _ e = e

-- | Replace the subtree at a given position.
replaceAt :: Int -> Expr -> Expr -> Expr
replaceAt 0 new _ = new
replaceAt n new (Add a b)
  | n <= size a = Add (replaceAt (n - 1) new a) b
  | otherwise   = Add a (replaceAt (n - 1 - size a) new b)
replaceAt n new (Mul a b)
  | n <= size a = Mul (replaceAt (n - 1) new a) b
  | otherwise   = Mul a (replaceAt (n - 1 - size a) new b)
replaceAt n new (Sub a b)
  | n <= size a = Sub (replaceAt (n - 1) new a) b
  | otherwise   = Sub a (replaceAt (n - 1 - size a) new b)
replaceAt n new (Neg a) = Neg (replaceAt (n - 1) new a)
replaceAt _ _ e = e

-- | Fitness for symbolic regression.
-- Negative mean squared error over a set of (x, y) data points.
-- Higher is better (closer to 0 = better fit).
-- Includes parsimony pressure: larger trees are penalized, which
-- combats the "intron bloat" problem common in GP.
regressionFitness :: [(Double, Double)] -> Expr -> Double
regressionFitness dataPoints expr =
  let errors = map (\(x, y) ->
          let predicted = eval x expr
          in if isNaN predicted || isInfinite predicted
             then 1e6  -- Penalty for numerical instability
             else (predicted - y) ** 2
        ) dataPoints
      mse = sum errors / fromIntegral (length errors)
      -- Parsimony pressure: penalize tree size
      bloatPenalty = fromIntegral (size expr) * 0.01
  in negate (mse + bloatPenalty)

-- | Run symbolic regression to discover a formula.
runSymbolicRegression :: [(Double, Double)] -> IO ()
runSymbolicRegression dataPoints = do
  let gen0 = mkStdGen 42
      config = defaultConfig
        { populationSize = 100
        , maxGenerations = 80
        , mutationRate   = 0.15
        , crossoverRate  = 0.8
        , tournamentSize = 5
        , eliteCount     = 3
        }
      fitFunc = regressionFitness dataPoints

      gpPipeline :: Int -> GeneticOp EvoM Expr Expr
      gpPipeline gen =
        evaluate fitFunc
          >>>: logGeneration gen
          >>>: elitistSelect
          >>>: treeCrossover
          >>>: treeMutate
          >>>: pointwise individual

      (initPop, gen', _) = runEvoM config gen0 $
        randomPopulation (populationSize config) 4

      maxGen = maxGenerations config
      (finalPop, _, log') = runEvoM config gen' $ evolveLoop gpPipeline 0 maxGen initPop

      scored = map (\e -> Scored e (fitFunc e)) finalPop
      best = head $ sortBy (\a b -> compare (fitness b) (fitness a)) scored

  putStrLn "=== Symbolic Regression ==="
  putStrLn ""
  putStrLn $ "Training points: " ++ show (length dataPoints)
  putStrLn $ "Best expression: " ++ showExpr (individual best)
  putStrLn $ "Fitness (neg MSE): " ++ showF4 (fitness best)
  putStrLn $ "Tree depth: " ++ show (depth (individual best))
  putStrLn $ "Tree size:  " ++ show (size (individual best))
  putStrLn ""
  putStrLn "Predictions vs actual:"
  mapM_ (\(x, y) ->
      let yPred = eval x (individual best)
      in putStrLn $ "  x=" ++ padLeft 6 (showF2 x)
                  ++ " actual=" ++ padLeft 9 (showF2 y)
                  ++ " predicted=" ++ padLeft 9 (showF2 yPred)
    ) (take 10 dataPoints)
  putStrLn ""
  putStrLn "Fitness over generations (sampled):"
  let stats = generations log'
  mapM_ (\gs -> putStrLn $ "  Gen " ++ padLeft 3 (show (genNumber gs))
                         ++ ": best=" ++ padLeft 10 (showF2 (bestFitness gs))
                         ++ " avg=" ++ padLeft 10 (showF2 (avgFitness gs))
    ) (every 10 stats)
  where
    evolveLoop :: (Int -> GeneticOp EvoM Expr Expr) -> Int -> Int -> [Expr] -> EvoM [Expr]
    evolveLoop pipe gen maxG pop
      | gen >= maxG = return pop
      | otherwise = do
          pop' <- runOp (pipe gen) pop
          evolveLoop pipe (gen + 1) maxG pop'

    every :: Int -> [a] -> [a]
    every _ [] = []
    every n xs = Prelude.head xs : every n (drop n xs)

    showF2 :: Double -> String
    showF2 d = show (fromIntegral (round (d * 100) :: Int) / 100.0 :: Double)

    showF4 :: Double -> String
    showF4 d = show (fromIntegral (round (d * 10000) :: Int) / 10000.0 :: Double)

    padLeft :: Int -> String -> String
    padLeft n s = replicate (n - length s) ' ' ++ s
