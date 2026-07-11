module Test.Maze (runTests) where

import System.Random (mkStdGen)

import Evolution.Effects
import Evolution.Examples.Maze

-- | Run maze tests. Returns number of failures.
runTests :: IO Int
runTests = do
  putStrLn "--- Maze tests ---"
  failures <- sequence
    [ test "genome length is 2*N*(N-1)"          testGenomeLength
    , test "decode produces correct cell count"   testDecodeSize
    , test "all-walls maze is unsolvable"         testAllWallsUnsolvable
    , test "no-walls maze is solvable"            testNoWallsSolvable
    , test "no-walls maze shortest path"          testNoWallsShortPath
    , test "dead-end ratio in [0,1]"              testDeadEndRange
    , test "branching factor non-negative"        testBranchingNonNeg
    , test "fitness in [0,1] for solvable"        testFitnessRange
    , test "unsolvable maze has zero fitness"      testUnsolvableFitness
    , test "random population correct size"        testRandomPopSize
    , test "mutation flips a wall"                 testMutationFlips
    , test "genotypic diversity non-negative"      testGenoDivNonNeg
    , test "phenotypic diversity non-negative"     testPhenoDivNonNeg
    , test "showMaze produces output"              testShowMaze
    ]
  return (sum failures)

test :: String -> Bool -> IO Int
test name True  = putStrLn ("  [PASS] " ++ name) >> return 0
test name False = putStrLn ("  [FAIL] " ++ name) >> return 1

-- | Genome length should be 2*6*(6-1) = 60.
testGenomeLength :: Bool
testGenomeLength = genomeLength == 2 * mazeSize * (mazeSize - 1)

-- | Decoded maze should have NxN cells.
testDecodeSize :: Bool
testDecodeSize =
  let genome = replicate genomeLength False
      grid = decodeGenome genome
  in length (mgNeighbors grid) == mazeSize * mazeSize

-- | A maze with all walls should be unsolvable.
testAllWallsUnsolvable :: Bool
testAllWallsUnsolvable =
  let genome = replicate genomeLength True
      grid = decodeGenome genome
  in bfsSolve grid 0 (mazeSize * mazeSize - 1) == Nothing

-- | A maze with no walls should be solvable.
testNoWallsSolvable :: Bool
testNoWallsSolvable =
  let genome = replicate genomeLength False
      grid = decodeGenome genome
  in case bfsSolve grid 0 (mazeSize * mazeSize - 1) of
       Just _  -> True
       Nothing -> False

-- | No-walls maze should have shortest path of 2*(N-1) = 10.
testNoWallsShortPath :: Bool
testNoWallsShortPath =
  let genome = replicate genomeLength False
      grid = decodeGenome genome
  in bfsSolve grid 0 (mazeSize * mazeSize - 1) == Just (2 * (mazeSize - 1))

-- | Dead-end ratio should be in [0, 1].
testDeadEndRange :: Bool
testDeadEndRange =
  let genome = replicate genomeLength False
      grid = decodeGenome genome
      der = deadEndRatio grid
  in der >= 0.0 && der <= 1.0

-- | Branching factor should be non-negative.
testBranchingNonNeg :: Bool
testBranchingNonNeg =
  let genome = replicate genomeLength False
      grid = decodeGenome genome
  in branchingFactor grid >= 0.0

-- | Fitness of a solvable maze should be in [0, 1].
testFitnessRange :: Bool
testFitnessRange =
  let genome = replicate genomeLength False
      f = mazeFitness genome
  in f >= 0.0 && f <= 1.0

-- | Unsolvable maze should have zero fitness.
testUnsolvableFitness :: Bool
testUnsolvableFitness =
  let genome = replicate genomeLength True
  in mazeFitness genome == 0.0

-- | Random population should have correct size.
testRandomPopSize :: Bool
testRandomPopSize =
  let config = defaultConfig { populationSize = 10 }
      gen = mkStdGen 42
      (pop, _, _) = runEvoM config gen (randomMazePop 10)
  in length pop == 10 && all (\g -> length g == genomeLength) pop

-- | Mutation should flip a wall value.
testMutationFlips :: Bool
testMutationFlips =
  let config = defaultConfig
      gen = mkStdGen 123
      (result, _, _) = runEvoM config gen (mazeFlipMutate True)
  in result == False

-- | Genotypic diversity should be non-negative.
testGenoDivNonNeg :: Bool
testGenoDivNonNeg =
  let g1 = replicate genomeLength False
      g2 = replicate genomeLength True
  in mazeGenotypicDiv [g1, g2] >= 0.0

-- | Phenotypic diversity should be non-negative.
testPhenoDivNonNeg :: Bool
testPhenoDivNonNeg =
  let g1 = replicate genomeLength False
      g2 = replicate genomeLength True
  in mazePhenotypicDiv [g1, g2] >= 0.0

-- | showMaze should produce non-empty output.
testShowMaze :: Bool
testShowMaze =
  let genome = replicate genomeLength False
  in not (null (showMaze genome))
