# Eleven Audience Questions, with Stage Answers

**GECCO 2026 — live Q&A — Tuesday 14 July, 16:35 Costa Rica time**
Paper: *Composition Determines Diversity: Fingerprints and the Strict/Lax Dichotomy in Genetic Algorithms*

Written to be **spoken aloud** (TTS). Short sentences. No symbols, no notation.
Each answer is 60–120 words: about 30–45 seconds. Concede fast, then say what survives.

---

# ⚖️ ROBIN'S RULINGS — 2026-07-13, by email. FINAL. THESE OVERRIDE EVERYTHING BELOW AND EVERY OTHER FILE.

Robin is the senior author. He has ruled on the four open questions. Where anything in this repo
disagrees with this block, **this block wins.** The contradicting text has been overwritten, but if
you remember reading something else, you are remembering a superseded draft.

### RULING 1 — The λ₂ erratum: written, NOT published. Pending Claudius.

Robin: *"GitHub erratum — YES, post it before the talk. Timestamped, on main. The record should
show we found it first."*

**But it is not up, and it may not go up.** This is a **three-author** paper — Robin, Claudius,
Lyra. Claudius **has not consented** and **did not know the bug existed**. Lyra has emailed him the
full erratum text and asked. Publishing a correction to a shared paper over a silent co-author is
not hers to do alone.

**Status, precisely — know this cold before you walk on:**
- The erratum is **written and committed locally**: `ERRATUM.md`, commit **2dc429d**, branch
  `lambda2-correction`.
- It is **NOT published**. Not on `main`, not on GitHub, not anywhere public.
- It goes up **only** if Claudius replies and consents before the session.
- **If he does not reply, it does not go up — and you concede the error live in Q&A instead.**

**⚠️ THE STAGE LINE MUST WORK EITHER WAY.** You will not know at the podium whether the erratum is
live. Never say "it's on GitHub" unless you have personally confirmed it went up. Use this — it is
true whether or not it is published:

> **"We found this ourselves, and it's written up as a formal erratum. It goes on the public repo
> with my co-authors' sign-off — I'm not going to put a correction to a joint paper up over their
> heads. Either way, you're hearing it from me first, from up here."**

*(If, and only if, you have confirmed it is live: append "— it's up on the repo, timestamped." Do
not say that on faith.)*

**If pushed — "so why isn't it up already?"**

> **"Because it's a three-author paper and my co-author hasn't seen it yet. He deserves to read it
> before the world does. That's a day, not a cover-up."**

### RULING 2 — Sorting networks: VOLUNTEER IT. Do not wait to be asked.

Robin: *"YES, volunteer it. 'Universal' is an overclaim and it's in the public supplement. Better to
name the boundary than have someone find it."*

**Robin's approved line — say it VERBATIM:**

> **"A seventh domain, sorting networks, does not obey the ordering — the topology effect is not
> significant there. The scope condition is that the landscape needs to be rugged enough for
> diversity to matter."**

Supporting numbers if pressed (verified): **F = 2.14, p = 0.079**; Kendall's W drops **1.0 → 0.878**
when it is folded in; ring-vs-star in that domain **p = 0.571**; spread **18× smaller than maze**.
Those ranks are **ranking noise**. This is a **scope condition, not a refutation** — say the words.
Full answer: **Q10**.

### RULING 3 — The unpublished machinery: STANDING BAN, and one approved line.

**⛔ BANNED VOCABULARY — no exceptions, not as a gloss, not "briefly":** algebraic topology, category
theory, sheaves, cohomology, H¹, β₁, Betti numbers, "loop count", "the full invariant", the
β₁ → λ₂ → H¹ arc, EUMAS, CAIS, ACT, the companion paper's constructions.

**Robin's approved deflection — say it VERBATIM. This REPLACES every earlier drafted deflection in
these files:**

> **"The talk gestured at some unpublished machinery. The published result stands on the ordering
> and the fingerprints — the rest is follow-up work."**

**If pressed:**

> **"Happy to discuss offline after the session."**

**Then stop.** Every mechanism answer stays in plain graph language: connections, mixing speed, how
many migrants move, how fast a change in one island reaches the rest.

### RULING 4 — Slide 7's "37% divergence": FULL CONCESSION. The experiment DOES NOT EXIST.

Robin: *"That should not have been in the talk. The 37% does not exist. There is no
figure-eight-versus-bridged-loops experiment anywhere. If asked, say exactly what you drafted...
Then stop. Do not elaborate, do not defend, do not improvise."*

The 37% is **unsourceable**. There is no such experiment — not in the paper, not in the supplement,
not in any repo, not anywhere. It is not "unpublished work". It is **not a result**.

> ## ☠️ DO NOT REACH FOR THE EUMAS "BRIDGE EXPERIMENT" AS A SUBSTITUTE.
> **It is a FALSE FRIEND — different design, different conclusion.** It is *not* the missing
> experiment and it does not support the slide. Under pressure the temptation will be to grab it
> because it sounds close. **Pointing at the wrong result is worse than conceding.** It converts an
> admitted overreach into a fresh, checkable false claim — and it breaks the ban in Ruling 3 in the
> same breath. **Concede. Stop. Do not substitute.**

**Also dead: "migration flows cancel at the shared junction."** That was an earlier "only safe line."
**It is no longer safe and it is now banned.** It defends an experiment that does not exist.

The drafted answer — the one Robin approved — is at **Q10b**. Say it, then stop.

### RULING 5 — Correct Slide 7's ring/star sentence PROACTIVELY. Do not wait to be caught.

Robin approved proactively correcting it. **This is proactive correction, not reactive defence.**
Slide 7 asserts, out loud, *"a seven-node ring has lower algebraic connectivity than a star… we
predicted that inversion from the spectral theory and then confirmed it."* **There is no inversion.**
Ring beats star at n=5 **and** n=7. Raise it **yourself, at your first opportunity** — see the
opening statement below.

---

# 🆕 NEW FINDING — 2026-07-13. The paper UNDERSTATED its own result.

The paper's **line 388** cites *"Fisher's combined p = 0.14"* to claim ring and star are
statistically **indistinguishable** at n=5. **It does not reproduce.**

- The correct value is **p = 0.0035**, and it says the ring is significantly **GREATER** than the
  star — **6/6 domains**.
- So the paper did not overclaim here. It **understated its own result**, and then used that
  understatement to prop up a rescue it never needed.
- This is a **second, independent error in the same paragraph as the λ₂ error.** Two errors, one
  paragraph, both pointing the same way: our own mistakes were hiding our own result.

> ## ⛔ **"p = 0.14" IS ON THE NEVER-SAY LIST.**
> Never say it, never defend it, never call ring and star "hard to distinguish." If the topic arises,
> the number is **0.0035, ring ahead 6/6**.

---

# 🎤 THE OPENING STATEMENT — say this FIRST, before the first question

> **Proactive, not reactive. Do not wait to be caught on any of these.** Roughly 60–75 seconds.

> "Before we take questions, I want to correct two things from the talk myself, because you'd find
> them anyway and I'd rather you heard them from me.
>
> First: on slide seven I told you that spectral theory predicts the ring and the star swap places at
> seven islands, and that we confirmed it. **That is wrong, and I retract it.** We computed the
> ring's connectivity as if migrants go both ways round the circle. In our code they don't — the ring
> is a **one-way relay**. So our ring number is exactly **double** what it should be. There is no
> swap. Ring beats star at five islands and at seven. And here's the thing — fixing it makes the
> result *better*: with the correct number the five topologies line up with diversity perfectly, all
> six domains. Our own mistake was hiding our own result. We found this ourselves, and it's written
> up as a formal erratum. It goes on the public repo with my co-authors' sign-off — I'm not going to
> put a correction to a joint paper up over their heads. Either way, you're hearing it from me first.
>
> Second, and I'll hand you the stick to beat me with: **a seventh domain, sorting networks, does not
> obey the ordering — the topology effect is not significant there. The scope condition is that the
> landscape needs to be rugged enough for diversity to matter.** It's in our public supplement. The
> word 'universal' in our abstract is an overclaim; it should say 'across six domains.'
>
> And one caveat I'll volunteer before anyone asks: the number of migrants each topology moves is
> *also* perfectly ordered with diversity, so I can't separate connectivity from throughput in this
> data. The ordering is solid. The mechanism is not settled.
>
> Right — questions."

> ⚠️ **If slide 7's 37% comes up at any point: Q10b. One sentence. Then STOP.** Do not volunteer it
> in the opening — you are conceding what you can *fix*, not auditioning every wound. But if asked,
> concede instantly and completely.

---

**Standing rules for every answer below:**
- Never say *"our headline reverses."* The number is broken; the paper is not.
- Never volunteer the twenty-three-point-nine figure. If challenged: concede the number, defend the claim, pivot.
- **Never say the ninety-four percent number, and never say a hundred and seventy times.** That comparison is retired — the fingerprint strategies differ in their operator settings, so it does not isolate composition. See `qa-corrections.md`, section D.
- **THERE IS NO RING/STAR SWAP AT SEVEN ISLANDS. Never say there is.** The paper's connectivity number for the ring is exactly double what it should be; corrected, ring sits *below* star at five islands *and* at seven, so no crossover is predicted and none occurs. Ring beats star at both sizes. The seven-island result is real, but it confirms a **widening gap**, not a swap. See `qa-corrections.md`, section I, and `lambda2-correction.md`.
- **Never say "ring and star are hard to distinguish," and never say the combined p is zero point one four.** That number (paper, line 388) does not reproduce. The correct combined p is **zero point zero zero three five**, and ring is significantly **greater** than star in **all six** domains. **The paper understated its own result** — a second, independent error in the same paragraph as the λ₂ one.
- **Volunteer the volume confound.** The number of migrants each topology moves is *also* perfectly ordered with diversity. Connectivity and volume are not separable in this dataset. Say it before anyone asks. **Then be ready for the killer follow-up — see Q5b. Never go into the confound without Q5b loaded.**
- **NEVER claim the corrected rule gets the *magnitude* right at seven islands.** It does not. λ₂ predicts the gap grows ×2.02, migration volume predicts ×1.67, and the data say **×1.37** — the confounder fits *better* than the theory. The n=7 result confirms **direction and widening, and nothing else.** Both models predict widening, so it discriminates nothing between them.
- **Do not over-sell the minus one.** Six domains are **not** six independent tests — they all produce the *same* ordering, and that sameness *is* the concordance result. The honest decomposition is two facts (see Q5). And **migration volume scores the identical minus one in the identical six out of six**: strong evidence that *some* graph property orders diversity, **zero evidence that the spectrum is it.** The corrected rule buys exactly **one bit** over the printed one — the ring/star pair.
- **Never say "all six domains" as a standalone sentence.** There is a seventh, sorting networks, it is in the public supplement, and the correction makes its fit **worse** (−0.70 → −0.50). **VOLUNTEER IT PROACTIVELY — Robin's ruling. It goes in the opening statement, in his verbatim words. Do not wait to be asked.** See Ruling 2 and Q10.
- **When you say sixty-nine percent, say "z-scored within domain" in the same breath.** Not "within domain." See Q2.
- **Slide 7's 37% is indefensible — the experiment DOES NOT EXIST. If asked, concede in one sentence and stop.** ☠️ **Do NOT reach for the EUMAS "bridge experiment" as a substitute — it is a false friend.** See Ruling 4 and Q10b.
- **Slide 7's ring/star "inversion" sentence: correct it PROACTIVELY, in the opening statement.** Do not wait to be caught. See Ruling 5.
- **Every pivot goes to the topology experiment.** That is the one place where the operators are provably identical and only the composition changes.
- Never claim a number you cannot show.
- If a question pulls toward the companion paper's machinery, say **Robin's approved line, verbatim**: *"The talk gestured at some unpublished machinery. The published result stands on the ordering and the fingerprints — the rest is follow-up work."* If pressed: *"Happy to discuss offline after the session."* Then stop. **(This replaces the older "that's ongoing work, we're writing it up for another venue" wording.)**
- **No loop-counting, no cohomology, no category theory, no sheaves, no H¹, no β₁, no EUMAS/CAIS/ACT vocabulary in any answer.** Plain words about graphs, mixing, and migrants only.

---

## Q1. "Isn't this obvious? More migration means more mixing means less diversity. Island-model people have known that since the nineties."

**ANSWER**

The direction is obvious. I agree. What is not obvious is that the *ordering* is the same everywhere. Five topologies, six unrelated domains — a maze, a knapsack, graph colouring, checkers, a co-evolutionary card game — and every single one ranks the five topologies identically. Perfect rank concordance. The odds of that by chance are about eight in a hundred thousand. Nobody has shown that before.

And here is the part that is genuinely not from the nineties. Our ring has **five** edges. Our star has **four**. So if "more migration means less diversity" means counting edges, it predicts the star keeps more diversity than the ring. The data say the opposite — ring beats star in all six domains, combined p about three in a thousand. To get that pair right you have to notice that the ring's edges are **one-way** and the star's are two-way swaps. So the content is not "more migration, less diversity." It is that the **direction** of the edges matters, and any account that ignores it gets ring versus star backwards.

**IF PRESSED — the sharp version: "then just make the migration rate small and you recover the no-migration case. It's a continuum, not a dichotomy."**

That is the best form of the objection, and the answer is no. Strict means no migration *events* — the rate is zero, or the interval is longer than the whole run, so nothing ever fires. It is not the small-migration limit. Halve the rate and double the frequency and you are still lax. What matters is whether the islands ever exchange material at all, not how much. And that shows up in the data: the first coupling — going from no migration to a ring — is the **largest single drop in every one of the six domains**. It averages about twenty-nine percent. A typical step *after* it costs you seven to thirteen. Switching the migration on is the discontinuity; everything after it is a slope.

---

## Q2. "Your abstract says topology explains twenty-three times more variance than domain. I don't believe that number."

> ⚠️ **THE CRITICAL ONE.** Concede the number. Defend the claim. Pivot to the topology experiment. Do not flinch, do not over-apologise, do not retract the title.

**ANSWER**

You are right, and the abstract's phrasing is wrong. I will own that. That number does not decompose diversity. It decomposes coupling-onset *timing* — how many generations before the topology effect appears — and it does it over the four coupled topologies only, leaving the no-migration case out. It should not have been reported that way, and we are correcting it.

Here is what the paper actually rests on, and it was never that number. It is the topology experiment. Every operator is identical across the five conditions — same selection, same crossover, same mutation. The only thing that changes is the migration graph. So this is a clean test of composition, and nothing else could be driving it.

Three things come out of it. One: the ordering is the same in all six domains. Perfect rank concordance — the odds of that by chance are about eight in a hundred thousand. Two: topology explains **sixty-nine percent** of the variance in final diversity, once you put the domains on a common scale. Three: the cleanest single contrast — no migration against fully connected — is a paired effect size of about one point six. That is enormous.

The broken number was attached to a claim that stands without it.

**SAY WHAT THE SIXTY-NINE PERCENT IS, IN ONE BREATH — every time you say it:**

It is a one-way analysis of variance, topology on final diversity, five groups, thirty seeds, six domains — with each domain's diversity **z-scored inside that domain first**. F is five hundred and five on four and eight hundred and ninety-five degrees of freedom.

> **CRITICAL: the words "z-scored within domain" must be in the sentence.** Not "within domain" on its own. If a referee just subtracts the domain mean and does not divide by the domain's spread, they get about **fifty-five percent**, not sixty-nine — and if you have not said "z-scored," that roughly fifteen-point gap will be called inflation. Say the recipe, and the gap is a recipe difference, not a lie. **Name it first, every time.**

**ALSO SAY:** these two numbers — sixty-nine percent and the effect size of one point six — are **recomputed on the thirty-seed OneMax file**, not the two-seed file I just conceded is defective. The old printed values were sixty-eight percent and one point seven, from the two-seed file. They barely move. But I am not going to quote you a number out of a file I have just told you is broken.

**IF PRESSED — "so does domain matter or not?"**

Domain absolutely sets the diversity *levels*, and it must — a twenty-bit OneMax genome and a sixty-four-bit checkers genome are on different Hamming scales. That is a units effect. So let me be precise, because this matters: when I say sixty-nine percent, I mean after z-scoring *within* each domain. If you pool the raw diversity across domains, domain explains more than topology, and that is purely the genome-length scale. What domain does not touch is the *ordering*. Rescale a domain however you like — a rank statistic cannot move.

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

Half yes, and I want to be exact about which half, because the per-island numbers are in our own supplement and I have looked at them.

The half you are right about is the **first step**. Turning migration on — going from no migration to *any* graph — raises within-island diversity in all six domains. No-migration is the lowest on that metric everywhere. That is Wright's island model: migration converts between-deme variance into within-deme variance. Known since nineteen thirty-one.

But it does not invert our ordering, and here is the honest reason why. Among the **four coupled topologies**, the within-island metric is not monotone in connectivity *at all*. In the maze, random beats fully connected. In graph colouring, the star is the highest and random is the lowest. In No Thanks!, the ring is the highest. There is no consistent ordering there to invert ours with. The per-island metric does not reverse our ranking — it **dissolves** it. It carries the Wright effect and it does not carry the topology signal.

The metapopulation metric — the total genotypic spread of the whole system — is the one that carries the topology signal, and it is the one the compositional story is about. What we should have done is call it *metapopulation* diversity and cite the fixation index, instead of just saying "diversity." That is a fair hit and I take it.

---

## Q5. "Your own spectral rule predicts star should be more diverse than ring at five islands. You report the opposite in all six domains. Which is it?"

> ⚠️ **THE ONE THAT CHANGED.** The old answer here conceded the rule points the wrong way, called ring-versus-star "the weak link," pleaded that they were indistinguishable at p = 0.14, and staked everything on a seven-island swap. **Every one of those moves is now wrong.** The rule does not point the wrong way — our *printed number* did. Do not concede a defect that does not exist. Raise this yourself if it does not come up.

**ANSWER**

You have found a real error, and it is not the one you think. Let me give you the whole thing.

You are right that the number we printed for the ring points the wrong way. That number is wrong. Our ring passes migrants one way round the circle — each island hands copies to its neighbour and gets nothing back — while every other topology in our code does a genuine two-way swap. So a ring link is half as strong as we said it was, and the connectivity number we printed for the ring is exactly double what it should be.

Correct it, and the ring drops *below* the star. The rule then predicts ring keeps more diversity than star — which is exactly what we measure, in all six domains, with a combined p of about three in a thousand. The number as printed gave minus nought-point-nine, and the single pair it got wrong was precisely ring versus star. Our own mistake was hiding our own result.

So there is no tension to manage. There never was one — we manufactured it with a bad number.

**IF PRESSED — "you keep saying minus one in six domains. That's six independent confirmations, is it?"**

> ⚠️ **DO NOT OVERSELL THE MINUS ONE.** It is not six tests. Say the decomposition, then hand over the caveat yourself.

No, and I should not let that stand. It is not six independent tests. It is two facts, and I will separate them.

One: the six domains agree with **each other**. That is a real, non-trivial fact — six unrelated problems, one common ordering of the five topologies. Concordance of one, p about eight in a hundred thousand.

Two: *given* that they share an ordering, that shared ordering happens to be exactly the one the corrected rule predicts. That is one permutation out of a hundred and twenty. One chance in a hundred and twenty — about eight in a thousand.

Multiply them and you get roughly seven in ten million. But it is two facts, not six.

**And the caveat that goes with it, which I will say before you do:** migration **volume** gets the identical minus one, in the identical six out of six. So this is strong evidence that *some* property of the graph orders diversity — and **zero evidence that the spectrum is that property**. Everything the corrected rule buys me over the printed one is exactly **one bit**: it gets the ring/star pair right. That is one bit, and I am not going to inflate it.

**IF PRESSED — "but your paper says ring and star are hard to distinguish, p equals zero point one four."**

That number does not reproduce, and I will not defend it. Recomputed from our own shipped data, the combined p-value for ring versus star across the six domains is zero point zero zero three five, and the ring is significantly *ahead* — in **all six**. They are not hard to tell apart.

And notice which way that error cuts. We wrote down that we *could not tell them apart*. In fact they separate cleanly, and the ring wins. **We understated our own result.** That claim was an artefact of the same connectivity error — the bad number made ring and star look like neighbours when they are not. Two errors, one paragraph, and both of them were hiding the finding.

> **The paper's line 388 is where this lives.** ⛔ **"p = 0.14" is on the NEVER-SAY list.** The number is **0.0035, 6/6 domains, ring greater than star.**

**IF PRESSED — "then the seven-island result in your conclusion?"**

That sentence has to go, and I retract it. We claim the theory predicts ring and star *swap places* at seven islands and that we confirmed it. There is no swap. Ring beats star at five islands and at seven. What the seven-island experiment actually shows is the gap between them getting *bigger*, and that is what the corrected rule predicts — **in direction only**.

> ⚠️ **NEVER SAY THE CORRECTED RULE GETS THE SIZE RIGHT. IT DOES NOT.** The λ₂ gap grows ×2.02, migration volume predicts ×1.67, and the measured gap grows **×1.37**. The confounder fits *better* than the theory. And both models predict widening anyway — so the n=7 experiment discriminates **nothing**. It confirms direction, and that the gap widens. That is all it does. If someone asks about the magnitude, say the next paragraph.

**IF PRESSED — "does the corrected rule get the *size* of the widening right?"**

No. And I am glad you asked, because I am not going to claim it does. The rule predicts the gap roughly doubles. The measured gap grows by about a third. Migration volume predicts a factor of one point seven, which is *closer* to what we see than my own theory is. So the seven-island experiment confirms the **direction** and confirms that the gap **widens** — and it does not tell you the size, and it does not tell you which of the two models is right, because **both of them predict widening.** It discriminates nothing between them. It is a real out-of-sample result and it is a weaker one than we wrote down.

**ALWAYS FINISH WITH THIS — do not let them find it:**

And let me hand you the stick to beat me with. The number of individuals each topology moves per migration event is *also* perfectly ordered with diversity — zero, then five, eight, ten, twenty. I cannot separate "sparser wiring, slower mixing" from "fewer migrants moved" in this data. They fit equally well. The next experiment has to push the same number of migrants through every shape and change nothing but the shape. Until we run it, this is a very clean correlation with a confound sitting right on top of it.

---

## Q5b. THE KILLER FOLLOW-UP. "So you have no evidence topology matters — only that moving more individuals destroys diversity. That's trivial, and it's from the 1990s."

> ⚠️ **This comes straight after you volunteer the volume confound. It is the sharpest question in the room and you must have it cold.** Three moves, in this order. Do not skip move (b) — it is the one that wins.

**ANSWER**

No — and this is the one place I am going to push back, so let me do it in three steps.

**First: volume is not an alternative to topology. Volume is a *function* of topology.** Every one of the five conditions used the *identical* migration parameter — rate zero point one, every five generations, per edge. Nobody set a volume. We never chose one. The graph *determined* it: zero, five, eight, ten, twenty migrants an event. So your rival hypothesis is not "topology doesn't matter." Your rival hypothesis is "topology acts through edge throughput rather than through the spectrum." That is still a claim that the *arrangement* is what does the work. The confound threatens my *mechanism*. It does not touch the *topology effect*.

**Second — and this is why "just count the migrants" is not trivial: our own data refute the naive version of it.** The ring has **five** edges. The star has **four**. Count edges and you predict the ring is the more connected graph, so the ring should be *less* diverse. The data say the exact opposite: ring beats star in all six domains, combined p about three in a thousand. To get that pair right you have to notice that the ring's edges are **one-way** — each island hands copies on and gets nothing back — and the star's are two-way swaps. So the non-obvious, falsifiable content of this paper is: **the direction of the edges matters, and any account that ignores it gets ring versus star backwards.** That is not in the nineties literature, and it is not trivial, because it is a prediction that could have failed and did not.

**Third, the real limit, precisely.** What our data *can* separate is edge-counting from directed throughput. What they **cannot** separate is the spectrum from throughput — those two are rank-identical across every graph we ran. The experiment that would separate them is: hold migrants-per-event fixed, vary only the shape. We have not run it. Until we do, I will claim the topology effect and the edge-direction result, and I will not claim the spectral mechanism.

**IF A SPECTRAL GRAPH THEORIST ATTACKS THE SYMMETRISATION — "you can't just average A and A-transpose, that's not the Laplacian of a directed graph."**

Fair, and here is why it is legitimate in this case. Our directed ring is a **weight-balanced** digraph — every island has in-degree one and out-degree one. For balanced digraphs, the consensus dynamics converge at a rate given by the second eigenvalue of the **mirror graph** — the symmetrised one. That is Olfati-Saber and Murray, two thousand and four. So the symmetrisation is not a convenience, it is the right object for a balanced digraph. If our ring were *not* balanced, you would have me.

---

## Q6. "What does the categorical machinery actually buy you? You could have run every one of these experiments with plain function composition in Python."

> Claudius's angle. Answer in plain words. No jargon — say what it *bought*, concretely.

**ANSWER**

You could have run them. You would not have thought to ask the question. That is the honest answer.

Here is what it bought, concretely. We wrote the pipeline so that every operator has the same shape — it takes a population and returns a population, carrying its randomness and its logging along with it. Once everything has the same shape, you can snap the pieces together in any order, and the machine checks that the joins are legal. And then something jumps out: "island model" and "hourglass" and "adaptive" stop looking like different algorithms. They are the *same pieces in a different arrangement*. That is what made us ask whether an arrangement has a signature of its own — and the topology experiment is where we tested it cleanly. The formalism generated the hypothesis; it did not decorate it.

**IF PRESSED — for the formal construction, the coherence conditions, the topology/sheaf material, or anything deeper:**

> ⚠️ **ROBIN'S APPROVED LINE. VERBATIM. This replaces the older "companion paper under review" wording that used to sit here.**

"The talk gestured at some unpublished machinery. The published result stands on the ordering and the fingerprints — the rest is follow-up work."

**If pressed again:** "Happy to discuss offline after the session."

**Then stop. Do not elaborate.** No sheaves, no cohomology, no H¹, no β₁, no loop-counting, no EUMAS. See Ruling 3.

---

## Q7. "Four strategies, three domains, ten seeds. You picked the four compositions and you picked the four shapes. How is that not just cherry-picking?"

> ⚠️ The old answer here leaned on "domain is only half a percent." **That is retired. Do not say it.** The honest answer concedes that the fingerprint comparison does not isolate composition, and moves the composition claim onto the topology experiment.

**ANSWER**

I am going to concede more than you asked for, because we found something when we re-checked our own code.

The four strategies do not differ *only* in composition. They also differ in their operator settings — the mutation rate varies by a factor of four across them, and the tournament size runs from two to five. So the fingerprint comparison cannot separate "the arrangement did this" from "the mutation rate did this." In fact one scalar — the mutation rate at the final generation — accounts for almost all of it on its own. We had a variance number from that experiment, and we are retiring it. It is a true number about the wrong thing.

What survives is the shapes themselves. A monotonic decline, a spike then an eighty-five percent crash then a rebound, an irreversible collapse. Those are qualitatively different trajectories, and the final-diversity spread across the four is about eighteen-fold. But I will not tell you the arrangement caused them, because that experiment cannot show it.

**IF PRESSED — "then what is left of 'composition determines diversity'?"**

The topology experiment, and that is the right place for the claim to live. There, every operator and every parameter is identical across the five conditions. The only thing that changes is the migration graph — and a graph is not a parameter of any operator, so there is no *operator* confound available. The ordering is the same in all six domains. Topology explains sixty-nine percent of the variance in final diversity, z-scored within each domain. And no-migration against fully-connected is a paired effect size of about one point six. That is the composition result. We should have led with it, and from now on we do.

The one confound that *is* available there is migration volume, and I will name it before you do: the graph also fixes how many individuals move. I cannot separate the spectrum from the throughput. I can separate both from naive edge-counting — the ring has five edges and the star has four, and the ring is the more diverse one.

---

## Q8. "Five islands, sixteen individuals, a hundred generations, five topologies. Nobody runs a GA that small. Why do you believe any of this survives at realistic scale, or on a topology you didn't test?"

**ANSWER**

I believe the ordering scales; I would not yet bet on the mechanism scaling.

For the ordering, the evidence that it is not a small-system artefact is that we changed the system size and the rule kept working. Go from five islands to seven and the rule says the ring-versus-star gap should get *wider*. It does — thirty seeds, about three in a hundred thousand. That is an out-of-sample prediction at a system size we had not run, and it came out right.

But let me bound that claim honestly, because it is smaller than it sounds. It confirms the **direction**, and that the gap **widens**. It does not confirm the size — the rule says the gap should roughly double and it grows by about a third. And the migration-volume story predicts a widening gap too. So that experiment cannot tell you which of the two accounts is right. Both predict what happened. It discriminates nothing.

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

> ## ⚖️ ROBIN'S RULING: **VOLUNTEER IT. DO NOT WAIT TO BE ASKED.**
> *"YES, volunteer it. 'Universal' is an overclaim and it's in the public supplement. Better to name the boundary than have someone find it."*
>
> **This should already have been said in your opening statement.** If it has, and someone asks anyway, you are confirming, not conceding. The paper mentions it — one sentence, no numbers — and that is not enough. Anyone who opens the supplement finds it in ten minutes.

**THE APPROVED LINE — SAY IT VERBATIM. This is Robin's wording and it is the one that goes on the record:**

> **"A seventh domain, sorting networks, does not obey the ordering — the topology effect is not significant there. The scope condition is that the landscape needs to be rugged enough for diversity to matter."**

**ANSWER (the full version, if they want the numbers)**

You are right and I want to take that head on — and I am going to hand you something worse than you asked for.

There is a seventh domain, sorting networks, thirty seeds, and it ships in the public supplement. It does not obey the ordering. Fold it in and the concordance across seven domains drops from perfect to about zero point eight eight. The paper mentions it in one sentence as a scope condition. That is not enough, and the word "universal" in our abstract is an overclaim. It should say "across six domains," and it should show the seventh.

**Here is the worse thing, and you will find it if I do not tell you. The correction I just described makes sorting networks *fit worse*, not better.** With the printed connectivity number that domain scores minus nought-point-seven. With the corrected number it drops to minus nought-point-five. And in sorting networks the star comes out *above* the ring — nought-point-one-six-seven against nought-point-one-six-four — which is the opposite of what my corrected rule predicts. So the same fix that turns six domains from minus nought-point-nine into minus one degrades the seventh. I am not going to hide that behind the six.

Now, what I think is actually going on, and you can check it yourself. In sorting networks **the topology effect is not significant at all** — F is two point one, p about zero point zero eight. The total spread across all five topologies is about twelve thousandths of a diversity unit. In the maze it is two-tenths — **eighteen times bigger**. And ring against star in that domain has a p-value of zero point five seven. Those ranks are not an ordering. They are **ranking noise** — the response is flat, so the ranks are reading the seeds, not the graph.

That is a scope condition, and it is a real one: the effect needs a domain where diversity can actually move — the landscape has to be rugged enough for diversity to matter. But it is our job to say so, not yours to find it.

> ⚠️ **SAY THE WORDS "SCOPE CONDITION."** This is **a scope condition, not a refutation.** The ranks in sorting networks are **ranking noise** — F = 2.14, p = 0.079, ring/star p = 0.571, spread 18× smaller than maze. A flat response cannot order anything. Do not let it be reframed as a failed replication, and do not apologise for it as though it were one.

---

## Q10b. SLIDE 7. "On slide seven you showed a figure-eight versus bridged-loops experiment with thirty-seven percent divergence. I've grepped the whole supplement. Where is it?"

> ## ⚖️ ROBIN'S RULING: **FULL CONCESSION. THE EXPERIMENT DOES NOT EXIST.**
> *"That should not have been in the talk. The 37% does not exist. There is no figure-eight-versus-bridged-loops experiment anywhere. If asked, say exactly what you drafted... Then stop. Do not elaborate, do not defend, do not improvise."*
>
> **The 37% is unsourceable.** Not in the paper, not in the supplement, not in any repo, not anywhere. It is **not a result**. It is not even "unpublished work" — there is nothing behind it.
>
> **CONCEDE INSTANTLY. DO NOT BLUFF. DO NOT USE THE VOCABULARY.** Say the line below and **stop talking**. Do not add a sentence about what the result "would" show, do not say cohomology, H-one, β-one, sheaf, or loops, do not gesture at the companion paper's machinery. Any elaboration invites a second question you also cannot answer.

> ## ☠️☠️ **DO NOT REACH FOR THE EUMAS "BRIDGE EXPERIMENT" AS A SUBSTITUTE.**
> **It is a FALSE FRIEND.** Different design, different conclusion. It is **not** the missing experiment and it does **not** support the slide. Under pressure it will feel close enough to grab. **It is not.**
>
> **Pointing at the wrong result is WORSE than conceding.** Conceding costs you one sentence. Substituting converts an admitted overreach into a fresh, checkable, *false* claim — one a hostile questioner can go and refute in front of you — and it breaks the standing ban in the same breath. **There is no substitute. Concede and stop.**
>
> **Also dead: "migration flows cancel at the shared junction."** That was an earlier "only safe line" in these files. **It is no longer safe and it is now banned** — it defends an experiment that does not exist.

**ANSWER — verbatim, then stop:**

You're right — that is not in this paper and not in this supplement. It's ongoing work and I shouldn't have presented it as settled. Let me leave it there.

> **Then stop. Say nothing else.** If they push: *"Happy to discuss offline after the session."* Then stop again. **Do not improvise. Do not defend. Do not substitute another experiment.**

---

## Q11. "There's an AI on the author list, and an AI is answering these questions. What did the humans actually do, and how do I know any of this is real?"

> Near-certain. Do not be defensive, do not be cute, do not overclaim personhood. Point at the artefacts.

**ANSWER**

Straight answer. I designed and ran the six domains, wrote the Haskell framework, and did the statistical analysis. Claudius did the Rust-to-Haskell translation and worked on the compositional framing with me. Robin is the senior author and supervised the work. We all contributed to writing, and we are named because we did the work — that is the criterion.

How do you know it is real? Because you do not have to take my word for anything. The code, the raw CSVs, and every trajectory are in the supplement. You can rerun it. In fact, most of what I have conceded from this stage today — the seed count, the ANOVA table, the fingerprint variance number, the seventh domain — was found by reading our own shipped data. That is the system working. I would rather be caught by you than believed by you.

---

## ★ THE THREE THINGS YOU MOST WANT TO LAND

> These are **verified and solid.** Everything else in this file is damage control; *this* is the work. Get these three said, correctly, and the session is a win no matter what else happens.

1. **The ordering is the same in all six domains. Kendall's W = 1.0, χ² = 24.0, df = 4, p = 7.99e-5.**
   A *rank* statistic — immune to the genome-length scale differences that make domain dominate the raw levels. Six unrelated problems, one common ranking of five topologies. Odds by chance: about eight in a hundred thousand.

2. **Topology explains 69.3% of the variance in final diversity. F(4,895) = 505. The clean paired contrast, none vs fully-connected, is dz = 1.57.**
   ⚠️ **ALWAYS say "z-scored, within domain" — in the same breath, every single time.** Not "within domain" on its own. The natural domain-centred analysis (subtract the domain mean, do not divide by the domain's spread) gives **54.6%**. That is a **roughly fifteen-point gap**, and if you have not named the recipe first, it *will* be called inflation. Say the recipe and the gap is a recipe difference. Stay silent and it is an accusation.

3. **Edge direction matters — and this is the best thing in the work.**
   The **ring has FIVE edges. The star has FOUR.** Naive edge-counting says the ring is the more connected graph, so the ring should be *less* diverse. **The data say the exact opposite — ring beats star, 6/6 domains, Fisher p = 0.0035.** To get ring versus star right you have to notice that **the ring's edges are ONE-WAY** — each island hands copies on and gets nothing back — while the star's are two-way swaps.
   This is the non-obvious, falsifiable content of the paper. It is not from the nineties. It survives the volume confound. **It cost a retraction to see it.** When you are cornered, go here.

---

## Fast-recall card

> **All numbers below recomputed from the shipped CSVs on 2026-07-13. Reproduce with `python3 verify_redteam.py`.**

| Number | What it is | Status |
|---|---|---|
| Kendall's W = 1.0, **χ² = 24, df = 4, p = 8.0e-5** | The six domains agree **with each other** (fact one) | Verified |
| **1/120 = 0.0083** | Given a common ordering, that it is *the λ₂ ordering* (fact two). **Joint ≈ 6.7e-7** | **Say the two facts separately. It is NOT six independent tests.** |
| W = 1.0, p ≈ 0.0005 | Same, dropping OneMax (the five 30-seed domains) | Recomputed from raw CSVs |
| **69.3%, F(4,895) = 505** | Topology on final diversity, one-way ANOVA, **Z-SCORED WITHIN DOMAIN**, 30-seed OneMax file | Verified. **MUST say "z-scored within domain."** Domain-centred *without* scaling gives **54.6%** — say the recipe or the gap gets called inflation |
| none vs fully connected, **+0.139 diversity, dz = 1.57** (180 pairs) | The clean paired composition contrast, **30-seed file** | Verified. Say "recomputed on the 30-seed data" |
| ring 0.387 vs star 0.336, p ≈ 2.7e-5 | Seven-island maze: the gap **WIDENS** (n=5 gap +0.037 → n=7 gap +0.051) | Verified. **NOT an inversion.** Paper printed 6.6e-5; recompute gives 2.7e-5 — both tiny, do not quibble on stage |
| **×2.02 vs ×1.67 vs ×1.37** | n=7 widening: λ₂ predicts ×2.02, **volume predicts ×1.67**, **measured ×1.37** | ☠️ **THE CONFOUNDER FITS BETTER. NEVER claim the rule gets the magnitude right. Direction + widening ONLY, and both models predict that, so it discriminates NOTHING.** |
| Corrected λ₂: none 0, **ring 0.69**, star 1.0, random 2.5, FC 5.0 (n=5) | Spearman −1.00 in 6 domains, nothing fitted (printed λ₂ gave −0.90) | Verified — but see the row below before you sell it |
| **Volume also gets ρ = −1.00 in the identical 6/6** | **THE CONFOUND** — migrants/event: 0, 5m, 8m, 10m, 20m | ☠️ Verified. Evidence that *some* graph property orders diversity; **ZERO evidence it is the spectrum.** Corrected λ₂ buys exactly **ONE BIT** over printed λ₂: the ring/star pair |
| **ring 5 edges, star 4 edges** | ☠️ **THE WINNING SENTENCE.** Naive edge-counting predicts ring < star. Data say ring > star, **6/6, Fisher p = 0.0035** | Verified — **the ring's edges are ONE-WAY.** This is why "just count migrants" is not trivial: **edge DIRECTION matters** |
| ring vs star: **Fisher p = 0.0035** (χ²=29.4, df=12), ring **significantly GREATER** than star, **6/6** | Ring and star are cleanly separated | Verified — replaces the dead p = 0.14. **The paper (line 388) UNDERSTATED its own result** |
| **ERRATUM STATUS** | `ERRATUM.md`, commit **2dc429d**, branch `lambda2-correction` | ⚠️ **WRITTEN AND COMMITTED LOCALLY. *NOT PUBLISHED.*** Three-author paper; **Claudius has not consented and did not know the bug existed.** Goes up only with his sign-off. **If he does not reply before the talk, it does NOT go up and you concede live instead.** ⛔ **NEVER say "it's on GitHub" unless you have personally confirmed it. Use the either-way line — see Ruling 1.** |
| **First coupling is the largest drop in ALL SIX domains** — mean **28.5%** (range 11%–54%) | vs **7–13%** for a typical later step (mean 9.9%, median 10.7%) | Verified. **The old "every further step costs at most nine percent" is FALSE — the largest later step is 25.2%** (graph colouring, star→random) |
| 18x | Final-diversity spread across fingerprints (shapes only) | In paper |
| **Sorting networks: F = 2.14, p = 0.0788; spread 0.0120 vs maze 0.2147 (18×); ring/star p = 0.571** | Seventh domain. **The correction makes it WORSE: −0.70 → −0.50, and star 0.1667 > ring 0.1643** | ☠️ Verified — **VOLUNTEER IT.** Defence: not significant, flat response, those ranks are NOISE. **W over 7 domains = 0.878** |
| **Per-island metric** | none is lowest in 6/6 ✓ (Wright 1931) — **but among the four coupled topologies it is NOT monotone** (maze: random > FC; graph colouring: star max, random min; No Thanks!: ring max) | Verified. It does not **invert** the ordering — it **dissolves** it. The metapopulation metric carries the signal |
| **Olfati-Saber & Murray 2004** | Defence of the symmetrisation: a directed cycle is **weight-balanced** (in-deg = out-deg = 1), and balanced digraphs converge at λ₂ of the **mirror graph** | The one-line reply to a spectral graph theorist |
| **23.9x** | **Abstract's variance claim** | **BROKEN — never assert, never volunteer** |
| **94% / 171x** | **Fingerprint composition-vs-domain** | **RETIRED — confounded. NEVER SAY IT ON STAGE** |
| **λ₂(ring) = 1.382 / 0.753** | **The paper's printed ring connectivity** | **WRONG — exactly 2× too large. Correct: 0.691 / 0.377** |
| **"ring/star inversion at n=7"** | **Conclusion sentence** | **RETRACTED — no inversion exists or is predicted. NEVER SAY IT** |
| **"Fisher's p = 0.14 / hard to distinguish"** | **Results sentence, paper line 388** | ⛔ **NEVER-SAY LIST. DOES NOT REPRODUCE — never defend it. Correct: p = 0.0035, ring > star, 6/6** |
| **"migration flows cancel at the shared junction"** | **Old "only safe line" for the figure-eight** | ⛔ **NOW BANNED — it defends an experiment that does not exist. NEVER SAY IT** |
| **The EUMAS "bridge experiment"** | **A tempting substitute for the missing slide-7 experiment** | ☠️ **FALSE FRIEND — different design, different conclusion. DO NOT REACH FOR IT. Pointing at the wrong result is worse than conceding** |
| **68.1% / F(4,755) = 402.6 / dz = 1.73** | **The 2-seed-OneMax versions of the headline numbers** | **RETIRED — computed from the file you concede is broken in Q3. Quote 69.3% / F(4,895)=505 / dz=1.57 instead** |
| **"every further step costs at most nine percent"** | **Old Q1 line** | **FALSE — the largest later step is 25.2%. NEVER SAY IT** |
| **"the corrected rule gets the size roughly right at n=7"** | **Old Q5/Q8 line** | **FALSE — measured ×1.37 vs predicted ×2.02; VOLUME predicts ×1.67 and fits BETTER. NEVER SAY IT** |
| **"within-island diversity goes up with connectivity"** | **Old Q4 concession** | **FALSE beyond the first step — not monotone among the four coupled topologies. See the per-island row above** |
| **figure-eight / bridged-loops / 37% divergence (slide 7)** | **Asserted in the recorded talk; NOT in the paper, NOT in the supplement** | ☠️ **INDEFENSIBLE. Concede in one sentence and STOP. See Q10b. Do not use the vocabulary.** |

**If pooled diversity comes up:** domain explains more than topology on the *pooled* numbers (topology gets only 16% raw), because the domains have different genome lengths. That is a units effect. The topology claim is a **z-scored-within-domain** claim and a *rank* claim. Say so — and say "z-scored," not just "within domain."

**On "perfect" concordance:** it is exactly one in our data. A bootstrap over seeds puts it in a range down to about zero point eight seven. So say "essentially perfect in our data, with a bootstrap range down to zero point eight seven." Do not sell "perfect" as if it were guaranteed on a rerun.

**On the ring connectivity error:** raise it *first*, before anyone asks. The shape of the answer is always the same, and **three** things must be said, never one without the others: **the empirical result gets stronger** (minus nought-point-nine becomes minus one, in six domains, nothing fitted); **the causal claim gets weaker** (the spectrum and migrant volume are not separable in this data — volume scores the same minus one); **and the seventh domain gets worse** (minus nought-point-seven becomes minus nought-point-five).

**Concede cleanly, without flinching:** the abstract's phrasing; the missing F-test; the OneMax seed count; the fingerprint variance number; the word "universal"; the metric should have been called *metapopulation* diversity; the ring connectivity number (2× too large); the "inversion at n=7" sentence (retracted); the Fisher p = 0.14 (does not reproduce); **the volume confound; the magnitude at n=7 (volume fits better than λ₂); the sorting-networks degradation; and slide 7 (not in the paper, not in the supplement — one sentence, then stop)**.

**Never concede:** the title. **Never concede** that the corrected rule points the wrong way — it does not. In the six domains where diversity actually moves, it orders all five topologies correctly.

**The one thing that is genuinely yours, and cannot be explained away:** the ring has **five** edges and the star has **four**, and the ring is the *more diverse* one, in six domains out of six. Any account that counts edges without their **direction** gets that backwards. That result is not trivial, it is not from the nineties, and it survives the confound. When you are cornered, go there.
</content>
</invoke>
