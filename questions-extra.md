# questions-extra.md — hostile / probing questions, with spoken answers

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
> statistic and it's exactly one. Within a domain, topology explains sixty-eight percent of the
> variance in final diversity. And no-migration against fully-connected is a paired effect size
> of one point seven. The abstract attached the wrong number to a claim that holds without it.
> Thank you for reading the supplement — genuinely."

---

## Q2. "You call it a two-way ANOVA, but there's no F-test anywhere in your released code. Where did F equals forty-seven point eight come from?"

> "It shouldn't be in the paper. The released scripts compute a variance ratio, not an F-test —
> there's no ANOVA in that code, and the F-values in that table don't have a source I can point
> you to. That's an error and we'll correct it. Run the analysis honestly on the topology data —
> and I have — and the result holds: the ordering is the same in all six domains, and within a
> domain topology explains sixty-eight percent of the variance in final diversity. That one I
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
> every domain is on the same footing, topology explains about sixty-eight percent of what's left.
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

> "Yes — and that's in our own supplement, in the per-island columns. Within an island, diversity
> goes *up* with connectivity, and the no-migration case is actually last on that metric.
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
> domain, topology explains sixty-eight percent of the variance in final diversity. And
> no-migration against fully-connected is a paired effect size of one point seven. The abstract
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
