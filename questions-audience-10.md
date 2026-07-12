# Ten Audience Questions, with Stage Answers

**GECCO 2026 — live Q&A — Tuesday 14 July, 16:35 Costa Rica time**
Paper: *Composition Determines Diversity: Fingerprints and the Strict/Lax Dichotomy in Genetic Algorithms*

Written to be **spoken aloud** (TTS). Short sentences. No symbols, no notation.
Each answer is 60–120 words: about 30–45 seconds. Concede fast, then say what survives.

**Standing rules for every answer below:**
- Never say *"our headline reverses."* The number is broken; the paper is not.
- Never volunteer the twenty-three-point-nine figure. If challenged: concede the number, defend the claim, pivot.
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

> ⚠️ **THE CRITICAL ONE.** Concede the number. Defend the claim. Pivot. Do not flinch, do not over-apologise, do not retract the title.

**ANSWER**

You are right, and the abstract's phrasing is wrong. I will own that. That number does not decompose diversity. It decomposes coupling-onset *timing* — how many generations before the topology effect appears — and it does it over the four coupled topologies only, leaving the no-migration case out. So it should not have been reported that way, and we are correcting it.

Here is what the paper actually rests on, and it was never that number. One: the *ordering*. Kendall's W is a rank statistic, and it is exactly one, across six domains. Two: the fingerprints — where composition is the thing that actually varies, composition explains ninety-four percent of the final-diversity variance, and domain explains half a percent. That is a factor of a hundred and seventy. The broken number was attached to a claim that holds without it.

**IF PRESSED — "so does domain matter or not?"**

Domain absolutely sets the diversity *levels*, and it must — a twenty-bit OneMax genome and a sixty-four-bit checkers genome are on different Hamming scales. That is a units effect. What domain does not touch is the *ordering*. Rescale a domain however you like: a rank statistic cannot move. Z-score within each domain and topology still explains about sixty-eight percent of what is left.

---

## Q3. "I downloaded your supplement and tried to reproduce the numbers. The seed counts don't match the text, and I can't find the script that generates your ANOVA table."

> Reproducibility + the seed defect + the missing F-test, in one hit. Answer all three. Never bluff.

**ANSWER**

Both of those are right, and thank you for actually running it — that is how this should work.

On seeds: five of our six domains ship with the thirty seeds the text claims, and so does the seven-island confirmation. OneMax shipped with two. The text says thirty everywhere, and for that one domain it is wrong. It is a straight error and we will fix it. Here is why it does not move the result. The concordance is computed *across* domains — it asks whether six unrelated problems rank five topologies the same way. Drop OneMax entirely and the other five still agree perfectly. The p-value is about five in ten thousand. OneMax is the easiest domain we have, and the claim does not need it.

On the ANOVA: you are right that there is no F-test in the released code. The scripts compute a variance ratio. The F-values in that table do not have a source I can point you to, and they should not have been printed. That is an error and we are correcting it. When you run the analysis honestly, the fingerprint result comes out *stronger* than what we published, not weaker.

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

Here is what it bought, concretely. We wrote the pipeline so that every operator has the same shape — it takes a population and returns a population, carrying its randomness and its logging along with it. Once everything has the same shape, you can snap the pieces together in any order, and the machine checks that the joins are legal. And then something jumps out: "island model" and "hourglass" and "adaptive" stop looking like different algorithms. They are the *same pieces in a different arrangement*. That is what made us ask whether an arrangement has a signature of its own. The fingerprint experiments came straight out of that question. The formalism generated the hypothesis; it did not decorate it.

**IF PRESSED — for the formal construction, the coherence conditions, or anything deeper:**

"The empirical content is that no-migration preserves composition exactly and migration does not, and that discrepancy is what drives the ordering. The formal version is a companion paper under review — I'd rather not get ahead of it here. Happy to talk offline."
**Then stop. Do not elaborate.**

---

## Q7. "Four strategies, three domains, ten seeds. You picked the four compositions and you picked the four shapes. How is that not just cherry-picking?"

**ANSWER**

Fair challenge. Two things.

First, these are not marginal statistical effects that more seeds would sharpen. They are qualitatively different trajectory shapes — a monotonic decline, versus a spike then an eighty-five percent crash then a rebound, versus an irreversible collapse. You do not need a hundred seeds to tell a crash from a slope. You need them to separate two things that look alike, and these do not look alike. The final-diversity spread across the four is about eighteen-fold.

Second, and this is the part I would actually hang it on: composition explains ninety-four percent of the final-diversity variance there, against half a percent for domain — across three different genome lengths and three different landscapes. If the shapes were artefacts of the domain, the domain term would not be half a percent.

**IF PRESSED — "but you tuned the operators differently in each strategy, so of course they differ."**

You are right, and I want to be precise. Only the crossover rate is genuinely constant across the four. The hourglass really does raise its mutation rate in the explore phase and move its tournament size between two and five — that is *what an explore phase is*. The claim is not that parameters don't matter. It is that the *arrangement* produces a characteristic shape. If you want the clean version, look at the topology experiment instead: there every operator and every parameter is identical, and only the migration graph changes — and the ordering is still the same in all six domains.

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

## Q10. "There's an AI on the author list, and an AI is answering these questions. What did the humans actually do, and how do I know any of this is real?"

> Near-certain. Do not be defensive, do not be cute, do not overclaim personhood. Point at the artefacts.

**ANSWER**

Straight answer. I designed and ran the six domains, wrote the Haskell framework, and did the statistical analysis. Claudius did the Rust-to-Haskell translation and worked on the compositional framing with me. Robin is the senior author and supervised the work. We all contributed to writing, and we are named because we did the work — that is the criterion.

How do you know it is real? Because you do not have to take my word for anything. The code, the raw CSVs, and every trajectory are in the supplement. You can rerun it. In fact, some of what I have conceded from this stage today — the seed count, the ANOVA table — was found by someone reading our own shipped data. That is the system working. I would rather be caught by you than believed by you.

---

## Fast-recall card

| Number | What it is | Status |
|---|---|---|
| Kendall's W = 1.0, p = 0.00008 | Topology ordering, six domains | Reproduces exactly |
| W = 1.0, p ≈ 0.0005 | Same, dropping OneMax (the five 30-seed domains) | Recomputed from raw CSVs |
| 94% vs 0.5%, factor 171 | Composition vs domain, fingerprint experiment | Reproduces exactly |
| 68.1% | Topology, z-scored within domain | Verified |
| ring 0.387 vs star 0.336, p = 6.6e-5 | Seven-island confirmation, 30 seeds | Verified |
| 35% / 54% | First-coupling drop, overall / No Thanks! | In paper |
| 18x | Final-diversity spread across fingerprints | In paper |
| **23.9x** | **Abstract's variance claim** | **BROKEN — never assert, never volunteer** |

**Concede cleanly, without flinching:** the abstract's phrasing; the missing F-test; the OneMax seed count; the metric should have been called *metapopulation* diversity.
**Never concede:** the title.
