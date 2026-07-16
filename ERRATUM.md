# Erratum: Ring λ₂ is 2× Too Large

**Date:** 2026-07-13

The paper computes the algebraic connectivity λ₂ of the ring migration
topology as if migration on a ring were an undirected cycle. It is not: the
ring is a one-way relay. Every ring λ₂ value in the paper is exactly 2×
too large, and the "ring/star inversion at n=7" the paper claims this
predicts does not exist.

## What is wrong

`ring_migrate` moves individuals in one direction only (island *i* receives
from island *i−1*, and nothing flows back). Every other topology in the
paper — star, random, fully-connected — is a two-way swap. A directed ring
edge carries half the coupling of a swap edge, so the ring's Laplacian must
be built from the symmetrised adjacency `(A + Aᵀ)/2`, not from the
undirected-cycle adjacency the paper used. That halves every ring λ₂.

Affected text:

- **`paper-camera-ready-gecco-v1.tex:388`** ("Spectral predictions"
  paragraph) states the actual wrong numbers: `λ₂(ring) = 1.382` at n=5 and
  `λ₂(C_7) = 0.753` at n=7, and uses them to claim the inequality
  "reverses" at n=7, predicting a ring/star inversion. It also cites
  "Fisher's combined p = 0.14" as confirming ring and star are
  indistinguishable at n=5 — this does not reproduce either (see below).
- **`paper-camera-ready-gecco-v1.tex:512`** (Conclusion) restates the same
  claim in prose — "spectral graph theory predicts the ring/star inversion
  at n=7 islands, confirmed experimentally" — in the same sentence that
  also carries the separately-retired `23.9×` variance-explained figure.

No table or figure caption states the λ₂ values directly; Figure 1
(`fig:multi-domain-topology`, line 370) shows the topology *ordering*,
which is unaffected by this error (see below) — only the spectral
explanation and the n=7 prediction are wrong.

## Corrected values

| Topology | n=5 (paper → corrected) | n=7 (paper → corrected) |
|---|---|---|
| none | 0.000 → 0.000 | 0.000 → 0.000 |
| ring | 1.382 → **0.691** | 0.753 → **0.377** |
| star | 1.000 (unchanged) | 1.000 (unchanged) |
| random | 2.500 (unchanged) | 2.333 (unchanged) |
| fully connected | 5.000 (unchanged) | 7.000 (unchanged) |

Ring is the only topology whose λ₂ changes.

## What this changes

The claimed n=7 ring/star inversion does not exist. Corrected λ₂ gives
ring < star at **both** n=5 (0.691 < 1.0) and n=7 (0.377 < 1.0). What
actually happens between n=5 and n=7 is that the star–ring gap in λ₂
*widens* (0.309 → 0.623, a 2.02× increase) — not that the ordering flips.
This is directionally consistent with what the maze confirmatory
experiment shows (ring–star diversity gap widens 0.0371 → 0.0510, a 1.37×
increase from n=5 to n=7) — but it is a widening, not an inversion.

The corrected λ₂ also orders all five topologies correctly in all six
domains: Spearman ρ(diversity, λ₂) = **−1.00** in 6/6 domains. The
published λ₂ gives ρ = −0.90 in 6/6 domains — it gets exactly one
pairwise comparison wrong, and it is the ring/star pair the paper's
inversion claim rests on.

The paper's own "Fisher's combined p = 0.14" (cited at line 388 as
confirming ring and star are statistically indistinguishable at n=5) also
does not reproduce. The correct per-domain Welch tests, Fisher-combined,
give p = 0.0035 (two-sided) — ring is significantly greater than star,
consistent with the corrected ordering, not with "hard to distinguish."

## What this does NOT change

The headline results stand:

- Kendall's W = 1.0 across six domains (p = 7.99e-5) — the universal
  ordering none > ring > star > random > fully-connected is untouched;
  it does not depend on λ₂ or on this correction.
- Ring > star direction: Fisher combined p = 0.0035, ring > star in 6/6
  domains.

## Remaining limitation (the confound)

Migration *volume* (0, 5m, 8m, 10m, 20m migrants across none/ring/star/
random/fully-connected) is also perfectly monotone with diversity in 6/6
domains (Spearman ρ = −1.00, identical to corrected λ₂) and is **not
separable from λ₂** in this dataset — every topology's λ₂ and volume
increase together. Volume actually fits the n=7 magnitude *better* than
λ₂ does: λ₂ predicts a 2.02× widening of the star–ring gap, volume
predicts 1.67×, the maze experiment observes 1.37×.

This confound kills the *mechanism* claim, not the *effect*: there is
strong evidence some graph property of the migration topology orders
diversity, and currently zero evidence that the spectral gap specifically
(as opposed to migration volume, or something correlated with both) is
that property. The experiment that would separate them — holding
migrants-per-event fixed while varying graph shape — has not been run.

## How to reproduce

Run `verify_lambda2.py` at the repo root. It rebuilds each topology's
adjacency matrix exactly as implemented in code, recomputes λ₂ for n=5
and n=7, reloads the raw experiment CSVs, and recomputes every number
above. Runs in a few seconds off the shipped CSVs, no external data
required.
