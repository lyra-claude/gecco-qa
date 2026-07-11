-- | The categorical foundation for composable genetic operators.
--
-- In category-printf, format specifications are morphisms in the co-Kleisli
-- category @Cokleisli ((->) m)@ where @m@ is a monoid. Composition concatenates
-- the monoid output and accumulates function arguments.
--
-- Here, genetic operators are morphisms in a Kleisli-like category where:
--
--   * Objects are population types (scored or unscored individuals)
--   * Morphisms are population transformations with monadic effects
--   * Composition is pipeline composition (evaluate >>> select >>> breed >>> mutate)
--
-- The monad @m@ carries effects: randomness, configuration, logging, selection.
-- Just as category-printf accumulates /arguments/, we accumulate /effects/.
module Evolution.Category
  ( -- * Core types
    GeneticOp(..)
  , Scored(..)
  , Population
  , ScoredPop
    -- * Category operations
  , composeOp
  , idOp
  , (>>>:)
    -- * Constructors
  , liftPure
  , liftMonadic
  , pointwise
  , pointwiseM
  ) where

import Control.Monad ((>=>))
import Prelude hiding (id)

-- | A scored individual: an individual paired with its fitness value.
data Scored a = Scored
  { individual :: !a
  , fitness    :: !Double
  } deriving (Show, Eq)

instance Functor Scored where
  fmap f (Scored x s) = Scored (f x) s

-- | A population is just a list of individuals.
type Population a = [a]

-- | A scored population: individuals paired with fitness values.
type ScoredPop a = [Scored a]

-- | A genetic operator: a morphism in the Kleisli category for monad @m@,
-- transforming a population of @a@'s into a population of @b@'s.
--
-- This is the central type. Operators compose via '>>>:' (left-to-right)
-- or 'composeOp' (right-to-left), forming a category.
--
-- Compare with category-printf's @Format m = Cokleisli ((->) m)@.
-- Where format specs compose to accumulate arguments, genetic operators
-- compose to accumulate effects.
newtype GeneticOp m a b = GeneticOp { runOp :: [a] -> m [b] }

-- | Identity operator: passes the population through unchanged.
idOp :: Monad m => GeneticOp m a a
idOp = GeneticOp return

-- | Right-to-left composition (like '.' for functions).
composeOp :: Monad m => GeneticOp m b c -> GeneticOp m a b -> GeneticOp m a c
composeOp (GeneticOp f) (GeneticOp g) = GeneticOp (g >=> f)

-- | Left-to-right composition (like '>>>' for arrows).
-- More natural for pipelines: @evaluate >>>: select >>>: breed >>>: mutate@
(>>>:) :: Monad m => GeneticOp m a b -> GeneticOp m b c -> GeneticOp m a c
(>>>:) = flip composeOp

infixl 1 >>>:

-- | Lift a pure population transformation into a GeneticOp.
liftPure :: Monad m => ([a] -> [b]) -> GeneticOp m a b
liftPure f = GeneticOp (return . f)

-- | Lift a monadic population transformation into a GeneticOp.
liftMonadic :: ([a] -> m [b]) -> GeneticOp m a b
liftMonadic = GeneticOp

-- | Apply a pure function to each individual independently.
pointwise :: Monad m => (a -> b) -> GeneticOp m a b
pointwise f = liftPure (map f)

-- | Apply a monadic function to each individual independently.
pointwiseM :: Monad m => (a -> m b) -> GeneticOp m a b
pointwiseM f = GeneticOp (mapM f)
