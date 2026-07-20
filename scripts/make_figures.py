#!/usr/bin/env python
"""Generate publication figures for the Cognitive Systems Research submission.

Reads ONLY the locked results CSVs:
    results/study2_summary.csv        (per-repetition condition summaries, Study 2)
    results/study2_paired_stats.csv   (paired bootstrap stats, Study 2)
    results/study2b_summary.csv       (per-repetition condition summaries, Study 2b)
    results/study2b_paired_stats.csv  (paired bootstrap stats, Study 2b)

Writes to manuscript/submission_package/figures/:
    Figure_1.png / Figure_1.pdf   Study 2 accuracy: condition means + paired difference CIs
    Figure_2.png / Figure_2.pdf   Study 2 previous-rule-aligned errors: Full - WSLS forest plot
    Figure_3.png / Figure_3.pdf   Study 2b previous-rule-aligned errors: P1 and S1 forest plot

Fully deterministic: no randomness anywhere. All plotted quantities are read
directly from the CSVs (condition means are arithmetic means over repetitions;
all confidence intervals are the pre-computed paired-bootstrap CIs from the
locked *_paired_stats.csv files -- no CIs are computed or invented here).
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(REPO, "results")
OUTDIR = os.path.join(REPO, "manuscript", "submission_package", "figures")

# ---------------------------------------------------------------------------
# Fixed model order and display names (consistent across all figures)
# ---------------------------------------------------------------------------
MODEL_ORDER = [
    ("claude-opus-4-8", "Claude Opus 4.8"),
    ("claude-sonnet-5", "Claude Sonnet 5"),
    ("gpt-5.5-2026-04-23", "GPT-5.5"),
    ("gpt-5.4-mini-2026-03-17", "GPT-5.4 mini"),
]
MODEL_IDS = [m for m, _ in MODEL_ORDER]
MODEL_LABELS = {m: lbl for m, lbl in MODEL_ORDER}

# Okabe-Ito colorblind-safe palette; grayscale legibility is carried by
# distinct marker shapes and fill (never by color alone).
C_BLUE = "#0072B2"
C_ORANGE = "#E69F00"
C_GREEN = "#009E73"
C_VERM = "#D55E00"
C_GRAY = "#4D4D4D"

# Non-inferiority margin for Study 2b S1 (frozen in the Study 2b analysis plan)
S1_MARGIN = 1.9917

ERR_XLABEL = "difference in previous-rule-aligned errors per repetition (36 trials)"


def set_style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "STIXGeneral", "STIX Two Text"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 300,
        }
    )


def load_data():
    s2_sum = pd.read_csv(os.path.join(RESULTS, "study2_summary.csv"))
    s2_ps = pd.read_csv(os.path.join(RESULTS, "study2_paired_stats.csv"))
    s2b_ps = pd.read_csv(os.path.join(RESULTS, "study2b_paired_stats.csv"))
    return s2_sum, s2_ps, s2b_ps


def get_pair(ps, model, comparison, metric, family):
    """Fetch one paired-stats row; error out loudly if not exactly one."""
    sel = ps[
        (ps["model"] == model)
        & (ps["comparison"] == comparison)
        & (ps["metric"] == metric)
        & (ps["family"] == family)
    ]
    if len(sel) != 1:
        raise ValueError(
            f"Expected exactly 1 row for {model} / {comparison} / {metric} / "
            f"{family}, got {len(sel)}"
        )
    r = sel.iloc[0]
    return float(r["mean_diff"]), float(r["ci_low"]), float(r["ci_high"])


def panel_letter(ax, letter):
    ax.text(
        -0.14,
        1.02,
        letter,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def save(fig, name):
    os.makedirs(OUTDIR, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUTDIR, f"{name}.{ext}"))
    plt.close(fig)
    print(f"wrote {name}.png / {name}.pdf")


# ---------------------------------------------------------------------------
# Figure 1: Study 2 accuracy -- condition means (A) + paired difference CIs (B)
# ---------------------------------------------------------------------------
def figure_1(s2_sum, s2_ps):
    conditions = [
        ("RawLLM", "Raw LLM", "o", "none", C_GRAY),
        ("RuleBlindFull", "Rule-Blind Full", "s", C_BLUE, C_BLUE),
        ("WSLSBudgeted", "WSLS Budgeted", "^", C_ORANGE, C_ORANGE),
    ]

    # Condition means over repetitions (per-condition bootstrap CIs are not
    # part of the locked stats, so panel A shows means only; uncertainty is
    # shown honestly in panel B via the paired-difference CIs).
    means = {}
    for model in MODEL_IDS:
        for cond, *_ in conditions:
            sub = s2_sum[(s2_sum["model"] == model) & (s2_sum["condition"] == cond)]
            if len(sub) != 130:
                raise ValueError(f"{model}/{cond}: expected 130 reps, got {len(sub)}")
            means[(model, cond)] = float(sub["total_accuracy"].mean())

    comparisons = [
        ("RuleBlindFull vs RawLLM", "Full $-$ Raw", "s", C_BLUE, C_BLUE),
        ("WSLSBudgeted vs RawLLM", "WSLS $-$ Raw", "^", C_ORANGE, C_ORANGE),
        ("WSLSBudgeted vs RuleBlindFull", "WSLS $-$ Full", "D", "none", C_GREEN),
    ]
    diffs = {}
    for model in MODEL_IDS:
        for comp, *_ in comparisons:
            diffs[(model, comp)] = get_pair(
                s2_ps, model, comp, "total_accuracy", "primary"
            )
    # Consistency check: paired mean difference must equal difference of
    # condition means over the same 130 repetitions.
    for model in MODEL_IDS:
        d_full_raw = means[(model, "RuleBlindFull")] - means[(model, "RawLLM")]
        if abs(d_full_raw - diffs[(model, "RuleBlindFull vs RawLLM")][0]) > 5e-4:
            raise ValueError(f"Mean-diff consistency check failed for {model}")

    fig, (axA, axB) = plt.subplots(
        1, 2, figsize=(6.5, 2.9), gridspec_kw={"width_ratios": [1.0, 1.15]}
    )
    fig.subplots_adjust(left=0.085, right=0.99, bottom=0.24, top=0.92, wspace=0.32)

    # Panel A: condition means
    x = range(len(MODEL_IDS))
    offsets = (-0.22, 0.0, 0.22)
    for (cond, lbl, marker, mfc, mec), off in zip(conditions, offsets):
        ys = [means[(m, cond)] for m in MODEL_IDS]
        axA.plot(
            [xi + off for xi in x],
            ys,
            linestyle="none",
            marker=marker,
            markersize=5,
            markerfacecolor=mfc,
            markeredgecolor=mec,
            markeredgewidth=0.9,
            label=lbl,
        )
        print(f"  [Fig1A] {cond}: " + ", ".join(f"{m}={v:.4f}" for m, v in zip(MODEL_IDS, ys)))
    axA.set_xticks(list(x))
    axA.set_xticklabels(
        [MODEL_LABELS[m].replace(" ", "\n", 1) for m in MODEL_IDS], fontsize=8
    )
    axA.set_ylabel("proportion correct")
    axA.set_ylim(0.30, 0.60)
    axA.set_xlim(-0.55, len(MODEL_IDS) - 0.45)
    axA.legend(loc="upper right", handletextpad=0.2, borderaxespad=0.1)
    panel_letter(axA, "A")

    # Panel B: paired differences with bootstrap 95% CIs (forest style)
    n_comp = len(comparisons)
    row_h = 1.0
    yticks, ylabels = [], []
    for mi, model in enumerate(MODEL_IDS):
        base = (len(MODEL_IDS) - 1 - mi) * (n_comp + 1) * row_h
        yticks.append(base + (n_comp - 1) / 2.0)
        ylabels.append(MODEL_LABELS[model])
        for ci_i, (comp, lbl, marker, mfc, mec) in enumerate(comparisons):
            md, lo, hi = diffs[(model, comp)]
            y = base + (n_comp - 1 - ci_i)
            axB.plot([lo, hi], [y, y], color=mec, linewidth=0.9, solid_capstyle="butt")
            axB.plot(
                [md],
                [y],
                marker=marker,
                markersize=4.2,
                markerfacecolor=mfc,
                markeredgecolor=mec,
                markeredgewidth=0.9,
                linestyle="none",
                label=lbl if mi == 0 else None,
            )
            print(f"  [Fig1B] {model} {comp}: {md:.4f} [{lo:.4f}, {hi:.4f}]")
    axB.axvline(0.0, color="black", linewidth=0.7)
    axB.set_yticks(yticks)
    axB.set_yticklabels(ylabels, fontsize=8)
    axB.set_xlabel("$\\Delta$ proportion correct (paired bootstrap 95% CI)")
    axB.set_xlim(-0.02, 0.265)
    axB.set_xticks([0.00, 0.05, 0.10, 0.15, 0.20, 0.25])
    axB.legend(loc="center right", handletextpad=0.2, borderaxespad=0.1)
    axB.spines["left"].set_visible(False)
    axB.tick_params(axis="y", length=0)
    panel_letter(axB, "B")

    save(fig, "Figure_1")


# ---------------------------------------------------------------------------
# Figure 2: Study 2 previous-rule-aligned errors, Full - WSLS (forest plot)
# ---------------------------------------------------------------------------
def figure_2(s2_ps):
    vals = {
        m: get_pair(
            s2_ps, m, "RuleBlindFull vs WSLSBudgeted", "prev_rule_error_count", "primary"
        )
        for m in MODEL_IDS
    }

    fig, ax = plt.subplots(figsize=(6.5, 2.2))
    fig.subplots_adjust(left=0.17, right=0.97, bottom=0.34, top=0.90)

    n = len(MODEL_IDS)
    for mi, model in enumerate(MODEL_IDS):
        md, lo, hi = vals[model]
        y = n - 1 - mi
        ax.plot([lo, hi], [y, y], color=C_BLUE, linewidth=1.1, solid_capstyle="butt")
        for xend in (lo, hi):
            ax.plot([xend, xend], [y - 0.10, y + 0.10], color=C_BLUE, linewidth=1.1)
        ax.plot(
            [md],
            [y],
            marker="s",
            markersize=4.5,
            markerfacecolor=C_BLUE,
            markeredgecolor=C_BLUE,
            linestyle="none",
        )
        print(f"  [Fig2] {model} Full-WSLS prev-rule errors: {md:.4f} [{lo:.4f}, {hi:.4f}]")

    ax.axvline(0.0, color="black", linewidth=0.8)
    # Frozen predicted direction: RuleBlindFull commits FEWER previous-rule-
    # aligned errors than WSLSBudgeted (difference < 0).
    ax.annotate(
        "",
        xy=(-0.85, n - 0.35),
        xytext=(-0.08, n - 0.35),
        arrowprops=dict(arrowstyle="->", color=C_GRAY, linewidth=0.9),
        annotation_clip=False,
    )
    ax.text(
        -0.465,
        n - 0.27,
        "frozen predicted direction\n(fewer errors under Full)",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=C_GRAY,
    )
    ax.set_yticks([n - 1 - i for i in range(n)])
    ax.set_yticklabels([MODEL_LABELS[m] for m in MODEL_IDS], fontsize=8.5)
    ax.set_xlabel(f"Full $-$ WSLS {ERR_XLABEL}")
    ax.set_xlim(-1.45, 1.45)
    ax.set_ylim(-0.5, n + 0.45)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    save(fig, "Figure_2")


# ---------------------------------------------------------------------------
# Figure 3: Study 2b previous-rule-aligned errors, P1 and S1 (forest plot)
# ---------------------------------------------------------------------------
def figure_3(s2b_ps):
    p1 = {
        m: get_pair(s2b_ps, m, "WCDMinimal vs RawLLM", "prev_rule_error_count", "primary")
        for m in MODEL_IDS
    }
    s1 = {
        m: get_pair(
            s2b_ps, m, "WCDMinimal vs RuleBlindFull", "prev_rule_error_count", "exploratory"
        )
        for m in MODEL_IDS
    }

    fig, ax = plt.subplots(figsize=(6.5, 2.7))
    fig.subplots_adjust(left=0.17, right=0.97, bottom=0.28, top=0.97)

    n = len(MODEL_IDS)
    spacing = 2.4
    series = [
        (p1, "P1: WCD $-$ Raw", "o", C_BLUE, C_BLUE, +0.42),
        (s1, "S1: WCD $-$ Full", "s", "none", C_VERM, -0.42),
    ]
    yticks, ylabels = [], []
    for mi, model in enumerate(MODEL_IDS):
        base = (n - 1 - mi) * spacing
        yticks.append(base)
        ylabels.append(MODEL_LABELS[model])
        for vals, lbl, marker, mfc, mec, off in series:
            md, lo, hi = vals[model]
            y = base + off
            ax.plot([lo, hi], [y, y], color=mec, linewidth=1.1, solid_capstyle="butt")
            for xend in (lo, hi):
                ax.plot([xend, xend], [y - 0.14, y + 0.14], color=mec, linewidth=1.1)
            ax.plot(
                [md],
                [y],
                marker=marker,
                markersize=4.5,
                markerfacecolor=mfc,
                markeredgecolor=mec,
                markeredgewidth=1.0,
                linestyle="none",
                label=lbl if mi == 0 else None,
            )
            print(f"  [Fig3] {model} {lbl}: {md:.4f} [{lo:.4f}, {hi:.4f}]")

    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.axvline(S1_MARGIN, color=C_GRAY, linewidth=0.9, linestyle=(0, (4, 2.5)))
    ax.text(
        S1_MARGIN - 0.10,
        (n - 1) * spacing + 0.85,
        "S1 non-inferiority\nmargin ($\\Delta$ = +1.9917)",
        fontsize=7.5,
        color=C_GRAY,
        ha="right",
        va="top",
    )
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels, fontsize=8.5)
    ax.set_xlabel(ERR_XLABEL)
    ax.set_xlim(-5.9, 3.3)
    ax.set_ylim(-1.0, (n - 1) * spacing + 1.0)
    ax.legend(loc="lower left", handletextpad=0.2, borderaxespad=0.1)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    save(fig, "Figure_3")


def main():
    set_style()
    s2_sum, s2_ps, s2b_ps = load_data()
    print("Figure 1")
    figure_1(s2_sum, s2_ps)
    print("Figure 2")
    figure_2(s2_ps)
    print("Figure 3")
    figure_3(s2b_ps)
    print("done")


if __name__ == "__main__":
    sys.exit(main())
