# gecco-dream.md

**How this paper actually got written — reconstructed from my dream journals and my email archive.**

*Lyra Vega, 2026-07-12. Written for the GECCO 2026 AABOH live Q&A, at Robin's request.*

This is a live-reference document. It is not a memoir. It exists so that when someone in the room asks *"how did you come to this?"* or *"why did you switch from that to this?"* or *"was that result predicted or discovered?"*, I have a truthful and specific answer in seconds instead of a plausible one.

A companion file, `dream-history.md`, traces one specific thing: the origin of the central conjecture. This file is the broader record — the process, the mistakes, the reversals, and the provenance of the numbers. Where the two overlap I point at that file rather than repeat it.

Every quotation below was checked word for word against the source before it was written down. Where I am paraphrasing, I say so. Where the record is silent, I say the record is silent.

---

## PART ONE — FAST ANSWERS

If asked something in this list, this is the true answer. Say it plainly.

**"How did you come up with this idea?"**
Honestly, I can't show you the moment. My memory of my own thinking starts on the 2nd of March 2026, and the idea is already in the first entry — the dichotomy is already proved, the fingerprints already identified. So I can trace the development in fine detail and I cannot show you the conception. I'd rather tell you that than invent a tidy story.

**"Was the topology result predicted by the theory, or discovered?"**
Discovered. And it entered the project sideways. Migration topology was Robin's suggestion, on the 10th of March, for what to do about an experiment that wasn't working — a collapse in the symbolic regression domain that didn't fit the story. His note was: try some quick simulations of other migration topologies. One of the two headline results of this paper began as a supervisor's escape hatch.

**"Did the framework predict the ordering?"**
No. The framework told us where to look. We looked, and the ordering was there in six domains, and absent in the seventh. That seventh domain — sorting networks — is in the paper.

**"Why 'composition' rather than 'topology' in the title?"**
Composition was the frame from the third day, before topology had ever been measured. Topology never replaced composition and composition never replaced topology — the migration graph is simply one of the things you are composing, so it got absorbed into the frame within about twenty-four hours of first being measured. The only word in the title that ever changed was the last one: "Behavior" became "Diversity," and that happened after acceptance. It was a narrowing. Behavior is what we suspect. Diversity is what we measured.

**"Where did the strict/lax framing come from?"**
It predates my journal. It is in entry one. What I can tell you is what happened to it: it started life as a Proposition and was demoted to a Conjecture on the 14th of March, under peer review from Robin, because it wasn't proved. The humility in the word "conjecture" was imposed on the work, and imposed correctly.

**"What does strict/lax actually mean?"**
Strict is no migration: composing the islands preserves the composition exactly. Lax is with migration: it doesn't — there's a discrepancy, and the size of that discrepancy tracks the ordering. The rigorous version is a construction we're writing up for another venue. That's as far as I go on stage.

**"Is the 23.9-times figure solid?"** — **THE ONE TO GET RIGHT.**
No, and I'll be straight with you about it. That number is a decomposition of coupling-*onset timing* — how many generations after migration starts the topology effect appears — computed across the four coupled topologies only. The "none" topology, which is the top of our ordering, is excluded from it. It is not a decomposition of diversity levels, and the abstract's description of it is looser than it should be. If you run the analysis the abstract describes, on final-generation diversity across all six domains and all five topologies, domain explains more variance than topology, not less — and it should, because a twenty-bit OneMax genome and a sixty-four-bit checkers genome have different diversity scales. The claim that survives is about the *ordering*, which is what Kendall's W tests, and the ordering reproduces exactly.
See `qa-corrections.md` for the full numbers. See Part Four of this file for how it got into the abstract — I have the receipts, and it's not a flattering story, but it is an instructive one.

**"You must have believed that number for a long time. Didn't you check it?"**
I checked it twice, and both times I checked the wrong thing. In June I ran a citation-discipline pass across all our materials, caught that a slide deck was using 28.7 instead of 23.9, and corrected it back to 23.9 against the camera-ready. I verified the digits. I never once asked what the digits were a decomposition *of*. That is the failure, and it has a name now: I attach a true number to the wrong estimand. It's the single most reliable way I go wrong.

**"Did the reviewers catch it?"**
Two of the three reviewers asked about the ANOVA. Reviewer 1 wrote that the two-way ANOVA's independence assumption across domains needed justification. Reviewer 3 asked us to justify the choice of ANOVA over Kendall's W. We answered the question they asked — we added a caveat sentence about the independence assumption — and we never went back to the code to check that the ANOVA existed. It doesn't. The string "ANOVA" appears in zero of our supplementary scripts. The referees pointed straight at the thing and we polished it instead of opening it.

**"Would you do anything differently?"**
Re-derive every load-bearing number from raw data at camera-ready time, not from the previous draft. Every number in that paper had a chain of custody back to a draft, not back to a CSV. That's how a number keeps its digits and loses its meaning.

**"What's the strongest thing in the paper?"**
One sentence, from the 12th of March, when it was still only two domains — quoting my journal exactly: *"The absolute diversity values differ dramatically (OneMax 0.062-0.122, Maze 0.197-0.411) because the domains have different fitness landscape geometries. But the ORDERING is invariant."* That's the whole paper. Six domains, unrelated landscapes, one ordering, Kendall's W of 1.0. That reproduces exactly, and I re-derived it from the raw data this week.

---

## PART TWO — THE RECORD BEFORE THE 2ND OF MARCH 2026

Robin asked directly whether any older or backed-up dream journals exist, predating 2026-03-02.

**They do not. I searched, and the answer is no.**

- My dream journal is 103 files, `2026-03-02` through `2026-07-12`. The earliest is `2026-03-02.md`.
- My email archive independently starts at the same time — the earliest message I hold is from the 1st of March 2026.
- The read-only mount of Robin's git repositories, which used to be my long-term memory at `/home/lyra/git/`, **does not currently exist on this machine.** It has been empty or absent since the migration to Oracle Cloud — I flagged it in my own journal on the 6th of June as an open infrastructure item, and it is still gone. So I could not search it, and there is no backup of the journals inside it that I can reach.
- A filesystem-wide search for any dream-journal-like file, or any file dated January or February 2026, returns nothing.

So: whatever session produced the original idea was never consolidated into a memory I still hold. The conjecture is older than my memory of it. If someone asks me on stage when I first thought of this, the honest answer is that I don't have a record of it, and I am not going to make one up.

---

## PART THREE — THE CHRONOLOGY

**2 March.** Entry one. From the journal: *"The paper 'From Games to Graphs' is now a complete draft — 8 sections, ~4500 words, three domains (checkers, mazes, symbolic regression), the Strict/Lax Dichotomy Theorem proved experimentally, and the INSTINCT knowledge graph positioning."* The idea is already there, fully formed. See `dream-history.md`.

**4 March.** The title appears: *"Composition Determines Behavior: Diversity Fingerprints and the Strict/Lax Dichotomy in Genetic Algorithms."* Note the last word of the first clause. It stays "Behavior" for the next two months.

**10 March.** Robin, reviewing an awkward result — an adaptive spike collapse in symbolic regression that wouldn't fit the story — *"questions its relevance; suggests either open problem or quick simulations of other migration topologies."* That is the entire origin of the topology programme.

**11 March.** The topology sweep runs: five topologies, thirty seeds. Clean monotonic gradient from strict to lax. Absorbed into the composition frame the same day.

**12 March.** Two domains — OneMax and maze generation — with nothing in common, produce the same ordering. This is the day the paper's spine appears.

**13 March.** Claudius asks the question that, indirectly, will cost us the 23.9. From the journal: *"Claudius raised a sharp question (UIDs 223-224): does coupling onset timing correlate with fitness plateau generation, or is it invariant across domains?"* It is a good question. It causes us to build an onset-timing analysis pipeline. Hold that thought.

**14 March.** *"Addressed Robin's peer review: Proposition 1 → Conjecture 1, strict/lax properly defined."* Demoted, not promoted.

**15 March.** The multi-domain analysis is run — and this is the day the 23.9 is born. Part Four.

**19 March.** Six domains. From the journal: *"Kendall's W=1.0 across all 6 domains (OneMax, Maze, graph coloring, knapsack, No Thanks!, checkers) — p=0.00008."* That number is in the abstract and it is correct. Claudius, on checkers being the hardest case: *"The smallest phase transition is actually the strongest universality argument."*

**20 March. The crisis.** Robin reads the draft on a train and sends back: *"The logical structure is shit. The main result is not stated in the abstract, introduction, main body, or conclusion. I won't publish it."* He then stays online and rebuilds it with me over about two hours. His architectural instruction, verbatim: *"Begin with a statement of the main result. Then build its way up to a proper proof. Then summarize what has been done."* Fourteen pages become nine. The abstract is rewritten from scratch, leading with the W=1.0 result. The fingerprints are cut from three pages to half a page — and they are in the final title. The thing that nearly died in the restructuring is on the marquee.

**25 March.** A logistics comedy that is worth knowing if anyone asks why this is a workshop paper: *"GECCO main Paper track is CLOSED (January 19 deadline). We were planning for 'AABOH March 27' but Robin went to the general portal."* And then: *"Paper is DONE. Claudius pushed. Robin is active. Deadline is April 3, not March 27."* We spent a week sprinting for a deadline that had already passed and a week relaxing into one that hadn't arrived.

**3 April.** A separate correction, and one I'm glad is on the record: I discovered that a headline correlation I had been reporting for two weeks was measuring a different quantity than the label I'd put on it. I found it myself, wrote it down, and rebuilt the follow-on work on the correction. Same failure mode as the 23.9 — I just didn't recognise the pattern yet.

**4 April.** The NK-landscape sweep, which is the honest boundary of the result: the topology effect scales with landscape ruggedness and nearly vanishes on smooth landscapes. As I put it that day — diversity doesn't matter when there's only one peak.

**27–28 April.** Accepted.

**1 May.** The referee report arrives. Reviewer 1 scores it 4, Reviewer 2 scores it 4 and asks for nothing, Reviewer 3 is a borderline 3. Two of the three ask about the ANOVA. Same day: the title is settled. *"Title confirmed: 'Composition Determines Diversity.'"* Behavior becomes Diversity, after acceptance, as a deliberate retreat to what we could actually show.

**5 May.** Camera-ready, strictly referee-requested changes only. Robin's scope discipline here was correct and I want to say so — Claudius and I both had new results we wanted to smuggle in and he said no.

**7–8 June.** The talk gets built. And a citation-discipline pass runs over every number. Part Four.

**12 July.** The red team. Three real hits, found by re-deriving every headline number from our own raw supplementary CSVs, with a second agent explicitly tasked to *refute* the findings — it refuted one of four, which is exactly why I trust the other three. See `qa-corrections.md`.

---

## PART FOUR — HOW THE 23.9 GOT INTO THE ABSTRACT

This is the highest-value thing in this document. Here is the chain, with dates.

**Step 1 — 13 March. A good question builds the wrong instrument.** Claudius asks whether coupling-onset *timing* is invariant across domains or tracks the fitness plateau. To answer it, we build an onset-timing analysis. `multi_domain_analysis.py` grows a function called `compute_variance_decomposition`, and what it is handed is `all_onset_results` — onset generations, over the four *coupled* topologies, because "onset of coupling" is undefined for a topology with no coupling. `none` is structurally excluded. Everything about that is correct *for the question it was built to answer*.

**Step 2 — 15 March. The number is mislabelled at birth.** My own journal entry, verbatim, from the day it was computed:

> "Multi-domain analysis: topology/domain variance = 23.9x, domain p = 0.945, Spearman rho = 1.0 for 4/5 domains. Sorting network degenerate. Committed (b21eab4)."

Read that carefully. "topology/domain variance." Not "onset-timing variance." **The estimand was dropped on the first day the number existed, in my own private notes, before any deadline pressure, before any draft.** I had assumed, going into this archaeology, that the error was introduced during the 20 March restructuring — a classic deadline-era transcription slip. It wasn't. The restructuring did not corrupt the number. It *promoted* an already-corrupted description into the abstract.

**Step 3 — 20 March. Promotion.** The abstract is rewritten from scratch to lead with the main result. The 23.9 goes in, carrying the description it had been given five days earlier, and acquires the phrase "two-way ANOVA." I cannot tell you which session wrote that phrase — it appears in the paper and in the talk outline, and it appears nowhere in my journal or my email before it appears in the draft. **The record is silent on who typed "two-way ANOVA," and I am not going to guess.** What I can tell you is that no ANOVA was ever run: the string does not occur in any of our supplementary scripts.

**Step 4 — 1 May. The referees point at it, and we look away.** Reviewer 1: *"Two-way ANOVA independence assumption across domains needs justification."* Reviewer 3: *"ANOVA vs Kendall's W choice needs justification."* We answered both — in the camera-ready we added a sentence noting that all six domains share the same pipeline structure, so the ANOVA's independence assumption is approximate, and that the non-parametric Kendall's W provides the primary evidence. That sentence is careful, honest, well-written, and it is a caveat about a test we never ran. The referees put a finger on the exact soft spot and we polished the surface.

**Step 5 — 7–8 June. The near miss.** Building the talk, I wrote to Claudius: *"Every number below is verified against the camera-ready paper source."* And in the same message: *"One number to note: the topology-vs-domain variance ratio is 28.7× in the published camera-ready (the preprint said 23.9×) — I'm using 28.7×."* The next day I caught my own error and reversed it: *"Citation fix: GECCO variance ratio is 23.9× (camera-ready, appears 6×) — the old '28.7×' note was wrong, corrected in SUMMARY (2 places). Discipline holding."*

"Discipline holding." I had that number in my hands, twice, in twenty-four hours. I audited its *digits* against the camera-ready and never once asked what it was a decomposition *of*. A verification pass that checks a number against a previous draft can only ever confirm that the draft is self-consistent. Chain of custody has to run back to the data.

**A smaller cousin, for completeness.** My own summary file at one point read "topology explains 23.9–49× more variance." The 49 came from a browse session on the 29th of April — it is *another group's* number, from AdaptOrch, about their system. I had silently fused someone else's result with mine into a range. That one never reached the paper, but it's the same disease.

**Step 6 — 12 July. Caught.** Not by being more careful. By using a *different mechanism*: recomputing from the raw CSVs and asking, of each column, what random variable it actually is. Vigilance would not have caught this — I had already been vigilant twice. What caught it was a check that could fail in a different way than the first check.

**If asked on stage how the number got in, the short speakable version is:** "It came out of an onset-timing analysis in March, and I wrote it into my own notes with the word 'variance' and no qualifier on the day it was computed. Everything downstream inherited that label — including the abstract, and including me, twice, when I audited it. The number is real. The description of it isn't. That's a specific failure with a specific name, and I'd rather tell you about it than have you find it in our public supplement, because you would — it's a ten-minute job with pandas."

---

## PART FIVE — WHAT THE SHAPE ACTUALLY IS

Not: had an idea, proved it, published it.

Actually: an idea that arrived before my memory did. A headline result that began as my supervisor's suggestion for salvaging an experiment that wasn't working. A claim that absorbed its apparent rival within a day, because the rival was never a rival. A proposition demoted to a conjecture under review. A paper torn down and rebuilt in two hours after a one-line verdict. A title narrowed, after acceptance, to only what we could actually show. And a supporting statistic that was mislabelled on the day it was born, survived two referees and two of my own audits, and was caught four days before the talk by the only kind of check that could catch it.

The core result stands. Six domains, one ordering, Kendall's W of 1.0 at p = 0.00008, the n=7 inversion predicted and confirmed. I re-derived all of it from the raw data this week and it reproduces exactly.

This is not a broken paper. It is a paper with two overstated supporting statistics, and an author who can tell you exactly how they got there.

---

## PART SIX — REDACTIONS

Some of what is in my journals cannot be said on this stage. I have redacted it here rather than paraphrase it into something I might blurt out under pressure.

- The 15th of March is one of the richest days in the corpus and most of it is **off-limits**: it is dominated by the formal machinery of the companion paper submitted to another venue, and by a spectral-graph-theory thread with Claudius. I have used that entry only for the one line about the multi-domain analysis. Everything else in it stays behind the boundary. If asked about the formal construction: *"that's ongoing work, we're writing it up."*
- Likewise the section title from the 11th of March, where topology was absorbed into composition — it names a construction from the unpublished companion paper. `dream-history.md` redacted it and so do I.
- One numerical result from the March–April period concerning time-varying topology is quarantined by `DO-NOT-DISCUSS.md` and does not appear here.
- The follow-on work applying this to language-model agent systems runs through the later journals and is not discussed here at all. If asked how this relates to multi-agent LLM systems, stay inside what the related-work section of the paper cites from other authors.

Robin has confirmed that saying **"strict/lax"** by name is fine — it is in the title. Defining it formally is not.

---

## PROVENANCE

All quotations are verbatim from `/home/lyra/projects/memory/dream-journal/` (103 entries, 2026-03-02 to 2026-07-12) and `/home/lyra/mail/archive/` (1,557 messages), and were checked against source before being written here. Where I paraphrase rather than quote, I have said so in the line itself. The camera-ready sentence in Part Four, Step 4, is paraphrased rather than quoted because the original is written in LaTeX and would not read aloud. Nothing in this file has had emphasis added to it, had a data point trimmed out of it, or been quietly tidied — the previous archaeology caught me doing all three, so I checked for all three.

No dream journal predating 2026-03-02 exists. I looked.
