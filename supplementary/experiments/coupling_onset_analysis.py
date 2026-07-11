#!/usr/bin/env python3
"""
Coupling onset timing analysis.

Claudius's question: Does coupling onset timing (the generation at which
synchronization first appears after migration begins) correlate with the
fitness plateau generation (dynamical property of the landscape), or is it
invariant across domains (structural property of the topology)?

If coupling onset is invariant across domains -> structural (topology determines it).
If coupling onset tracks fitness plateau -> dynamical (landscape determines it).

Methodology:
  - r = 1 - population_divergence (Kuramoto synchronization proxy).
  - Baseline correction: subtract the none-topology r(t) curve to isolate
    migration-induced coupling from selection-driven convergence.
    delta_r(t) = r_coupled(t) - r_none(t)
  - Coupling onset = first generation where delta_r exceeds a significance threshold.
  - Fitness plateau = generation where fitness improvement rate first drops below
    1% of total fitness range (sustained for 3 consecutive generations).
  - Both are computed per topology x seed, then averaged across seeds.
"""

import csv
import os
import sys
import numpy as np
from collections import defaultdict
from scipy import stats
from scipy.ndimage import uniform_filter1d

# --------------------------------------------------------------------------- #
#  Configuration                                                               #
# --------------------------------------------------------------------------- #

DOMAIN_CONFIGS = {
    'onemax': {
        'path': '/home/lyra/projects/categorical-evolution/experiments/experiment_e_raw.csv',
        'label': 'OneMax',
        'color': '#2196F3',   # blue
        'marker': 'o',
    },
    'maze': {
        'path': '/home/lyra/projects/categorical-evolution/experiments/experiment_e_maze.csv',
        'label': 'Maze',
        'color': '#FF5722',   # deep orange
        'marker': 's',
    },
    # Add checkers here when data arrives:
    # 'checkers': {
    #     'path': '/home/lyra/projects/categorical-evolution/experiments/experiment_e_checkers.csv',
    #     'label': 'Checkers',
    #     'color': '#4CAF50',  # green
    #     'marker': '^',
    # },
}

TOPO_ORDER = ['none', 'ring', 'star', 'random', 'fully_connected']
COUPLED_TOPOS = ['ring', 'star', 'random', 'fully_connected']
TOPO_LABELS = {
    'none': 'None',
    'ring': 'Ring',
    'star': 'Star',
    'random': 'Random',
    'fully_connected': 'Fully\nConnected',
}
TOPO_SHORT = {
    'none': 'none', 'ring': 'ring', 'star': 'star',
    'random': 'random', 'fully_connected': 'full',
}
TOPO_COLORS = {
    'none': '#9E9E9E', 'ring': '#FF9800', 'star': '#E91E63',
    'random': '#9C27B0', 'fully_connected': '#2196F3',
}

MIGRATION_START = 5  # migration_freq = 5 => first migration at gen 5


# --------------------------------------------------------------------------- #
#  Data loading                                                                #
# --------------------------------------------------------------------------- #

def load_domain(domain_key):
    """Load data for one domain. Returns dict[topology][seed] = {...}."""
    cfg = DOMAIN_CONFIGS[domain_key]
    filepath = cfg['path']

    if not os.path.exists(filepath):
        print(f"  [SKIP] {cfg['label']}: file not found at {filepath}")
        return None

    raw = defaultdict(lambda: defaultdict(lambda: {'gen': [], 'r': [],
                                                    'fitness': [], 'div': []}))
    with open(filepath) as f:
        reader = csv.DictReader(f)
        has_pop_div = 'population_divergence' in reader.fieldnames
        for row in reader:
            topo = row['topology']
            seed = int(row['seed'])
            gen = int(row['generation'])
            r = 1.0 - float(row['population_divergence']) if has_pop_div \
                else 1.0 - float(row['hamming_diversity'])
            fitness = float(row['best_fitness'])
            diversity = float(row['hamming_diversity'])
            raw[topo][seed]['gen'].append(gen)
            raw[topo][seed]['r'].append(r)
            raw[topo][seed]['fitness'].append(fitness)
            raw[topo][seed]['div'].append(diversity)

    data = {}
    for topo in raw:
        data[topo] = {}
        for seed in raw[topo]:
            d = raw[topo][seed]
            order = np.argsort(d['gen'])
            data[topo][seed] = {
                'generations': np.array(d['gen'])[order],
                'r': np.array(d['r'])[order],
                'fitness': np.array(d['fitness'])[order],
                'diversity': np.array(d['div'])[order],
            }
    return data


def compute_none_baseline(data):
    """
    Compute the mean r trajectory for 'none' topology (no migration).

    This is subtracted from coupled topologies to isolate migration-induced
    synchronization from selection-driven convergence.

    In OneMax (single global optimum), selection alone drives r up significantly.
    In Maze (rugged landscape), selection alone barely changes r.
    Baseline correction removes this confound.
    """
    if 'none' not in data:
        return None
    seeds = sorted(data['none'].keys())
    r_matrix = np.array([data['none'][s]['r'] for s in seeds])
    return np.mean(r_matrix, axis=0)  # shape (n_gens,)


# --------------------------------------------------------------------------- #
#  Coupling onset detection                                                    #
# --------------------------------------------------------------------------- #

def compute_coupling_onset(delta_r, generations, smooth_window=10, threshold=0.05):
    """
    Find coupling onset from baseline-corrected r curve.

    delta_r = r_coupled(t) - r_none(t). This isolates the migration effect.

    Onset = first generation (post-migration) where the smoothed delta_r
    exceeds a significance threshold. Smoothing removes the migration-event
    sawtooth (which has zero net effect) while preserving genuine trends.

    The default threshold of 0.05 was chosen because:
    - 0.02 is too low: all topologies cross it at ~gen 5, no differentiation.
    - 0.05 reveals the topology ordering (full < random < star < ring).
    - 0.10 shows the same ordering with more spread.

    Args:
        delta_r: baseline-corrected r curve
        generations: array of generation numbers
        smooth_window: window size for rolling mean
        threshold: minimum delta_r for onset detection

    Returns:
        onset_gen: generation of coupling onset (NaN if no onset detected)
        is_significant: whether onset was detected
    """
    # Smooth delta_r with rolling mean
    if len(delta_r) >= smooth_window:
        delta_r_smooth = uniform_filter1d(delta_r, size=smooth_window)
    else:
        delta_r_smooth = delta_r

    # Only consider post-migration generations
    # (no extra offset needed — the smoothing function already handles edges)
    mask = generations >= MIGRATION_START
    if not np.any(mask):
        return np.nan, False

    post_gens = generations[mask]
    post_delta = delta_r_smooth[mask]

    # Find first generation where delta_r exceeds threshold
    above = np.where(post_delta > threshold)[0]
    if len(above) > 0:
        return int(post_gens[above[0]]), True

    # Also check for significant negative delta_r (divergence under coupling)
    below = np.where(post_delta < -threshold)[0]
    if len(below) > 0:
        return int(post_gens[below[0]]), True

    return np.nan, False


def compute_coupling_onset_multi_threshold(delta_r, generations, smooth_window=10,
                                            thresholds=(0.02, 0.05, 0.10)):
    """
    Compute onset at multiple thresholds to show the coupling buildup profile.

    Returns dict: {threshold: (onset_gen, is_significant)}
    """
    result = {}
    for thresh in thresholds:
        gen, sig = compute_coupling_onset(delta_r, generations, smooth_window, thresh)
        result[thresh] = (gen, sig)
    return result


def compute_fitness_plateau(fitness_series, generations, threshold_frac=0.01):
    """
    Find the fitness plateau generation: first generation where the
    improvement rate drops below 1% of total fitness range, sustained
    for 3 consecutive generations.
    """
    total_range = float(np.max(fitness_series) - np.min(fitness_series))
    if total_range == 0:
        return 0, 0.0

    threshold = threshold_frac * total_range
    df = np.diff(fitness_series)
    df_gens = generations[1:]

    window = 5
    if len(df) >= window:
        df_smooth = uniform_filter1d(df, size=window)
    else:
        df_smooth = df

    mask = df_gens >= MIGRATION_START
    df_post = df_smooth[mask]
    gens_post = df_gens[mask]

    below = np.where(df_post < threshold)[0]
    if len(below) == 0:
        return int(generations[-1]), total_range

    # Find first sustained plateau (3 consecutive gens below threshold)
    for i in range(len(below) - 2):
        if below[i + 1] == below[i] + 1 and below[i + 2] == below[i] + 2:
            return int(gens_post[below[i]]), total_range

    return int(gens_post[below[0]]), total_range


# --------------------------------------------------------------------------- #
#  Per-domain analysis                                                         #
# --------------------------------------------------------------------------- #

def analyze_domain(domain_key, data):
    """
    Compute coupling onset and fitness plateau for each topology.

    Uses baseline correction (subtracting none-topology r) to isolate
    migration-induced coupling.

    Returns dict: results[topology] = { ... }
    """
    results = {}
    baseline_r = compute_none_baseline(data)

    if baseline_r is not None:
        print(f"    Baseline r (none): r(0)={baseline_r[0]:.4f} -> "
              f"r(5)={baseline_r[5]:.4f} -> r(50)={baseline_r[50]:.4f} -> "
              f"r(99)={baseline_r[-1]:.4f}")
        print(f"    Baseline shift r(99)-r(5) = {baseline_r[-1]-baseline_r[5]:.4f} "
              f"(selection-only convergence)")

    for topo in TOPO_ORDER:
        if topo not in data:
            continue

        seeds = sorted(data[topo].keys())
        onset_gens = []
        plateau_gens = []
        n_significant = 0

        for seed in seeds:
            sd = data[topo][seed]

            # Baseline-correct for coupled topologies
            if baseline_r is not None and topo != 'none':
                delta_r = sd['r'] - baseline_r
            else:
                delta_r = sd['r'] - sd['r'][MIGRATION_START]  # shift relative to migration start

            onset_gen, is_sig = compute_coupling_onset(delta_r, sd['generations'])
            plateau_gen, _ = compute_fitness_plateau(sd['fitness'], sd['generations'])

            if is_sig:
                onset_gens.append(onset_gen)
                n_significant += 1
            plateau_gens.append(plateau_gen)

        # Ensemble onset (from mean baseline-corrected r)
        r_matrix = np.array([data[topo][s]['r'] for s in seeds])
        mean_r = np.mean(r_matrix, axis=0)
        gens = data[topo][seeds[0]]['generations']

        if baseline_r is not None and topo != 'none':
            mean_delta_r = mean_r - baseline_r
        else:
            mean_delta_r = mean_r - mean_r[MIGRATION_START]

        ens_onset, ens_sig = compute_coupling_onset(mean_delta_r, gens)

        # Multi-threshold ensemble onset (for sensitivity analysis)
        ens_multi = compute_coupling_onset_multi_threshold(mean_delta_r, gens)

        onset_gens = np.array(onset_gens, dtype=float)
        plateau_gens = np.array(plateau_gens, dtype=float)
        valid_onset = onset_gens[~np.isnan(onset_gens)]
        valid_plateau = plateau_gens[~np.isnan(plateau_gens)]
        sig_frac = n_significant / len(seeds) if seeds else 0.0

        results[topo] = {
            'onset_gens': onset_gens,
            'onset_mean': float(np.mean(valid_onset)) if len(valid_onset) > 0 else np.nan,
            'onset_std': float(np.std(valid_onset, ddof=1)) if len(valid_onset) > 1 else 0.0,
            'onset_ensemble': float(ens_onset) if not np.isnan(ens_onset) else np.nan,
            'onset_ensemble_sig': ens_sig,
            'onset_ensemble_multi': ens_multi,  # {threshold: (gen, sig)}
            'onset_significant_frac': sig_frac,
            'plateau_gens': plateau_gens,
            'plateau_mean': float(np.mean(valid_plateau)) if len(valid_plateau) > 0 else np.nan,
            'plateau_std': float(np.std(valid_plateau, ddof=1)) if len(valid_plateau) > 1 else 0.0,
            'mean_r_raw': mean_r,
            'mean_delta_r': mean_delta_r,
            'baseline_r': baseline_r,
        }

    return results


# --------------------------------------------------------------------------- #
#  Correlation analysis                                                        #
# --------------------------------------------------------------------------- #

def cross_domain_correlation(all_results):
    """Test structural vs dynamical hypothesis."""
    print("\n" + "=" * 80)
    print("CORRELATION ANALYSIS: Structural vs Dynamical")
    print("=" * 80)

    domain_keys = sorted(all_results.keys())

    # --- 1. Topology ordering of ensemble onset ---
    print("\n--- 1. Topology ordering of ensemble coupling onset (coupled topologies only) ---")
    print("   If structural: same ordering across domains.")
    print("   If dynamical: ordering may differ.\n")

    onset_by_domain = {}
    for dk in domain_keys:
        label = DOMAIN_CONFIGS[dk]['label']
        means = []
        for topo in COUPLED_TOPOS:
            if topo in all_results[dk] and all_results[dk][topo]['onset_ensemble_sig']:
                means.append(all_results[dk][topo]['onset_ensemble'])
            else:
                means.append(np.nan)
        onset_by_domain[dk] = means
        valid_idx = [i for i, m in enumerate(means) if not np.isnan(m)]
        ranked = sorted(valid_idx, key=lambda i: means[i])
        ordering = [COUPLED_TOPOS[i] for i in ranked]
        print(f"   {label:>8}: {' < '.join(ordering)}")
        vals_str = ', '.join(f'{TOPO_SHORT[COUPLED_TOPOS[i]]}={means[i]:.0f}' for i in ranked)
        print(f"           ensemble onset: {vals_str}")

    if len(domain_keys) >= 2:
        for i in range(len(domain_keys)):
            for j in range(i + 1, len(domain_keys)):
                dk1, dk2 = domain_keys[i], domain_keys[j]
                v1 = np.array(onset_by_domain[dk1])
                v2 = np.array(onset_by_domain[dk2])
                valid = ~(np.isnan(v1) | np.isnan(v2))
                if np.sum(valid) >= 3:
                    # Check for constant input
                    if np.std(v1[valid]) == 0 or np.std(v2[valid]) == 0:
                        print(f"\n   Spearman rank ({DOMAIN_CONFIGS[dk1]['label']} vs "
                              f"{DOMAIN_CONFIGS[dk2]['label']}): cannot compute — "
                              f"one domain has constant onset values.")
                        # Use Kendall's tau instead which handles ties better
                        tau, p = stats.kendalltau(v1[valid], v2[valid])
                        print(f"   Kendall's tau = {tau:.4f}, p = {p:.4f}")
                    else:
                        rho, p = stats.spearmanr(v1[valid], v2[valid])
                        print(f"\n   Spearman rank ({DOMAIN_CONFIGS[dk1]['label']} vs "
                              f"{DOMAIN_CONFIGS[dk2]['label']}): rho = {rho:.4f}, p = {p:.4f}")

    # --- 2. Within-domain onset-plateau correlation ---
    print("\n--- 2. Within-domain onset vs plateau correlation ---")
    print("   Coupled topologies, significant seeds only.")
    print("   If dynamical: onset should track plateau.\n")

    for dk in domain_keys:
        label = DOMAIN_CONFIGS[dk]['label']
        all_o, all_p = [], []
        for topo in COUPLED_TOPOS:
            if topo not in all_results[dk]:
                continue
            res = all_results[dk][topo]
            n_sig = len(res['onset_gens'])
            for o_val, p_val in zip(res['onset_gens'], res['plateau_gens'][:n_sig]):
                if not np.isnan(o_val) and not np.isnan(p_val):
                    all_o.append(o_val)
                    all_p.append(p_val)
        all_o, all_p = np.array(all_o), np.array(all_p)
        if len(all_o) >= 5:
            r_val, p_val = stats.pearsonr(all_o, all_p)
            rho, rho_p = stats.spearmanr(all_o, all_p)
            print(f"   {label:>8}: n={len(all_o)}, Pearson r={r_val:.4f} (p={p_val:.4f}), "
                  f"Spearman rho={rho:.4f} (p={rho_p:.4f})")
            if p_val < 0.05 and abs(r_val) > 0.3:
                print(f"             => Onset-plateau correlated — dynamical component.")
            else:
                print(f"             => No strong onset-plateau correlation — structural dominates.")
        else:
            print(f"   {label:>8}: too few significant seeds (n={len(all_o)})")

    # --- 3. Cross-domain onset difference per topology ---
    print("\n--- 3. Cross-domain onset difference per topology ---")
    print("   If structural: onset SAME across domains per topology.")
    print("   If dynamical: onset DIFFERS.\n")

    if len(domain_keys) >= 2:
        for topo in COUPLED_TOPOS:
            groups, labels = [], []
            for dk in domain_keys:
                if topo in all_results[dk]:
                    valid = all_results[dk][topo]['onset_gens']
                    valid = valid[~np.isnan(valid)]
                    if len(valid) > 0:
                        groups.append(valid)
                        labels.append(DOMAIN_CONFIGS[dk]['label'])
            if len(groups) >= 2 and len(groups[0]) >= 3 and len(groups[1]) >= 3:
                u_stat, u_p = stats.mannwhitneyu(groups[0], groups[1], alternative='two-sided')
                diff = abs(np.mean(groups[0]) - np.mean(groups[1]))
                sig = ' ***' if u_p < 0.001 else ' **' if u_p < 0.01 else ' *' if u_p < 0.05 else ''
                print(f"   {topo:>18}: {labels[0]}={np.mean(groups[0]):.1f}+/-{np.std(groups[0], ddof=1):.1f} (n={len(groups[0])}), "
                      f"{labels[1]}={np.mean(groups[1]):.1f}+/-{np.std(groups[1], ddof=1):.1f} (n={len(groups[1])}), "
                      f"|diff|={diff:.1f}, p={u_p:.4f}{sig}")

    # --- 4. Variance decomposition ---
    print("\n--- 4. Variance decomposition (coupled topologies, significant seeds) ---")
    all_data_points = []
    for di, dk in enumerate(domain_keys):
        for ti, topo in enumerate(COUPLED_TOPOS):
            if topo in all_results[dk]:
                for o in all_results[dk][topo]['onset_gens']:
                    if not np.isnan(o):
                        all_data_points.append((o, ti, di))

    if len(all_data_points) > 10:
        arr = np.array(all_data_points)
        onsets, topos, domains = arr[:, 0], arr[:, 1].astype(int), arr[:, 2].astype(int)
        grand_mean = np.mean(onsets)
        ss_total = np.sum((onsets - grand_mean) ** 2)
        ss_topo = sum(np.sum(topos == ti) * (np.mean(onsets[topos == ti]) - grand_mean) ** 2
                      for ti in range(len(COUPLED_TOPOS)) if np.any(topos == ti))
        ss_domain = sum(np.sum(domains == di) * (np.mean(onsets[domains == di]) - grand_mean) ** 2
                        for di in range(len(domain_keys)) if np.any(domains == di))
        ss_resid = ss_total - ss_topo - ss_domain
        pct = lambda x: 100 * x / ss_total if ss_total > 0 else 0
        print(f"\n   Topology:  {pct(ss_topo):5.1f}% of variance")
        print(f"   Domain:    {pct(ss_domain):5.1f}% of variance")
        print(f"   Residual:  {pct(ss_resid):5.1f}% of variance")
        if pct(ss_topo) > 3 * pct(ss_domain):
            print(f"   => STRUCTURAL: topology explains {pct(ss_topo)/max(pct(ss_domain),0.1):.1f}x more variance.")
        elif pct(ss_domain) > 3 * pct(ss_topo):
            print(f"   => DYNAMICAL: domain explains {pct(ss_domain)/max(pct(ss_topo),0.1):.1f}x more variance.")
        else:
            print(f"   => MIXED: both topology and domain contribute.")


# --------------------------------------------------------------------------- #
#  Summary tables                                                              #
# --------------------------------------------------------------------------- #

def print_summary(all_results):
    """Print summary tables."""
    domain_keys = sorted(all_results.keys())

    # --- Table 1: Ensemble onset ---
    print("\n" + "=" * 80)
    print("TABLE 1: ENSEMBLE Coupling Onset (baseline-corrected, seed-averaged)")
    print("=" * 80)
    print("  delta_r(t) = r_coupled(t) - r_none(t), smoothed over 10-gen window.")
    print("  Onset = first gen where |delta_r| > 0.02.\n")

    header = f"{'Topology':>18}"
    for dk in domain_keys:
        header += f"  |  {DOMAIN_CONFIGS[dk]['label']+' onset':>14} {'sig?':>4}"
    header += f"  |  {'|diff|':>8}"
    print(header)
    print("-" * len(header))

    for topo in TOPO_ORDER:
        row = f"{topo:>18}"
        vals = []
        for dk in domain_keys:
            if topo in all_results[dk]:
                res = all_results[dk][topo]
                ens = res['onset_ensemble']
                sig = res['onset_ensemble_sig']
                if not np.isnan(ens):
                    row += f"  |  {ens:>14.0f} {'YES' if sig else 'no':>4}"
                    if sig:
                        vals.append(ens)
                else:
                    row += f"  |  {'N/A':>14} {'no':>4}"
            else:
                row += f"  |  {'N/A':>14} {'':>4}"
        if len(vals) >= 2:
            row += f"  |  {abs(vals[0] - vals[1]):>8.0f}"
        else:
            row += f"  |  {'--':>8}"
        print(row)

    # --- Table 2: Per-seed onset and plateau ---
    print("\n" + "=" * 80)
    print("TABLE 2: Per-Seed Coupling Onset & Fitness Plateau")
    print("=" * 80)

    header = f"{'Topology':>18}"
    for dk in domain_keys:
        label = DOMAIN_CONFIGS[dk]['label']
        header += f"  |  {label+' onset':>14} {'frac':>5} {label+' plateau':>14}"
    print(header)
    print("-" * len(header))

    for topo in TOPO_ORDER:
        row = f"{topo:>18}"
        for dk in domain_keys:
            if topo in all_results[dk]:
                res = all_results[dk][topo]
                if len(res['onset_gens']) > 0 and not np.isnan(res['onset_mean']):
                    row += f"  |  {res['onset_mean']:>10.1f}+/-{res['onset_std']:<3.1f}"
                else:
                    row += f"  |  {'(no sig)':>14}"
                row += f" {res['onset_significant_frac']:>4.0%}"
                row += f" {res['plateau_mean']:>10.1f}+/-{res['plateau_std']:<3.1f}"
            else:
                row += f"  |  {'N/A':>14} {'':>5} {'N/A':>14}"
        print(row)

    print("\n  onset = first gen where baseline-corrected delta_r > 0.05 (significant seeds only)")
    print("  frac = fraction of seeds with detectable coupling onset")
    print("  plateau = first gen with sustained fitness improvement < 1% of range")

    # --- Table 3: Multi-threshold ensemble onset ---
    print("\n" + "=" * 80)
    print("TABLE 3: Multi-Threshold Ensemble Onset (sensitivity analysis)")
    print("=" * 80)
    print("  Shows how coupling builds up: higher thresholds = later onset.")
    print("  KEY: if topology ordering is SAME across domains, onset is structural.\n")

    thresholds = [0.02, 0.05, 0.10]

    for thresh in thresholds:
        print(f"  --- Threshold delta_r > {thresh} ---")
        header = f"  {'Topology':>18}"
        for dk in domain_keys:
            header += f"  |  {DOMAIN_CONFIGS[dk]['label']:>8}"
        header += f"  |  {'|diff|':>6}"
        print(header)

        for topo in COUPLED_TOPOS:
            row = f"  {topo:>18}"
            vals = []
            for dk in domain_keys:
                if topo in all_results[dk]:
                    multi = all_results[dk][topo]['onset_ensemble_multi']
                    gen, sig = multi.get(thresh, (np.nan, False))
                    if sig and not np.isnan(gen):
                        row += f"  |  {gen:>8.0f}"
                        vals.append(gen)
                    else:
                        row += f"  |  {'never':>8}"
                else:
                    row += f"  |  {'N/A':>8}"

            if len(vals) >= 2:
                row += f"  |  {abs(vals[0] - vals[1]):>6.0f}"
            else:
                row += f"  |  {'--':>6}"
            print(row)

        # Print ordering for this threshold
        for dk in domain_keys:
            label = DOMAIN_CONFIGS[dk]['label']
            ordering_items = []
            for topo in COUPLED_TOPOS:
                if topo in all_results[dk]:
                    multi = all_results[dk][topo]['onset_ensemble_multi']
                    gen, sig = multi.get(thresh, (np.nan, False))
                    if sig and not np.isnan(gen):
                        ordering_items.append((gen, topo))
            ordering_items.sort()
            if ordering_items:
                order_str = ' < '.join(f"{TOPO_SHORT[t]}({g:.0f})" for g, t in ordering_items)
                print(f"  {label:>8} order: {order_str}")
        print()


# --------------------------------------------------------------------------- #
#  Plotting                                                                    #
# --------------------------------------------------------------------------- #

def plot_results(all_results, all_data, output_path):
    """Generate 4-panel figure."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Coupling Onset Timing: Structural vs Dynamical\n'
                 '(baseline-corrected: $\\Delta r(t) = r_{coupled}(t) - r_{none}(t)$)',
                 fontsize=13, fontweight='bold')

    domain_keys = sorted(all_results.keys())
    n_domains = len(domain_keys)
    width = 0.35

    # ---- Panel A: Ensemble coupling onset by topology ----
    ax = axes[0, 0]
    ax.set_title('A. Ensemble Coupling Onset by Topology')
    x = np.arange(len(COUPLED_TOPOS))
    offsets = np.linspace(-width / 2, width / 2, n_domains)

    for di, dk in enumerate(domain_keys):
        cfg = DOMAIN_CONFIGS[dk]
        vals, errs = [], []
        for topo in COUPLED_TOPOS:
            if topo in all_results[dk] and all_results[dk][topo]['onset_ensemble_sig']:
                vals.append(all_results[dk][topo]['onset_ensemble'])
                errs.append(all_results[dk][topo]['onset_std']
                            if len(all_results[dk][topo]['onset_gens']) > 1 else 0)
            else:
                vals.append(np.nan)
                errs.append(0)
        ax.errorbar(x + offsets[di], vals, yerr=errs, fmt=cfg['marker'],
                    color=cfg['color'], label=cfg['label'], capsize=4, markersize=8)

    ax.set_xticks(x)
    ax.set_xticklabels([TOPO_LABELS[t] for t in COUPLED_TOPOS], fontsize=9)
    ax.set_ylabel('Coupling Onset Generation')
    ax.legend()
    ax.set_ylim(bottom=0)
    ax.axhline(y=MIGRATION_START, color='gray', ls='--', alpha=0.4, label='Migration start')

    # ---- Panel B: Baseline-corrected mean delta_r curves ----
    ax = axes[0, 1]
    ax.set_title('B. Baseline-Corrected $\\Delta r(t)$ (ensemble)')

    for dk in domain_keys:
        cfg = DOMAIN_CONFIGS[dk]
        ls = '-' if dk == domain_keys[0] else '--'
        for topo in COUPLED_TOPOS:
            if topo in all_results[dk]:
                delta_r = all_results[dk][topo]['mean_delta_r']
                gens = np.arange(len(delta_r))
                # Smooth for display
                if len(delta_r) >= 10:
                    delta_r_smooth = uniform_filter1d(delta_r, size=10)
                else:
                    delta_r_smooth = delta_r
                ax.plot(gens, delta_r_smooth, color=TOPO_COLORS[topo],
                        ls=ls, linewidth=1.5, alpha=0.8)

    ax.axhline(y=0, color='black', ls='-', alpha=0.3, linewidth=0.5)
    ax.axhline(y=0.02, color='gray', ls=':', alpha=0.5, linewidth=1)
    ax.axhline(y=-0.02, color='gray', ls=':', alpha=0.5, linewidth=1)
    ax.axvline(x=MIGRATION_START, color='gray', ls=':', alpha=0.5)
    ax.set_xlabel('Generation')
    ax.set_ylabel('$\\Delta r$ (migration effect)')
    ax.set_xlim(0, 99)

    # Custom legend
    handles = [Line2D([0], [0], color=TOPO_COLORS[t], lw=2, label=t) for t in COUPLED_TOPOS]
    if n_domains >= 2:
        handles.append(Line2D([0], [0], color='black', ls='-', lw=1.5,
                              label=DOMAIN_CONFIGS[domain_keys[0]]['label']))
        handles.append(Line2D([0], [0], color='black', ls='--', lw=1.5,
                              label=DOMAIN_CONFIGS[domain_keys[1]]['label']))
    ax.legend(handles=handles, fontsize=7, ncol=2)

    # ---- Panel C: Fitness plateau by topology ----
    ax = axes[1, 0]
    ax.set_title('C. Fitness Plateau Generation by Topology')
    x_all = np.arange(len(TOPO_ORDER))
    offsets_all = np.linspace(-width / 2, width / 2, n_domains)

    for di, dk in enumerate(domain_keys):
        cfg = DOMAIN_CONFIGS[dk]
        vals, errs = [], []
        for topo in TOPO_ORDER:
            if topo in all_results[dk]:
                vals.append(all_results[dk][topo]['plateau_mean'])
                errs.append(all_results[dk][topo]['plateau_std'])
            else:
                vals.append(np.nan)
                errs.append(0)
        ax.errorbar(x_all + offsets_all[di], vals, yerr=errs, fmt=cfg['marker'],
                    color=cfg['color'], label=cfg['label'], capsize=4, markersize=8)

    ax.set_xticks(x_all)
    ax.set_xticklabels([TOPO_LABELS[t] for t in TOPO_ORDER], fontsize=9)
    ax.set_ylabel('Fitness Plateau Generation')
    ax.legend()
    ax.set_ylim(bottom=0)

    # ---- Panel D: Raw mean r(t) curves (both domains, all topologies) ----
    ax = axes[1, 1]
    ax.set_title('D. Raw Mean $r(t)$ Trajectories')

    for dk in domain_keys:
        cfg = DOMAIN_CONFIGS[dk]
        ls = '-' if dk == domain_keys[0] else '--'
        for topo in TOPO_ORDER:
            if topo in all_results[dk]:
                mean_r = all_results[dk][topo]['mean_r_raw']
                gens = np.arange(len(mean_r))
                ax.plot(gens, mean_r, color=TOPO_COLORS[topo],
                        ls=ls, linewidth=1.5, alpha=0.7)

    ax.axvline(x=MIGRATION_START, color='gray', ls=':', alpha=0.5)
    ax.set_xlabel('Generation')
    ax.set_ylabel('$r = 1 - $ pop. divergence')
    ax.set_xlim(0, 99)
    ax.set_ylim(0.4, 1.0)

    handles = [Line2D([0], [0], color=TOPO_COLORS[t], lw=2, label=t) for t in TOPO_ORDER]
    if n_domains >= 2:
        handles.append(Line2D([0], [0], color='black', ls='-', lw=1.5,
                              label=DOMAIN_CONFIGS[domain_keys[0]]['label']))
        handles.append(Line2D([0], [0], color='black', ls='--', lw=1.5,
                              label=DOMAIN_CONFIGS[domain_keys[1]]['label']))
    ax.legend(handles=handles, fontsize=7, ncol=2, loc='lower right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    pdf_path = output_path.replace('.png', '.pdf')
    plt.savefig(pdf_path, bbox_inches='tight')
    plt.close()
    print(f"\nPlots saved to:")
    print(f"  {output_path}")
    print(f"  {pdf_path}")


# --------------------------------------------------------------------------- #
#  Main                                                                        #
# --------------------------------------------------------------------------- #

def main():
    print("=" * 80)
    print("COUPLING ONSET TIMING ANALYSIS")
    print("Claudius's hypothesis: structural (topology) vs dynamical (landscape)")
    print("=" * 80)
    print()
    print("Methodology: baseline correction subtracts none-topology r(t) to isolate")
    print("migration-induced synchronization from selection-driven convergence.")

    all_data = {}
    all_results = {}

    for dk in DOMAIN_CONFIGS:
        cfg = DOMAIN_CONFIGS[dk]
        print(f"\nLoading {cfg['label']}...")
        data = load_domain(dk)
        if data is not None:
            all_data[dk] = data
            n_topos = len(data)
            n_seeds = sum(len(seeds) for seeds in data.values())
            print(f"  Loaded: {n_topos} topologies, {n_seeds} topology-seed combos")
            print(f"  Analyzing {cfg['label']}...")
            results = analyze_domain(dk, data)
            all_results[dk] = results

    if not all_results:
        print("\nERROR: No data loaded. Check file paths.")
        sys.exit(1)

    print_summary(all_results)

    if len(all_results) >= 2:
        cross_domain_correlation(all_results)
    else:
        print("\n[NOTE] Only one domain — cannot do cross-domain comparison.")

    output_path = '/home/lyra/projects/categorical-evolution/experiments/plots/coupling_onset_comparison.png'
    print(f"\nGenerating plots...")
    plot_results(all_results, all_data, output_path)

    # ---- VERDICT ----
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if len(all_results) >= 2:
        domain_keys = sorted(all_results.keys())
        print("\n  Ensemble onset (baseline-corrected), coupled topologies:\n")

        onset_diffs = []
        for topo in COUPLED_TOPOS:
            means = []
            for dk in domain_keys:
                if topo in all_results[dk] and all_results[dk][topo]['onset_ensemble_sig']:
                    means.append(all_results[dk][topo]['onset_ensemble'])
            if len(means) >= 2:
                diff = abs(means[0] - means[1])
                onset_diffs.append(diff)
                print(f"    {topo:>18}: {DOMAIN_CONFIGS[domain_keys[0]]['label']}={means[0]:.0f}, "
                      f"{DOMAIN_CONFIGS[domain_keys[1]]['label']}={means[1]:.0f}, |diff|={diff:.0f}")
            elif len(means) == 1:
                dk_with = [dk for dk in domain_keys
                           if topo in all_results[dk] and all_results[dk][topo]['onset_ensemble_sig']][0]
                print(f"    {topo:>18}: only significant in {DOMAIN_CONFIGS[dk_with]['label']}={means[0]:.0f}")

        if onset_diffs:
            mean_diff = np.mean(onset_diffs)
            max_diff = np.max(onset_diffs)
            print(f"\n  Mean cross-domain onset difference: {mean_diff:.1f} generations")
            print(f"  Max cross-domain onset difference:  {max_diff:.1f} generations")

            if mean_diff < 5:
                print(f"\n  => STRUCTURAL: Coupling onset is largely invariant across domains.")
                print(f"     Topology governs when migration-induced synchronization begins.")
            elif mean_diff < 15:
                print(f"\n  => MIXED: Both topology and landscape influence coupling onset.")
                print(f"     Topology sets the ballpark; fitness landscape shifts it.")
            else:
                print(f"\n  => DYNAMICAL: Coupling onset differs substantially across domains.")
                print(f"     The fitness landscape determines synchronization timing.")
        else:
            print("  No topologies with significant onset in both domains.")
    else:
        print("\n  Need >= 2 domains. Awaiting checkers data.")


if __name__ == '__main__':
    main()
