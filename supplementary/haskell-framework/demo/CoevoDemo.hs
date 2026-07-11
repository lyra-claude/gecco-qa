-- | Competitive coevolution demo: bit-matching arms race.
--
-- Two populations of bitstrings:
--   * Population A (Matchers): try to match Population B
--   * Population B (Evaders):  try to differ from Population A
--
-- This creates a Red Queen dynamic — both populations must keep evolving
-- just to maintain their current fitness, because the opponent is also evolving.
--
-- The demo shows how fitness oscillates rather than monotonically increasing,
-- which is characteristic of competitive coevolution and exactly what we see
-- in intransitive dynamics in virtual-creatures tournaments.
module Main (main) where

import System.Random (mkStdGen)

import Evolution.Effects
import Evolution.Coevolution

main :: IO ()
main = do
  putStrLn "=== Competitive Coevolution: Bit-Matching Arms Race ==="
  putStrLn ""
  putStrLn "Matchers (A): score by matching Evaders"
  putStrLn "Evaders  (B): score by differing from Matchers"
  putStrLn ""

  let genomeLen = 12
      popSize   = 30
      nGens     = 50

      config = defaultConfig
        { populationSize = popSize
        , maxGenerations = nGens
        , mutationRate   = 0.08
        , crossoverRate  = 0.7
        , tournamentSize = 3
        , eliteCount     = 2
        }

      coevoCfg = defaultCoevoConfig { opponentSampleSize = 10 }

      gen = mkStdGen 42

      -- Initial populations: A starts all-True, B starts all-False
      -- Maximum initial mismatch — the arms race starts here
      initA = replicate popSize (replicate genomeLen True)
      initB = replicate popSize (replicate genomeLen False)

      -- Run coevolution
      result = coevolve matchScore differScore
                        bitFlip bitFlip
                        coevoCfg config gen
                        initA initB

      -- Extract log
      stats = generations (coevoLog result)

  -- Print fitness trajectory
  putStrLn "Gen  | Matcher best | Matcher avg  | (logged from A's perspective)"
  putStrLn "-----|--------------|-------------"
  mapM_ (\gs -> putStrLn $
      padLeft 4 (show (genNumber gs))
      ++ " | " ++ padLeft 12 (showF (bestFitness gs))
      ++ " | " ++ padLeft 12 (showF (avgFitness gs))
    ) stats

  putStrLn ""
  putStrLn "--- Final Results ---"
  putStrLn $ "Best Matcher:   " ++ showBits (bestA result)
  putStrLn $ "Best Evader:    " ++ showBits (bestB result)
  putStrLn $ "Matcher score:  " ++ showF (bestAFitness result)
                                ++ " / " ++ show genomeLen
  putStrLn $ "Evader score:   " ++ showF (bestBFitness result)
                                ++ " / " ++ show genomeLen
  putStrLn ""

  -- Analyze the arms race: compute match between best A and best B
  let finalMatch = matchScore (bestA result) (bestB result)
      finalDiffer = differScore (bestB result) (bestA result)
  putStrLn $ "Direct match (best A vs best B): " ++ showF finalMatch
  putStrLn $ "Direct differ (best B vs best A): " ++ showF finalDiffer

  putStrLn ""
  putStrLn "Note: In a perfect arms race, neither side can fully dominate."
  putStrLn "Oscillating fitness is a hallmark of competitive coevolution —"
  putStrLn "the same Red Queen dynamics we see in morphological evolution."

-- | Matcher scores by matching
matchScore :: [Bool] -> [Bool] -> Double
matchScore a b = fromIntegral $ length $ filter id $ zipWith (==) a b

-- | Evader scores by differing
differScore :: [Bool] -> [Bool] -> Double
differScore b a = fromIntegral $ length $ filter id $ zipWith (/=) b a

-- | Bit flip mutation
bitFlip :: Bool -> EvoM Bool
bitFlip b = return (not b)

showBits :: [Bool] -> String
showBits = map (\b -> if b then '1' else '0')

showF :: Double -> String
showF d = show (fromIntegral (round (d * 100) :: Int) / 100.0 :: Double)

padLeft :: Int -> String -> String
padLeft n s = replicate (n - length s) ' ' ++ s
