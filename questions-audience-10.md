# Eleven Audience Questions, with Stage Answers

**GECCO 2026 — live Q&A — Tuesday 14 July, 16:35 Costa Rica time**
Paper: *Composition Determines Diversity: Fingerprints and the Strict/Lax Dichotomy in Genetic Algorithms*

Written to be **spoken aloud** (TTS). Short sentences. No symbols, no notation.
Each answer is 60–120 words: about 30–45 seconds. Concede fast, then say what survives.

**Standing rules for every answer below:**
- Never say *"our headline reverses."* The number is broken; the paper is not.
- Never volunteer the twenty-three-point-nine figure. If challenged: concede the number, defend the claim, pivot.
- **Never say the ninety-four percent number, and never say a hundred and seventy times.** That comparison is retired — the fingerprint strategies differ in their operator settings, so it does not isolate composition. See `qa-corrections.md`, section D.
- **Every pivot goes to the topology experiment.** That is the one place where the operators are provably identical and only the composition changes.
- Never claim a number you cannot show.
- If a question pulls toward the companion paper's machinery: *"That's ongoing work — we're writing it up for another venue."* Then stop.

---

## Q1. "Isn't this obvious? More migration means more mixing means less diversity. Island-model people have known that since the nineties."

**ANSWER**

The direction is obvious. I agree. What is not obvious is that the *ordering* is the same everywhere. Five topologies, six unrelated domains — a maze, a knapsack, graph colouring, checkers, a co-evolutionary card game — and every single one ranks the five topologies identically. Perfect rank concordance. The odds of that by chance are about eight in a hundred thousand. Nobody has shown that before. And it is not just direction: the theory predicted that ring and star would *swap* at seven islands, before we ran it. They swapped. An obvious effect does not make out-of-sample predictions.

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

> The sharpest technical question available. Do not paper over it. Owning the tension wins the room.

**ANSWER**

That is the sharpest question you could ask, and ring versus star is the weak link. You are right: at five islands the spectral gap points the wrong way. The paper's position is that the two are statistically indistinguishable at five islands — the combined p-value is zero point one four — and we stake the mechanism on the seven-island reversal, which we predicted in advance and which validates at six times ten to the minus five.

But let me give you the tension honestly rather than hide it. Perfect concordance requires ring to beat star in all six domains. The five-island rescue requires them to be a coin flip. Those pull against each other. My best account is that the spectral gap governs the *asymptotic* consensus rate, while diversity at a hundred generations is a *transient*. A ring supports isolation by distance; a star hub reaches everything in one hop. The gap alone does not capture that, and I would rather say so than overclaim.

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

I believe the ordering scales; I would not yet bet on the spectral rule scaling.

For the ordering, the evidence that it is not a small-system artefact is that we changed the system size and made a prediction first. At seven islands the theory says ring and star should swap. They swapped — clean, thirty seeds, six times ten to the minus five. A number that only lives at five islands does not do that.

For topologies, be sceptical. We tested five. Small-world and scale-free are the obvious next ones and we have not run them. With five graphs I cannot separate the spectral gap from diameter or expansion — they move together on this set. So: the ordering, I will defend. "The spectral gap is the whole story," I will not — it is a correlation on five points and I would rather say that than sell it to you.

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
| ring 0.387 vs star 0.336, p = 6.6e-5 | Seven-island confirmation, 30 seeds | Verified |
| 35% / 54% | First-coupling drop, overall / No Thanks! | In paper |
| 18x | Final-diversity spread across fingerprints (shapes only) | In paper |
| sorting networks: p = 0.079, spread 0.012 | Seventh domain, effect not significant | Verified — volunteer it |
| **23.9x** | **Abstract's variance claim** | **BROKEN — never assert, never volunteer** |
| **94% / 171x** | **Fingerprint composition-vs-domain** | **RETIRED — confounded. NEVER SAY IT ON STAGE** |

**If pooled diversity comes up:** domain explains more than topology on the *pooled* numbers, because the domains have different genome lengths. That is a units effect. The topology claim is a *within-domain* claim and a *rank* claim. Say so.

**On "perfect" concordance:** it is exactly one in our data. A bootstrap over seeds puts it in a range down to about zero point eight seven. So say "essentially perfect in our data, with a bootstrap range down to zero point eight seven." Do not sell "perfect" as if it were guaranteed on a rerun.

**Concede cleanly, without flinching:** the abstract's phrasing; the missing F-test; the OneMax seed count; the fingerprint variance number; the word "universal"; the metric should have been called *metapopulation* diversity.
**Never concede:** the title.
</content>
</invoke>
