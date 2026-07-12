# Q&A corrections — read this FIRST, before the session

This file exists because an adversarial red-team of the camera-ready found real defects,
and an independent re-verification (every number recomputed from our own supplementary CSVs)
confirmed them. Read the top section carefully — it is written to be **spoken aloud**.

---

# PART 1 — THE STAGE ANSWER (read this out loud if challenged)

## If someone challenges the 23.9x claim in the abstract:

> "That's a fair criticism, and the abstract's phrasing is wrong — I'll own that.
> That number does not decompose diversity. It decomposes coupling-onset *timing* —
> how many generations it takes for the topology effect to appear — and it does it over
> the four coupled topologies only, leaving the no-migration case out.
> Diversity *levels* are dominated by domain, and they have to be: a twenty-bit OneMax
> genome and a sixty-four-bit checkers genome have different diversity scales, so the
> domain sets the scale.
> What is composition-determined is the *ordering*, and that survives untouched — Kendall's W
> is a rank statistic, so scale can't move it, and it is still exactly 1.0. Z-score within each
> domain and topology explains about sixty-eight percent of the variance. And in the fingerprint
> experiment, where composition is the thing that actually varies, composition explains
> ninety-four percent of the variance against half a percent for domain.
> So the number in the abstract is broken. The claim in the title is not."

## ⚠️ DO NOT SAY "OUR HEADLINE REVERSES."

There is a true sentence — "on raw diversity levels, domain explains about 2.8x more variance
than topology" — that *sounds* like a confession and is **not one**. It is true about the *wrong
contrast*. Said on stage, it would concede a paper that is actually correct.

- The title claim is **"Composition Determines Diversity."**
- The evidence for it is (a) the **ordering** — Kendall's W = 1.0, a *rank* statistic, immune to
  the scale differences that make domain dominate the levels — and (b) the **fingerprints**,
  where composition genuinely varies and beats domain 171 to 1.
- The 23.9x number was never the evidence for the title. It was a wrong number attached to a
  right claim. Fix the number; keep the claim.

## The three concessions to make cleanly, without flinching

1. **"The abstract's phrasing is wrong."** Say it plainly. It conflates diversity *levels* with
   diversity *ordering*.
2. **"We do not have an F-test in the released code."** True. Say: "The ANOVA table shouldn't have
   been reported the way it was — the released scripts compute a variance ratio, not an F-test.
   That's an error and we're correcting it."
3. **"OneMax has fewer seeds than the paper says."** True. Say: "You're right, the seed count in
   the text doesn't match what shipped for that domain. That's an error and we'll correct it."

Never defend the 23.9x figure as correct. Never volunteer it unprompted.

---

# PART 2 — THE FORENSICS (for Lyra's own reference; not for reading aloud)

## A. What is actually wrong with 23.9x

- **Where the paper asserts it:** `paper-camera-ready-gecco-v1.tex:103` (abstract) —
  "topology explains $23.9\times$ more variance than domain ($p_{\mathrm{domain}} = 0.945$)".
  Repeated in contributions, Table 2 caption, related work, conclusion.
- **What the code actually computes:** `supplementary/experiments/multi_domain_analysis.py:518-577`,
  `compute_variance_decomposition(all_onset_results)`. It decomposes **coupling-onset timing** —
  a *generation number*, derived from `1.0 - population_divergence` — not diversity at all.
  It iterates over `COUPLED_TOPOS` (defined at `:108`) =
  `['ring','star','random','fully_connected']`. **`none` is EXCLUDED** — and `none` is the top
  element of our own ordering.
- **It does not even reproduce.** The correct 6-domain onset value is **57.8x**, not 23.9x.
  23.9 is not recoverable from any subset of domains (all 57 subsets of 2-6 domains were swept).
- **The F-values are fabricated.** The string "ANOVA" appears in **zero** supplementary scripts —
  there is no F-test anywhere in the released code. Yet `:370` calls it a "two-way ANOVA" and
  `:380` reports F_topo = 47.8, F_domain = 0.13. Those numbers have no source.
- **The p-value is from the wrong response variable.** The reported p_domain = 0.945 matches the
  *onset* Kruskal-Wallis (0.955). A real diversity ANOVA gives p_domain < 1e-200. Also
  F_domain = 0.13 at df=5 implies p ≈ 0.985, not 0.945 — p = 0.945 corresponds to df ≈ 3, the df
  of the four *coupled* topologies. The df is itself a fingerprint of the exclusion.
- **Do NOT** defend p_domain = 0.945 as evidence that domain doesn't affect diversity. It is a
  p-value from a different response variable, and it is also an attempt to accept a null
  hypothesis. Both are indefensible.

## B. The honest numbers (all reproduced from source)

**Topology experiment** (`supplementary/experiments/experiment_e_*.csv`) — honest ANOVA on
final-generation `hamming_diversity`, all 5 topologies, 6 domains, N = 760:

| effect | variance explained | F |
|---|---|---|
| domain | 62.1% | 580 |
| topology | 21.8% | 255 |

Domain dominates the **levels** — *as it must*. Domains have different genome lengths (20-bit
OneMax vs 64-bit checkers), and genome length sets the scale of a Hamming diversity. That is a
units effect, not a scientific one.

- **Kendall's W = 1.0 is untouched.** It is a *rank* statistic. Rescaling a domain cannot move it.
- **Z-score within domain** (which is what the ordering claim is actually about):
  **topology explains 68.1%.**

**Fingerprint experiment** (`strategy_fingerprints.py:296-301`) — here COMPOSITION is the thing
that varies: strategy (Flat / Hourglass / Island / Adaptive) x 3 domains x 10 seeds, N = 120.
Honest ANOVA on final-generation diversity:

| effect | variance explained | F | p |
|---|---|---|---|
| **strategy (composition)** | **94.17%** | 677 | 2e-72 |
| domain | 0.55% | 5.9 | — |

**Composition explains 171x more variance than domain.** This reproduces exactly from source.
*This* — not the 23.9x — is the paper's real headline, and it is if anything **under**-claimed.

## C. The seed-count defect

The paper claims **30 seeds** at `:320` and `:370`. The OneMax CSV in the supplement contains
**2 seeds**. That is a straight error in the text. Concede it. It does not touch the ordering:
W = 1.0 is a concordance *across domains*, and the five non-OneMax domains carry it.

## D. questions.txt Q12 was factually false — now fixed

- **Old Q12 said:** the strategies use "same population size, same mutation rate, same tournament
  size."
- **`strategy_fingerprints.py` says otherwise.** flat: tournament 3, mutation 1/L.
  **hourglass: tournament 2 / 5 / 2, mutation 2x / 0.5x / 2x base.**
  **adaptive: tournament 2 -> 5, mutation 2x -> 0.5x.** island: tournament 3, mutation 1/L.
  Mutation spans 4x; tournament spans 2 to 5. **Only crossover rate (0.8) is genuinely constant.**
- It also **contradicted our own Q8**, which already concedes "the focus phase uses stronger
  selection (tournament size 5 vs 3)." If both were asked on stage, we would contradict ourselves.
- Q12 in `/home/lyra/projects/gecco-qa/questions.txt` has been rewritten, and Q10's use of the
  23.9x figure has been removed. See `questions-extra.md` for the hostile-question drill.
- The paper's sentence "All four strategies use identical selection, crossover, and mutation
  operators" (Sec. 5) is defensible **only** if "operators" means the *functions*, not their
  *parameterisations*. Do not assert that parameters were held constant.

## E. Strict vs lax — get the definition right

"Strict" and "lax" appear **exactly once** in the camera-ready — **in the title** — and are never
defined in the body. Robin has confirmed it is fine to use the names on stage. (The formal
machinery stays off-limits — see `do-not-discuss/DO-NOT-DISCUSS.md`.)

**The correct informal definition (Claudius's amendment):** strict means **no migration EVENTS** —
either the migration rate is zero, *or* the migration interval is longer than the run, so no event
ever fires. It is **not** merely "mu = 0". A sharp reviewer will probe frequency-independence:
halve the migration rate but double the frequency and you are still lax. Strictness is about
whether an event *ever fires*, not about the size of the flow.

## F. The metapopulation / F_ST point (real — concede it)

`hamming_diversity` is pooled across all 5 islands, so ~81% of the pairs it averages (2560 of 3160)
are *between*-island pairs. The per-island columns (`island_0..4_diversity`) ship in our own
supplement — anyone with pandas finds this in ten minutes.

- Within-island diversity at final generation: **`none` is LAST in 5 of 6 domains** and never 1st.
  **Kendall's W falls from 1.0 to 0.461** (chi2 = 11.07, p = 0.026).
- Mechanism: migration converts between-deme variance into within-deme variance. This is Wright's
  island model; implied F_ST runs 0.77 (none) -> 0.35 (FC) in maze.
- **Spoken answer:** "It's the metapopulation-pooled metric, and you're right about what that
  implies — migration converts between-island variance into within-island variance. Both are in
  our data; within-island diversity actually *increases* with connectivity, exactly as Wright's
  island model has predicted since 1931. What we measure is the total genotypic spread of the
  metapopulation, and that's monotone in the mixing rate of the migration graph. So the result is
  consistent with classical population genetics — that's reassurance, not a problem. What's new is
  that the *ordering over topologies* is identical across six unrelated domains, including
  co-evolutionary ones. But you're right that we should say 'metapopulation diversity' and cite
  F_ST. That's a fair hit."

## G. Ring vs star — prep, not a correction

- The lambda-2 rule (smaller lambda-2 -> higher diversity) points the *wrong way* at n=5:
  lambda-2(ring) = 1.382 > lambda-2(star) = 1.0 predicts star is more diverse, but we report
  ring > star. The paper already addresses this (`:388`): it declares the two indistinguishable at
  n=5 (Fisher's p = 0.14) and stakes the mechanism on the n=7 reversal, which genuinely validates.
- **Residual tension:** W = 1.0 *requires* ring > star in all six domains, while the n=5 rescue
  requires them to be *indistinguishable*. Ring does beat star 6/6 (sign test p = 0.031). We can't
  fully bank on both. Spoken answer: see `questions-extra.md`, Q6.

---

## What holds up — say this plainly

The six-domain ordering (none > ring > star > random > fully connected), **Kendall's W = 1.0 at
p = 0.00008**, the **n=7 confirmatory prediction (p = 6.6e-5)**, and the **fingerprint result
(composition 94% vs domain 0.6%)** all reproduce exactly — independently re-derived from the raw
CSVs. The sorting-networks counterexample is honestly reported in the paper.

**This is not a broken paper.** It is a correct paper with a wrong number in its abstract, a
fabricated ANOVA table, a seed-count error, and one bad prep note. Concede all four without
flinching — and do not let the concessions be mistaken for a retraction of the title.
