{-# LANGUAGE ScopedTypeVariables #-}

-- | Maze topology evolution: binary genome representing wall structure.
--
-- A maze on an NxN grid is a set of internal walls between adjacent cells.
-- The genome is a @[Bool]@ where True = wall present, False = passage.
-- This gives a binary/combinatorial genome, structurally different from
-- the real-valued checkers weights or tree-structured GP expressions.
--
-- == Fitness
--
-- Maze quality is multi-objective but we combine into a single scalar:
--
--   * Solution length: longer paths from start to goal are harder
--   * Dead-end ratio: more dead ends increase difficulty
--   * Connectivity penalty: unreachable goal is heavily penalized
--
-- == Cross-domain comparison
--
-- The same categorical composition (hourglass, island, flat) should
-- produce qualitatively similar diversity trajectories regardless of
-- whether we're evolving weight vectors, expression trees, or maze walls.
module Evolution.Examples.Maze
  ( -- * Types
    MazeGenome
  , MazeGrid(..)
    -- * Grid construction
  , mazeSize
  , genomeLength
  , decodeGenome
    -- * Maze analysis
  , bfsSolve
  , deadEndRatio
  , branchingFactor
  , mazeFitness
    -- * GA integration
  , randomMazeGenome
  , randomMazePop
  , mazeFlipMutate
    -- * Diversity metrics
  , mazeGenotypicDiv
  , mazePhenotypicDiv
    -- * Display
  , showMaze
  ) where

import Control.Monad (replicateM)

import Evolution.Effects

-- | Grid size (6x6).
mazeSize :: Int
mazeSize = 6

-- | Total number of internal walls in an NxN grid.
-- Horizontal: (N-1)*N, Vertical: N*(N-1), Total: 2*N*(N-1)
genomeLength :: Int
genomeLength = 2 * mazeSize * (mazeSize - 1)

-- | Maze genome: Boolean vector, True = wall present.
type MazeGenome = [Bool]

-- | Decoded maze grid with adjacency information.
data MazeGrid = MazeGrid
  { mgSize      :: !Int
  , mgWalls     :: !MazeGenome
  , mgNeighbors :: ![(Int, [Int])]  -- ^ Cell index -> accessible neighbors
  } deriving (Show)

-- | Decode a genome into a grid with adjacency.
-- Wall indexing:
--   [0 .. (N-1)*N - 1]: horizontal walls. Wall k connects cell (k `div` N, k `mod` N) to (k `div` N + 1, k `mod` N)
--   [(N-1)*N .. 2*N*(N-1) - 1]: vertical walls. Wall k' (offset) connects cell (k' `div` (N-1), k' `mod` (N-1)) to (k' `div` (N-1), k' `mod` (N-1) + 1)
decodeGenome :: MazeGenome -> MazeGrid
decodeGenome genome = MazeGrid
  { mgSize = mazeSize
  , mgWalls = genome
  , mgNeighbors = [(c, neighborsOf c) | c <- [0 .. mazeSize * mazeSize - 1]]
  }
  where
    n = mazeSize
    hWallCount = (n - 1) * n  -- horizontal walls

    cellRC :: Int -> (Int, Int)
    cellRC c = (c `div` n, c `mod` n)

    neighborsOf :: Int -> [Int]
    neighborsOf c =
      let (r, col) = cellRC c
          -- Down: horizontal wall at index r*n + col (connects (r,col)-(r+1,col))
          down = if r < n - 1
                 then let wIdx = r * n + col
                      in if not (genome !! wIdx) then [c + n] else []
                 else []
          -- Up: horizontal wall at index (r-1)*n + col
          up = if r > 0
               then let wIdx = (r - 1) * n + col
                    in if not (genome !! wIdx) then [c - n] else []
               else []
          -- Right: vertical wall at index hWallCount + r*(n-1) + col
          right' = if col < n - 1
                   then let wIdx = hWallCount + r * (n - 1) + col
                        in if not (genome !! wIdx) then [c + 1] else []
                   else []
          -- Left: vertical wall at index hWallCount + r*(n-1) + (col-1)
          left' = if col > 0
                  then let wIdx = hWallCount + r * (n - 1) + (col - 1)
                       in if not (genome !! wIdx) then [c - 1] else []
                  else []
      in up ++ down ++ left' ++ right'

-- | BFS from start to goal. Returns path length or Nothing if unreachable.
bfsSolve :: MazeGrid -> Int -> Int -> Maybe Int
bfsSolve grid start goal = bfs [(start, 0)] visited0
  where
    n = mgSize grid
    totalCells = n * n
    visited0 = replicate totalCells False

    setVisited :: [Bool] -> Int -> [Bool]
    setVisited vs i = take i vs ++ [True] ++ drop (i + 1) vs

    bfs [] _ = Nothing
    bfs ((cell, dist):queue) visited
      | cell == goal = Just dist
      | visited !! cell = bfs queue visited
      | otherwise =
          let visited' = setVisited visited cell
              nbrs = getNeighbors grid cell
              newEntries = [(nb, dist + 1) | nb <- nbrs, not (visited' !! nb)]
          in bfs (queue ++ newEntries) visited'

-- | Get neighbors of a cell from the precomputed adjacency.
getNeighbors :: MazeGrid -> Int -> [Int]
getNeighbors grid cell =
  case lookup cell (mgNeighbors grid) of
    Just ns -> ns
    Nothing -> []

-- | Fraction of cells that are dead ends (exactly 1 neighbor).
deadEndRatio :: MazeGrid -> Double
deadEndRatio grid =
  let n = mgSize grid
      totalCells = n * n
      deadEnds = length [c | c <- [0 .. totalCells - 1],
                          length (getNeighbors grid c) == 1]
  in fromIntegral deadEnds / fromIntegral totalCells

-- | Average branching factor (average number of neighbors).
branchingFactor :: MazeGrid -> Double
branchingFactor grid =
  let n = mgSize grid
      totalCells = n * n
      totalNbrs = sum [length (getNeighbors grid c) | c <- [0 .. totalCells - 1]]
  in fromIntegral totalNbrs / fromIntegral totalCells

-- | Combined fitness function for maze quality.
-- Higher is better. Components:
--   1. Solution length (normalized): longer paths are harder, more interesting
--   2. Dead-end ratio: more dead ends = more exploration required
--   3. Connectivity bonus: big penalty if start and goal aren't connected
--   4. Branching penalty: too few passages = boring, too many = trivial
mazeFitness :: MazeGenome -> Double
mazeFitness genome =
  let grid = decodeGenome genome
      n = mgSize grid
      start = 0
      goal = n * n - 1
      maxPath = fromIntegral (n * n - 1) :: Double
  in case bfsSolve grid start goal of
       Nothing -> 0.0  -- Unreachable: zero fitness
       Just pathLen ->
         let -- Solution length component (0-1, longer is better)
             solScore = fromIntegral pathLen / maxPath
             -- Dead-end component (0-1, moderate is best)
             der = deadEndRatio grid
             deadEndScore = 1.0 - abs (der - 0.3) * 2.0  -- peak at 30%
             -- Branching component (target ~2.0 average neighbors)
             bf = branchingFactor grid
             branchScore = 1.0 - abs (bf - 2.0) / 2.0
             -- Weighted combination
         in 0.5 * solScore + 0.3 * max 0 deadEndScore + 0.2 * max 0 branchScore

-- | Generate a random maze genome.
-- Starts with ~40% walls so most random mazes are solvable.
randomMazeGenome :: EvoM MazeGenome
randomMazeGenome = replicateM genomeLength $ do
  r <- randomDouble
  return (r < 0.4)  -- 40% chance of wall

-- | Generate a random population of maze genomes.
randomMazePop :: Int -> EvoM [MazeGenome]
randomMazePop n = replicateM n randomMazeGenome

-- | Mutation operator for a single wall gene.
-- Called by 'pointMutate' which handles the mutation rate check.
-- When triggered, simply flips the wall state.
mazeFlipMutate :: Bool -> EvoM Bool
mazeFlipMutate wall = return (not wall)

-- | Genotypic diversity: average pairwise Hamming distance (sampled).
mazeGenotypicDiv :: [MazeGenome] -> Double
mazeGenotypicDiv [] = 0
mazeGenotypicDiv [_] = 0
mazeGenotypicDiv genomes =
  let n = length genomes
      -- Sample pairs (first 20 pairs for efficiency)
      pairs = take 20 [(i, j) | i <- [0..n-2], j <- [i+1..n-1]]
      dists = map (\(i, j) -> hammingDist (genomes !! i) (genomes !! j)) pairs
  in if null dists then 0 else sum dists / fromIntegral (length dists)
  where
    hammingDist a b = fromIntegral (length (filter id (zipWith (/=) a b)))
                    / fromIntegral genomeLength

-- | Phenotypic diversity: variance of solution lengths across population.
mazePhenotypicDiv :: [MazeGenome] -> Double
mazePhenotypicDiv genomes =
  let grids = map decodeGenome genomes
      n = mazeSize
      solLens = map (\g -> case bfsSolve g 0 (n*n-1) of
                             Just l  -> fromIntegral l
                             Nothing -> 0.0) grids
      nPop = length solLens
      mu = sum solLens / fromIntegral nPop
  in if nPop == 0 then 0
     else sum (map (\x -> (x - mu) ** 2) solLens) / fromIntegral nPop

-- | Display a maze as ASCII art.
showMaze :: MazeGenome -> String
showMaze genome = unlines (topBorder : concatMap showRow [0..n-1] ++ [bottomBorder])
  where
    n = mazeSize
    hWallCount = (n - 1) * n

    topBorder = "+" ++ concat (replicate n "---+")
    bottomBorder = topBorder

    showRow r =
      let -- Cell row: show vertical walls between cells
          cellLine = "|" ++ concatMap (\col ->
            let cell = " " ++ cellChar r col ++ " "
                rightWall = if col < n - 1
                  then let wIdx = hWallCount + r * (n - 1) + col
                       in if genome !! wIdx then "|" else " "
                  else "|"
            in cell ++ rightWall) [0..n-1]
          -- Wall row: show horizontal walls below cells
          wallLine = if r < n - 1
            then "+" ++ concatMap (\col ->
              let wIdx = r * n + col
                  hWall = if genome !! wIdx then "---" else "   "
                  corner = "+"
              in hWall ++ corner) [0..n-1]
            else ""
      in if r < n - 1 then [cellLine, wallLine] else [cellLine]

    cellChar r col
      | r == 0 && col == 0 = "S"
      | r == n-1 && col == n-1 = "G"
      | otherwise = " "
