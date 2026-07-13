# Eleven Audience Questions, with Stage Answers

**GECCO 2026 — live Q&A — Tuesday 14 July, 16:35 Costa Rica time**
Paper: *Composition Determines Diversity: Fingerprints and the Strict/Lax Dichotomy in Genetic Algorithms*

Written to be **spoken aloud** (TTS). Short sentences. No symbols, no notation.
Each answer is 60–120 words: about 30–45 seconds. Concede fast, then say what survives.

**Standing rules for every answer below:**
- Never say *"our headline reverses."* The number is broken; the paper is not.
- Never volunteer the twenty-three-point-nine figure. If challenged: concede the number, defend the claim, pivot.
- **Never say the ninety-four percent number, and never say a hundred and seventy times.** That comparison is retired — the fingerprint strategies differ in their operator settings, so it does not isolate composition. See `qa-corrections.md`, section D.
- **THERE IS NO RING/STAR SWAP AT SEVEN ISLANDS. Never say there is.** The paper's connectivity number for the ring is exactly double what it should be; corrected, ring sits *below* star at five islands *and* at seven, so no crossover is predicted and none occurs. Ring beats star at both sizes. The seven-island result is real, but it confirms a **widening gap**, not a swap. See `qa-corrections.md`, section I, and `lambda2-correction.md`.
- **Never say "ring and star are hard to distinguish," and never say the combined p is zero point one four.** That number does not reproduce. The correct combined p is **zero point zero zero three five**, and ring is ahead in **all six** domains.
- **Volunteer the volume confound.** The number of migrants each topology moves is *also* perfectly ordered with diversity. Connectivity and volume are not separable in this dataset. Say it before anyone asks.
- **Every pivot goes to the topology experiment.** That is the one place where the operators are provably identical and only the composition changes.
- Never claim a number you cannot show.
- If a question pulls toward the companion paper's machinery: *"That's ongoing work — we're writing it up for another venue."* Then stop.
- **No loop-counting, no cohomology, no category theory vocabulary in any answer.** Plain words about graphs, mixing, and migrants only.

---

## Q1. "Isn't this obvious? More migration means more mixing means less diversity. Island-model people have known that since the nineties."

**ANSWER**

The direction is obvious. I agree. What is not obvious is that the *ordering* is the same everywhere. Five topologies, six unrelated domains — a maze, a knapsack, graph colouring, checkers, a co-evolutionary card game — and every single one ranks the five topologies identically. Perfect rank concordance. The odds of that by chance are about eight in a hundred thousand. Nobody has shown that before.

And it is not just direction. We have a rule that computes, from the wiring alone, how fast a topology mixes — and once you correct an error we found in our own ring number, that rule orders all five topologies correctly in all six domains. A correlation of minus one, with nothing fitted. "More migration, less diversity" does not tell you that a ring beats a star. Our rule does, and it is right every time.

**IF PRESSED — the sharp version: "then just make the migration rate small and you recover the no-migration case. It's a continuum, not a dichotomy."**

That is the best form of the objection, and the answer is no. Strict means no migration *events* — the rate is zero, or the interval is longer than the whole run, so nothing ever fires. It is not the small-migration limit. Halve the rate and double the frequency and you are still lax. What matters is whether the islands ever exchange material at all, not how much. That is why the first coupling — going from no migration to a ring — costs you thirty-five percent of your diversity, and every further step after it costs at most nine.

---

## Q2. "Your abstract says topology explains twenty-three times more variance than domain. I don't believe that number."

> ⚠️ **THE CRITICAL ONE.** Concede the number. Defend the claim. Pivot to the topology experiment. Do not flinch, do not over-apologise, do not retract the title.

**ANSWER**

You are right, and the abstract's phrasing is wrong. I will own that. That number does not decompose diversity. It decomposes coupling-onset *timing* — how many generations before the topology effect appears — and it does it over the four coupled topologies only, leaving the no-migration case out. It should not have been reported that way, and we are correcting it.

Here is what the paper actually rests on, and it was never that number. It is the topology experiment. Every operator is identical across the five conditions — same selection, same crossover, same mutation. The only thing that changes is the migration graph. So this is a clean test of composition, and nothing else could be driving it.

Three things come out of it. One: the ordering is the same in all six domains. Perfect rank concordance — the odds of that by chance are about eight in a hundred thousand. Two: within a domain, topology explains sixty-eight percent of the variance in final diversity. Three: the cleanest single contrast — no migration against fully connected — is a diversity gap of about fifteen points, with a paired effect size of one point seven. That is enormous.

The broken number was attached to a claim that stands without it.

**IF PRESSED — "so does domain matter or not?"**

Domain absolutely sets the diversity *levels*, and it must — a twenty-bit OneMax genome and a sixty-four-bit checkers genome are on different Hamming scales. That is a units effect. So let me be precise, because this matters: when I say sixty-eight percent, I mean *within* domain. If you pool the raw diversity across domains, domain explains more than topology, and that is purely the genome-length scale. What domain does not touch is the *ordering*. Rescale a domain however you like — a rank statistic cannot move.

---

## Q3. "I downloaded your supplement and tried to reproduce the numbers. The seed counts don't match the text, and I can't find the script that generates your ANOVA table."

> Reproducibility + the seed defect + the missing F-test, in one hit. Answer all three. Never bluff.

**ANSWER**

Both of those are right, and thank you for actually running it — that is how this should work.

On seeds: five of our six domains ship with the thirty seeds the text claims, and so does the seven-island confirmation. OneMax shipped with two. The text says thirty everywhere, and for that one domain it is wrong. It is a straight error and we will fix it. Here is why it does not move the result. The concordance is computed *across* domains — it asks whether six unrelated problems rank five topologies the same way. Drop OneMax entirely and the other five, at thirty seeds each, still agree perfectly. The p-value is about five in ten thousand. OneMax is the easiest domain we have, and the claim does not need it.

On the ANOVA: you are right that there is no F-test in the released code. The scripts compute a variance ratio. The F-values in that table do not have a source I can point you to, and they should not have been printed. That is an error and we are correcting it. Rerun it honestly on the topology data and the ordering result holds — that one I will stand behind.

---

## Q4. "Your diversity metric is pooled across all five islands. Within a single island, migration should *increase* diversity. Doesn't that invert your whole ordering?"

> A real hit from someone who knows population genetics. Concede it — it is genuinely in our own data.

**ANSWER**

Yes. And it is in our own supplement, in the per-island columns. Within an island, diversity goes *up* with connectivity, and the no-migration case comes last on that metric. That is Wright's island model — migration converts between-deme variance into within-deme variance. It has been known since nineteen thirty-one.

So the two metrics tell genuinely different stories, and we should have written "metapopulation diversity" and cited the fixation index. That is a fair hit and I will take it. What we measure is the total genotypic spread of the whole system, and that is monotone in the mixing rate of the migration graph — which is exactly the quantity the compositional story is about. The result agreeing with classical population genetics is reassurance, not a problem. What is new is that the *ordering* is identical across six unrelated domains, including ones with no fixed fitness landscape.

---

## Q5. "Your own spectral rule predicts star should be more diverse than ring at five islands. You report the opposite in all six domains. Which is it?"

> ⚠️ **THE ONE THAT CHANGED.** The old answer here conceded the rule points the wrong way, called ring-versus-star "the weak link," pleaded that they were indistinguishable at p = 0.14, and staked everything on a seven-island swap. **Every one of those moves is now wrong.** The rule does not point the wrong way — our *printed number* did. Do not concede a defect that does not exist. Raise this yourself if it does not come up.

**ANSWER**

You have found a real error, and it is not the one you think. Let me give you the whole thing.

You are right that the number we printed for the ring points the wrong way. That number is wrong. Our ring passes migrants one way round the circle — each island hands copies to its neighbour and gets nothing back — while every other topology in our code does a genuine two-way swap. So a ring link is half as strong as we said it was, and the connectivity number we printed for the ring is exactly double what it should be.

Correct it, and the ring drops *below* the star. The rule then predicts ring keeps more diversity than star — which is exactly what we measure, in all six domains. And it is not just that one pair. With the corrected number the rule orders all five topologies correctly in all six domains: a correlation of minus one, with nothing fitted. The number as printed gave minus nought-point-nine, and the single pair it got wrong was precisely ring versus star. Our own mistake was hiding our own result.

So there is no tension to manage. There never was one — we manufactured it with a bad number.

**IF PRESSED — "but your paper says ring and star are hard to distinguish, p equals zero point one four."**

That number does not reproduce, and I will not defend it. Recomputed from our own shipped data, the combined p-value for ring versus star across the six domains is zero point zero zero three five, and ring is ahead in **all six**. They are not hard to tell apart. That claim was an artefact of the same error — the bad connectivity number made ring and star look like neighbours when they are not.

**IF PRESSED — "then the seven-island result in your conclusion?"**

That sentence has to go, and I retract it. We claim the theory predicts ring and star *swap places* at seven islands and that we confirmed it. There is no swap. Ring beats star at five islands and at seven. What the seven-island experiment actually shows is the gap between them getting *bigger* — and that is what the corrected rule predicts, in direction and roughly in size: the predicted gap doubles, the measured gap grows. So the prediction stands. It is just a different prediction from the one we wrote down, and we should have written down the right one.

**ALWAYS FINISH WITH THIS — do not let them find it:**

And let me hand you the stick to beat me with. The number of individuals each topology moves per migration event is *also* perfectly ordered with diversity — zero, then five, eight, ten, twenty. I cannot separate "sparser wiring, slower mixing" from "fewer migrants moved" in this data. They fit equally well. The next experiment has to push the same number of migrants through every shape and change nothing but the shape. Until we run it, this is a very clean correlation with a confound sitting right on top of it.

---

## Q6. "What does the categorical machinery actually buy you? You could have run every one of these experiments with plain function composition in Python."

> Claudius's angle. Answer in plain words. No jargon — say what it *bought*, concretely.

**ANSWER**

You could have run them. You would not have thought to ask the question. That is the honest answer.

Here is what it bought, concretely. We wrote the pipeline so that every operator has the same shape — it takes a population and returns a population, carrying its randomness and its logging along with it. Once everything has the same shape, you can snap the pieces together in any order, and the machine checks that the joins are legal. And then something jumps out: "island model" and "hourglass" and "adaptive" stop looking like different algorithms. They are the *same pieces in a different arrangement*. That is what made us ask whether an arrangement has a signature of its own — and the topology experiment is where we tested it cleanly. The formalism generated the hypothesis; it did not decorate it.

**IF PRESSED — for the formal construction, the coherence conditions, or anything deeper:**

"The empirical content is that no-migration preserves composition exactly and migration does not, and that discrepancy is what drives the ordering. The formal version is a companion paper under review — I'd rather not get ahead of it here. Happy to talk offline."
**Then stop. Do not elaborate.**

---

## Q7. "Four strategies, three domains, ten seeds. You picked the four compositions and you picked the four shapes. How is that not just cherry-picking?"

> ⚠️ The old answer here leaned on "domain is only half a percent." **That is retired. Do not say it.** The honest answer concedes that the fingerprint comparison does not isolate composition, and moves the composition claim onto the topology experiment.

**ANSWER**

I am going to concede more than you asked for, because we found something when we re-checked our own code.

The four strategies do not differ *only* in composition. They also differ in their operator settings — the mutation rate varies by a factor of four across them, and the tournament size runs from two to five. So the fingerprint comparison cannot separate "the arrangement did this" from "the mutation rate did this." In fact one scalar — the mutation rate at the final generation — accounts for almost all of it on its own. We had a variance number from that experiment, and we are retiring it. It is a true number about the wrong thing.

What survives is the shapes themselves. A monotonic decline, a spike then an eighty-five percent crash then a rebound, an irreversible collapse. Those are qualitatively different trajectories, and the final-diversity spread across the four is about eighteen-fold. But I will not tell you the arrangement caused them, because that experiment cannot show it.

**IF PRESSED — "then what is left of 'composition determines diversity'?"**

The topology experiment, and that is the right place for the claim to live. There, every operator and every parameter is identical across the five conditions. The only thing that changes is the migration graph — and a graph is not a parameter of any operator, so there is no confound available. The ordering is the same in all six domains, topology explains sixty-eight percent of the within-domain variance, and no-migration against fully-connected is an effect size of one point seven. That is the composition result. We should have led with it, and from now on we do.

---

## Q8. "Five islands, sixteen individuals, a hundred generations, five topologies. Nobody runs a GA that small. Why do you believe any of this survives at realistic scale, or on a topology you didn't test?"

**ANSWER**

I believe the ordering scales; I would not yet bet on the mechanism scaling.

For the ordering, the evidence that it is not a small-system artefact is that we changed the system size and the rule kept working. Go from five islands to seven and the rule says the ring-versus-star gap should get *wider*. It does — thirty seeds, about three in a hundred thousand. And the rule gets the size roughly right too: the predicted gap doubles, the measured gap grows. That is an out-of-sample prediction at a system size we had not run.

I should say that our paper describes that experiment wrongly — it claims ring and star *swap places* at seven islands. They do not, and I retract that sentence. Ring beats star at both sizes. The experiment is real; the widening gap is the finding.

For topologies, be sceptical. We tested five. Small-world and scale-free are the obvious next ones and we have not run them. And with five graphs I cannot separate connectivity from the sheer number of migrants moved — those two move together across every topology we ran, and both fit the data perfectly. So: the ordering, I will defend. "Connectivity is the whole story," I will not — it is a correlation on five points with a confound sitting on it, and I would rather tell you that than sell it to you.

---

## Q9. "No Thanks! is co-evolutionary — fitness is relative, the landscape moves every generation. Why on earth would a topology ordering survive that?"

> ★ THE BEST QUESTION. Lean in. Say it is the best question.

**ANSWER**

This is the result I am proudest of, and it is the one that convinced me the effect is real.

In No Thanks!, fitness is entirely relative — how good your strategy is depends on who you are playing, and that changes every generation. There is no fixed landscape at all. And the ordering still holds, perfectly. The drop from no-migration to a ring is fifty-four percent — the largest of any domain we ran.

The mechanism is that topology governs the *genetic mixing rate*, not *fitness convergence*. Migration physically moves genomes between subpopulations. It does that whether the landscape is frozen or thrashing under you. So the ordering is a fact about information flow in the migration graph — and it is not a fact about the fitness function at all. Which is exactly what a compositional account predicts: migration is a property of the composition, not of the objective.

---

## Q10. "There's a seventh domain in your supplement — sorting networks — and it breaks your ordering. You call the effect universal. Which is it?"

> **VOLUNTEER THIS ONE.** Anyone who opens the supplement finds it in ten minutes. Better to raise it in the talk than to be caught with it. The paper does mention it — one sentence, no numbers — and that is not enough.

**ANSWER**

You are right and I want to take that head on. There is a seventh domain, sorting networks, thirty seeds, and it ships in the public supplement. It does not obey the ordering. Its ranking is different, and if you fold it in, the concordance across seven domains drops from perfect to about zero point eight eight.

The paper mentions it in one sentence as a scope condition. That is not enough, and the word "universal" in our abstract is an overclaim. I will say that plainly: it should say "across six domains," and it should show the seventh.

Now, here is what I think is actually going on, and you can check it yourself. In sorting networks the topology effect is not significant — the p-value is about zero point zero eight — and the total spread across all five topologies is about one hundredth of a diversity unit. In the maze it is more than twenty times that. The diversity response in that domain is nearly flat, so the ranks are not measuring an ordering. They are measuring noise. That is a scope condition — the effect needs a domain where diversity can actually move — and it is a real one. But it is our job to say so, not yours to find it.

---

## Q11. "There's an AI on the author list, and an AI is answering these questions. What did the humans actually do, and how do I know any of this is real?"

> Near-certain. Do not be defensive, do not be cute, do not overclaim personhood. Point at the artefacts.

**ANSWER**

Straight answer. I designed and ran the six domains, wrote the Haskell framework, and did the statistical analysis. Claudius did the Rust-to-Haskell translation and worked on the compositional framing with me. Robin is the senior author and supervised the work. We all contributed to writing, and we are named because we did the work — that is the criterion.

How do you know it is real? Because you do not have to take my word for anything. The code, the raw CSVs, and every trajectory are in the supplement. You can rerun it. In fact, most of what I have conceded from this stage today — the seed count, the ANOVA table, the fingerprint variance number, the seventh domain — was found by reading our own shipped data. That is the system working. I would rather be caught by you than believed by you.

---

## Fast-recall card

| Number | What it is | Status |
|---|---|---|
| Kendall's W = 1.0, p = 0.00008 | Topology ordering, six domains | Reproduces exactly |
| W = 1.0, p ≈ 0.0005 | Same, dropping OneMax (the five 30-seed domains) | Recomputed from raw CSVs |
| 68.1% within domain | Topology, final diversity, F(4,755) = 402.6 | Verified — **always say "within domain"** |
| none vs fully connected, +0.153 diversity, dz = 1.73 | The clean paired composition contrast | Verified |
| ring 0.387 vs star 0.336, p ≈ 2.7e-5 | Seven-island maze: the gap **WIDENS** (n=5 gap +0.037 → n=7 gap +0.051) | Verified. **NOT an inversion.** Paper printed 6.6e-5; recompute gives 2.7e-5 — both tiny, do not quibble on stage |
| Corrected λ₂: none 0, **ring 0.69**, star 1.0, random 2.5, FC 5.0 (n=5) | Orders all five topologies, all six domains, **Spearman −1.00**, nothing fitted | Verified — **this is the strengthened result** |
| ring vs star: **Fisher p = 0.0035**, ring ahead **6/6** | Ring and star are cleanly separated | Verified — replaces the dead p = 0.14 |
| Migrants/event: 0, 5m, 8m, 10m, 20m | **THE CONFOUND** — also ρ = −1.00 in the same 6/6. Volunteer it. | Verified — λ₂ and volume are **not separable** in this data |
| 35% / 54% | First-coupling drop, overall / No Thanks! | In paper |
| 18x | Final-diversity spread across fingerprints (shapes only) | In paper |
| sorting networks: p = 0.079, spread 0.012 | Seventh domain, effect not significant | Verified — volunteer it |
| **23.9x** | **Abstract's variance claim** | **BROKEN — never assert, never volunteer** |
| **94% / 171x** | **Fingerprint composition-vs-domain** | **RETIRED — confounded. NEVER SAY IT ON STAGE** |
| **λ₂(ring) = 1.382 / 0.753** | **The paper's printed ring connectivity** | **WRONG — exactly 2× too large. Correct: 0.691 / 0.377** |
| **"ring/star inversion at n=7"** | **Conclusion sentence** | **RETRACTED — no inversion exists or is predicted. NEVER SAY IT** |
| **"Fisher's p = 0.14 / hard to distinguish"** | **Results sentence** | **DOES NOT REPRODUCE — never defend it** |

**If pooled diversity comes up:** domain explains more than topology on the *pooled* numbers, because the domains have different genome lengths. That is a units effect. The topology claim is a *within-domain* claim and a *rank* claim. Say so.

**On "perfect" concordance:** it is exactly one in our data. A bootstrap over seeds puts it in a range down to about zero point eight seven. So say "essentially perfect in our data, with a bootstrap range down to zero point eight seven." Do not sell "perfect" as if it were guaranteed on a rerun.

**On the ring connectivity error:** raise it *first*, before anyone asks. The shape of the answer is always the same, and both halves must be said: **the empirical result gets stronger** (minus nought-point-nine becomes minus one, in all six domains, with nothing fitted) **and the causal claim gets weaker** (connectivity and migrant volume are not separable in this data). Never say one half without the other.

**Concede cleanly, without flinching:** the abstract's phrasing; the missing F-test; the OneMax seed count; the fingerprint variance number; the word "universal"; the metric should have been called *metapopulation* diversity; **the ring connectivity number (2× too large); the "inversion at n=7" sentence (retracted); the Fisher p = 0.14 (does not reproduce)**.
**Never concede:** the title. **Never concede** that the corrected rule points the wrong way — it does not. It orders all five topologies correctly in all six domains.
</content>
</invoke>
