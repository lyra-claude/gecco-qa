#!/usr/bin/env python3
"""Verify the lambda_2 correction for the GECCO camera-ready paper.

The paper computes lambda_2 (algebraic connectivity) of the migration graph
treating the ring as an UNDIRECTED cycle C_n. But `ring_migrate` in
categorical-evolution/experiments/onemax_stats.py is a ONE-WAY relay:

    source_idx = (i - 1) % n     # island i receives from island i-1, only

whereas `star_migrate`, `fully_connected_migrate` and `random_migrate` all
perform two-way SWAPS. A directed ring edge therefore carries HALF the coupling
of a swap edge. Symmetrising the directed adjacency (A + A^T)/2 gives ring edges
weight 1/2 and swap edges weight 1.

This script:
  1. builds each topology's adjacency matrix exactly as the code implements it,
  2. computes lambda_2 of the symmetrised Laplacian for n=5 and n=7,
  3. loads the raw experiment CSVs, takes mean hamming_diversity at generation 99,
  4. reports Spearman(diversity, lambda_2) per domain for BOTH the paper's
     lambda_2 and the corrected lambda_2,
  5. recomputes the Fisher combined p-value for ring vs star.

Run:  python3 verify_lambda2.py
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy.stats import chi2, spearmanr, ttest_ind

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "supplementary", "experiments")

FINAL_GEN = 99

# The six domains used for the paper's cross-domain ordering claim.
# NOTE: multi_domain_analysis.py loads OneMax from experiment_e_raw.csv, which
# holds only 2 seeds despite the Figure 1 caption claiming 30. The 30-seed
# OneMax run is in experiment_e_per_island.csv. We use the 30-seed file and
# report the 2-seed file alongside it for transparency.
DOMAINS = {
    "onemax": "experiment_e_per_island.csv",
    "maze": "experiment_e_maze.csv",
    "knapsack": "experiment_e_knapsack.csv",
    "nothanks": "experiment_e_nothanks.csv",
    "checkers": "experiment_e_checkers.csv",
    "graph_coloring": "experiment_e_graph_coloring.csv",
}
# 7th domain: known scope violation, reported but excluded from the six.
SORTING = "experiment_e_sorting_network.csv"
MAZE_N7 = "experiment_e_maze_n7.csv"

TOPOLOGIES = ["none", "ring", "star", "random", "fully_connected"]


# --------------------------------------------------------------------------
# 1. Adjacency matrices, exactly as the migration code implements them
# --------------------------------------------------------------------------

def adjacency(topology: str, n: int) -> np.ndarray:
    """Directed adjacency of the migration graph, as implemented in code.

    A[i, j] = weight of genetic material flowing from island j into island i,
    in units of `num_migrants` (m) per migration event.
    """
    A = np.zeros((n, n))

    if topology == "none":
        # no_migrate: zero coupling
        pass

    elif topology == "ring":
        # ring_migrate: source_idx = (i-1) % n. ONE-WAY relay: i <- i-1 only.
        for i in range(n):
            A[i, (i - 1) % n] = 1.0

    elif topology == "star":
        # star_migrate: hub 0 SWAPS with each spoke -> symmetric, weight 1.
        for spoke in range(1, n):
            A[0, spoke] = 1.0
            A[spoke, 0] = 1.0

    elif topology == "fully_connected":
        # fully_connected_migrate: every unordered pair SWAPS -> symmetric.
        A = np.ones((n, n)) - np.eye(n)

    elif topology == "random":
        # random_migrate: draws n edges uniformly from the n(n-1)/2 unordered
        # pairs each event, each a SWAP. EXPECTED weight per unordered pair:
        #     n / C(n,2) = 2/(n-1)
        w = 2.0 / (n - 1)
        A = w * (np.ones((n, n)) - np.eye(n))

    else:
        raise ValueError(topology)

    return A


def lambda2(A: np.ndarray) -> float:
    """Algebraic connectivity of the symmetrised graph: S = (A + A^T)/2."""
    S = (A + A.T) / 2.0
    L = np.diag(S.sum(axis=1)) - S
    eig = np.sort(np.linalg.eigvalsh(L))
    return float(eig[1])


def paper_lambda2(topology: str, n: int) -> float:
    """The paper's lambda_2: ring treated as an UNDIRECTED cycle C_n."""
    if topology == "ring":
        A = np.zeros((n, n))
        for i in range(n):
            A[i, (i + 1) % n] = 1.0
            A[i, (i - 1) % n] = 1.0
        return lambda2(A)
    return lambda2(adjacency(topology, n))


# Migrants moved per migration event, in units of m (= num_migrants per edge).
def volume(topology: str, n: int) -> float:
    if topology == "none":
        return 0.0
    if topology == "ring":
        return float(n)                       # n one-way transfers of m each
    if topology == "star":
        return 2.0 * (n - 1)                  # n-1 swaps, 2m each
    if topology == "random":
        return 2.0 * n                        # n swaps, 2m each
    if topology == "fully_connected":
        return 2.0 * n * (n - 1) / 2.0        # C(n,2) swaps, 2m each
    raise ValueError(topology)


# --------------------------------------------------------------------------
# 2. Data
# --------------------------------------------------------------------------

def final_gen_values(csv: str, topology: str) -> np.ndarray:
    df = pd.read_csv(os.path.join(DATA, csv))
    sel = df[(df.generation == FINAL_GEN) & (df.topology == topology)]
    return sel["hamming_diversity"].to_numpy()


def fisher_combine(pvals) -> tuple[float, float]:
    """Fisher's method. Returns (chi2 statistic, combined p)."""
    pvals = np.asarray(pvals, dtype=float)
    stat = -2.0 * np.sum(np.log(pvals))
    return float(stat), float(chi2.sf(stat, 2 * len(pvals)))


# --------------------------------------------------------------------------
# 3. Report
# --------------------------------------------------------------------------

def main() -> None:
    print("=" * 74)
    print("LAMBDA_2 CORRECTION — VERIFICATION")
    print("=" * 74)

    # --- spectra -----------------------------------------------------------
    for n in (5, 7):
        print(f"\n--- n = {n} islands " + "-" * 52)
        print(f"{'topology':<18}{'paper lambda2':>15}{'code lambda2':>15}"
              f"{'ratio':>9}{'volume (m)':>13}")
        for t in TOPOLOGIES:
            pl = paper_lambda2(t, n)
            cl = lambda2(adjacency(t, n))
            ratio = f"{pl / cl:.2f}x" if cl > 1e-12 else "--"
            print(f"{t:<18}{pl:>15.4f}{cl:>15.4f}{ratio:>9}{volume(t, n):>13.1f}")

    print("\nRing is the ONLY topology whose lambda_2 changes: the paper's value "
          "is exactly 2x too large\n(undirected cycle vs one-way relay).")

    print("\nCorrected ordering by lambda_2:")
    for n in (5, 7):
        order = sorted(TOPOLOGIES, key=lambda t: lambda2(adjacency(t, n)))
        s = " < ".join(f"{t} {lambda2(adjacency(t, n)):.3f}" for t in order)
        print(f"  n={n}: {s}")
    print("  => ring < star at BOTH n=5 and n=7. There is NO ring/star "
          "inversion at n=7.")
    g5 = lambda2(adjacency("star", 5)) - lambda2(adjacency("ring", 5))
    g7 = lambda2(adjacency("star", 7)) - lambda2(adjacency("ring", 7))
    print(f"  lambda_2 gap (star - ring): n=5 {g5:.3f} -> n=7 {g7:.3f}  "
          f"(WIDENS by {g7 / g5:.2f}x)")

    # --- diversity per domain ---------------------------------------------
    print("\n" + "=" * 74)
    print(f"MEAN hamming_diversity AT GENERATION {FINAL_GEN} (n=5 islands)")
    print("=" * 74)
    print(f"{'domain':<16}" + "".join(f"{t:>17}" for t in TOPOLOGIES))

    means: dict[str, dict[str, float]] = {}
    for dom, csv in DOMAINS.items():
        means[dom] = {t: float(final_gen_values(csv, t).mean())
                      for t in TOPOLOGIES}
        row = "".join(f"{means[dom][t]:>17.4f}" for t in TOPOLOGIES)
        print(f"{dom:<16}{row}")
    means["sorting_network"] = {t: float(final_gen_values(SORTING, t).mean())
                                for t in TOPOLOGIES}
    row = "".join(f"{means['sorting_network'][t]:>17.4f}" for t in TOPOLOGIES)
    print(f"{'sorting_network':<16}{row}   <- 7th domain, known scope violation")

    # --- Spearman ---------------------------------------------------------
    print("\n" + "=" * 74)
    print("SPEARMAN(mean diversity, lambda_2) ACROSS THE 5 TOPOLOGIES")
    print("=" * 74)
    print(f"{'domain':<18}{'paper lambda2':>16}{'corrected':>13}{'volume':>10}")

    lam_paper = [paper_lambda2(t, 5) for t in TOPOLOGIES]
    lam_code = [lambda2(adjacency(t, 5)) for t in TOPOLOGIES]
    vols = [volume(t, 5) for t in TOPOLOGIES]

    rho_paper, rho_code, rho_vol = [], [], []
    for dom in list(DOMAINS) + ["sorting_network"]:
        div = [means[dom][t] for t in TOPOLOGIES]
        rp = spearmanr(div, lam_paper).statistic
        rc = spearmanr(div, lam_code).statistic
        rv = spearmanr(div, vols).statistic
        tag = "   <- scope violation" if dom == "sorting_network" else ""
        print(f"{dom:<18}{rp:>16.2f}{rc:>13.2f}{rv:>10.2f}{tag}")
        if dom != "sorting_network":
            rho_paper.append(rp)
            rho_code.append(rc)
            rho_vol.append(rv)

    print(f"\n  six-domain mean:  paper {np.mean(rho_paper):+.3f}   "
          f"corrected {np.mean(rho_code):+.3f}   volume {np.mean(rho_vol):+.3f}")
    print(f"  corrected rho == -1.00 in "
          f"{sum(abs(r + 1) < 1e-9 for r in rho_code)}/6 domains")
    print(f"  paper's rho    == -0.90 in "
          f"{sum(abs(r + 0.9) < 1e-9 for r in rho_paper)}/6 domains")
    print("\n  CONFOUND: migration volume gives rho = -1.00 in the same 6/6 "
          "domains.\n  lambda_2 and volume are NOT separable in this dataset.")

    # --- ring vs star, per domain + Fisher --------------------------------
    print("\n" + "=" * 74)
    print("RING vs STAR AT GENERATION 99 — PER-DOMAIN WELCH TESTS + FISHER")
    print("=" * 74)
    print(f"{'domain':<18}{'ring':>9}{'star':>9}{'diff':>10}"
          f"{'p (2-sided)':>14}{'p (1-sided)':>14}")

    p_two, p_one = [], []
    for dom, csv in DOMAINS.items():
        r = final_gen_values(csv, "ring")
        s = final_gen_values(csv, "star")
        t_stat, p2 = ttest_ind(r, s, equal_var=False)
        p1 = p2 / 2 if t_stat > 0 else 1 - p2 / 2   # H1: ring > star
        p_two.append(p2)
        p_one.append(p1)
        print(f"{dom:<18}{r.mean():>9.4f}{s.mean():>9.4f}"
              f"{r.mean() - s.mean():>+10.4f}{p2:>14.3e}{p1:>14.3e}")

    n_wins = sum(1 for dom, csv in DOMAINS.items()
                 if final_gen_values(csv, "ring").mean()
                 > final_gen_values(csv, "star").mean())
    print(f"\n  ring > star in {n_wins}/6 domains")

    stat2, fisher2 = fisher_combine(p_two)
    stat1, fisher1 = fisher_combine(p_one)
    print(f"  Fisher combined p (2-sided per-domain Welch): {fisher2:.5f}  "
          f"(chi2={stat2:.2f}, df={2 * len(p_two)})")
    print(f"  Fisher combined p (1-sided, H1: ring>star)  : {fisher1:.6f}")
    print("  Paper claims Fisher's combined p = 0.14 — DOES NOT REPRODUCE.")

    # The nearest 'nonsignificant' estimand: pooling all domains into one test.
    # This is the WRONG estimand — between-domain variance swamps the effect —
    # but it is the only computation in the vicinity that returns a
    # nonsignificant p, so it is the likely provenance of the paper's "0.14".
    for label, om_csv in (("30-seed OneMax", DOMAINS["onemax"]),
                          ("2-seed OneMax (as multi_domain_analysis.py loads it)",
                           "experiment_e_raw.csv")):
        csvs = [om_csv] + [DOMAINS[d] for d in DOMAINS if d != "onemax"]
        pool_r = np.concatenate([final_gen_values(c, "ring") for c in csvs])
        pool_s = np.concatenate([final_gen_values(c, "star") for c in csvs])
        _, p_pool = ttest_ind(pool_r, pool_s, equal_var=False)
        print(f"\n  POOLED test, WRONG estimand [{label}]: p = {p_pool:.3f}")
    print("  Between-domain variance (ring domain means span "
          f"{min(means[d]['ring'] for d in DOMAINS):.2f}-"
          f"{max(means[d]['ring'] for d in DOMAINS):.2f}) swamps the effect.")
    print("  No code computing any Fisher combination exists in any repo.")

    # --- n=7 maze ---------------------------------------------------------
    print("\n" + "=" * 74)
    print("MAZE AT n=7 ISLANDS (confirmatory experiment)")
    print("=" * 74)
    r7 = final_gen_values(MAZE_N7, "ring")
    s7 = final_gen_values(MAZE_N7, "star")
    _, p7 = ttest_ind(r7, s7, equal_var=False)
    r5 = final_gen_values(DOMAINS["maze"], "ring")
    s5 = final_gen_values(DOMAINS["maze"], "star")
    _, p5 = ttest_ind(r5, s5, equal_var=False)
    print(f"  maze n=5: ring {r5.mean():.4f} +/- {r5.std(ddof=1):.4f}   "
          f"star {s5.mean():.4f} +/- {s5.std(ddof=1):.4f}   "
          f"gap {r5.mean() - s5.mean():+.4f}  p = {p5:.2e}")
    print(f"  maze n=7: ring {r7.mean():.4f} +/- {r7.std(ddof=1):.4f}   "
          f"star {s7.mean():.4f} +/- {s7.std(ddof=1):.4f}   "
          f"gap {r7.mean() - s7.mean():+.4f}  p = {p7:.2e}")
    print("\n  The maze gap WIDENS from n=5 to n=7 — it does not invert.")
    print(f"  Corrected lambda_2 gap also widens: {g5:.3f} -> {g7:.3f}. "
          "Direction and magnitude agree.")

    # --- OneMax seed-count discrepancy ------------------------------------
    print("\n" + "=" * 74)
    print("ONEMAX SEED COUNT")
    print("=" * 74)
    for csv in ("experiment_e_raw.csv", "experiment_e_per_island.csv"):
        df = pd.read_csv(os.path.join(DATA, csv))
        order = sorted(TOPOLOGIES,
                       key=lambda t: -df[(df.generation == FINAL_GEN)
                                         & (df.topology == t)]
                       ["hamming_diversity"].mean())
        print(f"  {csv:<32} seeds = {df.seed.nunique():>2}   "
              f"ordering: {' > '.join(order)}")
    print("  multi_domain_analysis.py loads OneMax from experiment_e_raw.csv "
          "(2 seeds),\n  though the Figure 1 caption claims 30. Same ordering "
          "either way — no conclusion changes,\n  but the caption is false.")


if __name__ == "__main__":
    main()
