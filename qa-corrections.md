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
> is a rank statistic, so scale can't move it, and it is still exactly 1.0. And within a domain,
> topology explains about sixty-eight percent of the variance in final diversity. The single
> cleanest contrast — no migration against fully connected — is a paired effect size of one
> point seven. Every operator is identical across those five conditions; only the migration
> graph changes.
> So the number in the abstract is broken. The claim in the title is not."

## ⚠️ DO NOT SAY "OUR HEADLINE REVERSES."
## ⚠️ NEVER SAY THE 94 PERCENT OR THE 171x NUMBER ON STAGE.

There is a true sentence — "on raw diversity levels, domain explains about 2.8x more variance
than topology" — that *sounds* like a confession and is **not one**. It is true about the *wrong
contrast*. Said on stage, it would concede a paper that is actually correct.

- The title claim is **"Composition Determines Diversity."**
- The evidence for it is **the topology experiment**, and only that: (a) the **ordering** —
  Kendall's W = 1.0, a *rank* statistic, immune to the scale differences that make domain
  dominate the levels; (b) **68.1% of within-domain variance**; (c) the **clean paired contrast**
  none vs fully-connected, dz = 1.73. Operators are identical across all five topology
  conditions — a migration graph is not a parameter of any operator, so no operator confound is
  even constructible.
- It is **not** the fingerprints. That comparison is confounded — see section D.
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
  Kendall's W = 1.0, chi2 = 24.0, df = 4, p = 7.99e-5 — reproduces the paper exactly.
- **Within domain** (which is what the ordering claim is actually about):
  **topology explains 68.1%**, F(4,755) = 402.6, p = 1.5e-185.
- **The clean paired composition contrast:** none minus fully_connected = **+0.1533 diversity,
  dz = 1.73, p = 2.7e-47.**
- **Drop OneMax** (the 2-seed domain): W = 1.0 still holds on the five 30-seed domains, p = 5e-4.
- **Honest caveat — volunteer it, don't hide it.** Bootstrap over seeds: P(W = 1.0) = 0.254,
  mean W = 0.958, 95% CI [0.87, 1.0]. Say *"essentially perfect in our data, with a bootstrap
  range down to 0.87."* Never sell "perfect" as if it were guaranteed on a rerun.
- **ALWAYS say WITHIN-domain.** On *pooled* final diversity, domain beats topology (62.1% vs
  21.8%) purely because of genome-length scale. Saying "more variance than domain" over a pooled
  diversity plot is the wrong estimand, and a sharp questioner will nail it.

**This is the composition result.** The topology experiment is a clean composition contrast *by
construction*: the operators are identical across all five conditions, only the migration graph
varies, and a graph is not a parameter of any operator. No operator confound is possible.

## C. The seed-count defect

The paper claims **30 seeds** at `:320` and `:370`. The OneMax CSV in the supplement contains
**2 seeds**. That is a straight error in the text. Concede it. It does not touch the ordering:
W = 1.0 is a concordance *across domains*, and the five non-OneMax domains carry it.

## D. THE 94.17% / 171x NUMBER IS RETIRED

> ### ⛔ DO NOT SAY: **Never say the 94 percent or the 171x number on stage.**
> Not as a pivot, not as a fallback, not "in the fingerprint experiment where composition
> actually varies." It is dead. Every pivot goes to the topology experiment instead.

**This file used to call 94.17% "the paper's real headline... if anything under-claimed."
That was wrong.** Two independent recomputations from the raw supplementary CSVs — one trying to
refute it, one trying to defend it — reached the same verdict: **the number is arithmetically
true, but the estimand is confounded.**

**Why it dies.** The four "strategies" in `strategy_fingerprints.py` do **not** differ only in
composition. They differ in their operator settings:

- flat: tournament 3, mutation 1/L. island: tournament 3, mutation 1/L.
- **hourglass: tournament 2 / 5 / 2, mutation 2x / 0.5x / 2x base.**
- **adaptive: tournament 2 -> 5, mutation 2x -> 0.5x.**
- Terminal mutation rate spans **4x** (0.5/L to 2.0/L). Tournament spans **2 to 5**.
  **Only the crossover rate (0.8) is genuinely constant.**

So "strategy" is not a composition label. It is a bundle of composition *and* operator settings,
and the operator settings do almost all the work:

- **Terminal mutation rate ALONE gives R² = 0.9384**, against 0.9417 for the full 4-level strategy
  label. The composition label adds **0.33 points** over one scalar.
- **89.6% of the strategy sum-of-squares is the single Hourglass-vs-rest contrast** — and
  Hourglass is the one strategy that spends its final 25 generations in a high-mutation
  "diversify" phase. Measured at the final generation.
- **The clean contrast kills it.** Flat vs Island: identical mutation (1/L), identical tournament
  (3), differing **only** in compositional structure. Effect = **+0.0066, paired p = 0.478.**
- **And it is not underpowered.** The 80% MDE is 0.0268 — it could have detected an effect **13x
  smaller** than the headline. This is a null, not a shrug.

**No retreat is available.** The paper cannot fall back on "the schedule *is* the composition,"
because `paper-camera-ready-gecco-v1.tex:495-496` asserts: *"All four strategies use identical
selection, crossover, and mutation operators. Only how these operators are composed... differs."*
That sentence is **false against the code**. It is a defect, and it must be conceded, not leaned on.

**What survives from the fingerprint experiment:** the *shapes*. Monotonic decline;
spike-crash-rebound; stable maintenance; spike-then-collapse. The 18x final-diversity spread is in
the paper. Describe the shapes. Do **not** attribute them to composition, and do **not** quote a
variance decomposition off that experiment.

**Where the composition claim lives now: the topology experiment** (section B above). Operators
identical across all five conditions; only the migration graph varies; a migration graph is not a
parameter of any operator, so no operator confound is even constructible. W = 1.0 across six
domains (p = 0.00008); 68.1% of **within-domain** variance, F(4,755) = 402.6; none vs
fully-connected dz = 1.73, p = 2.7e-47.

**Downstream:** `questions-audience-10.md` Q2 and Q7 have been rewritten to pivot to topology.
`questions.txt` Q12 (which falsely claimed "same mutation rate, same tournament size") and
`questions-extra.md` still need scrubbing of the 94% figure before the session.

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
p = 0.00008**, the **68.1% within-domain topology effect**, the **none-vs-fully-connected paired
contrast (dz = 1.73)**, and the **n=7 confirmatory prediction (p = 6.6e-5)** all reproduce
exactly — independently re-derived from the raw CSVs. That is the composition result, and it is
clean.

**This is not a broken paper.** It is a correct paper with a wrong number in its abstract, a
fabricated ANOVA table, a seed-count error, a confounded fingerprint comparison, and an
under-reported seventh domain. Concede all five without flinching — and do not let the concessions
be mistaken for a retraction of the title.

## H. The seventh domain (sorting networks) — volunteer it

`supplementary/experiments/experiment_e_sorting_network.csv` ships publicly, 30 seeds. The paper
mentions it in **one sentence with no numbers** (`:146` and `:385`, "a falsifying scope
condition"). That is not enough, and the word **"universal"** (abstract `:103`, contribution
`:141`, section title `:365`) is an overclaim.

- Its ordering is **none > star > fully_connected > ring > random** — it violates the canonical one.
- Including it drops **W from 1.000 to 0.878**.
- **But its topology effect is not significant: F = 2.14, p = 0.079.** Total spread across all five
  topologies is **0.012**, against **0.21 in maze**. The diversity response is near-degenerate
  there — the ranks are noise, not an ordering.
- **Stage line:** concede "universal" is an overclaim, say it should read "across six domains,"
  then give the degeneracy numbers. See `questions-audience-10.md` Q10. Anyone who opens the
  supplement finds this in ten minutes — raise it first.

---

# I. THE λ₂ ERROR — found the day before the talk. RAISE IT FIRST.

Full technical erratum: **`lambda2-correction.md`** in this repo. Reproduce it yourself with
`python3 verify_lambda2.py` — it runs in two seconds off the shipped CSVs.

**What happened, in one line:** the paper's λ₂ for the ring is computed on a two-way cycle, but
the code's ring only passes migrants one way round. Ring λ₂ is exactly 2× too large at both n=5
and n=7. Every other topology is unaffected.

**The result gets STRONGER, and one sentence gets RETRACTED.** Both. Say both.

- Corrected: Spearman(diversity, λ₂) = **−1.00 in 6/6 domains** (paper's λ₂ gives −0.90, and it
  is wrong on exactly the ring/star pair — the one pair the fix touches).
- **RETRACTED:** the Conclusion's "spectral graph theory predicts the ring/star inversion at n=7,
  confirmed experimentally" (`:512`). **There is no inversion, and none is predicted.** Ring beats
  star at both sizes. The n=7 maze experiment is real and stands (p = 2.7e-5) — but it confirms a
  *widening gap*, not a crossover.
- **DOES NOT REPRODUCE:** "Fisher's combined p = 0.14 across six domains" (`:388`). Correct value
  is **p = 0.0035**, ring > star in **6/6** domains. No code computing any Fisher combination
  exists anywhere in the repos. Do not defend this number. It is gone.
- **VOLUNTEER THE CONFOUND:** migration volume (0, 5m, 8m, 10m, 20m) is *also* rank-perfect with
  diversity, ρ = −1.00 in the same 6/6, and it also predicts ring > star at n=7. λ₂ and volume are
  **not separable in this dataset**. The paper's own volume control (in `random_migrate`) is
  broken by the same directed/undirected slip. Say this before anyone asks.

---

## THE STAGE ANSWER — λ₂ / the ring/star inversion (~45 seconds, say it out loud)

> "I have to correct the paper, and I'd rather do it from up here than have you find it.
>
> We report the connectivity of the ring as if migrants go both ways round the circle. They don't.
> In our code the ring is a one-way relay — each island passes copies to its neighbour and gets
> nothing back — while every other topology does a genuine two-way swap. So a ring connection is
> half as strong as we said. Our ring number is exactly double what it should be.
>
> Here is the thing: fixing it makes the result better, not worse. With the correct number, the
> ordering of the five topologies matches the ordering of the diversity perfectly — a correlation
> of minus one, in all six domains. With the number as printed, we got minus nought-point-nine, and
> the one place we got it wrong was precisely the ring-versus-star pair. Our own mistake was hiding
> our own result.
>
> But one sentence in the conclusion has to go. We claim the theory predicts ring and star swap
> places at seven islands, and that we confirmed it. There is no swap. Ring beats star at five
> islands and at seven. The seven-island experiment is real, and the gap gets *bigger* — which is
> what the corrected theory actually predicts, and it gets the size about right. So the prediction
> stands, but it is a different prediction from the one we wrote down.
>
> And I'll hand you the stick to beat me with: the number of individuals each topology moves is
> *also* perfectly ordered with diversity. I cannot separate the two in this data. The next
> experiment has to move the same number of migrants through every shape and change only the shape.
> Until then, this is a very clean correlation with a confound sitting right on top of it."

---

## THE 15-SECOND VERSION (for a hostile one-liner)

> "You're right, and it's worse than you think — our ring number is exactly double what it should
> be, because our ring only passes migrants one way. Fix it and the correlation goes from minus
> nought-point-nine to minus one, in all six domains. But the inversion sentence in our conclusion
> is wrong and I retract it: there is no inversion. Ring beats star at both sizes. And the honest
> caveat is that migration volume fits the data just as well as connectivity does — we can't tell
> them apart yet."

---

## If pressed on the Fisher p = 0.14

> "That number doesn't reproduce, and I'm not going to defend it. The correct combined p-value for
> ring versus star across the six domains is nought-point-nought-nought-three-five, and ring is
> ahead in all six. We wrote that they were hard to tell apart. They aren't. That claim was an
> artefact of the same connectivity error — it made ring and star look like neighbours when they
> aren't."

## If pressed on "so is λ₂ the mechanism?"

> "Honestly? Not established. λ₂ and the sheer number of migrants moved are rank-identical across
> every topology we ran, so this data cannot tell you which one is doing the work. What I can tell
> you is that the ordering is real, it's perfect, and it's the same in six very different domains.
> The mechanism is the next paper, and it needs an experiment we haven't run."
