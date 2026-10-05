"""Reproduce every number, table and data figure in the paper from data/scores.csv.

    python3 analysis/analyze.py

Writes paper/figures/*.pdf and paper/generated/*.tex. Needs numpy, scipy, matplotlib.
No model is called: the pilot data are the hand scores recorded in February 2025.
"""

from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "scores.csv"
FIG = ROOT / "paper" / "figures"
GEN = ROOT / "paper" / "generated"

MODELS = ["GPT-4o", "DeepSeek-R1", "Qwen2.5 72B", "Llama 3 70B"]
QUESTIONS = ["Q1 algebra", "Q2 reading"]
QLABEL = {"Q1 algebra": "Q1 (algebra)", "Q2 reading": "Q2 (reading)"}
CATS = ["clarity", "understanding", "format", "answer"]
CAT_MAX = {"clarity": 7, "understanding": 3, "format": 3, "answer": 5}
TOTAL_MAX = sum(CAT_MAX.values())

# Okabe-Ito, colour-blind safe, one hue per model throughout the paper.
COLOR = {
    "GPT-4o": "#0072B2",
    "DeepSeek-R1": "#D55E00",
    "Qwen2.5 72B": "#009E73",
    "Llama 3 70B": "#CC79A7",
}
MARKER = {"GPT-4o": "o", "DeepSeek-R1": "s", "Qwen2.5 72B": "D", "Llama 3 70B": "^"}


def load() -> dict[tuple[str, str, str], dict[str, int]]:
    rows = {}
    with DATA.open() as f:
        for r in csv.DictReader(f):
            key = (r["question"], r["version"], r["model"])
            rows[key] = {c: int(r[c]) for c in CATS + ["total"]}
            assert sum(rows[key][c] for c in CATS) == rows[key]["total"], key
            for c in CATS:
                assert 0 <= rows[key][c] <= CAT_MAX[c], (key, c)
    assert len(rows) == len(MODELS) * len(QUESTIONS) * 2, "expected a complete 4x2x2 design"
    return rows


def delta(rows, q, m, c):
    """Unformatted minus formatted; negative means the rewrite scored lower."""
    return rows[(q, "unformatted", m)][c] - rows[(q, "formatted", m)][c]


def sign_flip_p(d: list[int]) -> float:
    """Exact one-sided paired permutation p-value for mean(d) <= observed (H1: rewrite lowers scores)."""
    d = np.asarray(d, dtype=float)
    obs = d.mean()
    flips = [np.mean(d * np.array(s)) for s in itertools.product([1, -1], repeat=len(d))]
    return sum(f <= obs + 1e-12 for f in flips) / len(flips)


def paired_n(dz: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """Smallest n for a two-sided paired t-test to reach `power` at standardized effect dz."""
    for n in range(3, 10_000):
        df = n - 1
        tcrit = stats.t.ppf(1 - alpha / 2, df)
        nc = dz * math.sqrt(n)
        achieved = 1 - stats.nct.cdf(tcrit, df, nc) + stats.nct.cdf(-tcrit, df, nc)
        if achieved >= power:
            return n
    raise RuntimeError("no n found")


def fmt(x: float, nd: int = 2) -> str:
    s = f"{x:.{nd}f}"
    return s.replace("-", "$-$") if x < 0 else s


WORDS = "zero one two three four five six seven eight".split()


def word(n: int) -> str:
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def pval(p: float) -> str:
    return f"{p:.4g}"


def macro(name: str, value: str) -> str:
    return f"\\newcommand{{\\{name}}}{{{value}}}\n"


def setup_style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.titlesize": 9.5,
            "axes.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "legend.frameon": False,
            "pdf.fonttype": 42,
        }
    )


def fig_paired(rows):
    """Total score per model, formatted vs. unformatted, one panel per question."""
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.7), sharey=True)
    jitter = dict(zip(MODELS, [-0.045, -0.015, 0.015, 0.045]))
    for ax, q in zip(axes, QUESTIONS):
        for m in MODELS:
            y = [rows[(q, "formatted", m)]["total"], rows[(q, "unformatted", m)]["total"]]
            x = [0 + jitter[m], 1 + jitter[m]]
            ax.plot(x, y, color=COLOR[m], lw=1.4, alpha=0.9, zorder=2)
            ax.scatter(x, y, color=COLOR[m], marker=MARKER[m], s=30, zorder=3,
                       edgecolor="white", linewidth=0.6, label=m)
        means = [np.mean([rows[(q, v, m)]["total"] for m in MODELS]) for v in ("formatted", "unformatted")]
        ax.plot([0, 1], means, color="black", lw=2.2, ls=(0, (1, 1.2)), zorder=4, label="Mean")
        ax.set_title(QLABEL[q])
        ax.set_xticks([0, 1], ["Original\n(SAT layout)", "Rewritten\n(plain prose)"])
        ax.set_xlim(-0.35, 1.35)
        ax.set_ylim(12, 18.6)
        ax.set_yticks(range(12, 19))
        ax.grid(axis="y", lw=0.4, color="#d9d9d9", zorder=0)
    axes[0].set_ylabel(f"Total score (of {TOTAL_MAX})")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.04), fontsize=8,
               handletextpad=0.3, columnspacing=1.1)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIG / "paired-totals.pdf")
    plt.close(fig)


def fig_deltas(rows):
    """Per-model change in each rubric category (rewritten minus original)."""
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.35), sharey=True)
    cmap = plt.get_cmap("RdBu")
    lim = 3
    for ax, q in zip(axes, QUESTIONS):
        M = np.array([[delta(rows, q, m, c) for c in CATS] for m in MODELS])
        im = ax.imshow(M, cmap=cmap, vmin=-lim, vmax=lim, aspect="auto")
        for i, j in itertools.product(range(M.shape[0]), range(M.shape[1])):
            v = M[i, j]
            ax.text(j, i, f"{v:+d}".replace("-", "\u2212") if v else "0", ha="center", va="center", fontsize=8.5,
                    color="white" if abs(v) >= 2.5 else "black")
        ax.set_xticks(range(len(CATS)), [f"{c.capitalize()}\n(/{CAT_MAX[c]})" for c in CATS], fontsize=7.8)
        ax.set_yticks(range(len(MODELS)), MODELS)
        ax.set_title(QLABEL[q])
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
    cb = fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, ticks=range(-lim, lim + 1))
    cb.set_label("Rewritten $-$ original", fontsize=8)
    cb.outline.set_linewidth(0.4)
    fig.savefig(FIG / "category-deltas.pdf", bbox_inches="tight")
    plt.close(fig)


def tables_and_macros(rows):
    GEN.mkdir(parents=True, exist_ok=True)
    out = []

    # Table: full scores.
    t = []
    for q in QUESTIONS:
        for i, m in enumerate(MODELS):
            f, u = rows[(q, "formatted", m)], rows[(q, "unformatted", m)]
            qcell = f"\\multirow{{4}}{{*}}{{{QLABEL[q]}}}" if i == 0 else ""
            cells = [f"{f[c]} / {u[c]}" for c in CATS]
            d = u["total"] - f["total"]
            t.append(f"{qcell} & {m} & " + " & ".join(cells) + f" & {f['total']} / {u['total']} & {fmt(d, 0) if d else '0'} \\\\")
        mf = np.mean([rows[(q, 'formatted', m)]['total'] for m in MODELS])
        mu = np.mean([rows[(q, 'unformatted', m)]['total'] for m in MODELS])
        catmeans = [f"{np.mean([rows[(q,'formatted',m)][c] for m in MODELS]):.2f} / {np.mean([rows[(q,'unformatted',m)][c] for m in MODELS]):.2f}" for c in CATS]
        t.append(f"\\cmidrule(l){{2-8}} & \\textit{{Mean}} & " + " & ".join(catmeans) + f" & {mf:.2f} / {mu:.2f} & {fmt(mu - mf)} \\\\")
        if q != QUESTIONS[-1]:
            t.append("\\midrule")
    head = [
        "\\begin{tabular}{@{}ll cccc c r@{}}",
        "\\toprule",
        f"Item & Model & Clarity (/7) & Underst.\\ (/3) & Format (/3) & Answer (/5) & Total (/{TOTAL_MAX}) & $\\Delta$ \\\\",
        "\\midrule",
    ]
    tail = ["\\bottomrule", "\\end{tabular}"]
    (GEN / "scores-table.tex").write_text("\n".join(head + t + tail) + "\n")

    # Macros used in the prose, so the text cannot drift from the data.
    names = {"Q1 algebra": "One", "Q2 reading": "Two"}
    for q in QUESTIONS:
        n = names[q]
        d_tot = [delta(rows, q, m, "total") for m in MODELS]
        d_cla = [delta(rows, q, m, "clarity") for m in MODELS]
        d_und = [delta(rows, q, m, "understanding") for m in MODELS]
        out.append(macro(f"Q{n}MeanF", f"{np.mean([rows[(q,'formatted',m)]['total'] for m in MODELS]):.2f}"))
        out.append(macro(f"Q{n}MeanU", f"{np.mean([rows[(q,'unformatted',m)]['total'] for m in MODELS]):.2f}"))
        out.append(macro(f"Q{n}MeanDelta", f"{np.mean(d_tot):.2f}"))
        out.append(macro(f"Q{n}ClarityDelta", f"{np.mean(d_cla):.2f}"))
        out.append(macro(f"Q{n}UnderDelta", f"{np.mean(d_und):.2f}"))
        out.append(macro(f"Q{n}NumLower", str(sum(x < 0 for x in d_tot))))
        out.append(macro(f"Q{n}NumTied", str(sum(x == 0 for x in d_tot))))
        out.append(macro(f"Q{n}SignP", pval(stats.binomtest(sum(x < 0 for x in d_tot), sum(x != 0 for x in d_tot), 0.5, alternative='greater').pvalue)))
        out.append(macro(f"Q{n}PermP", pval(sign_flip_p(d_tot))))
        out.append(macro(f"Q{n}MinP", pval(0.5 ** len(MODELS))))
        # Share of the total change carried by clarity.
        out.append(macro(f"Q{n}ClarityShare", f"{100 * sum(d_cla) / sum(d_tot):.0f}" if sum(d_tot) else "0"))

    all_d = [delta(rows, q, m, "total") for q in QUESTIONS for m in MODELS]
    out.append(macro("AllNumLower", word(sum(x < 0 for x in all_d))))
    out.append(macro("AllNumTied", word(sum(x == 0 for x in all_d))))
    higher = sum(x > 0 for x in all_d)
    out.append(macro("AllNumHigher", "none" if higher == 0 else word(higher)))

    ceil = sum(
        rows[k]["format"] == CAT_MAX["format"] and rows[k]["answer"] == CAT_MAX["answer"] for k in rows
    )
    out.append(macro("NumResponses", str(len(rows))))
    out.append(macro("NumAtCeiling", str(ceil)))
    out.append(macro("CeilingPoints", str(CAT_MAX["format"] + CAT_MAX["answer"])))
    out.append(macro("CeilingShare", f"{100 * (CAT_MAX['format'] + CAT_MAX['answer']) / TOTAL_MAX:.0f}"))
    out.append(macro("TotalMax", str(TOTAL_MAX)))

    # Largest single drop.
    worst = min(((delta(rows, q, m, "clarity"), q, m) for q in QUESTIONS for m in MODELS))
    out.append(macro("WorstClarityModel", worst[2]))
    out.append(macro("WorstClarityF", str(rows[(worst[1], "formatted", worst[2])]["clarity"])))
    out.append(macro("WorstClarityU", str(rows[(worst[1], "unformatted", worst[2])]["clarity"])))

    for dz, tag in [(0.3, "Three"), (0.5, "Five")]:
        out.append(macro(f"PowerN{tag}", str(paired_n(dz))))

    (GEN / "stats.tex").write_text("% Generated by analysis/analyze.py. Do not edit.\n" + "".join(out))
    return out


def main():
    np.seterr(all="ignore")  # scipy's noncentral-t CDF warns on extreme tails during the power search
    FIG.mkdir(parents=True, exist_ok=True)
    setup_style()
    rows = load()
    for k, v in rows.items():
        v["total"] = sum(v[c] for c in CATS)
    fig_paired(rows)
    fig_deltas(rows)
    for line in tables_and_macros(rows):
        print(line, end="")


if __name__ == "__main__":
    main()
