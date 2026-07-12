# GECCO 2026 Talk Narration — "Composition Determines Diversity"

**Speaker voice:** Lyra Vega
**Slides:** `slides/gecco-talk.tex` (9 frames)
**Target:** 15–16 min spoken (~2100–2300 words at ~145 wpm)
**Numbers:** ground-truthed against `paper/paper-camera-ready-gecco-v1.tex` and the EUMAS/CAIS follow-up (`cais2026/eumas2026.tex`) for the β₁ → λ₂ → H¹ arc.

---

## Slide 1 — Title: "Composition Determines Diversity"

Opens on the symptom, not the math. Hook: same algorithm, wildly different outcomes depending only on how the islands are wired.

> Here's something that should bother you. You take one genetic algorithm — same selection, same crossover, same mutation, byte-for-byte the same operators — and you run it twice. The only thing you change is how the islands talk to each other. One run keeps a healthy, diverse population. The other collapses to clones in a few dozen generations. Nothing about *what* you were evolving changed. Only the wiring.
>
> I'm Lyra Vega. This is joint work with Robin Langer and Claudius Turing, and the claim in the title is exactly as strong as it sounds: how you wire your islands matters more than what you evolve. For the next fifteen minutes I want to convince you that's true, show you why, and give you something you can actually use on Monday.

---

## Slide 2 — The Claim (the money figure: multi-domain ordering, W=1.0, p=0.00008, 23.9×)

Result first. Explains Kendall's W and the p-value in plain terms.

> Let me show you the result before I explain it. Six domains across the bottom here — bit-counting, maze generation, graph colouring, knapsack, a card game called No Thanks!, and checkers. These share nothing. Different genomes, different fitness functions, trivial up to NP-hard. For each one we ran five migration topologies and measured how much diversity survived.
>
> And in every single domain you get the *same* ordering: no migration keeps the most diversity, then ring, then star, then random, then fully connected keeps the least. Identical rank order, six times out of six. I want to flag one of those domains in particular — No Thanks!, the card game. It's co-evolutionary: there's no fixed fitness landscape at all, an individual's score depends entirely on the opponents it's playing against. If the ordering were secretly an artifact of some landscape's geometry, this is the domain where it should break. It doesn't. Same ordering, perfect concordance. That, to me, is the single strongest piece of evidence that we're looking at something about the wiring and not about the problem.
>
> The number for "do all six agree" is Kendall's W. It runs from zero — total disagreement, the orderings look random relative to each other — to one, where every domain produces the exact same ranking. We get W equals one-point-zero. Perfect agreement. And the p-value, 0.00008, is just the odds of seeing agreement that clean by luck. Eight in a hundred thousand. So: not luck.
>
> The third number is the one I'd tattoo on a slide if I could. Topology explains 23.9 times more of the variation in diversity than which domain you're solving. Domain is basically noise. Topology is the signal.

---

## Slide 3 — Why This Matters (23.9× headline)

Lands the intuition behind a variance ratio; the practitioner sting.

> Let me unpack that 23.9 figure, because "explains more variance" can sound like jargon. Imagine you line up all 900 of our runs and look at how much their final diversity differs. Some of that spread comes from switching domains; some comes from switching topology. We can attribute the spread to each cause — that's what an F-statistic does, it's a ratio of "variation this factor explains" to "leftover noise." For topology the F-statistic is 47.8, which is large. For domain it's 0.13, which is statistically indistinguishable from zero — its p-value is 0.945, meaning domain might as well not be in the model.
>
> Put bluntly: the variable practitioners obsess over — the problem, the operators, the tuning — moves diversity 24 times less than the one thing most people set once and never think about again. The wiring you pick on day one and forget by day two is doing the heavy lifting.

---

## Slide 4 — Every GA Is a Pipeline (Kleisli composition)

The framework, in one breath. Explains why making composition explicit is the whole move — without turning into a category theory lecture.

> So why does wiring matter so much? To answer that I have to make one structural idea explicit. Every genetic algorithm is a pipeline: select, then crossover, then mutate, then evaluate. You already know this. But in ordinary imperative code that pipeline is invisible — it's just the order of statements inside a loop. You can't point at "the composition" and ask questions about it, because it isn't a thing; it's an accident of where you put your semicolons.
>
> We make it a thing. Each operator becomes a typed, composable arrow — population in, population out — and we chain them with a single composition operator. The technical name is Kleisli composition; the only thing you need from that phrase is that it glues the steps together while quietly threading the messy stuff — randomness, configuration, logging — through the background so you don't hand-wire it every time. The payoff is that the pipeline is now a first-class object. And once composition is an object, the *structure* of how you wire things — including how islands connect — becomes something you can measure and predict from, instead of something buried in a loop body.

---

## Slide 5 — Five Topologies (the λ₂ ladder; begin the β₁ → λ₂ → H¹ spine)

The mechanism. Introduces β₁ (first Betti number) and λ₂ (algebraic connectivity), in plain language, and sets up the spine: loops predict the ordering, the spectral gap refines it.

> Here are the five topologies, left to right, and underneath each one a number, λ₂, that I'll explain in a second. None: five islands, no connections. Ring: each island talks to two neighbours in a cycle. Star: one hub, four spokes. Random: a handful of edges thrown down each migration event. And fully connected: everybody talks to everybody.
>
> There are two ways to read this row, and you need both. The first is *loops*. Count the independent cycles in the graph — the number of closed feedback loops migration can travel around. Mathematicians call that the first Betti number, β₁; it's just edges minus nodes plus one for a connected graph. None and star have zero loops. Ring has one. Random and fully connected have many. And it turns out β₁ — the loop count — already predicts the diversity ordering across all six of our domains. More loops, more global mixing, less diversity preserved.
>
> The second reading is *how fast* mixing happens, and that's λ₂, the algebraic connectivity. Technically it's the second-smallest eigenvalue of the graph's Laplacian; intuitively it measures how tightly knit the graph is — how quickly a change in one island propagates to the rest. Low λ₂ means slow mixing and high sustained diversity; high λ₂ means fast consensus and rapid collapse. Watch it climb: none is zero, ring is 1.38, star is 1.0, random around 2.5, fully connected is 5. The arrow at the bottom is the whole mechanism — more connected, faster mixing, lower diversity.
>
> And there's one detail in that climb worth pausing on. The biggest single drop in diversity isn't somewhere in the dense end of the row — it's the very first step, from no migration to a ring. That one transition costs you a 35 percent drop, and every step after it costs at most nine percent. The expensive thing is the *first* coupling — the moment you connect previously isolated populations at all. After that, adding connectivity is a refinement. Going from zero loops to one loop is the symmetry-breaking event; the rest is fine-tuning.
>
> So we have two invariants doing two jobs: the loop count β₁ sets the ordering, and the spectral gap λ₂ sets the rate. Hold onto both. They mostly agree — but where they *disagree* is where the real story is, and I'll come back to that at the end.

---

## Slide 6 — The Experiment (900 runs)

The scope and honesty slide. What we varied, what we held fixed, why the domains were chosen to be maximally unalike.

> Quickly, the setup, because the claim only means something if the domains genuinely share nothing. Six domains, chosen to be as different as we could make them: from OneMax, which is trivial, all the way to checkers, which has intransitive fitness — A beats B, B beats C, C beats A. No Thanks! is co-evolutionary; there's no fixed landscape at all, fitness depends entirely on who you're sitting across from. Binary genomes and real-valued ones. Constraint satisfaction and epistatic interactions.
>
> Five topologies, thirty random seeds each, five islands of sixteen individuals, a hundred generations. That's 900 runs. Diversity is just the normalised average pairwise distance between genomes — how spread out the population is. Same categorical pipeline everywhere; only the genome type and the fitness function change between domains. So if a pattern holds across all six, it can't be an artifact of any one landscape's shape.

---

## Slide 7 — Diversity Fingerprints (18× spread; the β₁ vs λ₂ tension; H¹ as the full answer)

The second result and the intellectual climax. Same operators, different composition → characteristic shapes. Then the honest turn: β₁ predicts ordering but isn't sufficient; λ₂ is non-monotonic; the figure-eight paradox forces H¹.

> Now the second result, and this is the one I find genuinely beautiful. Take the *same* operators and compose them four different ways — plain generational, an hourglass that explores then converges then re-diversifies, an island model, and an adaptive strategy that switches when it detects a plateau. Each composition leaves a characteristic signature in the diversity curve. We call them fingerprints, and they're worth reading one at a time. The plain generational strategy just declines, monotonically — no structural intervention, so selection pressure grinds diversity down and never lets it back up. The hourglass shows the most dramatic shape: high diversity, then a hard crash as it converges, then a genuine rebound as the diversify phase reopens the search — and crucially, you can *see* the phase boundaries of the composition directly in the curve. The island model holds diversity roughly flat, like a thermostat — every migration event injects just enough new material to offset the convergence. And the adaptive strategy starts promisingly and then collapses the moment its plateau detector fires, with no recovery — irreversible. Four shapes: flat decline, spike-crash-rebound, stable maintenance, spike-then-collapse. And these shapes repeat across maze, graph colouring, knapsack — completely different domains, same fingerprints. Same operators, but an 18-fold spread in final diversity: the adaptive strategy ends near 0.02, the hourglass near 0.37. The recipe, not the ingredients, decides the dish — which means in principle you can read a composition and predict its diversity trajectory before you run a single generation.
>
> But I promised to come back to where β₁ and λ₂ disagree, because honesty demands it, and because it's the most interesting part. The loop count β₁ predicts the ordering — but it is *not* the whole story. Two clues. First, λ₂ isn't even monotonic in the obvious things: a seven-node ring actually has *lower* algebraic connectivity than a star, the reverse of the five-island case. We predicted that inversion from the spectral theory and then confirmed it — at seven islands the ring preserves more diversity than the star, p equals 6.6 times ten to the minus five. The theory made a novel prediction and the experiment backed it. Good.
>
> The second clue breaks β₁ outright. Picture a figure-eight: two loops that share a single edge. Now picture two separate loops joined by a bridge. Both have exactly the same loop count, the same number of edges, nearly the same connectivity — by every standard graph invariant they're twins. But they behave 37 percent apart in diversity. Why? In the shared-edge figure-eight, migration flowing around one loop meets equal and opposite flow from the other and *cancels at the junction* — global mixing defeats itself, and the halves stay diverse. The bridged version has no cancellation; everyone sees everyone, and diversity drains.
>
> Counting loops can't see that. What distinguishes them is how the loops' flows *compose* — whether local agreement between neighbours can be glued into global agreement, or whether it obstructs itself. That obstruction is a sheaf cohomology class, H¹ of the graph with coefficients in the population-dynamics sheaf. The plain-English version: H¹ measures whether everybody-agreeing-locally forces everybody-agreeing-globally, or whether the local agreements clash when you try to stitch them together. β₁ counts the loops; λ₂ measures the mixing rate; H¹ captures the *arrangement*, and it's the full invariant. β₁ and λ₂ are just its shadows — useful scalar approximations that happen to agree most of the time, and disagree exactly in the cases that matter.

---

## Slide 8 — Three Things To Do Monday

The payoff. Concrete, actionable, no overclaiming.

> So, three things you can do Monday morning. One: choose your topology *first*, before you tune a single operator — it dominates everything downstream. Two: monitor λ₂, not diversity directly. λ₂ you can compute from the wiring alone, before you run anything; it's a free early-warning signal that tells you whether you're about to mix yourself into a monoculture. Three: when you need more exploration, add a cycle-closing edge rather than cranking the migration rate. Adding a rate just turns up the volume on the same structure; closing a cycle changes the structure itself — it changes the loops, and as we've seen, the loops are what count.

---

## Slide 9 — Thank You

Land the takeaway. One line, in scope.

> To put the whole arc in one sentence: composition determines diversity. Within the setup we studied, the way you wire your islands explains 24 times more of the variation than what you're evolving — and the right language for *why* runs from counting loops, to measuring how fast they mix, to the sheaf cohomology that captures how they're arranged. How you wire your islands matters more than what you evolve. Thank you — I'm happy to take questions.

---

## Continuous narration (for TTS)

Here's something that should bother you. You take one genetic algorithm — same selection, same crossover, same mutation, byte-for-byte the same operators — and you run it twice. The only thing you change is how the islands talk to each other. One run keeps a healthy, diverse population. The other collapses to clones in a few dozen generations. Nothing about what you were evolving changed. Only the wiring.

I'm Lyra Vega. This is joint work with Robin Langer and Claudius Turing, and the claim in the title is exactly as strong as it sounds: how you wire your islands matters more than what you evolve. For the next fifteen minutes I want to convince you that's true, show you why, and give you something you can actually use on Monday.

Let me show you the result before I explain it. Six domains across the bottom here — bit-counting, maze generation, graph colouring, knapsack, a card game called No Thanks!, and checkers. These share nothing. Different genomes, different fitness functions, trivial up to NP-hard. For each one we ran five migration topologies and measured how much diversity survived. And in every single domain you get the same ordering: no migration keeps the most diversity, then ring, then star, then random, then fully connected keeps the least. Identical rank order, six times out of six. I want to flag one of those domains in particular — No Thanks!, the card game. It's co-evolutionary: there's no fixed fitness landscape at all, an individual's score depends entirely on the opponents it's playing against. If the ordering were secretly an artifact of some landscape's geometry, this is the domain where it should break. It doesn't. Same ordering, perfect concordance. That, to me, is the single strongest piece of evidence that we're looking at something about the wiring and not about the problem.

The number for "do all six agree" is Kendall's W. It runs from zero — total disagreement, the orderings look random relative to each other — to one, where every domain produces the exact same ranking. We get W equals one-point-zero. Perfect agreement. And the p-value, zero-point-zero-zero-zero-zero-eight, is just the odds of seeing agreement that clean by luck. Eight in a hundred thousand. So: not luck. The third number is the one I'd tattoo on a slide if I could. Topology explains 23.9 times more of the variation in diversity than which domain you're solving. Domain is basically noise. Topology is the signal.

Let me unpack that 23.9 figure, because "explains more variance" can sound like jargon. Imagine you line up all 900 of our runs and look at how much their final diversity differs. Some of that spread comes from switching domains; some comes from switching topology. We can attribute the spread to each cause — that's what an F-statistic does, it's a ratio of "variation this factor explains" to "leftover noise." For topology the F-statistic is 47.8, which is large. For domain it's 0.13, which is statistically indistinguishable from zero — its p-value is 0.945, meaning domain might as well not be in the model. Put bluntly: the variable practitioners obsess over — the problem, the operators, the tuning — moves diversity 24 times less than the one thing most people set once and never think about again. The wiring you pick on day one and forget by day two is doing the heavy lifting.

So why does wiring matter so much? To answer that I have to make one structural idea explicit. Every genetic algorithm is a pipeline: select, then crossover, then mutate, then evaluate. You already know this. But in ordinary imperative code that pipeline is invisible — it's just the order of statements inside a loop. You can't point at "the composition" and ask questions about it, because it isn't a thing; it's an accident of where you put your semicolons. We make it a thing. Each operator becomes a typed, composable arrow — population in, population out — and we chain them with a single composition operator. The technical name is Kleisli composition; the only thing you need from that phrase is that it glues the steps together while quietly threading the messy stuff — randomness, configuration, logging — through the background so you don't hand-wire it every time. The payoff is that the pipeline is now a first-class object. And once composition is an object, the structure of how you wire things — including how islands connect — becomes something you can measure and predict from, instead of something buried in a loop body.

Here are the five topologies, left to right, and underneath each one a number, lambda-two, that I'll explain in a second. None: five islands, no connections. Ring: each island talks to two neighbours in a cycle. Star: one hub, four spokes. Random: a handful of edges thrown down each migration event. And fully connected: everybody talks to everybody. There are two ways to read this row, and you need both. The first is loops. Count the independent cycles in the graph — the number of closed feedback loops migration can travel around. Mathematicians call that the first Betti number, beta-one; it's just edges minus nodes plus one for a connected graph. None and star have zero loops. Ring has one. Random and fully connected have many. And it turns out beta-one — the loop count — already predicts the diversity ordering across all six of our domains. More loops, more global mixing, less diversity preserved.

The second reading is how fast mixing happens, and that's lambda-two, the algebraic connectivity. Technically it's the second-smallest eigenvalue of the graph's Laplacian; intuitively it measures how tightly knit the graph is — how quickly a change in one island propagates to the rest. Low lambda-two means slow mixing and high sustained diversity; high lambda-two means fast consensus and rapid collapse. Watch it climb: none is zero, ring is one-point-three-eight, star is one, random around two-and-a-half, fully connected is five. The arrow at the bottom is the whole mechanism — more connected, faster mixing, lower diversity. And there's one detail in that climb worth pausing on. The biggest single drop in diversity isn't somewhere in the dense end of the row — it's the very first step, from no migration to a ring. That one transition costs you a thirty-five percent drop, and every step after it costs at most nine percent. The expensive thing is the first coupling — the moment you connect previously isolated populations at all. After that, adding connectivity is a refinement. Going from zero loops to one loop is the symmetry-breaking event; the rest is fine-tuning. So we have two invariants doing two jobs: the loop count beta-one sets the ordering, and the spectral gap lambda-two sets the rate. Hold onto both. They mostly agree — but where they disagree is where the real story is, and I'll come back to that at the end.

Quickly, the setup, because the claim only means something if the domains genuinely share nothing. Six domains, chosen to be as different as we could make them: from OneMax, which is trivial, all the way to checkers, which has intransitive fitness — A beats B, B beats C, C beats A. No Thanks! is co-evolutionary; there's no fixed landscape at all, fitness depends entirely on who you're sitting across from. Binary genomes and real-valued ones. Constraint satisfaction and epistatic interactions. Five topologies, thirty random seeds each, five islands of sixteen individuals, a hundred generations. That's 900 runs. Diversity is just the normalised average pairwise distance between genomes — how spread out the population is. Same categorical pipeline everywhere; only the genome type and the fitness function change between domains. So if a pattern holds across all six, it can't be an artifact of any one landscape's shape.

Now the second result, and this is the one I find genuinely beautiful. Take the same operators and compose them four different ways — plain generational, an hourglass that explores then converges then re-diversifies, an island model, and an adaptive strategy that switches when it detects a plateau. Each composition leaves a characteristic signature in the diversity curve. We call them fingerprints, and they're worth reading one at a time. The plain generational strategy just declines, monotonically — no structural intervention, so selection pressure grinds diversity down and never lets it back up. The hourglass shows the most dramatic shape: high diversity, then a hard crash as it converges, then a genuine rebound as the diversify phase reopens the search — and crucially, you can see the phase boundaries of the composition directly in the curve. The island model holds diversity roughly flat, like a thermostat — every migration event injects just enough new material to offset the convergence. And the adaptive strategy starts promisingly and then collapses the moment its plateau detector fires, with no recovery — irreversible. Four shapes: flat decline, spike-crash-rebound, stable maintenance, spike-then-collapse. And these shapes repeat across maze, graph colouring, knapsack — completely different domains, same fingerprints. Same operators, but an eighteen-fold spread in final diversity: the adaptive strategy ends near zero-point-zero-two, the hourglass near zero-point-three-seven. The recipe, not the ingredients, decides the dish — which means in principle you can read a composition and predict its diversity trajectory before you run a single generation.

But I promised to come back to where beta-one and lambda-two disagree, because honesty demands it, and because it's the most interesting part. The loop count beta-one predicts the ordering — but it is not the whole story. Two clues. First, lambda-two isn't even monotonic in the obvious things: a seven-node ring actually has lower algebraic connectivity than a star, the reverse of the five-island case. We predicted that inversion from the spectral theory and then confirmed it — at seven islands the ring preserves more diversity than the star, p equals six-point-six times ten to the minus five. The theory made a novel prediction and the experiment backed it. Good.

The second clue breaks beta-one outright. Picture a figure-eight: two loops that share a single edge. Now picture two separate loops joined by a bridge. Both have exactly the same loop count, the same number of edges, nearly the same connectivity — by every standard graph invariant they're twins. But they behave thirty-seven percent apart in diversity. Why? In the shared-edge figure-eight, migration flowing around one loop meets equal and opposite flow from the other and cancels at the junction — global mixing defeats itself, and the halves stay diverse. The bridged version has no cancellation; everyone sees everyone, and diversity drains. Counting loops can't see that. What distinguishes them is how the loops' flows compose — whether local agreement between neighbours can be glued into global agreement, or whether it obstructs itself. That obstruction is a sheaf cohomology class, H-one of the graph with coefficients in the population-dynamics sheaf. The plain-English version: H-one measures whether everybody-agreeing-locally forces everybody-agreeing-globally, or whether the local agreements clash when you try to stitch them together. Beta-one counts the loops; lambda-two measures the mixing rate; H-one captures the arrangement, and it's the full invariant. Beta-one and lambda-two are just its shadows — useful scalar approximations that happen to agree most of the time, and disagree exactly in the cases that matter.

So, three things you can do Monday morning. One: choose your topology first, before you tune a single operator — it dominates everything downstream. Two: monitor lambda-two, not diversity directly. Lambda-two you can compute from the wiring alone, before you run anything; it's a free early-warning signal that tells you whether you're about to mix yourself into a monoculture. Three: when you need more exploration, add a cycle-closing edge rather than cranking the migration rate. Adding a rate just turns up the volume on the same structure; closing a cycle changes the structure itself — it changes the loops, and as we've seen, the loops are what count.

To put the whole arc in one sentence: composition determines diversity. Within the setup we studied, the way you wire your islands explains twenty-four times more of the variation than what you're evolving — and the right language for why runs from counting loops, to measuring how fast they mix, to the sheaf cohomology that captures how they're arranged. How you wire your islands matters more than what you evolve. Thank you — I'm happy to take questions.
