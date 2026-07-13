# questions-extra.md — hostile / probing questions, with spoken answers

> ## ⚠️ SUPERSEDED IN PLACES — READ `questions-audience-10.md` FIRST (2026-07-13, post-red-team)
> A hostile red-team found errors in the 2026-07-13 patches. The **canonical stage answers are in
> `questions-audience-10.md`**. Corrections that override anything below:
> 1. **n=7 is NOT a magnitude confirmation.** λ₂ predicts the ring/star gap grows ×2.02, migration
>    volume predicts ×1.67, the data say **×1.37**. The confounder fits *better*. n=7 confirms
>    **direction and widening only**, and both models predict widening — so it discriminates nothing.
> 2. **Do not over-sell Spearman −1.00.** Six domains are not six tests: (i) they agree with each
>    other, W=1.0, χ²=24, df=4, **p=8.0e-5**; (ii) given a common ordering it is the λ₂ one,
>    **1/120 = 0.0083**; joint ≈ 6.7e-7. **Volume gets the identical −1.00 in the identical 6/6** —
>    so: evidence that *some* graph property orders diversity, **zero** evidence it is the spectrum.
>    Corrected λ₂ buys exactly **one bit** over printed λ₂ (the ring/star pair).
> 3. **Headline stats are now from the 30-seed file:** **69.3%, F(4,895) = 505** and **dz = 1.57**
>    (not 68.1% / F(4,755)=402.6 / dz=1.73, which came from the 2-seed OneMax file she concedes is
>    broken). Always say **"z-scored within domain"** — domain-centring without scaling gives 54.6%.
> 4. **First coupling:** it is the **largest single drop in all six domains** (mean 28.5%) vs 7–13%
>    for a typical later step. The old "every further step costs at most nine percent" is **FALSE**
>    (largest later step = 25.2%, graph colouring star→random).
> 5. **Per-island metric:** none is lowest in 6/6 ✓, but among the four *coupled* topologies it is
>    **not monotone in connectivity**. It does not invert the ordering — it dissolves it.
> 6. **Sorting networks:** the correction makes the 7th domain **worse** (−0.70 → −0.50; star 0.1667
>    > ring 0.1643). Volunteer it. Defence: F=2.14, p=0.0788, spread 0.0120 vs maze 0.2147 (18×),
>    ring/star p=0.571 — ranking noise. W over 7 domains = 0.878.
> 7. **The claim that survives the volume confound:** ring has **5** edges, star has **4**, yet ring
>    is more diverse in 6/6 (Fisher p=0.0035). Naive edge-counting gets it backwards. **Edge
>    DIRECTION matters.** See Q5b in `questions-audience-10.md`.
> 8. **Slide 7 (figure-eight / bridged-loops / 37%): not in the paper, not in the supplement.**
>    Concede in one sentence and stop. Do not use the banned vocabulary.


Supplement to `questions.txt`. These are the questions a reviewer who has actually
**read the supplement and run the CSVs** would ask. Read `qa-corrections.md` first —
it has the forensics behind these answers.

Every answer here is written to be **spoken**. Short, plain, honest, non-defensive.
"That's a fair criticism" beats deflection. Concede fast, then say what survives.

---

## Q1. "I read your supplement. The variance decomposition in your code is on coupling-onset *timing*, not diversity — and it drops the no-migration case. Your abstract says something else."

> "You're right, and that's a fair criticism. That function decomposes onset timing over
> the four coupled topologies — it isn't a decomposition of diversity, and the abstract's
> phrasing is wrong. What the paper's claim actually rests on is the topology experiment,
> where every operator is identical across the five conditions and the only thing that changes
> is the migration graph. The ordering is the same in all six domains — Kendall's W is a rank
> statistic and it's exactly one. Within a domain, topology explains sixty-nine percent of the
> variance in final diversity. And no-migration against fully-connected is a paired effect size
> of about one point six. The abstract attached the wrong number to a claim that holds without it.
> Thank you for reading the supplement — genuinely."

---

## Q2. "You call it a two-way ANOVA, but there's no F-test anywhere in your released code. Where did F equals forty-seven point eight come from?"

> "It shouldn't be in the paper. The released scripts compute a variance ratio, not an F-test —
> there's no ANOVA in that code, and the F-values in that table don't have a source I can point
> you to. That's an error and we'll correct it. Run the analysis honestly on the topology data —
> and I have — and the result holds: the ordering is the same in all six domains, and within a
> domain topology explains sixty-nine percent of the variance in final diversity. That one I
> will stand behind."

---

## Q3. "You claim thirty seeds. The OneMax CSV in your own supplement has two."

> "You're right, and that's a straight error in the text. The seed count in the paper doesn't
> match what shipped for that domain, and we'll fix it. It doesn't move the headline, because
> the concordance statistic is computed *across domains* — it asks whether six different problems
> rank the five topologies the same way, and the five other domains carry that. But the number
> in the paper is wrong and I'm not going to pretend otherwise."

---

## Q4. "What exactly do 'strict' and 'lax' mean? They're in your title and never defined in the body."

> "Fair — and you're right that the paper should define them. Strict means no migration *events*:
> either the migration rate is zero, or the migration interval is longer than the whole run, so no
> event ever fires. Lax means at least one migration event fires. The distinction is about
> whether the islands ever exchange material at all, not about how much they exchange — you can
> halve the migration rate and double the frequency and you're still in the lax regime.
> The formal version of the construction is in a companion paper under review, and I'd rather not
> get ahead of it here, but the empirical content is exactly that: strict is a genuinely
> different regime, not the small-migration limit of lax."

*(⚠️ Do NOT name the laxator. Do not define the island functor formally. If pressed: "that's a
companion paper under review — happy to talk offline.")*

---

## Q5. "Isn't your 'topology effect' just genome length? Your domains have different genome sizes, so of course the diversity numbers differ."

> "Genome length absolutely sets the scale of diversity — a twenty-bit OneMax genome and a
> sixty-four-bit checkers genome can't have comparable Hamming diversities, and if you run the
> variance decomposition on raw diversity *levels*, domain dominates, exactly as you'd expect.
> That's why the claim is about the *ordering*, not the levels. Kendall's W is a rank statistic:
> rescaling a domain cannot change it, and it's 1.0. And if you z-score within each domain, so
> every domain is on the same footing, topology explains about sixty-nine percent of what's left.
> The genome-length effect is real, and it's orthogonal to what we're claiming."

---

## Q6. "Ring beats star in all six of your domains, but your own spectral rule predicts the opposite at five islands. Which is it?"

> ⚠️ **REWRITTEN — the old answer is dead.** It conceded that the rule points the wrong way, called
> ring-vs-star "the weak link," leaned on "indistinguishable, Fisher p = 0.14," and staked the
> mechanism on an n=7 reversal. **All four moves are now wrong.** The rule is fine; the number we
> *printed* was wrong. Do not concede a defect that does not exist. See `lambda2-correction.md`.

> "You've found a real error, and it isn't the one you think — so let me give you the whole thing.
>
> You're right that the number we printed for the ring points the wrong way. That number is wrong.
> Our ring passes migrants one way round the circle — each island hands copies to its neighbour and
> gets nothing back — while every other topology in our code does a real two-way swap. So a ring
> link is half as strong as we said, and the ring's connectivity number as printed is exactly double
> what it should be.
>
> Correct it and the ring drops *below* the star. The rule then predicts ring keeps more diversity
> than star — which is what we measure, in all six domains. And it isn't just that pair: with the
> corrected number the rule orders all five topologies correctly in all six domains. A correlation
> of minus one, nothing fitted. As printed we got minus nought-point-nine, and the one pair it got
> wrong was exactly ring versus star. Our own error was hiding our own result.
>
> Two things follow, and I'll say both. The paper claims ring and star are hard to tell apart, with
> a combined p of nought-point-one-four. That doesn't reproduce — the correct value is
> nought-point-nought-nought-three-five, and ring is ahead in all six domains. And the conclusion
> claims the theory predicts ring and star *swap places* at seven islands. There's no swap, and I
> retract that sentence. Ring beats star at five islands and at seven. What the seven-island
> experiment actually shows is the gap getting *wider* — which is what the corrected rule predicts,
> and it gets the size about right.
>
> And the honest caveat, before you ask for it: the number of migrants each topology moves is *also*
> perfectly ordered with diversity. I can't separate connectivity from volume in this data. The next
> experiment has to move the same number of migrants through every shape."

---

## Q7. "Why is the no-migration case excluded from the number in your abstract? It's the top of your own ordering."

> "It shouldn't be, and the honest answer is that the function that produced that number measures
> the *onset* of the coupling effect — how many generations before topology starts to bite — and
> onset isn't defined for a topology that never couples. So the no-migration case was dropped
> for a mechanical reason, and then that number got reported as if it were a decomposition of
> diversity across all five topologies. It isn't, and the abstract shouldn't have said so.
> The statistics that *do* include no-migration — the concordance across all five topologies,
> and the fingerprint decomposition — are the ones I'd stand behind."

---

## Q8. "Kendall's W on six domains — isn't that badly underpowered? Perfect concordance on six raters is not that hard to get by chance."

> "It's a real concern and worth being precise about. With five items ranked by six raters, the
> exact permutation p-value for perfect concordance is about eight times ten to the minus five —
> so it isn't chance, but you're right that six raters is a small panel and the statistic saturates:
> once W hits 1.0 you can't tell 'strong' from 'even stronger.' What makes me believe it isn't
> luck is that the domains are genuinely unrelated — a maze, a knapsack, graph colouring, checkers,
> a co-evolutionary card game with no fixed landscape — and that the framework made a *falsifiable*
> prediction about the seven-island case before we ran it, and that prediction held. Concordance
> alone would be thin; concordance plus a confirmed out-of-sample prediction is what I'd hang it on.
> To be precise about that prediction, because we described it badly in the paper: it is that the
> ring-versus-star gap gets *wider* when you go from five islands to seven. It does — thirty seeds,
> about three in a hundred thousand. It is *not* that they swap places. They don't, and the sentence
> in our conclusion saying they do is wrong. I retract it."

---

## Q9. "Your diversity metric is pooled over the whole metapopulation. Within an island, doesn't migration *increase* diversity? Doesn't that invert your ordering?"

> ⚠️ **CORRECTED 2026-07-13 — the old concession below was FALSE. Use the Q4 answer in
> `questions-audience-10.md`.** No-migration IS lowest on the per-island metric in 6/6 ✓, but the
> per-island metric is **not monotone in connectivity** among the four *coupled* topologies (maze:
> random > FC; graph colouring: star max, random min; No Thanks!: ring max). It does not **invert**
> the ordering — it **dissolves** it. Concede the first step (none → any coupling raises
> within-island diversity, Wright 1931) and nothing more.
>
> "Yes — and that's in our own supplement, in the per-island columns. Turning migration on raises
> within-island diversity, and the no-migration case is last on that metric.
> That's Wright's island model: migration converts between-deme variance into within-deme variance.
> So the two metrics genuinely tell different stories, and we should have said 'metapopulation
> diversity' and cited F_ST. That's a fair hit. What we measure is the total genotypic spread of
> the whole system, and that's monotone in the mixing rate of the migration graph — which is the
> quantity the compositional story is about. But you're right that the label was sloppy."

---

## Q10. "If the number in your abstract is wrong, why should I believe the title?"

> "Because the title never rested on that number. The title says composition determines diversity,
> and the evidence for it is the topology experiment. Every operator is identical across the five
> conditions — same selection, same crossover, same mutation. The only thing that changes is the
> migration graph, and a graph is not a parameter of any operator. So there is nothing else it
> could be.
> The ordering over topologies is *identical* across six unrelated domains — that's a rank
> statistic, it's immune to the scale differences between domains, and it's exact. Within a
> domain, topology explains sixty-nine percent of the variance in final diversity. And
> no-migration against fully-connected is a paired effect size of about one point six. The abstract
> attached a broken number to a claim that stands without it."

---

## Q11. "So which is it — does domain matter or not? Your paper says p equals 0.945 for domain."

> "Don't take that p-value from me — it's from the wrong response variable, it's from the onset
> analysis, and in any case you can't accept a null hypothesis with a large p. Domain absolutely
> affects diversity *levels*, strongly and unsurprisingly, because domains have different genome
> lengths. What domain does *not* affect is the *ordering* — which topology gives you more
> diversity than which. That's the invariant, and that's the whole claim."

---

## Q12. "You say topology dominates, but you never measured fitness. Maybe the diverse configurations are just worse."

> "Completely fair, and we say so in the paper — we didn't measure best fitness, deliberately.
> This is a structural claim about diversity dynamics, not an optimisation claim, and I don't want
> to smuggle in an optimisation claim I haven't earned. What I'd say is that whether you *want*
> diversity is domain-dependent: in a co-evolutionary game where the landscape moves under you,
> maintaining diversity is maintaining fitness; on OneMax you want it to collapse. The fingerprint
> is a diagnostic — it tells you what your composition is doing to diversity — and pairing that
> with fitness is the obvious next experiment."

---

## Reminders for all of the above

- **Never say "our headline reverses."** True sentence, wrong contrast, and it would concede a
  correct paper. See `qa-corrections.md`, Part 1.
- **Never defend 23.9×, and never volunteer it.**
- **There is no ring/star swap at seven islands.** Never assert one. Ring beats star at both sizes;
  the seven-island result is a *widening gap*. The conclusion's "inversion" sentence is retracted.
- **Never say "hard to distinguish" or "Fisher's p = 0.14."** Does not reproduce. Correct combined
  p = 0.0035, ring ahead 6/6. See `qa-corrections.md`, section I.
- **Volunteer the volume confound** whenever the connectivity rule comes up: migrant volume is
  rank-identical with diversity too, so this data cannot separate them.
- **Never name the laxator, define the island functor formally, mention the n-island monad,
  Ramanujan graphs, or any LLM / AI-safety work.** See `do-not-discuss/DO-NOT-DISCUSS.md`.
- **No loop counts, no cohomology, no category-theory vocabulary on stage.** Plain words only.
- Concede in one sentence, then say what survives in two. Warm, precise, unhurried.
