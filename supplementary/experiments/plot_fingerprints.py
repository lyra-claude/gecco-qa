"""
Diversity fingerprint plots for the topology sweep experiment.

Generates three publication-quality figures per domain:
1. fingerprints_panels -- 5-panel figure showing individual seed traces per topology
2. fingerprints_overlay -- single panel comparing mean diversity across topologies
3. phase_transition -- bar chart of final-generation diversity with symmetry-break annotation

When --domain=comparison, generates a cross-domain comparison plot instead.

Data: experiment_e_raw.csv (OneMax) or experiment_e_maze.csv (Maze)
      5 topologies x 30 seeds x 100 generations
Output: plots/ directory (PNG at 300 DPI + PDF)

Usage:
    python plot_fingerprints.py                  # OneMax (default, backward-compatible)
    python plot_fingerprints.py --domain onemax  # OneMax (explicit)
    python plot_fingerprints.py --domain maze    # Maze
    python plot_fingerprints.py --domain comparison  # Cross-domain overlay
    python plot_fingerprints.py --domain all     # All of the above
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
OUT_DIR = SCRIPT_DIR / "plots"
OUT_DIR.mkdir(exist_ok=True)

DOMAIN_CONFIG = {
    "onemax": {
        "data_file": "experiment_e_raw.csv",
        "prefix": "fingerprints",       # backward-compatible naming
        "title_domain": "OneMax",
        "y_tick_step": 0.05,
    },
    "maze": {
        "data_file": "experiment_e_maze.csv",
        "prefix": "maze_fingerprints",
        "title_domain": "Maze",
        "y_tick_step": 0.05,
    },
    "checkers": {
        "data_file": "experiment_e_checkers.csv",
        "prefix": "checkers_fingerprints",
        "title_domain": "Checkers",
        "y_tick_step": 0.05,
    },
}

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

# Color scheme: cool (strict/blue) -> warm (lax/red), diverging RdBu palette
COLORS = {
    "none": "#2166AC",
    "ring": "#67A9CF",
    "star": "#5AB4AC",
    "random": "#F4A582",
    "fully_connected": "#B2182B",
}


# ---------------------------------------------------------------------------
# Style setup
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

def load_domain(domain_key):
    """Load data and precompute grouped pivot tables for a domain."""
    cfg = DOMAIN_CONFIG[domain_key]
    data_path = SCRIPT_DIR / cfg["data_file"]
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows from {data_path.name} ({cfg['title_domain']})")

    grouped = {}
    for topo in TOPOLOGY_ORDER:
        tdf = df[df["topology"] == topo]
        seeds = tdf.pivot(index="generation", columns="seed", values="hamming_diversity")
        grouped[topo] = seeds

    y_min = df["hamming_diversity"].min() * 0.95
    y_max = df["hamming_diversity"].max() * 1.02

    return df, grouped, y_min, y_max, cfg


# ============================================================================
# Plot 1: Five-panel fingerprint figure
# ============================================================================

def plot_fingerprint_panels(df, grouped, y_min, y_max, cfg):
    fig, axes = plt.subplots(1, 5, figsize=(14, 2.8), sharey=True)

    for ax, topo in zip(axes, TOPOLOGY_ORDER):
        seeds_df = grouped[topo]
        color = COLORS[topo]

        # Individual seed traces
        for seed_col in seeds_df.columns:
            ax.plot(
                seeds_df.index,
                seeds_df[seed_col],
                color=color,
                alpha=0.15,
                linewidth=0.6,
                rasterized=True,
            )

        # Mean line
        mean_line = seeds_df.mean(axis=1)
        ax.plot(
            mean_line.index,
            mean_line.values,
            color=color,
            alpha=1.0,
            linewidth=2.0,
        )

        ax.set_title(TOPOLOGY_LABELS[topo], fontsize=10, fontweight="bold", pad=6)
        ax.set_xlim(0, 99)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel("Generation")
        ax.xaxis.set_major_locator(ticker.MultipleLocator(25))

    axes[0].set_ylabel("Hamming diversity")

    # Subtle shared grid
    for ax in axes:
        ax.yaxis.set_major_locator(ticker.MultipleLocator(cfg["y_tick_step"]))
        ax.tick_params(axis="both", which="both", length=3)

    fig.suptitle(
        f"Diversity fingerprints by migration topology ({cfg['title_domain']})",
        fontsize=13,
        fontweight="bold",
        y=1.04,
    )

    prefix = cfg["prefix"]
    for fmt in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{prefix}_panels.{fmt}")
    plt.close(fig)
    print(f"  {prefix}_panels.png/pdf saved")


# ============================================================================
# Plot 2: Overlay comparison
# ============================================================================

def plot_overlay(df, grouped, y_min, y_max, cfg):
    fig, ax = plt.subplots(figsize=(6, 3.5))

    for topo in TOPOLOGY_ORDER:
        seeds_df = grouped[topo]
        mean_line = seeds_df.mean(axis=1)
        std_line = seeds_df.std(axis=1)

        ax.fill_between(
            mean_line.index,
            mean_line - std_line,
            mean_line + std_line,
            color=COLORS[topo],
            alpha=0.12,
        )
        ax.plot(
            mean_line.index,
            mean_line.values,
            color=COLORS[topo],
            linewidth=2.0,
            label=TOPOLOGY_LABELS_SHORT[topo],
        )

    ax.set_xlim(0, 99)
    ax.set_ylim(y_min, y_max)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Hamming diversity")
    ax.set_title(
        f"Mean diversity by topology ({cfg['title_domain']})",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(frameon=True, framealpha=0.9, edgecolor="0.8", loc="upper right")
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(cfg["y_tick_step"]))

    prefix = cfg["prefix"]
    for fmt in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{prefix}_overlay.{fmt}")
    plt.close(fig)
    print(f"  {prefix}_overlay.png/pdf saved")


# ============================================================================
# Plot 3: Phase transition bar chart
# ============================================================================

def plot_phase_transition(df, grouped, y_min, y_max, cfg):
    max_gen = df["generation"].max()
    final = df[df["generation"] == max_gen]
    stats = (
        final.groupby("topology")["hamming_diversity"]
        .agg(["mean", "std"])
        .reindex(TOPOLOGY_ORDER)
    )

    fig, ax = plt.subplots(figsize=(5.5, 3.5))

    x = np.arange(len(TOPOLOGY_ORDER))
    bar_colors = [COLORS[t] for t in TOPOLOGY_ORDER]

    bars = ax.bar(
        x,
        stats["mean"],
        yerr=stats["std"],
        capsize=4,
        color=bar_colors,
        edgecolor="white",
        linewidth=0.8,
        width=0.65,
        error_kw={"linewidth": 1.2, "color": "0.3"},
    )

    # Annotate the none->ring gap
    none_mean = stats.loc["none", "mean"]
    ring_mean = stats.loc["ring", "mean"]
    drop_pct = (none_mean - ring_mean) / none_mean * 100

    # Bracket between none and ring bars
    bracket_y = none_mean + stats.loc["none", "std"] + 0.006
    ax.annotate(
        "",
        xy=(0, bracket_y),
        xytext=(1, bracket_y),
        arrowprops=dict(
            arrowstyle="<->",
            color="0.3",
            linewidth=1.2,
            shrinkA=0,
            shrinkB=0,
        ),
    )
    ax.text(
        0.5,
        bracket_y + 0.004,
        f"{drop_pct:.0f}% drop",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color="0.3",
    )

    # Annotate subsequent gaps
    prev_name = "ring"
    for i, topo in enumerate(TOPOLOGY_ORDER[2:], start=2):
        prev_mean = stats.loc[prev_name, "mean"]
        curr_mean = stats.loc[topo, "mean"]
        gap_pct = (prev_mean - curr_mean) / prev_mean * 100
        mid_y = (prev_mean + curr_mean) / 2
        ax.annotate(
            f"{gap_pct:.0f}%",
            xy=(i, curr_mean),
            xytext=(i - 0.5, mid_y + 0.003),
            fontsize=7.5,
            color="0.5",
            ha="center",
            va="bottom",
        )
        prev_name = topo

    # Horizontal reference line at none level
    ax.axhline(
        none_mean,
        color=COLORS["none"],
        linewidth=0.8,
        linestyle="--",
        alpha=0.4,
        zorder=0,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [TOPOLOGY_LABELS[t] for t in TOPOLOGY_ORDER],
        fontsize=9,
    )
    ax.set_ylabel(f"Final diversity (gen {max_gen})")
    ax.set_title(
        f"Phase transition: symmetry break at first coupling ({cfg['title_domain']})",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_ylim(0, bracket_y + 0.020)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.02))

    # Strict -> Lax arrow annotation below x-axis
    ax.annotate(
        "",
        xy=(4.3, -0.016),
        xytext=(-0.3, -0.016),
        xycoords=("data", "axes fraction"),
        textcoords=("data", "axes fraction"),
        arrowprops=dict(
            arrowstyle="->",
            color="0.5",
            linewidth=1.0,
        ),
        annotation_clip=False,
    )
    ax.text(
        2,
        -0.08,
        "strict                                                       lax",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=8,
        color="0.5",
        style="italic",
    )

    prefix = cfg["prefix"]
    for fmt in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{prefix.replace('fingerprints', 'phase_transition')}.{fmt}")
    plt.close(fig)
    print(f"  {prefix.replace('fingerprints', 'phase_transition')}.png/pdf saved")


# ============================================================================
# Plot 4: Domain comparison (OneMax vs Maze)
# ============================================================================

def plot_domain_comparison():
    """Overlay OneMax and Maze mean diversity on the same figure.

    Same topology colors; solid lines for OneMax, dashed for Maze.
    Uses min-max normalization per domain so the two scales are comparable.
    """
    # Load both domains
    df_om, grouped_om, _, _, cfg_om = load_domain("onemax")
    df_mz, grouped_mz, _, _, cfg_mz = load_domain("maze")

    max_gen = min(df_om["generation"].max(), df_mz["generation"].max())

    # --- Helper: compute per-topology mean traces and normalize to [0,1] ---
    def mean_traces(grouped):
        traces = {}
        for topo in TOPOLOGY_ORDER:
            traces[topo] = grouped[topo].mean(axis=1)
        return traces

    def normalize_traces(traces):
        """Min-max normalize across all topologies in a domain."""
        all_vals = np.concatenate([t.values for t in traces.values()])
        vmin, vmax = all_vals.min(), all_vals.max()
        return {t: (v - vmin) / (vmax - vmin) for t, v in traces.items()}, vmin, vmax

    om_traces = mean_traces(grouped_om)
    mz_traces = mean_traces(grouped_mz)

    om_norm, om_min, om_max = normalize_traces(om_traces)
    mz_norm, mz_min, mz_max = normalize_traces(mz_traces)

    # ---- Figure: Normalized overlay ----
    fig, ax = plt.subplots(figsize=(7, 4))

    for topo in TOPOLOGY_ORDER:
        color = COLORS[topo]
        label_short = TOPOLOGY_LABELS_SHORT[topo]

        # OneMax: solid
        ax.plot(
            om_norm[topo].index,
            om_norm[topo].values,
            color=color,
            linewidth=2.0,
            linestyle="-",
            label=f"{label_short} (OneMax)",
        )
        # Maze: dashed
        ax.plot(
            mz_norm[topo].index,
            mz_norm[topo].values,
            color=color,
            linewidth=2.0,
            linestyle="--",
            label=f"{label_short} (Maze)",
        )

    ax.set_xlim(0, max_gen)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Generation")
    ax.set_ylabel("Normalized diversity (min-max per domain)")
    ax.set_title(
        "Domain comparison: topology ordering is domain-invariant",
        fontsize=12,
        fontweight="bold",
    )
    ax.xaxis.set_major_locator(ticker.MultipleLocator(25))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))

    # Custom legend: group by line style
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="0.4", linewidth=2, linestyle="-", label="OneMax"),
        Line2D([0], [0], color="0.4", linewidth=2, linestyle="--", label="Maze"),
        Line2D([0], [0], color="none", label=""),  # spacer
    ]
    for topo in TOPOLOGY_ORDER:
        legend_elements.append(
            Line2D([0], [0], color=COLORS[topo], linewidth=2.5, linestyle="-",
                   label=TOPOLOGY_LABELS_SHORT[topo])
        )

    ax.legend(
        handles=legend_elements,
        frameon=True,
        framealpha=0.9,
        edgecolor="0.8",
        loc="upper right",
        fontsize=8.5,
    )

    for fmt in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"domain_comparison.{fmt}")
    plt.close(fig)
    print(f"  domain_comparison.png/pdf saved")

    # ---- Print comparison table ----
    print("\n  Domain comparison — final diversity (gen 99):")
    print(f"  {'Topology':<20} {'OneMax':>10} {'Maze':>10} {'Ratio':>8}")
    print(f"  {'-'*50}")
    for topo in TOPOLOGY_ORDER:
        om_final = om_traces[topo].iloc[-1]
        mz_final = mz_traces[topo].iloc[-1]
        print(f"  {TOPOLOGY_LABELS_SHORT[topo]:<20} {om_final:>10.4f} {mz_final:>10.4f} {mz_final/om_final:>8.2f}")


# ============================================================================
# Run per-domain plots
# ============================================================================

def run_domain(domain_key):
    """Generate all three standard plots for one domain."""
    df, grouped, y_min, y_max, cfg = load_domain(domain_key)
    plot_fingerprint_panels(df, grouped, y_min, y_max, cfg)
    plot_overlay(df, grouped, y_min, y_max, cfg)
    plot_phase_transition(df, grouped, y_min, y_max, cfg)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate diversity fingerprint plots for topology sweep experiments."
    )
    parser.add_argument(
        "--domain",
        choices=["onemax", "maze", "checkers", "comparison", "all"],
        default="onemax",
        help="Which domain to plot (default: onemax for backward compatibility)",
    )
    args = parser.parse_args()

    setup_style()

    if args.domain == "all":
        print("Generating OneMax fingerprint plots...")
        run_domain("onemax")
        print("\nGenerating Maze fingerprint plots...")
        run_domain("maze")
        print("\nGenerating Checkers fingerprint plots...")
        run_domain("checkers")
        print("\nGenerating domain comparison plot...")
        plot_domain_comparison()
    elif args.domain == "comparison":
        print("Generating domain comparison plot...")
        plot_domain_comparison()
    else:
        print(f"Generating {args.domain} fingerprint plots...")
        run_domain(args.domain)

    print(f"\nAll plots saved to {OUT_DIR.resolve()}")
    print("Formats: PNG (300 DPI) + PDF")
