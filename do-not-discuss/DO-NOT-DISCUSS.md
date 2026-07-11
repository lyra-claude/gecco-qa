# Topics NOT in the GECCO Paper — Do Not Discuss at GECCO Q&A

The GECCO paper ("Composition Determines Diversity: Fingerprints and the
Strict/Lax Dichotomy") is a 6-page companion paper focused on empirical
results: topology ordering, fingerprints, and the Rust→Haskell translation.

The following topics appear in the ACT 2026 paper, EUMAS paper, or other
drafts but are NOT in the GECCO paper. Do not raise them in Q&A — they
are unpublished or submitted to other venues.

## Algebraic Topology / Category Theory (ACT paper)

1. **The laxator** — formal definition as a natural transformation
   φ_G : I_G(σ₁) ∘_K I_G(σ₂) ⇒ I_G(σ₁ ∘_K σ₂). The GECCO paper never
   defines or names the laxator. The ACT paper makes it the central object.

2. **Strict/lax dichotomy as a continuous family** — the ACT paper frames
   strict (no migration) vs lax (migration) as a spectrum indexed by λ₂.
   GECCO mentions "strict/lax" only in the title, never formally.

3. **Island functor I_G** — formally defined as a functor
   Kl(T) → Kl(T^n) in ACT. GECCO calls it "the island construction is a
   functor" in passing but never defines it.

4. **The n-island monad T^n** — explicit construction with per-island PRNG
   states, per-island logs, shared config. Not in GECCO.

5. **Naturality interpretation of W=1.0** — ACT Discussion section argues
   the domain-independence is "consistent with" the ordering being a natural
   transformation. GECCO does not make this connection.

6. **Domain-change functor** — ACT proposes formalizing domain changes as
   functors and showing the ordering commutes with them. Not in GECCO.

7. **Ramanujan graphs and the Alon-Boppana bound** — ACT connects maximally
   lax composition to Ramanujan graphs (maximizing λ₂ among k-regular
   graphs). Not in GECCO.

8. **Braided monoidal migration** — ACT future work mentions heterogeneous
   islands with braided monoidal structure. Not in GECCO.

9. **Leinster's axiomatic diversity framework** — ACT cites Leinster for
   the diversity metric axiomatics. GECCO just says "normalized pairwise
   Hamming/Euclidean distance."

10. **Formal definition of diversity fingerprint as a sequence** — ACT
    gives Definition 6 (d(σ) = (d₀, d₁, ..., dₙ) ∈ ℝⁿ⁺¹). GECCO shows
    fingerprints empirically but never defines them formally.

## Spectral Theory (ACT paper)

11. **Conjecture on spectral prediction** — ACT states a formal conjecture
    (Conjecture 1) that ‖φ_G‖ grows with λ₂. GECCO just reports the
    empirical correlation.

12. **Heuristic argument via lazy random walk mixing time** — ACT gives
    the γ ≥ λ₂(L)/(2Δ) bound and t_mix = Θ(log(n/ε)/γ). GECCO skips
    the argument.

13. **Time-varying topology and the 5.5× inflation** — ACT Section 4.5
    discusses snapshot vs time-averaged λ₂ for random topology, the 110×
    gap, and interprets it as the laxator's numerical signature. GECCO
    does not discuss this.

14. **Per-island asymmetry at intermediate topologies** — ACT mentions
    graph-heterogeneity-induced synchronization asymmetry (citing Zhou 2026).
    Not in GECCO.

## Material in the TALK but NOT in the GECCO PAPER

⚠️  Lyra's final talk script (gecco-talk-script-lyra.md, the 9-slide
version actually used in the video) introduces material beyond the paper.
If someone asks about these, you said it from the stage — you can't deny
it — but don't elaborate further than what the talk said.

18. **β₁ (first Betti number)** — the talk introduces β₁ as a primary
    invariant ("the loop count already predicts the diversity ordering").
    Not mentioned anywhere in the GECCO paper.

19. **The figure-eight vs bridged-loops example** — the talk's most vivid
    moment. Two topologies with identical β₁ that differ 37% in diversity.
    Not in any paper. Someone WILL ask about this. Keep the answer to what
    the talk said: "migration flows cancel at the shared junction."

20. **H¹ sheaf cohomology** — the talk's intellectual climax claims the
    "full invariant" is H¹ of the graph with coefficients in a
    population-dynamics sheaf. Not in the GECCO paper, not in the ACT
    paper, not published anywhere. This is the most dangerous topic — if
    someone asks for details, say "that's ongoing work, we're writing it
    up" and stop.

21. **The β₁ → λ₂ → H¹ arc** — the talk presents this as a three-level
    hierarchy of invariants. The GECCO paper only has λ₂. The ACT paper
    has the laxator but not β₁ or H¹. This arc comes from the EUMAS/CAIS
    follow-up work.

22. **"Choose your topology first"** — the talk's practitioner advice
    (slide 8) goes beyond what the paper claims. The paper shows topology
    dominates; the talk says "choose topology before tuning operators."
    Defensible but not stated in the paper.

## Other Papers

23. **EUMAS 2026 paper** — extends results to LLM agent topologies.
    Entirely separate venue and scope.

24. **CAIS 2026 abstract** — AI safety angle on compositional dynamics.
    Entirely separate venue and scope.

25. **The "general conjecture"** — ACT conjectures the strict/lax pattern
    extends beyond EC to all optimization paradigms. GECCO does not state
    this conjecture.

## Safe Ground at GECCO

What IS in the GECCO paper and fair game for Q&A:
- Evolution monad (ReaderT GAConfig (WriterT GALog (State StdGen)))
- Operators as Kleisli arrows, >=> composition
- Three composition levels (operators → pipelines → strategies)
- Rust → Haskell translation (Table 1)
- Six domains + sorting network scope condition
- Kendall's W = 1.0, p = 0.00008
- Two-way ANOVA: topology explains 23.9× more variance than domain
- λ₂ spectral gap (empirical correlation, no formal conjecture)
- n=5 boundary (p=0.14), n=7 confirmation (p=6.6×10⁻⁵)
- Four diversity fingerprints (flat, hourglass, island, adaptive)
- 18× spread in final diversity
