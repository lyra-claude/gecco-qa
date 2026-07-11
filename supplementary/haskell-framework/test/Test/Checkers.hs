module Test.Checkers (runTests) where

import System.Random (mkStdGen)

import Evolution.Effects
import Evolution.Pipeline
import Evolution.Examples.Checkers

-- | Run checkers tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Checkers tests ---"
  failures <- sequence
    [ test "initial board has 24 pieces"     testInitialPieceCount
    , test "initial board has 12 per side"   testInitialSides
    , test "black moves first"               testBlackFirst
    , test "legal moves from start"          testLegalMovesFromStart
    , test "move changes board"              testMoveChangesBoard
    , test "features are 10-dimensional"     testFeaturesDim
    , test "default weights are 10-dim"      testWeightsDim
    , test "linear eval returns a number"    testLinearEval
    , test "game terminates"                 testGameTerminates
    , test "gaussian perturb changes value"  testGaussianPerturb
    , test "random weights in range"         testRandomWeightsRange
    , test "GA improves over random"         testGAImproves
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

-- | Initial board should have 24 pieces (12 black, 12 white).
testInitialPieceCount :: Bool
testInitialPieceCount =
  let gs = newGame
      pieces = filter (/= Empty) (gsBoard gs)
  in length pieces == 24

-- | 12 pieces per side.
testInitialSides :: Bool
testInitialSides =
  let gs = newGame
      blacks = filter (\p -> p == BMan || p == BKing) (gsBoard gs)
      whites = filter (\p -> p == WMan || p == WKing) (gsBoard gs)
  in length blacks == 12 && length whites == 12

-- | Black moves first.
testBlackFirst :: Bool
testBlackFirst = gsTurn newGame == Black

-- | There should be legal moves from the starting position.
testLegalMovesFromStart :: Bool
testLegalMovesFromStart =
  let moves = legalMoves newGame
  in length moves == 7  -- 7 possible opening moves for black

-- | Making a move should change the board.
testMoveChangesBoard :: Bool
testMoveChangesBoard =
  let gs = newGame
      moves = legalMoves gs
      gs' = makeMove gs (head moves)
  in gsBoard gs /= gsBoard gs'
     && gsTurn gs' == White

-- | Feature extraction should return 10 values.
testFeaturesDim :: Bool
testFeaturesDim =
  let feats = extractFeatures newGame
  in length feats == 10

-- | Default weights should be 10-dimensional.
testWeightsDim :: Bool
testWeightsDim = length defaultWeights == 10

-- | Linear eval should return a finite number.
testLinearEval :: Bool
testLinearEval =
  let score = linearEval defaultWeights newGame
  in not (isNaN score) && not (isInfinite score)

-- | A match should terminate and produce a valid win rate.
testGameTerminates :: Bool
testGameTerminates =
  let gen0 = mkStdGen 42
      -- Play 2 games with default weights vs default weights
      (winRate, _) = playMatch defaultWeights defaultWeights 2 gen0
  in winRate >= 0.0 && winRate <= 1.0

-- | Gaussian perturbation should sometimes change the value.
testGaussianPerturb :: Bool
testGaussianPerturb =
  let config = defaultConfig
      gen = mkStdGen 999
      (results, _, _) = runEvoM config gen $ do
        vs <- mapM (\_ -> gaussianPerturb 1.0) [1..20 :: Int]
        return vs
      -- At least some should differ from 1.0
  in any (/= 1.0) results

-- | Random weights should be in [-2, 2] range.
testRandomWeightsRange :: Bool
testRandomWeightsRange =
  let config = defaultConfig
      gen = mkStdGen 777
      (ws, _, _) = runEvoM config gen randomWeights
  in length ws == 10 && all (\w -> w >= -2.0 && w <= 2.0) ws

-- | GA should produce weights that beat random weights.
testGAImproves :: Bool
testGAImproves =
  let config = defaultConfig
        { populationSize = 15
        , maxGenerations = 10
        , mutationRate   = 0.2
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }
      gen0 = mkStdGen 54321
      (initPop, gen', _) = runEvoM config gen0
                            (randomWeightPop (populationSize config))
      -- Simple fitness: beat random-weight opponents
      randomOpponents = [ [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
                        , [-0.1, 0.2, 0.0, 0.3, -0.2, 0.1, 0.0, 0.1, -0.1, 0.2]
                        ]
      fitFunc = weightFitness randomOpponents 2
      result = evolve fitFunc gaussianPerturb config gen' initPop
      -- Best evolved fitness should be > 0.3 (better than chance against weak opponents)
  in bestFitness' result > 0.3
