#!/usr/bin/env python3
"""generate_plots.py - figures for the report, straight from the CSVs.

Every number plotted here comes from results/*.csv, which in turn come
from real stats.txt files (see extract_stats.py). Axis labels use the
standard English technical terms; the Persian captions live in the
LaTeX report.

Outputs (report/figures/):
  matrix_ipc.png            IPC of the four matrix runs
  matrix_simticks.png       simTicks of the four matrix runs
  matrix_missrates.png      L1i/L1d/L2 miss rates (cache runs)
  matrix_speedup.png        speedups (simTicks ratio, formula in label)
  list_ipc.png              IPC of the four linked-list runs
  list_simseconds.png       simSeconds of the four linked-list runs
"""

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
FIG_DIR = os.path.join(PROJECT_ROOT, "report", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

COLORS = ["#4878CF", "#EE854A", "#6ACC65", "#D65F5F"]


def load(name):
    with open(os.path.join(RESULTS_DIR, name), newline="") as fh:
        return {row["run"]: row for row in csv.DictReader(fh)}


def fnum(row, key):
    v = row.get(key, "")
    if v in ("", None):
        raise ValueError(f"metric {key} missing for run {row.get('run')}")
    return float(v)


def bar(ax, labels, values, colors=None, fmt="{:.3f}"):
    bars = ax.bar(labels, values, color=colors or COLORS[: len(values)],
                  edgecolor="black", linewidth=0.6)
    for b, v in zip(bars, values):
        ax.annotate(fmt.format(v), (b.get_x() + b.get_width() / 2, v),
                    ha="center", va="bottom", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)


def save(fig, name):
    path = os.path.join(FIG_DIR, name)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"wrote {path}")


def main():
    m = load("matrix_results.csv")
    l = load("linked_list_results.csv")

    matrix_runs = ["matrix_no_cache_naive", "matrix_no_cache_tiled",
                   "matrix_cache_naive", "matrix_cache_tiled"]
    matrix_labels = ["No-cache\nNaive", "No-cache\nTiled",
                     "Cache\nNaive", "Cache\nTiled"]

    # 1. IPC - matrix
    fig, ax = plt.subplots(figsize=(6.5, 4))
    bar(ax, matrix_labels, [fnum(m[r], "ipc") for r in matrix_runs])
    ax.set_ylabel("IPC (instructions per cycle)")
    ax.set_title("Matrix Multiplication - IPC (TimingSimpleCPU, 2 GHz)")
    save(fig, "matrix_ipc.png")

    # 2. simTicks - matrix
    fig, ax = plt.subplots(figsize=(6.5, 4))
    vals = [fnum(m[r], "simTicks") / 1e9 for r in matrix_runs]
    bar(ax, matrix_labels, vals, fmt="{:.2f}")
    ax.set_ylabel("simTicks (x 10^9 ticks)")
    ax.set_title("Matrix Multiplication - simTicks")
    save(fig, "matrix_simticks.png")

    # 3. miss rates - cache runs
    fig, ax = plt.subplots(figsize=(6.5, 4))
    cats = ["L1i", "L1d", "L2"]
    naive = [fnum(m["matrix_cache_naive"], k) * 100
             for k in ("l1i_missRate", "l1d_missRate", "l2_missRate")]
    tiled = [fnum(m["matrix_cache_tiled"], k) * 100
             for k in ("l1i_missRate", "l1d_missRate", "l2_missRate")]
    x = range(len(cats))
    w = 0.35
    b1 = ax.bar([i - w / 2 for i in x], naive, w, label="Naive",
                color=COLORS[0], edgecolor="black", linewidth=0.6)
    b2 = ax.bar([i + w / 2 for i in x], tiled, w, label="Tiled",
                color=COLORS[1], edgecolor="black", linewidth=0.6)
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.2f}%",
                        (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cats)
    ax.set_ylabel("Miss rate (%)")
    ax.set_title("Cache Miss Rates - Naive vs Tiled (overall, demand)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    save(fig, "matrix_missrates.png")

    # 4. speedups: S = simTicks(reference) / simTicks(improved)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    t = {r: fnum(m[r], "simTicks") for r in matrix_runs}
    speedups = [
        ("Tiled vs Naive\n(no cache)",
         t["matrix_no_cache_naive"] / t["matrix_no_cache_tiled"]),
        ("Tiled vs Naive\n(with cache)",
         t["matrix_cache_naive"] / t["matrix_cache_tiled"]),
        ("Cache vs No-cache\n(Naive)",
         t["matrix_no_cache_naive"] / t["matrix_cache_naive"]),
        ("Cache vs No-cache\n(Tiled)",
         t["matrix_no_cache_tiled"] / t["matrix_cache_tiled"]),
    ]
    bar(ax, [s[0] for s in speedups], [s[1] for s in speedups], fmt="{:.2f}x")
    ax.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    ax.set_ylabel("Speedup  S = simTicks(base) / simTicks(new)")
    ax.set_title("Matrix Multiplication - Speedups")
    save(fig, "matrix_speedup.png")

    list_runs = ["list_recursive_atomic", "list_recursive_o3",
                 "list_iterative_atomic", "list_iterative_o3"]
    list_labels = ["Recursive\nAtomic", "Recursive\nO3",
                   "Iterative\nAtomic", "Iterative\nO3"]

    # 5. IPC - linked list
    fig, ax = plt.subplots(figsize=(6.5, 4))
    bar(ax, list_labels, [fnum(l[r], "ipc") for r in list_runs])
    ax.set_ylabel("IPC (instructions per cycle)")
    ax.set_title("Linked-List Reversal - IPC by CPU model")
    save(fig, "list_ipc.png")

    # 6. simSeconds - linked list
    fig, ax = plt.subplots(figsize=(6.5, 4))
    vals = [fnum(l[r], "simSeconds") * 1e3 for r in list_runs]
    bar(ax, list_labels, vals, fmt="{:.3f}")
    ax.set_ylabel("simSeconds (ms)")
    ax.set_title("Linked-List Reversal - simSeconds by CPU model")
    save(fig, "list_simseconds.png")

    print("generate_plots.py: done")


if __name__ == "__main__":
    main()
