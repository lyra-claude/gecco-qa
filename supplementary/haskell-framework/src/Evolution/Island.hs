{-# LANGUAGE ScopedTypeVariables #-}

-- | Island model: parallel populations with migration.
--
-- == Categorical interpretation
--
-- Each island runs its own evolutionary pipeline — a morphism in the Kleisli
-- category for 'EvoM'. The island model adds a /migration/ step that transfers
-- individuals between islands.
--
-- In categorical terms:
--
--   * Each island has its own 'GeneticOp' pipeline (possibly different!)
--   * Migration is a natural transformation between population functors:
--     it doesn't care about the specific pipeline on each island, only
--     about moving individuals between them.
--   * The topology (ring, fully connected, etc.) is encoded as an adjacency
--     structure on island indices.
--
-- == Type conventions
--
-- The type parameter @a@ is the /individual/ type (e.g., @[Bool]@ for a
-- bitstring genome). 'GeneticOp' 'EvoM' @a@ @a@ operates on populations
-- @[a]@ via 'runOp'. This matches "Evolution.Pipeline" where
-- @generationStep :: ([gene] -> Double) -> ... -> GeneticOp EvoM [gene] [gene]@.
module Evolution.Island
  ( -- * Island types
    Island(..)
  , IslandModel(..)
  , Topology(..)
    -- * Construction
  , makeIslands
  , uniformIslands
    -- * Migration
  , migrate
  , ringMigrate
    -- * Running
  , evolveIslands
  , IslandResult(..)
  ) where

import Data.List (sortBy)
import Data.Ord (comparing, Down(..))
import System.Random

import Evolution.Category
import Evolution.Effects
import Evolution.Pipeline

-- | A single island. Type parameter @a@ is the individual type.
-- 'islandPop' is the population @[a]@.
data Island a = Island
  { islandPop      :: ![a]              -- ^ Current population
  , islandPipeline :: !(Int -> GeneticOp EvoM a a)
    -- ^ Pipeline parameterized by generation number.
    -- 'runOp' takes @[a]@ (population) and produces @EvoM [a]@.
  }

-- | Migration topology between islands.
data Topology
  = Ring           -- ^ Each island sends migrants to the next (circular)
  | FullyConnected -- ^ Every island exchanges with every other
  deriving (Show, Eq)

-- | Configuration for the island model.
data IslandModel = IslandModel
  { numIslands     :: !Int      -- ^ Number of islands
  , migrationRate  :: !Double   -- ^ Fraction of population to migrate (0-1)
  , migrationFreq  :: !Int      -- ^ Migrate every n generations
  , topology       :: !Topology -- ^ How islands are connected
  } deriving (Show, Eq)

-- | Result of island model evolution.
data IslandResult a = IslandResult
  { bestIslandIndividual :: !a
  , bestIslandFitness    :: !Double
  , allIslandPops        :: ![[a]]      -- ^ Final populations from all islands
  , islandLog            :: !GALog
  , islandFinalGen       :: !StdGen
  } deriving (Show)

-- | Create islands from a list of (population, pipeline) pairs.
makeIslands :: [([a], Int -> GeneticOp EvoM a a)] -> [Island a]
makeIslands = map (\(pop, pipe) -> Island pop pipe)

-- | Create uniform islands: all use the same pipeline, different initial populations.
-- Here @a@ is the gene type; individuals are @[a]@ (genomes).
uniformIslands :: ([a] -> Double) -> (a -> EvoM a) -> [[[a]]] -> [Island [a]]
uniformIslands fitFunc mutFunc pops =
  map (\pop -> Island pop (generationStep fitFunc mutFunc)) pops

-- | Ring migration: each island sends random individuals to the next island.
-- Island i sends migrants to island (i+1) mod n.
ringMigrate :: Double -> [Island a] -> EvoM [Island a]
ringMigrate rate islands = do
  let n = length islands
  if n <= 1 then return islands
  else do
    let migrantCounts = map (\isl ->
            max 1 (round (rate * fromIntegral (length (islandPop isl))) :: Int)
          ) islands
    migrants <- mapM (\(isl, k) -> do
        shuffled <- shuffle (islandPop isl)
        return (take k shuffled)
      ) (zip islands migrantCounts)
    -- Send migrants[i] to island (i+1) mod n
    -- So island 1 receives from island 0, etc.
    let updatedIslands = zipWith (\isl migrantsIn ->
            let pop = islandPop isl
                trimmed = take (length pop - length migrantsIn) pop
            in isl { islandPop = migrantsIn ++ trimmed }
          ) islands (last migrants : init migrants)
    return updatedIslands

-- | General migration: applies based on topology.
migrate :: IslandModel -> [Island a] -> EvoM [Island a]
migrate model islands = case topology model of
  Ring           -> ringMigrate (migrationRate model) islands
  FullyConnected -> fullyConnectedMigrate (migrationRate model) islands

-- | Fully connected migration: each island sends migrants to all others.
fullyConnectedMigrate :: Double -> [Island a] -> EvoM [Island a]
fullyConnectedMigrate rate islands = do
  let n = length islands
  if n <= 1 then return islands
  else do
    let perIsland = max 1 (round (rate * fromIntegral (length (islandPop (head islands)))
                                  / fromIntegral (n - 1)) :: Int)
    donors <- mapM (\isl -> do
        shuffled <- shuffle (islandPop isl)
        return (take (perIsland * (n - 1)) shuffled)
      ) islands
    let updatedIslands = zipWith3 (\i isl _ ->
            let incoming = concatMap (\(j, d) -> if j /= i then take perIsland d else [])
                           (zip [0::Int ..] donors)
                pop = islandPop isl
                trimmed = take (length pop - length incoming) pop
            in isl { islandPop = incoming ++ trimmed }
          ) [0::Int ..] islands donors
    return updatedIslands

-- | Run the island model for a given number of generations.
evolveIslands :: forall a.
                 IslandModel
              -> (a -> Double)      -- ^ Fitness function (individual -> fitness)
              -> GAConfig
              -> StdGen
              -> [Island a]
              -> IslandResult a
evolveIslands model fitFunc config gen0 islands0 =
  let maxGen = maxGenerations config
      (finalIslands, gen', log') = runEvoM config gen0 (go 0 maxGen islands0)
      allPops = map islandPop finalIslands
      allGenomes = concat allPops
      scored = map (\g -> Scored g (fitFunc g)) allGenomes
      best = head $ sortBy (comparing (Down . fitness)) scored
  in IslandResult
      { bestIslandIndividual = individual best
      , bestIslandFitness    = fitness best
      , allIslandPops        = allPops
      , islandLog            = log'
      , islandFinalGen       = gen'
      }
  where
    go :: Int -> Int -> [Island a] -> EvoM [Island a]
    go gen maxG isls
      | gen >= maxG = return isls
      | otherwise = do
          -- Evolve each island for one generation
          isls' <- mapM (\isl -> do
              pop' <- runOp (islandPipeline isl gen) (islandPop isl)
              return isl { islandPop = pop' }
            ) isls
          -- Migrate if it's time
          isls'' <- if gen > 0 && gen `mod` migrationFreq model == 0
                    then migrate model isls'
                    else return isls'
          go (gen + 1) maxG isls''
