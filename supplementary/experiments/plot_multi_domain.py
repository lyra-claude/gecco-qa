"""
Multi-domain comparison plots for the categorical evolution paper.

Generates three publication-quality figures that demonstrate domain independence
of topology ordering (none > ring > star > random > fully_connected in diversity):

1. Figure 1: Domain Independence Panel (2x2 grid) -- diversity over generations
   per domain, with confidence bands for each topology.
2. Figure 2: Final-Generation Diversity Comparison -- grouped bar chart with
   one bar per domain, grouped by topology. Error bars show standard error.
3. Figure 3: Normalized Overlay -- all domains on a single axis, min-max
   normalized, showing the invariant topology ordering.

Gracefully handles missing CSVs (prints a warning, proceeds with available data).

Data:  experiment_e_raw.csv (OneMax), experiment_e_maze.csv,
       experiment_e_sorting_network.csv, experiment_e_graph_coloring.csv,
       experiment_e_knapsack.csv
Output: plots/ directory (PNG at 300 DPI + PDF)

Usage:
    python plot_multi_domain.py              # generate all three figures
    python plot_multi_domain.py --only panel # just figure 1
    python plot_multi_domain.py --only bar   # just figure 2
    python plot_multi_domain.py --only overlay # just figure 3
"""

import argparse
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path
from matplotlib.lines import Line2D

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
OUT_DIR = SCRIPT_DIR / "plots"
OUT_DIR.mkdir(exist_ok=True)

# Domains in presentation order.  Each entry maps to:
#   data_file  -- CSV filename (relative to SCRIPT_DIR)
#   label      -- display name used in titles / legends
#   marker     -- marker shape for overlay plots
DOMAIN_SPECS = [
    {
        "key": "onemax",
        "data_files": ["experiment_e_raw.csv", "experiment_e_onemax.csv"],
        "label": "OneMax",
        "marker": "o",
    },
    {
        "key": "maze",
        "data_files": ["experiment_e_maze.csv"],
        "label": "Maze",
        "marker": "s",
    },
    {
        "key": "sorting_network",
        "data_files": ["experiment_e_sorting_network.csv"],
        "label": "Sorting Networks",
        "marker": "^",
    },
    {
        "key": "graph_coloring",
        "data_files": ["experiment_e_graph_coloring.csv"],
        "label": "Graph Coloring",
        "marker": "D",
    },
    {
        "key": "knapsack",
        "data_files": ["experiment_e_knapsack.csv"],
        "label": "Knapsack",
        "marker": "v",
    },
    {
        "key": "nothanks",
        "data_files": ["experiment_e_nothanks.csv"],
        "label": "No Thanks!",
        "marker": "X",
    },
    {
        "key": "checkers",
        "data_files": ["experiment_e_checkers.csv"],
        "label": "Checkers",
        "marker": "P",
    },
]

# Topology ordering: strict (isolated) -> lax (fully connected)
TOPOLOGY_ORDER = ["none", "ring", "star", "random", "fully_connected"]

TOPOLOGY_LABELS = {
    "none": "None\n(isolated)",
    "ring": "Ring",
    "star": "Star",
    "random": "Random",
    "fully_connected": "Fully\nconnected",
}

TOPOLOGY_LABELS_SHORT = {
    "none": "None (isolated)",
    "ring": "Ring",
    "star": "Star",
    "random": "Random",
    "fully_connected": "Fully connected",
}

# Topology colors -- diverging RdBu palette (consistent with plot_fingerprints.py)
TOPO_COLORS = {
    "none": "#2166AC",
    "ring": "#67A9CF",
    "star": "#5AB4AC",
    "random": "#F4A582",
    "fully_connected": "#B2182B",
}

# Domain colors -- used in the grouped bar chart and overlay
DOMAIN_COLORS = [
    "#4E79A7",  # OneMax -- steel blue
    "#F28E2B",  # Maze -- orange
    "#59A14F",  # Sorting Networks -- green
    "#E15759",  # Graph Coloring -- red
    "#B07AA1",  # Knapsack -- purple
    "#EDC948",  # No Thanks! -- gold
    "#76B7B2",  # Checkers -- teal
]

# Domain hatching patterns (for additional differentiation in bar chart)
DOMAIN_HATCHES = ["", "//", "\\\\", "xx", "..", "++", "oo"]


# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_domains():
    """Load all available domain CSVs.

    Returns a list of dicts:
        {key, label, marker, df, color, hatch}
    Skips domains whose CSV files are missing.
    """
    loaded = []
    for i, spec in enumerate(DOMAIN_SPECS):
        data_path = None
        for candidate in spec["data_files"]:
            p = SCRIPT_DIR / candidate
            if p.exists():
                data_path = p
                break

        if data_path is None:
            tried = ", ".join(spec["data_files"])
            print(f"  [SKIP] {spec['label']}: no data file found (tried {tried})")
            continue

        df = pd.read_csv(data_path)
        print(f"  Loaded {spec['label']}: {len(df)} rows from {data_path.name}"
              f" ({df['seed'].nunique()} seeds, gens 0-{df['generation'].max()})")

        loaded.append({
            "key": spec["key"],
            "label": spec["label"],
            "marker": spec["marker"],
            "df": df,
            "color": DOMAIN_COLORS[i],
            "hatch": DOMAIN_HATCHES[i],
        })

    if len(loaded) < 2:
        print(f"\n  WARNING: Only {len(loaded)} domain(s) loaded. "
              "Multi-domain comparison needs at least 2.")
        if len(loaded) == 0:
            print("  ERROR: No data files found. Exiting.")
            sys.exit(1)

    return loaded


def compute_topology_stats(df):
    """Return per-topology mean and CI over seeds at each generation.

    Returns dict[topology] -> DataFrame with columns: mean, ci_lo, ci_hi
    (95% confidence interval using t-distribution).
    """
    from scipy import stats as sp_stats

    result = {}
    for topo in TOPOLOGY_ORDER:
        tdf = df[df["topology"] == topo]
        pivot = tdf.pivot(index="generation", columns="seed", values="hamming_diversity")
        n_seeds = pivot.shape[1]
        mean = pivot.mean(axis=1)
        se = pivot.std(axis=1) / np.sqrt(n_seeds)

        if n_seeds > 1:
            t_crit = sp_stats.t.ppf(0.975, df=n_seeds - 1)
        else:
            t_crit = 0.0  # no CI for single seed

        result[topo] = pd.DataFrame({
            "mean": mean,
            "ci_lo": mean - t_crit * se,
            "ci_hi": mean + t_crit * se,
            "se": se,
        })

    return result


def compute_final_stats(df):
    """Return final-generation stats per topology.

    Returns DataFrame indexed by topology with columns: mean, se, n_seeds.
    """
    max_gen = df["generation"].max()
    final = df[df["generation"] == max_gen]

    rows = []
    for topo in TOPOLOGY_ORDER:
        vals = final[final["topology"] == topo]["hamming_diversity"]
        rows.append({
            "topology": topo,
            "mean": vals.mean(),
            "se": vals.std() / np.sqrt(len(vals)) if len(vals) > 1 else 0.0,
            "std": vals.std() if len(vals) > 1 else 0.0,
            "n_seeds": len(vals),
        })

    return pd.DataFrame(rows).set_index("topology").reindex(TOPOLOGY_ORDER)


# ============================================================================
# Figure 1: Domain Independence Panel (2x2)
# ============================================================================

def plot_panel(domains):
    """2x2 grid of subplots, one per domain.

    Each subplot shows diversity over generations for all 5 topologies
    with 95% confidence bands.
    """
    n = len(domains)
    if n == 0:
        return

    # Determine grid layout
    if n <= 2:
        nrows, ncols = 1, n
        figsize = (6 * n, 4)
    elif n <= 4:
        nrows, ncols = 2, 2
        figsize = (12, 7.5)
    else:
        nrows = (n + 2) // 3
        ncols = 3
        figsize = (14, 4 * nrows)

    fig, axes_arr = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False)
    axes = axes_arr.flatten()

    for idx, dom in enumerate(domains):
        ax = axes[idx]
        stats = compute_topology_stats(dom["df"])

        for topo in TOPOLOGY_ORDER:
            s = stats[topo]
            color = TOPO_COLORS[topo]

            # Confidence band
            ax.fill_between(
                s.index, s["ci_lo"], s["ci_hi"],
                color=color, alpha=0.15,
            )
            # Mean line
            ax.plot(
                s.index, s["mean"],
                color=color, linewidth=1.8,
                label=TOPOLOGY_LABELS_SHORT[topo],
            )

        ax.set_xlim(0, dom["df"]["generation"].max())
        ax.set_xlabel("Generation")
        ax.set_ylabel("Hamming diversity")
        ax.set_title(dom["label"], fontsize=12, fontweight="bold")
        ax.xaxis.set_major_locator(ticker.MultipleLocator(25))

    # Hide unused subplots
    for idx in range(n, len(axes)):
        axes[idx].set_visible(False)

    # Single shared legend from the first subplot
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels,
        loc="lower center",
        ncol=len(TOPOLOGY_ORDER),
        frameon=True,
        framealpha=0.95,
        edgecolor="0.8",
        fontsize=9,
        bbox_to_anchor=(0.5, -0.02),
    )

    fig.suptitle(
        "Domain Independence of Topology Ordering",
        fontsize=14,
        fontweight="bold",
        y=1.01,
    )

    fig.tight_layout(rect=[0, 0.04, 1, 0.98])

    for fmt in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"multi_domain_panel.{fmt}")
    plt.close(fig)
    print("  -> multi_domain_panel.png/pdf saved")


# ============================================================================
# Figure 2: Grouped Bar Chart (final-generation diversity)
# ============================================================================

def plot_grouped_bar(domains):
    """Grouped bar chart: topology on x-axis, one bar per domain.

    Diversity is normalized to [0,1] per domain for comparability.
    Error bars show standard error (also normalized).
    """
    n_domains = len(domains)
    if n_domains == 0:
        return

    n_topos = len(TOPOLOGY_ORDER)
    bar_width = 0.8 / n_domains
    x_base = np.arange(n_topos)

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for i, dom in enumerate(domains):
        final_stats = compute_final_stats(dom["df"])

        # Min-max normalization using all topology means for this domain
        raw_means = final_stats["mean"].values
        vmin, vmax = raw_means.min(), raw_means.max()
        drange = vmax - vmin if vmax != vmin else 1.0

        norm_means = (raw_means - vmin) / drange
        norm_se = final_stats["se"].values / drange

        x_offset = x_base + (i - (n_domains - 1) / 2) * bar_width

        ax.bar(
            x_offset,
            norm_means,
            width=bar_width * 0.9,
            yerr=norm_se,
            capsize=3,
            color=dom["color"],
            hatch=dom["hatch"],
            edgecolor="white",
            linewidth=0.6,
            label=dom["label"],
            error_kw={"linewidth": 1.0, "color": "0.3"},
        )

    ax.set_xticks(x_base)
    ax.set_xticklabels(
        [TOPOLOGY_LABELS[t] for t in TOPOLOGY_ORDER],
        fontsize=9,
    )
    ax.set_ylabel("Normalized final diversity")
    ax.set_ylim(0, 1.15)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.set_title(
        "Final-Generation Diversity by Topology (Normalized per Domain)",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(
        frameon=True,
        framealpha=0.95,
        edgecolor="0.8",
        loc="upper right",
        fontsize=9,
    )

    # Strict -> Lax arrow below x-axis
    ax.annotate(
        "",
        xy=(n_topos - 0.6, -0.015),
        xytext=(-0.4, -0.015),
        xycoords=("data", "axes fraction"),
        textcoords=("data", "axes fraction"),
        arrowprops=dict(arrowstyle="->", color="0.5", linewidth=1.0),
        annotation_clip=False,
    )
    ax.text(
        (n_topos - 1) / 2,
        -0.08,
        "strict                                                                  lax",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=8,
        color="0.5",
        style="italic",
    )

    fig.tight_layout()

    for fmt in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"multi_domain_bar.{fmt}")
    plt.close(fig)
    print("  -> multi_domain_bar.png/pdf saved")


# ============================================================================
# Figure 3: Normalized Overlay (all domains on one axis)
# ============================================================================

def plot_normalized_overlay(domains):
    """Single plot with all domains overlaid, diversity normalized to [0,1].

    Each domain gets a different line style + marker; topologies use the
    standard color scheme.  Shows final-generation values connected by lines.
    """
    n = len(domains)
    if n == 0:
        return

    linestyles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1, 1, 1))]

    fig, ax = plt.subplots(figsize=(7, 4.5))

    for i, dom in enumerate(domains):
        final_stats = compute_final_stats(dom["df"])
        raw_means = final_stats["mean"].values

        vmin, vmax = raw_means.min(), raw_means.max()
        drange = vmax - vmin if vmax != vmin else 1.0
        norm_means = (raw_means - vmin) / drange

        x = np.arange(len(TOPOLOGY_ORDER))
        ls = linestyles[i % len(linestyles)]

        # Domain line (connecting the topologies)
        ax.plot(
            x, norm_means,
            color=dom["color"],
            linewidth=2.0,
            linestyle=ls,
            marker=dom["marker"],
            markersize=8,
            markeredgecolor="white",
            markeredgewidth=1.0,
            label=dom["label"],
            zorder=3,
        )

    ax.set_xticks(np.arange(len(TOPOLOGY_ORDER)))
    ax.set_xticklabels(
        [TOPOLOGY_LABELS[t] for t in TOPOLOGY_ORDER],
        fontsize=9,
    )
    ax.set_ylabel("Normalized diversity (min-max per domain)")
    ax.set_ylim(-0.05, 1.15)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax.set_title(
        "Topology Ordering is Domain-Invariant",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(
        frameon=True,
        framealpha=0.95,
        edgecolor="0.8",
        loc="upper right",
        fontsize=9,
    )

    # Strict -> Lax arrow
    ax.annotate(
        "",
        xy=(len(TOPOLOGY_ORDER) - 0.6, -0.015),
        xytext=(-0.4, -0.015),
        xycoords=("data", "axes fraction"),
        textcoords=("data", "axes fraction"),
        arrowprops=dict(arrowstyle="->", color="0.5", linewidth=1.0),
        annotation_clip=False,
    )
    ax.text(
        (len(TOPOLOGY_ORDER) - 1) / 2,
        -0.08,
        "strict                                                                  lax",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=8,
        color="0.5",
        style="italic",
    )

    fig.tight_layout()

    for fmt in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"multi_domain_overlay.{fmt}")
    plt.close(fig)
    print("  -> multi_domain_overlay.png/pdf saved")


# ============================================================================
# Summary table
# ============================================================================

def print_summary_table(domains):
    """Print a table: domain x topology -> mean final-generation diversity."""
    print("\n" + "=" * 78)
    print("  SUMMARY: Mean final-generation Hamming diversity")
    print("=" * 78)

    # Header
    col_w = 14
    header = f"  {'Topology':<20}"
    for dom in domains:
        header += f" {dom['label']:>{col_w}}"
    print(header)
    print("  " + "-" * (20 + (col_w + 1) * len(domains)))

    # Rows
    for topo in TOPOLOGY_ORDER:
        row = f"  {TOPOLOGY_LABELS_SHORT[topo]:<20}"
        for dom in domains:
            max_gen = dom["df"]["generation"].max()
            final = dom["df"][
                (dom["df"]["generation"] == max_gen)
                & (dom["df"]["topology"] == topo)
            ]["hamming_diversity"]
            row += f" {final.mean():>{col_w}.6f}"
        print(row)

    # Normalized row
    print()
    print(f"  {'(Normalized)':<20}", end="")
    for dom in domains:
        print(f" {'[0, 1]':>{col_w}}", end="")
    print()

    for topo in TOPOLOGY_ORDER:
        row = f"  {TOPOLOGY_LABELS_SHORT[topo]:<20}"
        for dom in domains:
            final_stats = compute_final_stats(dom["df"])
            raw = final_stats["mean"].values
            vmin, vmax = raw.min(), raw.max()
            drange = vmax - vmin if vmax != vmin else 1.0
            norm_val = (final_stats.loc[topo, "mean"] - vmin) / drange
            row += f" {norm_val:>{col_w}.4f}"
        print(row)

    # Rank ordering per domain
    print()
    print("  Rank ordering (highest -> lowest diversity):")
    for dom in domains:
        final_stats = compute_final_stats(dom["df"])
        ranked = final_stats.sort_values("mean", ascending=False)
        order_str = " > ".join(ranked.index.tolist())
        print(f"    {dom['label']:<20} {order_str}")

    print("=" * 78)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate multi-domain comparison plots for the categorical evolution paper."
    )
    parser.add_argument(
        "--only",
        choices=["panel", "bar", "overlay"],
        default=None,
        help="Generate only one figure type (default: all three).",
    )
    args = parser.parse_args()

    setup_style()

    print("Loading domain data...")
    domains = load_domains()
    print(f"\n  {len(domains)} domain(s) loaded.\n")

    if args.only is None or args.only == "panel":
        print("Generating Figure 1: Domain Independence Panel...")
        plot_panel(domains)

    if args.only is None or args.only == "bar":
        print("Generating Figure 2: Grouped Bar Chart...")
        plot_grouped_bar(domains)

    if args.only is None or args.only == "overlay":
        print("Generating Figure 3: Normalized Overlay...")
        plot_normalized_overlay(domains)

    print_summary_table(domains)

    print(f"\nAll plots saved to {OUT_DIR.resolve()}")
    print("Formats: PNG (300 DPI) + PDF")


if __name__ == "__main__":
    main()
