# Technical Erratum: λ₂ of the Ring Topology

**Status:** confirmed. Reproduce with `python3 verify_lambda2.py` in this repo.
**Affects:** `paper-camera-ready-gecco-v1.tex` §Results (:383, :388) and Conclusion (:512).
**Written:** 2026-07-13, the day before the GECCO talk.

---

## 1. The error

The paper's λ₂ (algebraic connectivity) values are computed from the Laplacian of an
**undirected cycle** C_n for the ring topology. The code does not implement an undirected
cycle.

`ring_migrate` in `categorical-evolution/experiments/onemax_stats.py` (~line 202):

```python
source_idx = (i - 1) % n   # island i receives from island i-1
```

This is a **one-way relay**. Island *i* receives *m* migrants from island *i−1* and sends
nothing back to it. Meanwhile `star_migrate`, `fully_connected_migrate` and `random_migrate`
all perform **two-way swaps** — each edge exchanges *m* individuals in both directions.

A ring edge therefore carries **half the coupling** of a swap edge. Symmetrising the directed
adjacency, S = (A + Aᵀ)/2, gives directed ring edges weight ½ and swap edges weight 1. The
paper implicitly gave ring edges weight 1, i.e. it modelled a topology the code never ran.

The error is confined to the ring. Every other topology's λ₂ is unchanged.

---

## 2. Corrected numbers

Adjacency built exactly as the code implements it; λ₂ from the symmetrised Laplacian.
`random`'s expected weight per unordered pair is n/C(n,2) = 2/(n−1), since it draws *n* swap
edges uniformly per event.

### n = 5 islands

| topology | paper λ₂ | **code λ₂** | ratio | migrants/event |
|---|---|---|---|---|
| none | 0.000 | **0.000** | — | 0 |
| ring | 1.382 | **0.691** | **2.00×** | 5m |
| star | 1.000 | **1.000** | 1.00× | 8m |
| random | 2.500 | **2.500** | 1.00× | 10m |
| fully connected | 5.000 | **5.000** | 1.00× | 20m |

### n = 7 islands

| topology | paper λ₂ | **code λ₂** | ratio | migrants/event |
|---|---|---|---|---|
| none | 0.000 | **0.000** | — | 0 |
| ring | 0.753 | **0.377** | **2.00×** | 7m |
| star | 1.000 | **1.000** | 1.00× | 12m |
| random | 2.333 | **2.333** | 1.00× | 14m |
| fully connected | 7.000 | **7.000** | 1.00× | 42m |

Both of the paper's ring values are **exactly 2× too large**.

---

## 3. What this strengthens

**The spectral ordering becomes perfect.**

Corrected λ₂ ordering, identical at both n:

> none (0) < **ring** < **star** (1.0) < random < fully connected

Observed diversity ordering, all six domains:

> none > ring > star > random > fully connected

These are exact reverses. Spearman(mean diversity at gen 99, λ₂) across the five topologies:

| | paper λ₂ | **corrected λ₂** |
|---|---|---|
| OneMax | −0.90 | **−1.00** |
| Maze | −0.90 | **−1.00** |
| Knapsack | −0.90 | **−1.00** |
| No Thanks! | −0.90 | **−1.00** |
| Checkers | −0.90 | **−1.00** |
| Graph colouring | −0.90 | **−1.00** |
| *Sorting networks* | *−0.70* | *−0.50* |

The paper's λ₂ gets −0.90 in every domain, and it is wrong on **exactly the ring/star pair** —
the single pair the correction touches. The corrected λ₂ gets **−1.00 in 6/6 domains**. The
error was *suppressing* the paper's own result.

(Sorting networks, the 7th domain, still violates the ordering. That was already a known scope
condition and it survives the correction unchanged.)

---

## 4. What is retracted

### 4.1 The ring/star inversion at n=7 — RETRACTED

Camera-ready Conclusion (`:512`):

> "…and spectral graph theory predicts the ring/star inversion at n=7 islands, confirmed
> experimentally (p = 6.6 × 10⁻⁵)."

**There is no inversion.** Under the corrected λ₂, ring < star at *both* n=5 (0.691 < 1.000) and
n=7 (0.377 < 1.000). The theory predicts ring > star in diversity at both sizes, and that is
what the data show. Nothing crosses over.

The n=7 maze experiment is real and it is not the confirmation the paper claims — it is a
*different*, better confirmation. The gap does not flip sign; it **widens**:

| | ring | star | gap | p (Welch) | corrected λ₂ gap (star − ring) |
|---|---|---|---|---|---|
| maze, n=5 | 0.3156 ± 0.0438 | 0.2785 ± 0.0689 | **+0.0371** | 0.016 | 0.309 |
| maze, n=7 | 0.3872 ± 0.0275 | 0.3362 ± 0.0528 | **+0.0510** | 2.7 × 10⁻⁵ | 0.623 |

The corrected rule predicts the widening in **direction and magnitude**: the λ₂ gap roughly
doubles (0.309 → 0.623, ×2.02) and the observed diversity gap grows (+0.0371 → +0.0510, ×1.37).
The paper's λ₂ predicts a sign flip that does not occur. The correction converts a false
prediction into a true one.

The sentence at `:512` must be replaced. Suggested wording:

> "…and spectral graph theory predicts the ring/star diversity gap and its widening at n=7
> islands, confirmed experimentally (p = 2.7 × 10⁻⁵)."

### 4.2 "Fisher's combined p = 0.14 across six domains" — DOES NOT REPRODUCE

Camera-ready `:388`:

> "…predicting ring and star should be hard to distinguish—confirmed: Fisher's combined
> p = 0.14 across six domains."

**No code computing any Fisher combination exists in any repository.** The number's provenance
could not be established.

Recomputing from the raw CSVs — per-domain Welch t-tests on `hamming_diversity` at generation 99,
ring vs star, then Fisher's method over the six p-values:

| domain | ring | star | diff | p (2-sided) |
|---|---|---|---|---|
| OneMax | 0.0792 | 0.0769 | +0.0023 | 0.428 |
| Maze | 0.3156 | 0.2785 | +0.0371 | 0.016 |
| Knapsack | 0.1734 | 0.1704 | +0.0030 | 0.544 |
| No Thanks! | 0.1092 | 0.0984 | +0.0108 | 0.071 |
| Checkers | 0.3713 | 0.3618 | +0.0095 | 0.029 |
| Graph colouring | 0.2827 | 0.2477 | +0.0350 | 0.054 |

**ring > star in 6/6 domains.**
**Fisher's combined p = 0.0035** (χ² = 29.36, df = 12). One-sided (H₁: ring > star): p = 1.7 × 10⁻⁴.

Ring and star are *not* hard to distinguish. They are cleanly separated, in the direction the
corrected λ₂ predicts. The claim at `:388` is doubly wrong: the number is wrong, and the
interpretation it was recruited to support ("hard to distinguish") was an artefact of the λ₂ bug
that made ring and star look adjacent in the spectrum.

**Nearest reproducible "nonsignificant" number.** Pooling all six domains' seeds into a single
Welch test gives p = 0.112 (using the 2-seed OneMax file that `multi_domain_analysis.py` actually
loads) or p = 0.168 (using the 30-seed OneMax file). This is the **wrong estimand**: between-domain
variance dominates — ring's domain means span 0.08 to 0.37 — and swamps a within-domain effect of
0.002–0.037. It is the only computation in the neighbourhood that returns a nonsignificant p, so it
is the plausible provenance of "0.14", but it does not test the claim it was used to support.

---

## 5. Limitation: the volume confound (NAMED, NOT BURIED)

**λ₂ is not identified in this dataset.** Migration *volume* — migrants moved per migration event —
is also perfectly monotone with diversity:

| topology | migrants/event (n=5) | corrected λ₂ (n=5) |
|---|---|---|
| none | 0 | 0.000 |
| ring | 5m | 0.691 |
| star | 8m | 1.000 |
| random | 10m | 2.500 |
| fully connected | 20m | 5.000 |

Spearman(diversity, volume) = **−1.00 in the same 6/6 domains**. Volume also predicts ring > star
at n=7. **λ₂ and volume are rank-equivalent across every topology in this study.** Nothing in this
dataset can separate "sparser spectrum ⇒ slower mixing ⇒ more diversity" from "fewer migrants
moved ⇒ less homogenisation ⇒ more diversity". The paper's causal reading of λ₂ is not licensed
by these experiments.

This is made worse by the fact that the study's own volume control is broken.
`random_migrate`'s docstring states:

> "Number of random edges = n (same as ring) to control for migration volume."

**That control fails.** Ring's *n* edges are one-way (m migrants each, total *nm*); random's *n*
edges are swaps (2m each, total *2nm*). Random moves exactly twice the volume of ring. The same
directed/undirected slip that produced the λ₂ error also silently voided the volume control. Both
bugs have the same root cause.

**Required next experiment:** hold migrants-per-event fixed across topologies and vary only graph
shape. `generic_migrate(..., volume_mode='per_event')` in `onemax_stats.py` already normalises
volume by edge count and is the right instrument. Until that is run, the λ₂ story is a *correlation
with a perfect confound*, not a mechanism.

---

## 6. Secondary finding: the OneMax seed count in the Figure 1 caption is false

`multi_domain_analysis.py` loads OneMax from `experiment_e_raw.csv`, which contains **2 seeds**.
The Figure 1 caption claims 30. The 30-seed OneMax run exists, in `experiment_e_per_island.csv`.

Both files give the identical topology ordering (none > ring > star > random > FC), so **no
conclusion changes**. But the caption is false and should be corrected — either by pointing the
analysis at the 30-seed file or by amending the caption to say 2.

---

## 7. Summary

| claim | status |
|---|---|
| Universal ordering none > ring > star > random > FC, 6 domains | **holds** |
| Sorting networks violate the ordering (scope condition) | **holds** |
| λ₂(ring) = 1.382 (n=5), 0.753 (n=7) | **wrong — exactly 2× too large** |
| Spearman(diversity, λ₂) | **improves: −0.90 → −1.00 in 6/6** |
| "ring/star inversion at n=7, confirmed" (`:512`) | **RETRACTED — no inversion exists or is predicted** |
| n=7 maze result itself (p = 2.7 × 10⁻⁵) | **holds — and now confirms a correct prediction** |
| "Fisher's combined p = 0.14" (`:388`) | **DOES NOT REPRODUCE — correct value 0.0035** |
| "ring and star hard to distinguish" (`:388`) | **RETRACTED — ring > star in 6/6, p = 0.0035** |
| λ₂ as the *mechanism* | **NOT ESTABLISHED — perfectly confounded with migration volume** |
| OneMax n=30 seeds (Fig. 1 caption) | **false caption; conclusions unaffected** |

The correction makes the empirical result stronger and the causal claim weaker. Both halves of
that sentence must be said out loud.
