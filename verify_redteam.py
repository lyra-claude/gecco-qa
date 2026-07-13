#!/usr/bin/env python3
"""Verify every number the red-team patch asks Lyra to quote on stage.

Run: python3 verify_redteam.py   (from the repo root)
Prints each claim with the recomputed value so the two can be compared by eye.
"""
import numpy as np
import pandas as pd
from scipy import stats

EXP = "supplementary/experiments"
TOPO = ["none", "ring", "star", "random", "fully_connected"]
FINAL_GEN = 99

# 30-seed files. OneMax's 30-seed run lives in experiment_e_per_island.csv;
# experiment_e_raw.csv is the 2-seed file the paper's analysis script loads.
DOMAINS = {
    "OneMax": "experiment_e_per_island.csv",
    "Maze": "experiment_e_maze.csv",
    "Knapsack": "experiment_e_knapsack.csv",
    "No Thanks!": "experiment_e_nothanks.csv",
    "Checkers": "experiment_e_checkers.csv",
    "Graph colouring": "experiment_e_graph_coloring.csv",
}
SORTING = "experiment_e_sorting_network.csv"


def final(fname):
    df = pd.read_csv(f"{EXP}/{fname}")
    return df[df.generation == FINAL_GEN]


def per_island_mean(df):
    cols = [c for c in df.columns if c.startswith("island_") and c.endswith("_diversity")]
    return df[cols].mean(axis=1)


print("=" * 72)
print("(5)/(6)  Pooled ANOVA of topology on final diversity, 30-seed OneMax")
print("=" * 72)
rows = []
for dom, f in DOMAINS.items():
    d = final(f)[["topology", "seed", "hamming_diversity"]].copy()
    d["domain"] = dom
    rows.append(d)
allf = pd.concat(rows)
print("n per domain/topology:\n", allf.groupby(["domain", "topology"]).size().unstack().to_string())


def anova(vals, groups):
    gs = [vals[groups == t] for t in TOPO]
    F, p = stats.f_oneway(*gs)
    grand = vals.mean()
    ssb = sum(len(g) * (g.mean() - grand) ** 2 for g in gs)
    sst = ((vals - grand) ** 2).sum()
    return F, p, ssb / sst, len(vals)


# z-scored within domain (the claimed 69.3% / F(4,895)=505)
z = allf.groupby("domain")["hamming_diversity"].transform(lambda x: (x - x.mean()) / x.std(ddof=1))
F, p, eta, n = anova(z.values, allf.topology.values)
print(f"\nZ-SCORED within domain : eta^2 = {eta*100:.1f}%   F(4,{n-5}) = {F:.1f}   p = {p:.2e}")

# domain-centred only (the referee's natural analysis: claimed 57.6%)
c = allf.groupby("domain")["hamming_diversity"].transform(lambda x: x - x.mean())
F2, p2, eta2, n2 = anova(c.values, allf.topology.values)
print(f"Domain-CENTRED only    : eta^2 = {eta2*100:.1f}%   F(4,{n2-5}) = {F2:.1f}")

# the old 2-seed number, for the record
rows2 = []
for dom, f in DOMAINS.items():
    fn = "experiment_e_raw.csv" if dom == "OneMax" else f
    d = final(fn)[["topology", "seed", "hamming_diversity"]].copy()
    d["domain"] = dom
    rows2.append(d)
old = pd.concat(rows2)
z_old = old.groupby("domain")["hamming_diversity"].transform(lambda x: (x - x.mean()) / x.std(ddof=1))
F3, p3, eta3, n3 = anova(z_old.values, old.topology.values)
print(f"OLD (2-seed OneMax)    : eta^2 = {eta3*100:.1f}%   F(4,{n3-5}) = {F3:.1f}   <- the retired number")

print()
print("=" * 72)
print("(5)  Paired none vs fully_connected, 30-seed OneMax")
print("=" * 72)
for label, frame in [("30-seed OneMax", allf), ("2-seed OneMax (old)", old)]:
    w = frame.pivot_table(index=["domain", "seed"], columns="topology", values="hamming_diversity")
    w = w.dropna(subset=["none", "fully_connected"])
    diff = (w["none"] - w["fully_connected"]).values
    dz = diff.mean() / diff.std(ddof=1)
    t, pt = stats.ttest_rel(w["none"], w["fully_connected"])
    print(f"{label:22s}: n_pairs={len(diff)}  mean diff = +{diff.mean():.4f}  dz = {dz:.2f}  p = {pt:.2e}")

print()
print("=" * 72)
print("(7)  Is the FIRST coupling the largest single drop in every domain?")
print("=" * 72)
steps = [("none->ring", "none", "ring"), ("ring->star", "ring", "star"),
         ("star->random", "star", "random"), ("random->FC", "random", "fully_connected")]
firsts, laters = [], []
for dom, f in DOMAINS.items():
    m = final(f).groupby("topology")["hamming_diversity"].mean()
    drops = {name: 100 * (m[a] - m[b]) / m[a] for name, a, b in steps}
    first = drops["none->ring"]
    rest = [v for k, v in drops.items() if k != "none->ring"]
    firsts.append(first)
    laters += rest
    flag = "OK " if first > max(rest) else "*** FIRST NOT LARGEST ***"
    print(f"{dom:16s} " + "  ".join(f"{k}={v:5.1f}%" for k, v in drops.items()) + f"   {flag}")
print(f"\nfirst-coupling drops: mean {np.mean(firsts):.1f}%  range {min(firsts):.1f}%-{max(firsts):.1f}%")
print(f"subsequent steps    : mean {np.mean(laters):.1f}%  median {np.median(laters):.1f}%  "
      f"range {min(laters):.1f}%-{max(laters):.1f}%   MAX = {max(laters):.1f}%")

print()
print("=" * 72)
print("(4)  Per-island (within-island) diversity: monotone in connectivity?")
print("=" * 72)
for dom, f in DOMAINS.items():
    d = final(f).copy()
    d["pi"] = per_island_mean(d)
    m = d.groupby("topology")["pi"].mean()
    order = " > ".join(m.sort_values(ascending=False).index)
    none_lowest = m.idxmin() == "none"
    coupled = m[["ring", "star", "random", "fully_connected"]]
    monotone = list(coupled.sort_values(ascending=False).index) == ["ring", "star", "random", "fully_connected"]
    print(f"{dom:16s} " + "  ".join(f"{t}={m[t]:.4f}" for t in TOPO))
    print(f"{'':16s} rank: {order}   none lowest: {none_lowest}   coupled monotone-in-connectivity: {monotone}")

print()
print("=" * 72)
print("(4)  Metapopulation (pooled hamming) ordering, for contrast")
print("=" * 72)
for dom, f in DOMAINS.items():
    m = final(f).groupby("topology")["hamming_diversity"].mean()
    print(f"{dom:16s} rank: " + " > ".join(m.sort_values(ascending=False).index))

print()
print("=" * 72)
print("(2)  Kendall's W over the six domains")
print("=" * 72)
R = np.array([final(f).groupby("topology")["hamming_diversity"].mean()[TOPO].rank(ascending=False).values
              for f in DOMAINS.values()])
m_, n_ = R.shape
S = ((R.sum(axis=0) - R.sum() / n_) ** 2).sum()
W = 12 * S / (m_ ** 2 * (n_ ** 3 - n_))
chi2 = m_ * (n_ - 1) * W
print(f"rank sums {R.sum(axis=0)}   W = {W:.3f}   chi2 = {chi2:.1f}  df = {n_-1}  "
      f"p = {stats.chi2.sf(chi2, n_-1):.2e}")
print(f"(ii) given a common ordering, P(it is the lambda2 ordering) = 1/120 = {1/120:.4f}")
print(f"joint = {stats.chi2.sf(chi2, n_-1) * (1/120):.2e}")

# 7 domains incl. sorting networks
D7 = dict(DOMAINS, **{"Sorting networks": SORTING})
R7 = np.array([final(f).groupby("topology")["hamming_diversity"].mean()[TOPO].rank(ascending=False).values
               for f in D7.values()])
m7, n7 = R7.shape
S7 = ((R7.sum(axis=0) - R7.sum() / n7) ** 2).sum()
W7 = 12 * S7 / (m7 ** 2 * (n7 ** 3 - n7))
print(f"W over 7 domains (incl. sorting networks) = {W7:.3f}")

print()
print("=" * 72)
print("(2)/(3)  Spearman(diversity, corrected lambda2) and (diversity, volume)")
print("=" * 72)
LAM = {"none": 0.0, "ring": 0.691, "star": 1.0, "random": 2.5, "fully_connected": 5.0}
VOL = {"none": 0, "ring": 5, "star": 8, "random": 10, "fully_connected": 20}
PAPER_LAM = {"none": 0.0, "ring": 1.382, "star": 1.0, "random": 2.5, "fully_connected": 5.0}
for dom, f in D7.items():
    m = final(f).groupby("topology")["hamming_diversity"].mean()[TOPO]
    r_l = stats.spearmanr(m.values, [LAM[t] for t in TOPO]).correlation
    r_v = stats.spearmanr(m.values, [VOL[t] for t in TOPO]).correlation
    r_p = stats.spearmanr(m.values, [PAPER_LAM[t] for t in TOPO]).correlation
    print(f"{dom:17s} corrected lambda2 {r_l:+.2f}   volume {r_v:+.2f}   paper lambda2 {r_p:+.2f}")

print()
print("=" * 72)
print("(4b)/(3b) Ring has 5 edges, star has 4 -- naive edge count predicts ring < star")
print("=" * 72)
print("ring (n=5): 5 directed edges, one-way.  star (n=5): 4 undirected swap edges.")
print("Migrants/event: ring = 5m (5 one-way);  star = 8m (4 edges x 2m).")

print()
print("=" * 72)
print("(4/10)  Sorting networks: the degradation")
print("=" * 72)
sn = final(SORTING)
m = sn.groupby("topology")["hamming_diversity"].mean()[TOPO]
print("means: " + "  ".join(f"{t}={m[t]:.4f}" for t in TOPO))
print(f"star ({m['star']:.4f}) > ring ({m['ring']:.4f})? {m['star'] > m['ring']}  <- opposite to prediction")
gs = [sn[sn.topology == t]["hamming_diversity"] for t in TOPO]
F, p = stats.f_oneway(*gs)
print(f"one-way ANOVA topology: F(4,{len(sn)-5}) = {F:.2f}, p = {p:.4f}")
print(f"spread across 5 topologies (max-min of means) = {m.max()-m.min():.4f}")
mz = final(DOMAINS["Maze"]).groupby("topology")["hamming_diversity"].mean()
print(f"maze spread = {mz.max()-mz.min():.4f}   ratio = {(mz.max()-mz.min())/(m.max()-m.min()):.1f}x")
t, prs = stats.ttest_ind(sn[sn.topology == "ring"]["hamming_diversity"],
                         sn[sn.topology == "star"]["hamming_diversity"], equal_var=False)
print(f"ring vs star (Welch) p = {prs:.3f}")

print()
print("=" * 72)
print("(2)  Ring vs star across the six domains: Fisher combination")
print("=" * 72)
ps, wins = [], 0
for dom, f in DOMAINS.items():
    d = final(f)
    r = d[d.topology == "ring"]["hamming_diversity"]
    s = d[d.topology == "star"]["hamming_diversity"]
    t, p = stats.ttest_ind(r, s, equal_var=False)
    ps.append(p)
    wins += r.mean() > s.mean()
    print(f"{dom:16s} ring={r.mean():.4f} star={s.mean():.4f} diff=+{r.mean()-s.mean():.4f} p={p:.3f}")
chi, pf = stats.combine_pvalues(ps, method="fisher")
print(f"\nring > star in {wins}/6.  Fisher chi2 = {chi:.2f}, df = 12, combined p = {pf:.4f}")
