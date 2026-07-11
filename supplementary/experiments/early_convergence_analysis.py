#!/usr/bin/env python3
"""
Early Convergence Analysis — Across All Completed Domains

Tests Claudius's hypothesis: Does ring topology establish its advantage
before generation 30? If so, the compositional structure (topology)
determines dynamics from the start, not through gradual divergence.

Analysis:
1. Diversity by topology at gen 10, 30, 99 (final)
2. Mann-Whitney tests: ring vs star, ring vs FC at each time point
3. Diversity trajectory plots per domain
4. Coupling onset generation: first gen where diversity drops below
   none-baseline by more than 1 SE
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os
import warnings
warnings.filterwarnings('ignore')

# ─── Configuration ────────────────────────────────────────────────────
EXPERIMENT_DIR = '/home/lyra/projects/categorical-evolution/experiments'
PLOT_DIR = os.path.join(EXPERIMENT_DIR, 'plots')
os.makedirs(PLOT_DIR, exist_ok=True)

# Domains to analyze (skip sorting_network: degenerate)
DOMAINS = {
    'maze': {'file': 'experiment_e_maze.csv', 'label': 'Maze'},
    'onemax': {'file': 'experiment_e_onemax.csv', 'label': 'OneMax'},
    'graph_coloring': {'file': 'experiment_e_graph_coloring.csv', 'label': 'Graph Coloring'},
    'knapsack': {'file': 'experiment_e_knapsack.csv', 'label': 'Knapsack'},
    'nothanks': {'file': 'experiment_e_nothanks.csv', 'label': 'No Thanks!'},
    'checkers': {'file': 'experiment_e_checkers.csv', 'label': 'Checkers'},
}

TOPOLOGIES = ['none', 'ring', 'star', 'random', 'fully_connected']
TOPO_COLORS = {
    'none': '#888888',
    'ring': '#e74c3c',
    'star': '#3498db',
    'random': '#2ecc71',
    'fully_connected': '#9b59b6',
}
TOPO_LABELS = {
    'none': 'None',
    'ring': 'Ring',
    'star': 'Star',
    'random': 'Random',
    'fully_connected': 'FC',
}

TIME_POINTS = [10, 30, 99]  # early, mid, final


def load_domain(domain_key):
    """Load a domain CSV and return DataFrame."""
    info = DOMAINS[domain_key]
    path = os.path.join(EXPERIMENT_DIR, info['file'])
    df = pd.read_csv(path)
    return df


def diversity_at_gen(df, gen, metric='hamming_diversity'):
    """Get diversity values per topology at a specific generation.
    Returns dict: topology -> array of diversity values (one per seed)."""
    gen_data = df[df['generation'] == gen]
    result = {}
    for topo in TOPOLOGIES:
        vals = gen_data[gen_data['topology'] == topo][metric].values
        if len(vals) > 0:
            result[topo] = vals
    return result


def mann_whitney_test(a, b):
    """Run Mann-Whitney U test, return (U, p, effect_size_r)."""
    if len(a) < 2 or len(b) < 2:
        return np.nan, np.nan, np.nan
    try:
        u_stat, p_val = stats.mannwhitneyu(a, b, alternative='two-sided')
        # Effect size r = Z / sqrt(N)
        n = len(a) + len(b)
        z = stats.norm.ppf(1 - p_val / 2) if p_val < 1 else 0
        r = z / np.sqrt(n)
        return u_stat, p_val, r
    except Exception:
        return np.nan, np.nan, np.nan


def cohens_d(a, b):
    """Compute Cohen's d effect size."""
    if len(a) < 2 or len(b) < 2:
        return np.nan
    na, nb = len(a), len(b)
    pooled_std = np.sqrt(((na - 1) * np.std(a, ddof=1)**2 + (nb - 1) * np.std(b, ddof=1)**2) / (na + nb - 2))
    if pooled_std == 0:
        return 0
    return (np.mean(a) - np.mean(b)) / pooled_std


def compute_coupling_onset(df, metric='hamming_diversity'):
    """For each topology, find the first generation where diversity drops below
    the none-topology baseline by more than 1 standard error.

    Returns dict: topology -> onset_generation (or None if never crosses)."""
    onsets = {}

    for topo in TOPOLOGIES:
        if topo == 'none':
            continue

        onset_gen = None
        for gen in range(df['generation'].max() + 1):
            none_vals = df[(df['topology'] == 'none') & (df['generation'] == gen)][metric].values
            topo_vals = df[(df['topology'] == topo) & (df['generation'] == gen)][metric].values

            if len(none_vals) < 2 or len(topo_vals) < 2:
                continue

            none_mean = np.mean(none_vals)
            none_se = np.std(none_vals, ddof=1) / np.sqrt(len(none_vals))
            topo_mean = np.mean(topo_vals)

            # Topology diversity drops below none - 1 SE
            if topo_mean < (none_mean - none_se):
                onset_gen = gen
                break

        onsets[topo] = onset_gen

    return onsets


def compute_diversity_trajectories(df, metric='hamming_diversity'):
    """Compute mean and SE of diversity over all generations per topology.
    Returns dict: topology -> (generations, means, ses)."""
    trajectories = {}
    all_gens = sorted(df['generation'].unique())

    for topo in TOPOLOGIES:
        topo_df = df[df['topology'] == topo]
        means = []
        ses = []
        gens_out = []

        for gen in all_gens:
            vals = topo_df[topo_df['generation'] == gen][metric].values
            if len(vals) > 0:
                means.append(np.mean(vals))
                ses.append(np.std(vals, ddof=1) / np.sqrt(len(vals)) if len(vals) > 1 else 0)
                gens_out.append(gen)

        trajectories[topo] = (np.array(gens_out), np.array(means), np.array(ses))

    return trajectories


def plot_diversity_trajectories(trajectories, domain_label, filename):
    """Plot diversity trajectories for all topologies with SE bands."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for topo in TOPOLOGIES:
        if topo not in trajectories:
            continue
        gens, means, ses = trajectories[topo]
        color = TOPO_COLORS[topo]
        label = TOPO_LABELS[topo]

        ax.plot(gens, means, color=color, label=label, linewidth=2)
        ax.fill_between(gens, means - ses, means + ses, color=color, alpha=0.15)

    # Mark time points
    for tp in TIME_POINTS:
        ax.axvline(x=tp, color='gray', linestyle='--', alpha=0.3, linewidth=1)
        ax.text(tp + 0.5, ax.get_ylim()[1] * 0.98, f'gen {tp}', fontsize=8,
                color='gray', va='top')

    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Hamming Diversity', fontsize=12)
    ax.set_title(f'Diversity Trajectories — {domain_label}', fontsize=14)
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 99)

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()


def plot_combined_early_vs_late(all_results, filename):
    """Plot a summary figure showing ring vs star and ring vs FC
    effect sizes at gen 10, 30, 99 across all domains."""
    domains_with_data = [d for d in all_results if all_results[d]['comparisons'] is not None]
    n_domains = len(domains_with_data)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax_idx, comparison in enumerate(['ring_vs_star', 'ring_vs_fc']):
        ax = axes[ax_idx]

        x = np.arange(len(TIME_POINTS))
        width = 0.8 / n_domains

        for i, domain in enumerate(domains_with_data):
            comp_data = all_results[domain]['comparisons']
            ds = []
            for tp in TIME_POINTS:
                key = f'{comparison}_gen{tp}'
                if key in comp_data and comp_data[key] is not None:
                    ds.append(comp_data[key]['cohens_d'])
                else:
                    ds.append(0)

            offset = (i - n_domains / 2 + 0.5) * width
            bars = ax.bar(x + offset, ds, width, label=DOMAINS[domain]['label'],
                         alpha=0.8)

        ax.set_xlabel('Generation', fontsize=12)
        ax.set_ylabel("Cohen's d (ring advantage)", fontsize=12)
        title = 'Ring vs Star' if comparison == 'ring_vs_star' else 'Ring vs FC'
        ax.set_title(f'{title} — Effect Size Over Time', fontsize=13)
        ax.set_xticks(x)
        ax.set_xticklabels([f'Gen {tp}' for tp in TIME_POINTS])
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.axhline(y=0.2, color='gray', linestyle=':', alpha=0.5, linewidth=1)
        ax.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, linewidth=1)
        ax.axhline(y=0.8, color='gray', linestyle=':', alpha=0.5, linewidth=1)
        ax.legend(fontsize=8, loc='best')
        ax.grid(True, axis='y', alpha=0.3)

    plt.suptitle('Early Convergence: Is Topology Ordering Established by Gen 30?',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()


def plot_coupling_onset(all_onsets, filename):
    """Bar chart of coupling onset generation by topology across domains."""
    domains_with_data = [d for d in all_onsets if all_onsets[d] is not None]
    coupled_topos = ['ring', 'star', 'random', 'fully_connected']
    n_domains = len(domains_with_data)

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(coupled_topos))
    width = 0.8 / n_domains

    for i, domain in enumerate(domains_with_data):
        onsets = all_onsets[domain]
        vals = []
        for topo in coupled_topos:
            v = onsets.get(topo)
            vals.append(v if v is not None else 100)  # 100 = never crossed

        offset = (i - n_domains / 2 + 0.5) * width
        ax.bar(x + offset, vals, width, label=DOMAINS[domain]['label'], alpha=0.8)

    ax.set_xlabel('Topology', fontsize=12)
    ax.set_ylabel('Coupling Onset Generation', fontsize=12)
    ax.set_title('Coupling Onset: First Gen Where Diversity < None - 1SE', fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels([TOPO_LABELS[t] for t in coupled_topos])
    ax.legend(fontsize=9, loc='best')
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_ylim(0, max(30, ax.get_ylim()[1]))

    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()


def analyze_ordering_stability(df, metric='hamming_diversity'):
    """Check if the topology ordering at gen 10, 30, 99 is the same.
    Returns the ranking at each time point."""
    rankings = {}
    for tp in TIME_POINTS:
        div_data = diversity_at_gen(df, tp, metric)
        means = {topo: np.mean(vals) for topo, vals in div_data.items() if len(vals) > 0}
        ranked = sorted(means.keys(), key=lambda t: means[t], reverse=True)
        rankings[tp] = ranked
    return rankings


def format_ranking(ranking):
    """Format a ranking list as a string."""
    return ' > '.join([TOPO_LABELS.get(t, t) for t in ranking])


# ═══════════════════════════════════════════════════════════════════════
# Main Analysis
# ═══════════════════════════════════════════════════════════════════════

def main():
    all_results = {}
    all_onsets = {}
    all_rankings = {}

    print("=" * 70)
    print("EARLY CONVERGENCE ANALYSIS — ALL DOMAINS")
    print("=" * 70)
    print()

    for domain_key, domain_info in DOMAINS.items():
        print(f"\n{'─' * 60}")
        print(f"  {domain_info['label'].upper()}")
        print(f"{'─' * 60}")

        df = load_domain(domain_key)
        n_seeds = df.groupby('topology')['seed'].nunique()
        print(f"  Seeds: {dict(n_seeds)}")

        # ─── Diversity at time points ─────────────────────────────────
        comparisons = {}
        print(f"\n  {'':>20} {'Gen 10':>12} {'Gen 30':>12} {'Gen 99':>12}")
        print(f"  {'':>20} {'─'*12} {'─'*12} {'─'*12}")

        for topo in TOPOLOGIES:
            means = []
            for tp in TIME_POINTS:
                div_data = diversity_at_gen(df, tp)
                if topo in div_data:
                    means.append(f"{np.mean(div_data[topo]):.4f}")
                else:
                    means.append("N/A")
            print(f"  {TOPO_LABELS[topo]:>20} {means[0]:>12} {means[1]:>12} {means[2]:>12}")

        # ─── Statistical tests ────────────────────────────────────────
        print(f"\n  Mann-Whitney Tests:")
        print(f"  {'Comparison':>25} {'Gen':>5} {'p-value':>10} {'Cohen d':>10} {'Sig':>5}")
        print(f"  {'─'*25} {'─'*5} {'─'*10} {'─'*10} {'─'*5}")

        for tp in TIME_POINTS:
            div_data = diversity_at_gen(df, tp)

            # Ring vs Star
            if 'ring' in div_data and 'star' in div_data:
                u, p, r = mann_whitney_test(div_data['ring'], div_data['star'])
                d = cohens_d(div_data['ring'], div_data['star'])
                sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
                print(f"  {'Ring vs Star':>25} {tp:>5} {p:>10.4f} {d:>10.3f} {sig:>5}")
                comparisons[f'ring_vs_star_gen{tp}'] = {'p': p, 'cohens_d': d, 'U': u}

            # Ring vs FC
            if 'ring' in div_data and 'fully_connected' in div_data:
                u, p, r = mann_whitney_test(div_data['ring'], div_data['fully_connected'])
                d = cohens_d(div_data['ring'], div_data['fully_connected'])
                sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
                print(f"  {'Ring vs FC':>25} {tp:>5} {p:>10.4f} {d:>10.3f} {sig:>5}")
                comparisons[f'ring_vs_fc_gen{tp}'] = {'p': p, 'cohens_d': d, 'U': u}

        all_results[domain_key] = {'comparisons': comparisons}

        # ─── Coupling onset ───────────────────────────────────────────
        onsets = compute_coupling_onset(df)
        all_onsets[domain_key] = onsets
        print(f"\n  Coupling Onset (gen where topo diversity < none - 1SE):")
        for topo in ['ring', 'star', 'random', 'fully_connected']:
            g = onsets.get(topo)
            print(f"    {TOPO_LABELS[topo]:>12}: gen {g}" if g is not None else f"    {TOPO_LABELS[topo]:>12}: never")

        # ─── Ordering stability ───────────────────────────────────────
        rankings = analyze_ordering_stability(df)
        all_rankings[domain_key] = rankings
        print(f"\n  Topology Ordering (highest diversity first):")
        for tp in TIME_POINTS:
            print(f"    Gen {tp:>3}: {format_ranking(rankings[tp])}")

        # Check if ordering is stable
        if rankings[10] == rankings[30] == rankings[99]:
            print(f"    ==> STABLE: Same ordering at all time points")
        elif rankings[10] == rankings[30]:
            print(f"    ==> Early-stable: Gen 10 = Gen 30, then shifts")
        elif rankings[30] == rankings[99]:
            print(f"    ==> Late-stable: Gen 30 = Gen 99, early differs")
        else:
            print(f"    ==> UNSTABLE: Different ordering at each time point")

        # ─── Diversity trajectories plot ──────────────────────────────
        trajectories = compute_diversity_trajectories(df)
        plot_file = os.path.join(PLOT_DIR, f'early_convergence_{domain_key}.png')
        plot_diversity_trajectories(trajectories, domain_info['label'], plot_file)
        print(f"\n  Plot saved: {plot_file}")

    # ═══════════════════════════════════════════════════════════════════
    # Combined analysis
    # ═══════════════════════════════════════════════════════════════════

    print(f"\n\n{'=' * 70}")
    print("COMBINED ANALYSIS")
    print(f"{'=' * 70}")

    # ─── Effect size evolution summary ────────────────────────────────
    print(f"\n  Cohen's d (Ring vs Star) across domains:")
    print(f"  {'Domain':>20} {'Gen 10':>10} {'Gen 30':>10} {'Gen 99':>10} {'Trend':>15}")
    print(f"  {'─'*20} {'─'*10} {'─'*10} {'─'*10} {'─'*15}")

    trends = []
    for domain_key in DOMAINS:
        comp = all_results[domain_key]['comparisons']
        ds = []
        for tp in TIME_POINTS:
            key = f'ring_vs_star_gen{tp}'
            if key in comp and comp[key] is not None:
                ds.append(comp[key]['cohens_d'])
            else:
                ds.append(np.nan)

        if not any(np.isnan(d) for d in ds):
            if ds[0] >= ds[2] * 0.8:
                trend = 'EARLY (stable)'
            elif ds[1] >= ds[2] * 0.8:
                trend = 'MID (by gen 30)'
            else:
                trend = 'LATE (growing)'
            trends.append(trend)
        else:
            trend = 'insufficient'
            trends.append(trend)

        ds_str = [f"{d:.3f}" if not np.isnan(d) else "N/A" for d in ds]
        print(f"  {DOMAINS[domain_key]['label']:>20} {ds_str[0]:>10} {ds_str[1]:>10} {ds_str[2]:>10} {trend:>15}")

    # ─── Coupling onset summary ───────────────────────────────────────
    print(f"\n  Coupling Onset Generation Summary:")
    print(f"  {'Domain':>20} {'Ring':>8} {'Star':>8} {'Random':>8} {'FC':>8}")
    print(f"  {'─'*20} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")

    for domain_key in DOMAINS:
        onsets = all_onsets[domain_key]
        vals = []
        for topo in ['ring', 'star', 'random', 'fully_connected']:
            g = onsets.get(topo)
            vals.append(f"{g}" if g is not None else "never")
        print(f"  {DOMAINS[domain_key]['label']:>20} {vals[0]:>8} {vals[1]:>8} {vals[2]:>8} {vals[3]:>8}")

    # ─── Ordering stability summary ──────────────────────────────────
    print(f"\n  Ordering Stability Summary:")
    stable_count = 0
    final_by_30 = 0  # gen 30 ordering matches gen 99 (final)
    for domain_key in DOMAINS:
        r = all_rankings[domain_key]
        label = DOMAINS[domain_key]['label']
        if r[10] == r[30] == r[99]:
            print(f"    {label}: STABLE across all time points")
            stable_count += 1
            final_by_30 += 1
        elif r[10] == r[30]:
            print(f"    {label}: Early ordering (gen 10 = gen 30), but shifts by gen 99")
        elif r[30] == r[99]:
            print(f"    {label}: FINAL ordering established by gen 30")
            final_by_30 += 1
        else:
            print(f"    {label}: UNSTABLE — ordering changes at each checkpoint")

    print(f"\n  ==> {final_by_30}/{len(DOMAINS)} domains: FINAL ordering established by gen 30")
    print(f"  ==> {stable_count}/{len(DOMAINS)} domains: ordering stable from gen 10 through gen 99")

    # ─── Key question ─────────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print("KEY QUESTION: Is the topology ordering established by generation 30?")
    print(f"{'=' * 70}")

    if final_by_30 >= len(DOMAINS) * 0.8:
        answer = "YES"
        detail = (
            f"In {final_by_30}/{len(DOMAINS)} domains, the FINAL topology ordering "
            f"is established by generation 30. This strongly supports the hypothesis "
            f"that compositional structure determines dynamics from the start."
        )
    elif final_by_30 >= len(DOMAINS) * 0.5:
        answer = "MOSTLY YES"
        detail = (
            f"In {final_by_30}/{len(DOMAINS)} domains, the FINAL topology ordering "
            f"is established by generation 30. The evidence is strong but not universal."
        )
    else:
        answer = "NO"
        detail = (
            f"Only {final_by_30}/{len(DOMAINS)} domains show the final ordering by gen 30. "
            f"The topology effect appears to develop gradually."
        )

    print(f"\n  ANSWER: {answer}")
    print(f"  {detail}")

    # ─── Combined plots ──────────────────────────────────────────────
    plot_combined_early_vs_late(all_results,
                                os.path.join(PLOT_DIR, 'early_convergence_combined.png'))
    print(f"\n  Combined plot: {os.path.join(PLOT_DIR, 'early_convergence_combined.png')}")

    plot_coupling_onset(all_onsets,
                        os.path.join(PLOT_DIR, 'coupling_onset_all_domains.png'))
    print(f"  Onset plot: {os.path.join(PLOT_DIR, 'coupling_onset_all_domains.png')}")

    # ─── Generate markdown report ─────────────────────────────────────
    generate_report(all_results, all_onsets, all_rankings, trends)

    print(f"\n  Report: {os.path.join(EXPERIMENT_DIR, 'early_convergence_results.md')}")
    print(f"\nDone.")


def generate_report(all_results, all_onsets, all_rankings, trends):
    """Write the full results to markdown."""
    report_path = os.path.join(EXPERIMENT_DIR, 'early_convergence_results.md')

    lines = []
    lines.append("# Early Convergence Analysis")
    lines.append("")
    lines.append(f"**Date:** 2026-03-18")
    lines.append(f"**Hypothesis:** Ring topology establishes its diversity advantage before generation 30.")
    lines.append(f"**Method:** Mann-Whitney tests + Cohen's d at gen 10, 30, 99 across 6 domains.")
    lines.append("")

    # ─── Summary table: Ring vs Star ──────────────────────────────────
    lines.append("## Ring vs Star: Cohen's d Over Time")
    lines.append("")
    lines.append("| Domain | Gen 10 | Gen 30 | Gen 99 | Trend |")
    lines.append("|--------|--------|--------|--------|-------|")

    for i, domain_key in enumerate(DOMAINS):
        comp = all_results[domain_key]['comparisons']
        row = [DOMAINS[domain_key]['label']]
        for tp in TIME_POINTS:
            key = f'ring_vs_star_gen{tp}'
            if key in comp and comp[key] is not None:
                d = comp[key]['cohens_d']
                p = comp[key]['p']
                sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
                row.append(f"{d:.3f}{sig}")
            else:
                row.append("N/A")
        row.append(trends[i] if i < len(trends) else '?')
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

    # ─── Summary table: Ring vs FC ────────────────────────────────────
    lines.append("## Ring vs FC: Cohen's d Over Time")
    lines.append("")
    lines.append("| Domain | Gen 10 | Gen 30 | Gen 99 | p (Gen 10) | p (Gen 99) |")
    lines.append("|--------|--------|--------|--------|------------|------------|")

    for domain_key in DOMAINS:
        comp = all_results[domain_key]['comparisons']
        row = [DOMAINS[domain_key]['label']]
        for tp in TIME_POINTS:
            key = f'ring_vs_fc_gen{tp}'
            if key in comp and comp[key] is not None:
                d = comp[key]['cohens_d']
                sig = '***' if comp[key]['p'] < 0.001 else '**' if comp[key]['p'] < 0.01 else '*' if comp[key]['p'] < 0.05 else ''
                row.append(f"{d:.3f}{sig}")
            else:
                row.append("N/A")
        # Add p-values for gen 10 and 99
        for tp in [10, 99]:
            key = f'ring_vs_fc_gen{tp}'
            if key in comp and comp[key] is not None:
                row.append(f"{comp[key]['p']:.4f}")
            else:
                row.append("N/A")
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

    # ─── Coupling onset table ─────────────────────────────────────────
    lines.append("## Coupling Onset Generation")
    lines.append("")
    lines.append("First generation where topology diversity drops below none-baseline by >1 SE.")
    lines.append("")
    lines.append("| Domain | Ring | Star | Random | FC |")
    lines.append("|--------|------|------|--------|----|")

    for domain_key in DOMAINS:
        onsets = all_onsets[domain_key]
        row = [DOMAINS[domain_key]['label']]
        for topo in ['ring', 'star', 'random', 'fully_connected']:
            g = onsets.get(topo)
            row.append(str(g) if g is not None else "never")
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

    # ─── Ordering stability ───────────────────────────────────────────
    lines.append("## Topology Ordering Stability")
    lines.append("")
    lines.append("| Domain | Gen 10 | Gen 30 | Gen 99 | Stable? |")
    lines.append("|--------|--------|--------|--------|---------|")

    for domain_key in DOMAINS:
        r = all_rankings[domain_key]
        label = DOMAINS[domain_key]['label']
        r10 = format_ranking(r[10])
        r30 = format_ranking(r[30])
        r99 = format_ranking(r[99])

        if r[10] == r[30] == r[99]:
            stable = "YES (all)"
        elif r[30] == r[99]:
            stable = "By gen 30"
        elif r[10] == r[30]:
            stable = "Early only"
        else:
            stable = "NO"

        lines.append(f"| {label} | {r10} | {r30} | {r99} | {stable} |")

    lines.append("")

    # ─── Key finding ──────────────────────────────────────────────────
    stable_count = sum(1 for dk in DOMAINS if all_rankings[dk][10] == all_rankings[dk][30] == all_rankings[dk][99])
    by_30_count = sum(1 for dk in DOMAINS if all_rankings[dk][30] == all_rankings[dk][99])

    lines.append("## Key Finding")
    lines.append("")
    lines.append(f"- **{stable_count}/{len(DOMAINS)}** domains show identical topology ordering at gen 10, 30, and 99.")
    lines.append(f"- **{by_30_count}/{len(DOMAINS)}** domains have ordering established by gen 30.")
    lines.append("")

    if by_30_count >= len(DOMAINS) * 0.8:
        lines.append("**Conclusion:** The topology ordering IS established by generation 30 in the vast majority ")
        lines.append("of domains. The compositional structure (migration topology) determines the diversity ")
        lines.append("dynamics from the earliest generations. This is consistent with the coupling onset ")
        lines.append("analysis — the phase transition happens early, and subsequent evolution preserves ")
        lines.append("the ordering established at that transition point.")
    elif by_30_count >= len(DOMAINS) * 0.5:
        lines.append("**Conclusion:** The topology ordering is MOSTLY established by generation 30, ")
        lines.append("though some domains show later shifts. The compositional structure has a strong ")
        lines.append("early effect, but domain-specific dynamics can modulate the ordering over time.")
    else:
        lines.append("**Conclusion:** The topology ordering is NOT reliably established by generation 30. ")
        lines.append("While topology has a measurable effect early, the ranking between topologies ")
        lines.append("evolves over time in domain-specific ways.")

    lines.append("")
    lines.append("## Plots")
    lines.append("")
    lines.append("- Per-domain trajectory plots: `plots/early_convergence_<domain>.png`")
    lines.append("- Combined effect size plot: `plots/early_convergence_combined.png`")
    lines.append("- Coupling onset bar chart: `plots/coupling_onset_all_domains.png`")
    lines.append("")

    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    main()
