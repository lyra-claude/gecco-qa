{-# LANGUAGE ScopedTypeVariables #-}

-- | Checkers: evolving evaluation function weights via genetic algorithm.
--
-- Arthur Samuel (1959) trained checkers evaluation weights by self-play —
-- the first machine learning paper is also an evolutionary computation paper.
-- Here we make this connection explicit: the 10-weight evaluation function
-- is a genome, tournament play is fitness, and the categorical GA pipeline
-- discovers strong evaluation strategies.
--
-- == The Profound Connection
--
-- A checkers evaluation function is a linear combination:
--
-- @
--   score = w1*material + w2*kings + w3*center + ... + w10*protected
-- @
--
-- The weight vector @[w1..w10]@ IS a genome. Its fitness is how well
-- the resulting player performs in games. Selection, crossover, and
-- mutation on weight vectors compose as categorical morphisms — the
-- same pipeline that evolves bitstrings or symbolic regression trees.
--
-- == Pipeline
--
-- @
--   evaluate (checkersWinRate opponents depth)
--     >>>: logGeneration gen
--     >>>: elitistSelect
--     >>>: blendCrossover
--     >>>: gaussianMutate
-- @
--
-- Same structure as BitString.OneMax. Different genome type, different
-- fitness function, identical categorical composition.
module Evolution.Examples.Checkers
  ( -- * Board representation
    Piece(..)
  , Board
  , Color(..)
  , GameState(..)
    -- * Game logic
  , initialBoard
  , newGame
  , legalMoves
  , makeMove
  , gameOver
  , gameResult
    -- * Evaluation
  , Feature(..)
  , featureNames
  , extractFeatures
  , linearEval
  , defaultWeights
    -- * GA integration
  , WeightGenome
  , randomWeights
  , randomWeightPop
  , gaussianPerturb
  , weightFitness
  , playMatch
    -- * Running examples
  , runCheckersGA
  , showBoard
  ) where

import Control.Monad (replicateM)
import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import System.Random

import Evolution.Effects
import Evolution.Pipeline

-- ---------------------------------------------------------------------------
-- Board representation
-- ---------------------------------------------------------------------------

-- | Piece on a square.
data Piece = Empty | BMan | BKing | WMan | WKing
  deriving (Show, Eq, Ord)

-- | Player color.
data Color = Black | White
  deriving (Show, Eq, Ord)

-- | 32-square board. Index 0-31, mapping to dark squares of 8x8 grid.
-- Row r = sq `div` 4. Column depends on row parity:
--   Even rows: col = 2*(sq `mod` 4) + 1
--   Odd rows:  col = 2*(sq `mod` 4)
type Board = [Piece]

-- | Full game state.
data GameState = GameState
  { gsBoard    :: !Board
  , gsTurn     :: !Color
  , gsHalfMoves :: !Int  -- ^ Moves since last capture (draw detection)
  } deriving (Show, Eq)

-- | A move: list of square indices [from, to] or [from, over1, over2, ..., to]
type Move = [Int]

-- | Square index to (row, col) on 8x8 board.
sqToRC :: Int -> (Int, Int)
sqToRC sq = (r, c)
  where
    r = sq `div` 4
    c = 2 * (sq `mod` 4) + (if even r then 1 else 0)

-- | (row, col) to square index, if valid.
rcToSq :: Int -> Int -> Maybe Int
rcToSq r c
  | r < 0 || r > 7 || c < 0 || c > 7 = Nothing
  | even r && odd c  = Just (r * 4 + (c - 1) `div` 2)
  | odd r  && even c = Just (r * 4 + c `div` 2)
  | otherwise = Nothing

-- | Initial board: black on rows 0-2, white on rows 5-7.
initialBoard :: Board
initialBoard =
  replicate 12 BMan ++ replicate 8 Empty ++ replicate 12 WMan

-- | New game from initial position.
newGame :: GameState
newGame = GameState initialBoard Black 0

-- | Color of a piece.
pieceColor :: Piece -> Maybe Color
pieceColor BMan  = Just Black
pieceColor BKing = Just Black
pieceColor WMan  = Just White
pieceColor WKing = Just White
pieceColor Empty = Nothing

-- | Is this piece a king?
isKing :: Piece -> Bool
isKing BKing = True
isKing WKing = True
isKing _     = False

-- | Opponent color.
opponent :: Color -> Color
opponent Black = White
opponent White = Black

-- | Forward row directions for a color.
forwardDirs :: Color -> [Int]
forwardDirs Black = [1]    -- Black moves down (increasing row)
forwardDirs White = [-1]   -- White moves up (decreasing row)

-- | Get piece at square.
pieceAt :: Board -> Int -> Piece
pieceAt board sq
  | sq >= 0 && sq < 32 = board !! sq
  | otherwise = Empty

-- | Set piece at square.
setAt :: Board -> Int -> Piece -> Board
setAt board sq piece =
  take sq board ++ [piece] ++ drop (sq + 1) board

-- ---------------------------------------------------------------------------
-- Move generation
-- ---------------------------------------------------------------------------

-- | Generate all simple (non-capture) moves.
simpleMoves :: GameState -> [Move]
simpleMoves gs = concatMap movesFrom [0..31]
  where
    board = gsBoard gs
    turn = gsTurn gs
    movesFrom sq =
      let piece = pieceAt board sq
      in case pieceColor piece of
        Just c | c == turn ->
          let (r, col) = sqToRC sq
              dirs = if isKing piece then [-1, 1] else forwardDirs turn
              dcols = [-1, 1]
          in [ [sq, nsq]
             | dr <- dirs
             , dc <- dcols
             , let nr = r + dr
             , let nc = col + dc
             , Just nsq <- [rcToSq nr nc]
             , pieceAt board nsq == Empty
             ]
        _ -> []

-- | Generate all capture sequences (mandatory).
captureSequences :: GameState -> [Move]
captureSequences gs = concatMap capturesFrom [0..31]
  where
    board = gsBoard gs
    turn = gsTurn gs
    capturesFrom sq =
      let piece = pieceAt board sq
      in case pieceColor piece of
        Just c | c == turn ->
          let seqs = dfsCaptures board turn piece sq [sq]
          in seqs
        _ -> []

-- | DFS to find all capture sequences from a square.
dfsCaptures :: Board -> Color -> Piece -> Int -> [Int] -> [Move]
dfsCaptures board turn piece sq path =
  let (r, col) = sqToRC sq
      dirs = if isKing piece then [-1, 1] else forwardDirs turn
      dcols = [-1, 1]
      jumps = [ (overSq, landSq)
              | dr <- dirs
              , dc <- dcols
              , let mr = r + dr
              , let mc = col + dc
              , Just overSq <- [rcToSq mr mc]
              , let overPiece = pieceAt board overSq
              , pieceColor overPiece == Just (opponent turn)
              -- Don't re-capture same piece
              , overSq `notElem` drop 1 (init' path)
              , let lr = r + 2 * dr
              , let lc = col + 2 * dc
              , Just landSq <- [rcToSq lr lc]
              , pieceAt board landSq == Empty || landSq == head path
              ]
      -- For each jump, recurse
      results = concatMap (\(overSq, landSq) ->
        let board' = setAt (setAt (setAt board sq Empty) overSq Empty) landSq piece
            -- Check if promotion happens (ends turn)
            promotes = case piece of
              BMan | fst (sqToRC landSq) == 7 -> True
              WMan | fst (sqToRC landSq) == 0 -> True
              _ -> False
            path' = path ++ [landSq]
        in if promotes
           then [path']
           else dfsCaptures board' turn piece landSq path'
        ) jumps
  in if null jumps && length path > 1
     then [path]
     else results
  where
    init' [] = []
    init' xs = init xs

-- | All legal moves (captures are mandatory if available).
legalMoves :: GameState -> [Move]
legalMoves gs =
  let caps = captureSequences gs
  in if null caps then simpleMoves gs else caps

-- | Execute a move on the game state.
makeMove :: GameState -> Move -> GameState
makeMove gs move =
  let board0 = gsBoard gs
      startSq = head move
      piece = pieceAt board0 startSq
      (board', isCapture) = foldl applyStep (board0, False) (zip move (tail move))
      -- Check promotion at final square
      endSq = last move
      endRow = fst (sqToRC endSq)
      board'' = case piece of
        BMan | endRow == 7 -> setAt board' endSq BKing
        WMan | endRow == 0 -> setAt board' endSq WKing
        _ -> board'
      halfMoves = if isCapture then 0 else gsHalfMoves gs + 1
  in GameState board'' (opponent (gsTurn gs)) halfMoves
  where
    applyStep (board, wasCap) (from, to) =
      let p = pieceAt board from
          board1 = setAt board from Empty
          board2 = setAt board1 to p
          (fr, fc) = sqToRC from
          (tr, tc) = sqToRC to
          isJump = abs (tr - fr) == 2
          board3 = if isJump
            then case rcToSq ((fr + tr) `div` 2) ((fc + tc) `div` 2) of
              Just midSq -> setAt board2 midSq Empty
              Nothing    -> board2
            else board2
      in (board3, wasCap || isJump)

-- | Is the game over?
gameOver :: GameState -> Bool
gameOver gs = gsHalfMoves gs >= 80 || null (legalMoves gs)

-- | Game result from Black's perspective: 1.0 = Black wins, 0.0 = White wins, 0.5 = draw.
gameResult :: GameState -> Double
gameResult gs
  | gsHalfMoves gs >= 80 = 0.5
  | null (legalMoves gs) =
      case gsTurn gs of
        Black -> 0.0  -- Black can't move, White wins
        White -> 1.0  -- White can't move, Black wins
  | otherwise = 0.5  -- Game not over

-- ---------------------------------------------------------------------------
-- Evaluation features (Samuel-style)
-- ---------------------------------------------------------------------------

-- | Named features for board evaluation.
data Feature = Feature
  { fMaterial    :: !Double  -- ^ Piece count differential
  , fKings       :: !Double  -- ^ King count differential
  , fBackRow     :: !Double  -- ^ Back row occupation differential
  , fCenter      :: !Double  -- ^ Center control differential
  , fAdvancement :: !Double  -- ^ How far forward men have pushed
  , fMobility    :: !Double  -- ^ Legal move count differential
  , fVulnerable  :: !Double  -- ^ Pieces under attack differential
  , fProtected   :: !Double  -- ^ Pieces with friendly support differential
  , fKingCenter  :: !Double  -- ^ Kings in center differential
  , fEdge        :: !Double  -- ^ Pieces on edge (defensive) differential
  } deriving (Show)

-- | Feature names matching the Python AI.
featureNames :: [String]
featureNames =
  [ "material", "kings", "back_row", "center", "advancement"
  , "mobility", "vulnerable", "protected", "king_center", "edge"
  ]

-- | Center squares: rows 2-5, inner columns.
isCenterSq :: Int -> Bool
isCenterSq sq =
  let (r, c) = sqToRC sq
  in r >= 2 && r <= 5 && c >= 2 && c <= 5

-- | Edge squares: column 0 or 7.
isEdgeSq :: Int -> Bool
isEdgeSq sq =
  let (_, c) = sqToRC sq
  in c == 0 || c == 7

-- | Extract 10 features from Black's perspective.
extractFeatures :: GameState -> [Double]
extractFeatures gs =
  let -- Per-square accumulation
      stats = foldl accumSq (replicate 10 0.0) [0..31]
      -- Mobility
      myMoves = length (legalMoves gs)
      oppGs = gs { gsTurn = opponent (gsTurn gs) }
      oppMoves = length (legalMoves oppGs)
      (mobSign :: Double) = if gsTurn gs == Black then 1.0 else -1.0
      mobDiff = mobSign * fromIntegral (myMoves - oppMoves)
      -- Insert mobility
      feats = take 5 stats ++ [mobDiff] ++ drop 5 stats
      -- Normalize
      scales = [12.0, 12.0, 4.0, 4.0, 40.0, 15.0, 12.0, 12.0, 4.0, 4.0]
  in zipWith (/) feats scales
  where
    board = gsBoard gs
    accumSq acc sq =
      let piece = pieceAt board sq
          (r, _) = sqToRC sq
          sign = case piece of
            BMan  ->  1.0
            BKing ->  1.0
            WMan  -> -1.0
            WKing -> -1.0
            Empty ->  0.0
          isK = isKing piece
          isEmpty = piece == Empty
      in if isEmpty then acc
         else [ acc !! 0 + (if not isK then sign else 0)  -- material (men only)
              , acc !! 1 + (if isK then sign else 0)      -- kings
              , acc !! 2 + (if isBackRow piece r then sign else 0) -- back row
              , acc !! 3 + (if isCenterSq sq && not isK then sign else 0) -- center men
              , acc !! 4 + advancementVal piece r sign     -- advancement
              -- (mobility inserted later)
              , acc !! 5 -- vulnerable (simplified: skip for now)
              , acc !! 6 -- protected (simplified: skip for now)
              , acc !! 7 + (if isCenterSq sq && isK then sign else 0) -- king center
              , acc !! 8 + (if isEdgeSq sq then sign else 0) -- edge
              ]

    isBackRow piece r = case piece of
      BMan  -> r == 0
      BKing -> r == 0
      WMan  -> r == 7
      WKing -> r == 7
      Empty -> False

    advancementVal piece r sign = case piece of
      BMan  -> sign * fromIntegral r
      WMan  -> sign * fromIntegral (7 - r)
      _     -> 0

-- | Linear evaluation: dot product of weights and features.
linearEval :: [Double] -> GameState -> Double
linearEval weights gs =
  let feats = extractFeatures gs
  in sum (zipWith (*) weights feats)

-- | Default hand-tuned weights (from the Python AI).
defaultWeights :: [Double]
defaultWeights = [1.0, 1.5, 0.3, 0.1, 0.1, 0.05, 0.15, 0.1, 0.3, 0.05]

-- ---------------------------------------------------------------------------
-- Game playing with evaluation function
-- ---------------------------------------------------------------------------

-- | Play a single game between two evaluation functions.
-- Returns result from Black's perspective.
playGame :: [Double] -> [Double] -> StdGen -> Int -> Double
playGame blackWeights whiteWeights gen0 maxMoves =
  go newGame 0 gen0
  where
    go gs moveCount gen
      | gameOver gs = gameResult gs
      | moveCount >= maxMoves = 0.5  -- Draw by move limit
      | otherwise =
          let moves = legalMoves gs
              weights = if gsTurn gs == Black then blackWeights else whiteWeights
              -- Evaluate each move's resulting position
              scored = map (\m -> (m, evalMove gs weights m)) moves
              -- Pick best (with small random tiebreaker)
              (bestMove, gen') = pickBest scored gen
              gs' = makeMove gs bestMove
          in go gs' (moveCount + 1) gen'

    evalMove gs weights m =
      let gs' = makeMove gs m
          raw = linearEval weights gs'
      in if gsTurn gs == Black then raw else negate raw

    pickBest [] _gen = error "no moves"
    pickBest scored gen =
      let sorted = sortBy (comparing (Down . snd)) scored
          best = fst (head sorted)
      in (best, gen)

-- | Play a match of N games between two weight vectors.
-- Alternates colors. Returns win rate for the first player.
playMatch :: [Double] -> [Double] -> Int -> StdGen -> (Double, StdGen)
playMatch w1 w2 numGames gen0 =
  let (score, gen') = foldl playOne (0.0, gen0) [0 .. numGames - 1]
  in (score / fromIntegral numGames, gen')
  where
    playOne (acc, gen) i =
      let (g1, g2) = split gen
          result = if even i
            then playGame w1 w2 g1 100        -- w1 plays Black
            else 1.0 - playGame w2 w1 g1 100  -- w1 plays White
      in (acc + result, g2)

-- ---------------------------------------------------------------------------
-- GA integration
-- ---------------------------------------------------------------------------

-- | A weight genome: 10 real-valued weights for the evaluation function.
type WeightGenome = [Double]

-- | Generate random weights in [-2, 2].
randomWeights :: EvoM WeightGenome
randomWeights = replicateM 10 $ do
  r <- randomDouble
  return (r * 4.0 - 2.0)

-- | Generate a random initial population of weight vectors.
randomWeightPop :: Int -> EvoM [WeightGenome]
randomWeightPop n = replicateM n randomWeights

-- | Gaussian perturbation mutation for real-valued weights.
-- Uses Box-Muller transform to generate normal(0, sigma) noise.
gaussianPerturb :: Double -> EvoM Double
gaussianPerturb w = do
  u1 <- randomDouble
  u2 <- randomDouble
  let sigma = 0.3
      -- Box-Muller transform
      z = sigma * sqrt (-2.0 * log (max 1e-10 u1)) * cos (2.0 * pi * u2)
      w' = w + z
  return (max (-5.0) (min 5.0 w'))

-- | Fitness function: play games against a set of opponents.
-- The genome's fitness is its average win rate across all opponents.
weightFitness :: [[Double]] -> Int -> WeightGenome -> Double
weightFitness opponents gamesPerOpponent genome =
  let gen0 = mkStdGen (hashGenome genome)
      scores = map (\opp ->
        fst (playMatch genome opp gamesPerOpponent gen0)
        ) opponents
  in sum scores / fromIntegral (length scores)
  where
    -- Deterministic seed from genome (for reproducibility)
    hashGenome ws = abs (round (sum (zipWith (*) ws [1..]) * 1000)) `mod` maxBound

-- | Run the checkers weight evolution example.
--
-- Evolves evaluation weights to beat the default hand-tuned weights.
-- Demonstrates that the same categorical pipeline (evaluate >>> select >>>
-- crossover >>> mutate) works for real-valued game strategy optimization.
runCheckersGA :: IO ()
runCheckersGA = do
  gen <- newStdGen
  let config = defaultConfig
        { populationSize = 30
        , maxGenerations = 40
        , mutationRate   = 0.2    -- Higher mutation rate for real-valued genomes
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }
      -- Generate initial population
      (initPop, gen', _) = runEvoM config gen
                            (randomWeightPop (populationSize config))
      -- Opponents: default weights + some random variants
      (opponents, gen'') = makeOpponents gen'
      -- Fitness: win rate against opponents
      fitFunc = weightFitness opponents 4
      -- Evolve!
      result = evolve fitFunc (gaussianPerturb) config gen'' initPop

  putStrLn "=== Checkers Evaluation Weight Evolution ==="
  putStrLn ""
  putStrLn "Evolving 10-weight evaluation functions via GA."
  putStrLn "Fitness = win rate against baseline opponents."
  putStrLn ""
  putStrLn $ "Generations: " ++ show (maxGenerations config)
  putStrLn $ "Population:  " ++ show (populationSize config)
  putStrLn ""

  -- Show evolution progress
  putStrLn "Evolution progress:"
  mapM_ (\gs -> putStrLn $ "  Gen " ++ padLeft 3 (show (genNumber gs))
                         ++ ": best=" ++ showF (bestFitness gs)
                         ++ " avg=" ++ showF (avgFitness gs)
                         ++ " div=" ++ showF (diversity gs))
        (generations (evoLog result))
  putStrLn ""

  -- Show best evolved weights vs default
  let bestW = bestIndividual result
  putStrLn "Best evolved weights vs default weights:"
  putStrLn $ "  " ++ padRight 14 "Feature" ++ padLeft 10 "Evolved" ++ padLeft 10 "Default"
  putStrLn $ "  " ++ replicate 34 '-'
  mapM_ (\(name, ew, dw) ->
    putStrLn $ "  " ++ padRight 14 name
                     ++ padLeft 10 (showF ew)
                     ++ padLeft 10 (showF dw))
    (zip3 featureNames bestW defaultWeights)
  putStrLn ""

  -- Play match: evolved vs default
  let (winRate, _) = playMatch bestW defaultWeights 20 gen''
  putStrLn $ "Match result (evolved vs default, 20 games):"
  putStrLn $ "  Evolved win rate: " ++ showF winRate
  putStrLn ""
  putStrLn "The same categorical pipeline that evolves bitstrings"
  putStrLn "discovers strong checkers evaluation strategies."

  where
    makeOpponents gen =
      let (_g1, g2) = split gen
          -- Default weights as primary opponent
          -- Plus 3 random variants for diversity
          (vars, g3) = foldl (\(acc, g) _ ->
            let (ws, g') = randomWeightsIO g
            in (ws : acc, g')
            ) ([], g2) [1..3 :: Int]
      in (defaultWeights : vars, g3)

    randomWeightsIO gen =
      let (ws, gen') = foldl (\(acc, g) _ ->
            let (v, g') = uniformR (-2.0, 2.0) g
            in (v : acc, g')
            ) ([], gen) [1..10 :: Int]
      in (reverse ws, gen')

    showF d = let s = show (fromIntegral (round (d * 1000) :: Int) / 1000.0 :: Double)
              in take 6 (s ++ repeat '0')
    padLeft n s = replicate (max 0 (n - length s)) ' ' ++ s
    padRight n s = s ++ replicate (max 0 (n - length s)) ' '

-- ---------------------------------------------------------------------------
-- Display
-- ---------------------------------------------------------------------------

-- | Show a board position as ASCII art.
showBoard :: GameState -> String
showBoard gs = unlines $
  ["  0 1 2 3 4 5 6 7"] ++
  [ show r ++ " " ++ concatMap (showSq r) [0..7] | r <- [0..7] ] ++
  [ "Turn: " ++ show (gsTurn gs) ]
  where
    showSq r c = case rcToSq r c of
      Nothing -> ". "
      Just sq -> pieceChar (pieceAt (gsBoard gs) sq) ++ " "
    pieceChar BMan  = "b"
    pieceChar BKing = "B"
    pieceChar WMan  = "w"
    pieceChar WKing = "W"
    pieceChar Empty = "_"
