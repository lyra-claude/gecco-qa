#!/usr/bin/env python3
"""
Multi-domain analysis: 6-domain comparison (OneMax, Maze, Graph Coloring, Knapsack, No Thanks!, Checkers).

Generates three publication-quality figures:
  1. Multi-domain topology ordering -- bar chart of final-generation mean diversity
     for each topology, grouped by domain, with SE error bars.
  2. Multi-domain coupling onset -- onset generation by topology for each domain.
  3. Variance decomposition -- bar chart showing topology vs domain vs residual
     variance in coupling onset timing.

Also prints a detailed summary table to stdout.

Sorting Network is excluded from main figures (degenerate: near-flat diversity
across topologies). A brief diagnostic is printed at the end.

Data:
  experiment_e_raw.csv            (OneMax)
  experiment_e_maze.csv           (Maze)
  experiment_e_graph_coloring.csv (Graph Coloring)
  experiment_e_knapsack.csv       (Knapsack)
  experiment_e_nothanks.csv       (No Thanks!)
  experiment_e_checkers.csv       (Checkers)
  experiment_e_sorting_network.csv (Sorting Network -- diagnostic only)

Output:
  plots/multi_domain_topology_ordering.{png,pdf}   (Figure 1)
  plots/multi_domain_coupling_onset.{png,pdf}       (Figure 2)
  plots/multi_domain_variance_decomposition.{png,pdf} (Figure 3)
  Console: summary table + key statistics

Usage:
    python multi_domain_analysis.py
"""

import csv
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats
from scipy.ndimage import uniform_filter1d

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D

# --------------------------------------------------------------------------- #
#  Configuration                                                               #
# --------------------------------------------------------------------------- #

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLOT_DIR = os.path.join(SCRIPT_DIR, 'plots')

DOMAIN_CONFIGS = {
    'onemax': {
        'path': os.path.join(SCRIPT_DIR, 'experiment_e_raw.csv'),
        'label': 'OneMax',
        'color': '#4E79A7',
        'marker': 'o',
        'hatch': '',
    },
    'maze': {
        'path': os.path.join(SCRIPT_DIR, 'experiment_e_maze.csv'),
        'label': 'Maze',
        'color': '#F28E2B',
        'marker': 's',
        'hatch': '//',
    },
    'graph_coloring': {
        'path': os.path.join(SCRIPT_DIR, 'experiment_e_graph_coloring.csv'),
        'label': 'Graph Coloring',
        'color': '#E15759',
        'marker': 'D',
        'hatch': 'xx',
    },
    'knapsack': {
        'path': os.path.join(SCRIPT_DIR, 'experiment_e_knapsack.csv'),
        'label': 'Knapsack',
        'color': '#B07AA1',
        'marker': 'v',
        'hatch': '..',
    },
    'nothanks': {
        'path': os.path.join(SCRIPT_DIR, 'experiment_e_nothanks.csv'),
        'label': 'No Thanks!',
        'color': '#59A14F',
        'marker': 'P',
        'hatch': '++',
    },
    'checkers': {
        'path': os.path.join(SCRIPT_DIR, 'experiment_e_checkers.csv'),
        'label': 'Checkers',
        'color': '#76B7B2',
        'marker': 'X',
        'hatch': 'oo',
    },
}

# Canonical domain order for consistent plotting
DOMAIN_ORDER = ['onemax', 'maze', 'graph_coloring', 'knapsack', 'nothanks', 'checkers']

TOPO_ORDER = ['none', 'ring', 'star', 'random', 'fully_connected']
COUPLED_TOPOS = ['ring', 'star', 'random', 'fully_connected']

TOPO_LABELS = {
    'none': 'None\n(isolated)',
    'ring': 'Ring',
    'star': 'Star',
    'random': 'Random',
    'fully_connected': 'Fully\nConnected',
}
TOPO_LABELS_SHORT = {
    'none': 'None (isolated)',
    'ring': 'Ring',
    'star': 'Star',
    'random': 'Random',
    'fully_connected': 'Fully connected',
}
TOPO_SHORT = {
    'none': 'none', 'ring': 'ring', 'star': 'star',
    'random': 'random', 'fully_connected': 'full',
}
TOPO_COLORS = {
    'none': '#2166AC', 'ring': '#67A9CF', 'star': '#5AB4AC',
    'random': '#F4A582', 'fully_connected': '#B2182B',
}

MIGRATION_START = 5  # migration_freq = 5 => first migration at gen 5


# --------------------------------------------------------------------------- #
#  Style setup                                                                 #
# --------------------------------------------------------------------------- #

def setup_style():
    plt.style.use("seaborn-v0_8-paper")
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
    })


# --------------------------------------------------------------------------- #
#  Data loading                                                                #
# --------------------------------------------------------------------------- #

def load_domain_df(domain_key):
    """Load a domain CSV as a pandas DataFrame."""
    cfg = DOMAIN_CONFIGS[domain_key]
    filepath = cfg['path']
    if not os.path.exists(filepath):
        print(f"  [SKIP] {cfg['label']}: file not found at {filepath}")
        return None
    df = pd.read_csv(filepath)
    print(f"  Loaded {cfg['label']}: {len(df)} rows, "
          f"{df['seed'].nunique()} seeds, gens 0-{df['generation'].max()}")
    return df


def load_domain_raw(domain_key):
    """Load domain CSV as dict[topology][seed] = {gen, r, fitness, div}."""
    cfg = DOMAIN_CONFIGS[domain_key]
    filepath = cfg['path']
    if not os.path.exists(filepath):
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


# --------------------------------------------------------------------------- #
#  Coupling onset detection (from coupling_onset_checkers.py)                  #
# --------------------------------------------------------------------------- #

def compute_none_baseline(data):
    """Mean r trajectory for 'none' topology (no migration)."""
    if 'none' not in data:
        return None
    seeds = sorted(data['none'].keys())
    r_matrix = np.array([data['none'][s]['r'] for s in seeds])
    return np.mean(r_matrix, axis=0)


def compute_coupling_onset(delta_r, generations, smooth_window=10, threshold=0.05):
    """Find coupling onset from baseline-corrected r curve."""
    if len(delta_r) >= smooth_window:
        delta_r_smooth = uniform_filter1d(delta_r, size=smooth_window)
    else:
        delta_r_smooth = delta_r

    mask = generations >= MIGRATION_START
    if not np.any(mask):
        return np.nan, False

    post_gens = generations[mask]
    post_delta = delta_r_smooth[mask]

    above = np.where(post_delta > threshold)[0]
    if len(above) > 0:
        return int(post_gens[above[0]]), True

    below = np.where(post_delta < -threshold)[0]
    if len(below) > 0:
        return int(post_gens[below[0]]), True

    return np.nan, False


def analyze_domain_onset(domain_key, data):
    """Compute coupling onset for each topology in a domain."""
    results = {}
    baseline_r = compute_none_baseline(data)

    for topo in TOPO_ORDER:
        if topo not in data:
            continue

        seeds = sorted(data[topo].keys())
        onset_gens = []
        n_significant = 0

        for seed in seeds:
            sd = data[topo][seed]
            if baseline_r is not None and topo != 'none':
                delta_r = sd['r'] - baseline_r
            else:
                start_idx = min(MIGRATION_START, len(sd['r']) - 1)
                delta_r = sd['r'] - sd['r'][start_idx]

            onset_gen, is_sig = compute_coupling_onset(delta_r, sd['generations'])
            if is_sig:
                onset_gens.append(onset_gen)
                n_significant += 1

        # Ensemble onset
        r_matrix = np.array([data[topo][s]['r'] for s in seeds])
        mean_r = np.mean(r_matrix, axis=0)
        gens = data[topo][seeds[0]]['generations']

        if baseline_r is not None and topo != 'none':
            mean_delta_r = mean_r - baseline_r
        else:
            start_idx = min(MIGRATION_START, len(mean_r) - 1)
            mean_delta_r = mean_r - mean_r[start_idx]

        ens_onset, ens_sig = compute_coupling_onset(mean_delta_r, gens)
        onset_gens = np.array(onset_gens, dtype=float)
        valid_onset = onset_gens[~np.isnan(onset_gens)]
        sig_frac = n_significant / len(seeds) if seeds else 0.0

        results[topo] = {
            'onset_gens': onset_gens,
            'onset_mean': float(np.mean(valid_onset)) if len(valid_onset) > 0 else np.nan,
            'onset_std': float(np.std(valid_onset, ddof=1)) if len(valid_onset) > 1 else 0.0,
            'onset_se': float(np.std(valid_onset, ddof=1) / np.sqrt(len(valid_onset))) if len(valid_onset) > 1 else 0.0,
            'onset_ensemble': float(ens_onset) if not np.isnan(ens_onset) else np.nan,
            'onset_ensemble_sig': ens_sig,
            'onset_significant_frac': sig_frac,
            'mean_r_raw': mean_r,
            'mean_delta_r': mean_delta_r,
        }

    return results


# --------------------------------------------------------------------------- #
#  Final-generation diversity stats                                            #
# --------------------------------------------------------------------------- #

def compute_final_stats(df):
    """Return final-generation stats per topology."""
    max_gen = df['generation'].max()
    final = df[df['generation'] == max_gen]
    result = {}
    for topo in TOPO_ORDER:
        vals = final[final['topology'] == topo]['hamming_diversity']
        result[topo] = {
            'mean': vals.mean(),
            'std': vals.std() if len(vals) > 1 else 0.0,
            'se': vals.std() / np.sqrt(len(vals)) if len(vals) > 1 else 0.0,
            'n': len(vals),
        }
    return result


# =========================================================================== #
#  Figure 1: Multi-domain topology ordering (bar chart)                       #
# =========================================================================== #

def plot_topology_ordering(all_final_stats, output_prefix):
    """Grouped bar chart: domains on x-axis, one bar per topology within each group.

    Shows the same none > ring > star > random > FC ordering repeating
    in every domain — the paper's central visual claim.
    """
    available = [dk for dk in DOMAIN_ORDER if dk in all_final_stats]
    n_domains = len(available)
    n_topos = len(TOPO_ORDER)
    bar_width = 0.85 / n_topos
    x_base = np.arange(n_domains)

    # Topology colors
    topo_colors = {
        'none':             '#2166AC',
        'ring':             '#67A9CF',
        'star':             '#5AB4AC',
        'random':           '#F4A582',
        'fully_connected':  '#B2182B',
    }
    topo_display = {
        'none': 'None (isolated)',
        'ring': 'Ring',
        'star': 'Star',
        'random': 'Random',
        'fully_connected': 'Fully connected',
    }

    fig, ax = plt.subplots(figsize=(12, 5.5))

    for j, topo in enumerate(TOPO_ORDER):
        means = []
        ses = []
        for dk in available:
            fs = all_final_stats[dk]
            means.append(fs[topo]['mean'])
            ses.append(fs[topo]['se'])

        x_offset = x_base + (j - (n_topos - 1) / 2) * bar_width

        ax.bar(
            x_offset, means, width=bar_width * 0.88,
            yerr=ses, capsize=2,
            color=topo_colors[topo],
            edgecolor='white', linewidth=0.5,
            label=topo_display[topo],
            error_kw={'linewidth': 0.8, 'color': '0.3'},
        )

    ax.set_xticks(x_base)
    ax.set_xticklabels(
        [DOMAIN_CONFIGS[dk]['label'] for dk in available], fontsize=9,
    )
    ax.set_ylabel('Final-generation Hamming diversity')
    ax.set_title(
        f'Multi-Domain Topology Ordering ({n_domains} domains)\n'
        '(mean $\\pm$ SE across 30 seeds, generation 99)',
        fontsize=12, fontweight='bold',
    )
    ax.legend(
        frameon=True, framealpha=0.95, edgecolor='0.8',
        loc='upper right', fontsize=8, ncol=1,
    )

    plt.tight_layout()
    for fmt in ('png', 'pdf'):
        path = f'{output_prefix}.{fmt}'
        fig.savefig(path, dpi=300, bbox_inches='tight')
        print(f"  Saved {path}")
    plt.close(fig)


# =========================================================================== #
#  Figure 2: Multi-domain coupling onset                                      #
# =========================================================================== #

def plot_coupling_onset(all_onset_results, output_prefix):
    """Multi-domain coupling onset comparison: ensemble onset by topology."""
    n_domains = len(DOMAIN_ORDER)
    available = [dk for dk in DOMAIN_ORDER if dk in all_onset_results]

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    # ---- Panel A: Ensemble onset by topology ----
    ax = axes[0]
    ax.set_title('(a) Coupling Onset by Topology', fontsize=12, fontweight='bold')

    x = np.arange(len(COUPLED_TOPOS))
    width = 0.85 / max(len(available), 1)
    offsets = np.linspace(-width * (len(available) - 1) / 2,
                          width * (len(available) - 1) / 2,
                          len(available))

    for di, dk in enumerate(available):
        cfg = DOMAIN_CONFIGS[dk]
        vals, errs = [], []
        for topo in COUPLED_TOPOS:
            if topo in all_onset_results[dk]:
                res = all_onset_results[dk][topo]
                if res['onset_ensemble_sig'] and not np.isnan(res['onset_ensemble']):
                    vals.append(res['onset_ensemble'])
                    errs.append(res['onset_se'])
                else:
                    vals.append(np.nan)
                    errs.append(0)
            else:
                vals.append(np.nan)
                errs.append(0)

        ax.bar(
            x + offsets[di], vals, width=width * 0.9,
            yerr=errs, capsize=3,
            color=cfg['color'], hatch=cfg['hatch'],
            edgecolor='white', linewidth=0.6,
            label=cfg['label'],
            error_kw={'linewidth': 1.0, 'color': '0.3'},
        )

    ax.set_xticks(x)
    ax.set_xticklabels([TOPO_LABELS[t] for t in COUPLED_TOPOS], fontsize=9)
    ax.set_ylabel('Coupling Onset Generation')
    ax.legend(fontsize=8, frameon=True, framealpha=0.95, edgecolor='0.8')
    ax.set_ylim(bottom=0)
    ax.axhline(y=MIGRATION_START, color='gray', ls='--', alpha=0.4,
               label='_Migration start')

    # ---- Panel B: Baseline-corrected delta_r curves ----
    ax = axes[1]
    ax.set_title('(b) Baseline-Corrected $\\Delta r(t)$ (ensemble mean)', fontsize=12, fontweight='bold')

    linestyles = {available[i]: ['-', '--', '-.', ':'][i % 4] for i in range(len(available))}

    for dk in available:
        ls = linestyles[dk]
        for topo in COUPLED_TOPOS:
            if topo in all_onset_results[dk]:
                delta_r = all_onset_results[dk][topo]['mean_delta_r']
                gens = np.arange(len(delta_r))
                if len(delta_r) >= 10:
                    delta_r_smooth = uniform_filter1d(delta_r, size=10)
                else:
                    delta_r_smooth = delta_r
                ax.plot(gens, delta_r_smooth, color=TOPO_COLORS[topo],
                        ls=ls, linewidth=1.5, alpha=0.8)

    ax.axhline(y=0, color='black', ls='-', alpha=0.3, linewidth=0.5)
    ax.axhline(y=0.05, color='gray', ls=':', alpha=0.5, linewidth=1,
               label='Threshold ($\\Delta r = 0.05$)')
    ax.axhline(y=-0.05, color='gray', ls=':', alpha=0.5, linewidth=1)
    ax.axvline(x=MIGRATION_START, color='gray', ls=':', alpha=0.5)
    ax.set_xlabel('Generation')
    ax.set_ylabel('$\\Delta r$ (migration effect)')
    ax.set_xlim(0, 99)

    # Combined legend: topology colors + domain linestyles
    handles = [Line2D([0], [0], color=TOPO_COLORS[t], lw=2, label=TOPO_LABELS_SHORT[t])
               for t in COUPLED_TOPOS]
    handles.append(Line2D([0], [0], color='none', label=''))
    for dk in available:
        handles.append(Line2D([0], [0], color='black', ls=linestyles[dk], lw=1.5,
                              label=DOMAIN_CONFIGS[dk]['label']))
    ax.legend(handles=handles, fontsize=7, ncol=2, frameon=True,
              framealpha=0.95, edgecolor='0.8')

    fig.suptitle(
        'Multi-Domain Coupling Onset Analysis\n'
        '($\\Delta r = r_{coupled} - r_{none}$, threshold = 0.05)',
        fontsize=13, fontweight='bold',
    )
    plt.tight_layout()

    for fmt in ('png', 'pdf'):
        path = f'{output_prefix}.{fmt}'
        fig.savefig(path, dpi=300, bbox_inches='tight')
        print(f"  Saved {path}")
    plt.close(fig)


# =========================================================================== #
#  Figure 3: Variance decomposition                                           #
# =========================================================================== #

def compute_variance_decomposition(all_onset_results):
    """Compute SS_topology, SS_domain, SS_residual from onset data."""
    available = [dk for dk in DOMAIN_ORDER if dk in all_onset_results]
    all_data_points = []

    for di, dk in enumerate(available):
        for ti, topo in enumerate(COUPLED_TOPOS):
            if topo in all_onset_results[dk]:
                for o in all_onset_results[dk][topo]['onset_gens']:
                    if not np.isnan(o):
                        all_data_points.append((o, ti, di))

    if len(all_data_points) < 10:
        return None

    arr = np.array(all_data_points)
    onsets = arr[:, 0]
    topos_arr = arr[:, 1].astype(int)
    domains_arr = arr[:, 2].astype(int)

    grand_mean = np.mean(onsets)
    ss_total = np.sum((onsets - grand_mean) ** 2)

    ss_topo = sum(
        np.sum(topos_arr == ti) * (np.mean(onsets[topos_arr == ti]) - grand_mean) ** 2
        for ti in range(len(COUPLED_TOPOS)) if np.any(topos_arr == ti)
    )
    ss_domain = sum(
        np.sum(domains_arr == di) * (np.mean(onsets[domains_arr == di]) - grand_mean) ** 2
        for di in range(len(available)) if np.any(domains_arr == di)
    )
    ss_resid = ss_total - ss_topo - ss_domain

    pct_topo = 100 * ss_topo / ss_total if ss_total > 0 else 0
    pct_domain = 100 * ss_domain / ss_total if ss_total > 0 else 0
    pct_resid = 100 * ss_resid / ss_total if ss_total > 0 else 0

    # Kruskal-Wallis tests
    kw_topo_h, kw_topo_p = np.nan, np.nan
    groups_by_topo = [onsets[topos_arr == ti] for ti in range(len(COUPLED_TOPOS))
                      if np.any(topos_arr == ti)]
    if len(groups_by_topo) >= 2 and all(len(g) >= 2 for g in groups_by_topo):
        kw_topo_h, kw_topo_p = stats.kruskal(*groups_by_topo)

    kw_domain_h, kw_domain_p = np.nan, np.nan
    groups_by_domain = [onsets[domains_arr == di] for di in range(len(available))
                        if np.any(domains_arr == di)]
    if len(groups_by_domain) >= 2 and all(len(g) >= 2 for g in groups_by_domain):
        kw_domain_h, kw_domain_p = stats.kruskal(*groups_by_domain)

    return {
        'n': len(all_data_points),
        'ss_total': ss_total,
        'ss_topo': ss_topo,
        'ss_domain': ss_domain,
        'ss_resid': ss_resid,
        'pct_topo': pct_topo,
        'pct_domain': pct_domain,
        'pct_resid': pct_resid,
        'ratio': pct_topo / pct_domain if pct_domain > 0.1 else float('inf'),
        'kw_topo_h': kw_topo_h,
        'kw_topo_p': kw_topo_p,
        'kw_domain_h': kw_domain_h,
        'kw_domain_p': kw_domain_p,
    }


def plot_variance_decomposition(var_decomp, output_prefix):
    """Bar chart of variance decomposition."""
    if var_decomp is None:
        print("  [SKIP] Not enough data for variance decomposition.")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5),
                                    gridspec_kw={'width_ratios': [1.2, 1]})

    # ---- Panel A: Bar chart ----
    pcts = [var_decomp['pct_topo'], var_decomp['pct_domain'], var_decomp['pct_resid']]
    labels_bar = ['Topology', 'Domain', 'Residual']
    colors_bar = ['#2196F3', '#FF5722', '#9E9E9E']

    bars = ax1.bar(labels_bar, pcts, color=colors_bar, edgecolor='white', linewidth=1.2,
                   width=0.6)
    for bar_obj, pct_val in zip(bars, pcts):
        ax1.text(bar_obj.get_x() + bar_obj.get_width() / 2,
                 bar_obj.get_height() + 1.5,
                 f'{pct_val:.1f}%',
                 ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax1.set_ylabel('% of total variance in coupling onset timing')
    ax1.set_ylim(0, max(pcts) * 1.25)
    ax1.set_title('(a) Variance Decomposition', fontsize=12, fontweight='bold')

    # Add annotation
    ratio = var_decomp['ratio']
    if ratio == float('inf'):
        ratio_str = '>1000x'
    else:
        ratio_str = f'{ratio:.1f}x'
    ax1.text(0.5, 0.92,
             f'Topology/Domain ratio: {ratio_str}\n'
             f'N = {var_decomp["n"]} data points',
             transform=ax1.transAxes, ha='center', va='top',
             fontsize=10, style='italic', color='0.4',
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                       edgecolor='0.8', alpha=0.9))

    # ---- Panel B: Statistical tests ----
    ax2.axis('off')
    ax2.set_title('(b) Statistical Tests', fontsize=12, fontweight='bold')

    test_text = []
    test_text.append('Kruskal-Wallis: onset by TOPOLOGY')
    test_text.append(f'  H = {var_decomp["kw_topo_h"]:.3f}')
    if not np.isnan(var_decomp['kw_topo_p']):
        if var_decomp['kw_topo_p'] < 0.001:
            test_text.append(f'  p < 0.001 ***')
        else:
            test_text.append(f'  p = {var_decomp["kw_topo_p"]:.6f}')
    test_text.append('')
    test_text.append('Kruskal-Wallis: onset by DOMAIN')
    test_text.append(f'  H = {var_decomp["kw_domain_h"]:.3f}')
    if not np.isnan(var_decomp['kw_domain_p']):
        if var_decomp['kw_domain_p'] > 0.05:
            test_text.append(f'  p = {var_decomp["kw_domain_p"]:.4f} (n.s.)')
        elif var_decomp['kw_domain_p'] < 0.001:
            test_text.append(f'  p < 0.001 ***')
        else:
            test_text.append(f'  p = {var_decomp["kw_domain_p"]:.6f}')
    test_text.append('')
    test_text.append('Interpretation:')

    if var_decomp['pct_topo'] > 3 * var_decomp['pct_domain']:
        test_text.append('  STRUCTURAL: topology governs')
        test_text.append('  coupling onset timing.')
    elif var_decomp['pct_domain'] > 3 * var_decomp['pct_topo']:
        test_text.append('  DYNAMICAL: domain governs')
        test_text.append('  coupling onset timing.')
    else:
        test_text.append('  MIXED: both topology and')
        test_text.append('  domain contribute.')

    ax2.text(0.1, 0.85, '\n'.join(test_text),
             transform=ax2.transAxes, fontsize=11, fontfamily='monospace',
             va='top', ha='left',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8f8f8',
                       edgecolor='0.7'))

    fig.suptitle(
        f'Variance Decomposition of Coupling Onset Timing\n'
        f'({len(DOMAIN_ORDER)} domains, 4 coupled topologies, 30 seeds each)',
        fontsize=13, fontweight='bold',
    )
    plt.tight_layout()

    for fmt in ('png', 'pdf'):
        path = f'{output_prefix}.{fmt}'
        fig.savefig(path, dpi=300, bbox_inches='tight')
        print(f"  Saved {path}")
    plt.close(fig)


# --------------------------------------------------------------------------- #
#  Summary table                                                               #
# --------------------------------------------------------------------------- #

def print_summary_table(all_final_stats, all_onset_results, var_decomp):
    """Print comprehensive summary to stdout."""
    available_fs = [dk for dk in DOMAIN_ORDER if dk in all_final_stats]
    available_on = [dk for dk in DOMAIN_ORDER if dk in all_onset_results]

    print("\n" + "=" * 90)
    print("  MULTI-DOMAIN ANALYSIS SUMMARY")
    print("  Domains: " + ", ".join(DOMAIN_CONFIGS[dk]['label'] for dk in available_fs))
    print("=" * 90)

    # ---- Table 1: Final-generation diversity ----
    print("\n--- Table 1: Final-Generation Hamming Diversity (mean +/- SE) ---\n")

    col_w = 16
    header = f"  {'Topology':<20}"
    for dk in available_fs:
        header += f" {DOMAIN_CONFIGS[dk]['label']:>{col_w}}"
    print(header)
    print("  " + "-" * (20 + (col_w + 1) * len(available_fs)))

    for topo in TOPO_ORDER:
        row = f"  {TOPO_LABELS_SHORT[topo]:<20}"
        for dk in available_fs:
            fs = all_final_stats[dk][topo]
            row += f" {fs['mean']:.4f}+/-{fs['se']:.4f}".rjust(col_w + 1)
        print(row)

    # Rank ordering
    print("\n  Topology rank ordering (highest -> lowest diversity):")
    for dk in available_fs:
        fs = all_final_stats[dk]
        ranked = sorted(TOPO_ORDER, key=lambda t: fs[t]['mean'], reverse=True)
        print(f"    {DOMAIN_CONFIGS[dk]['label']:<20} {' > '.join(ranked)}")

    # Check if all orderings match
    orderings = []
    for dk in available_fs:
        fs = all_final_stats[dk]
        orderings.append(sorted(TOPO_ORDER, key=lambda t: fs[t]['mean'], reverse=True))
    all_match = all(o == orderings[0] for o in orderings)
    print(f"\n  All orderings identical: {all_match}")

    # Phase transition: none->ring drop
    print("\n  Phase transition (none -> ring drop):")
    for dk in available_fs:
        fs = all_final_stats[dk]
        none_m = fs['none']['mean']
        ring_m = fs['ring']['mean']
        drop = (none_m - ring_m) / none_m * 100
        print(f"    {DOMAIN_CONFIGS[dk]['label']:<20} {drop:.1f}%")

    # ---- Table 2: Coupling onset ----
    if available_on:
        print("\n--- Table 2: Ensemble Coupling Onset Generation ---\n")

        header = f"  {'Topology':<20}"
        for dk in available_on:
            header += f" {DOMAIN_CONFIGS[dk]['label']:>{col_w}}"
        header += f" {'max|diff|':>{col_w}}"
        print(header)
        print("  " + "-" * (20 + (col_w + 1) * (len(available_on) + 1)))

        for topo in COUPLED_TOPOS:
            row = f"  {TOPO_LABELS_SHORT[topo]:<20}"
            vals = []
            for dk in available_on:
                if topo in all_onset_results[dk]:
                    res = all_onset_results[dk][topo]
                    if res['onset_ensemble_sig'] and not np.isnan(res['onset_ensemble']):
                        row += f" {res['onset_ensemble']:>{col_w}.0f}"
                        vals.append(res['onset_ensemble'])
                    else:
                        row += f" {'N/A':>{col_w}}"
                else:
                    row += f" {'N/A':>{col_w}}"
            if len(vals) >= 2:
                max_diff = max(abs(vals[i] - vals[j])
                               for i in range(len(vals))
                               for j in range(i + 1, len(vals)))
                row += f" {max_diff:>{col_w}.0f}"
            else:
                row += f" {'--':>{col_w}}"
            print(row)

        # Onset ordering per domain
        print("\n  Onset ordering (earliest -> latest):")
        for dk in available_on:
            items = []
            for topo in COUPLED_TOPOS:
                if topo in all_onset_results[dk]:
                    res = all_onset_results[dk][topo]
                    if res['onset_ensemble_sig'] and not np.isnan(res['onset_ensemble']):
                        items.append((res['onset_ensemble'], topo))
            items.sort()
            if items:
                order_str = ' < '.join(f'{TOPO_SHORT[t]}({g:.0f})' for g, t in items)
                print(f"    {DOMAIN_CONFIGS[dk]['label']:<20} {order_str}")

        # Pairwise rank correlations
        if len(available_on) >= 2:
            print("\n  Pairwise rank correlations (onset ordering):")
            onset_by_domain = {}
            for dk in available_on:
                vals = []
                for topo in COUPLED_TOPOS:
                    if topo in all_onset_results[dk] and all_onset_results[dk][topo]['onset_ensemble_sig']:
                        vals.append(all_onset_results[dk][topo]['onset_ensemble'])
                    else:
                        vals.append(np.nan)
                onset_by_domain[dk] = vals

            for i in range(len(available_on)):
                for j in range(i + 1, len(available_on)):
                    dk1, dk2 = available_on[i], available_on[j]
                    v1, v2 = np.array(onset_by_domain[dk1]), np.array(onset_by_domain[dk2])
                    valid = ~(np.isnan(v1) | np.isnan(v2))
                    if np.sum(valid) >= 3:
                        l1, l2 = DOMAIN_CONFIGS[dk1]['label'], DOMAIN_CONFIGS[dk2]['label']
                        rho, p = stats.spearmanr(v1[valid], v2[valid])
                        print(f"    {l1} vs {l2}: Spearman rho = {rho:.4f}, p = {p:.4f}")

    # ---- Table 3: Variance decomposition ----
    if var_decomp:
        print("\n--- Table 3: Variance Decomposition ---\n")
        print(f"  N data points:  {var_decomp['n']}")
        print(f"  Topology:       {var_decomp['pct_topo']:.1f}% of variance (SS={var_decomp['ss_topo']:.1f})")
        print(f"  Domain:         {var_decomp['pct_domain']:.1f}% of variance (SS={var_decomp['ss_domain']:.1f})")
        print(f"  Residual:       {var_decomp['pct_resid']:.1f}% of variance (SS={var_decomp['ss_resid']:.1f})")
        ratio = var_decomp['ratio']
        if ratio == float('inf'):
            print(f"  Topology/Domain ratio: >1000x")
        else:
            print(f"  Topology/Domain ratio: {ratio:.1f}x")

        if not np.isnan(var_decomp['kw_topo_p']):
            print(f"\n  Kruskal-Wallis (by topology): H={var_decomp['kw_topo_h']:.3f}, p={var_decomp['kw_topo_p']:.6f}")
        if not np.isnan(var_decomp['kw_domain_p']):
            print(f"  Kruskal-Wallis (by domain):   H={var_decomp['kw_domain_h']:.3f}, p={var_decomp['kw_domain_p']:.6f}")


# --------------------------------------------------------------------------- #
#  Sorting Network diagnostic                                                  #
# --------------------------------------------------------------------------- #

def sorting_network_diagnostic():
    """Brief check on sorting network data."""
    sn_path = os.path.join(SCRIPT_DIR, 'experiment_e_sorting_network.csv')
    if not os.path.exists(sn_path):
        print("\n  [SKIP] Sorting Network CSV not found.")
        return

    df = pd.read_csv(sn_path)
    max_gen = df['generation'].max()
    final = df[df['generation'] == max_gen]

    print("\n" + "=" * 90)
    print("  SORTING NETWORK DIAGNOSTIC (excluded from main figures)")
    print("=" * 90)

    print(f"\n  Data: {df['seed'].nunique()} seeds, gens 0-{max_gen}")
    print(f"\n  Final-generation diversity by topology:")

    all_vals = []
    for topo in TOPO_ORDER:
        vals = final[final['topology'] == topo]['hamming_diversity']
        mean_v = vals.mean()
        std_v = vals.std()
        all_vals.append(mean_v)
        print(f"    {TOPO_LABELS_SHORT[topo]:<20} mean={mean_v:.6f} std={std_v:.6f}")

    total_range = max(all_vals) - min(all_vals)
    onemax_range = (all_final_stats_global['onemax']['none']['mean'] -
                    all_final_stats_global['onemax']['fully_connected']['mean']
                    if 'onemax' in all_final_stats_global else 0)
    print(f"\n  Total range across topologies: {total_range:.6f}")
    if onemax_range > 0:
        print(f"  OneMax range for comparison:   {onemax_range:.6f}")
        print(f"  Sorting Net / OneMax range:    {total_range / onemax_range:.2f}x")

    # Check if ordering matches
    ranked = sorted(TOPO_ORDER, key=lambda t: final[final['topology'] == t]['hamming_diversity'].mean(), reverse=True)
    canonical = ['none', 'ring', 'star', 'random', 'fully_connected']
    matches = ranked == canonical
    print(f"\n  Ordering: {' > '.join(ranked)}")
    print(f"  Matches canonical: {matches}")

    if total_range < 0.02:
        print(f"\n  VERDICT: DEGENERATE. Range ({total_range:.6f}) is negligible.")
        print(f"  Topology has no meaningful effect on sorting network diversity.")
    else:
        print(f"\n  NOTE: Range ({total_range:.6f}) is non-trivial.")
        print(f"  Sorting network may be worth including after all.")


# --------------------------------------------------------------------------- #
#  Main                                                                        #
# --------------------------------------------------------------------------- #

all_final_stats_global = {}  # Module-level for sorting network diagnostic


def main():
    global all_final_stats_global

    setup_style()
    os.makedirs(PLOT_DIR, exist_ok=True)

    print("=" * 90)
    print("  MULTI-DOMAIN ANALYSIS")
    print("  6 domains: OneMax, Maze, Graph Coloring, Knapsack, No Thanks!, Checkers")
    print("  5 topologies: none, ring, star, random, fully_connected")
    print("  30 seeds each, 100 generations")
    print("=" * 90)

    # ---- Load data ----
    print("\nLoading data...")
    all_dfs = {}
    all_raw = {}
    for dk in DOMAIN_ORDER:
        df = load_domain_df(dk)
        if df is not None:
            all_dfs[dk] = df
        raw = load_domain_raw(dk)
        if raw is not None:
            all_raw[dk] = raw

    if len(all_dfs) < 2:
        print("\nERROR: Need at least 2 domains. Exiting.")
        sys.exit(1)

    print(f"\n  {len(all_dfs)} domain(s) loaded successfully.\n")

    # ---- Compute final-generation stats ----
    print("Computing final-generation diversity stats...")
    all_final_stats = {}
    for dk in DOMAIN_ORDER:
        if dk in all_dfs:
            all_final_stats[dk] = compute_final_stats(all_dfs[dk])
    all_final_stats_global = all_final_stats

    # ---- Compute coupling onset ----
    print("Computing coupling onset analysis...")
    all_onset_results = {}
    for dk in DOMAIN_ORDER:
        if dk in all_raw:
            print(f"  Analyzing {DOMAIN_CONFIGS[dk]['label']}...")
            all_onset_results[dk] = analyze_domain_onset(dk, all_raw[dk])

    # ---- Variance decomposition ----
    print("Computing variance decomposition...")
    var_decomp = compute_variance_decomposition(all_onset_results)

    # ---- Generate Figure 1 ----
    print("\nGenerating Figure 1: Multi-domain topology ordering...")
    plot_topology_ordering(
        all_final_stats,
        os.path.join(PLOT_DIR, 'multi_domain_topology_ordering'),
    )

    # ---- Generate Figure 2 ----
    print("\nGenerating Figure 2: Multi-domain coupling onset...")
    plot_coupling_onset(
        all_onset_results,
        os.path.join(PLOT_DIR, 'multi_domain_coupling_onset'),
    )

    # ---- Generate Figure 3 ----
    print("\nGenerating Figure 3: Variance decomposition...")
    plot_variance_decomposition(
        var_decomp,
        os.path.join(PLOT_DIR, 'multi_domain_variance_decomposition'),
    )

    # ---- Summary table ----
    print_summary_table(all_final_stats, all_onset_results, var_decomp)

    # ---- Sorting network diagnostic ----
    sorting_network_diagnostic()

    # ---- Final output ----
    print("\n" + "=" * 90)
    print("  DONE. All plots saved to:")
    print(f"    {os.path.abspath(PLOT_DIR)}/")
    print("  Formats: PNG (300 DPI) + PDF")
    print("=" * 90)


if __name__ == '__main__':
    main()
