#!/usr/bin/env python3
"""extract_stats.py - robust gem5 stats.txt parser and CSV generator.

Reads every stats.txt under results/raw/<run>/, resolves each requested
metric through a list of known gem5 aliases (old snake_case names and the
new camelCase names), and writes:

  results/summary.csv             all runs x all metrics (+ source stat key)
  results/matrix_results.csv      the four matrix runs
  results/linked_list_results.csv the four linked-list runs
  results/config_parameters.csv   Q2: clock domain / memory mode / memory
                                  size taken from the RUNTIME config.ini
                                  of the Question-1 runs (not from source
                                  defaults)

Rules honoured:
  - both the value and the actual stat key used are recorded,
  - cache hit/miss rates are computed from real hit/miss COUNTS
    (hit_rate = hits/(hits+misses)); the derivation is recorded,
  - a missing metric stays EMPTY and produces a warning - never a fake 0.
"""

import csv
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "results", "raw")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

MATRIX_RUNS = [
    "matrix_no_cache_naive",
    "matrix_no_cache_tiled",
    "matrix_cache_naive",
    "matrix_cache_tiled",
]
LIST_RUNS = [
    "list_recursive_atomic",
    "list_recursive_o3",
    "list_iterative_atomic",
    "list_iterative_o3",
]
ALL_RUNS = MATRIX_RUNS + LIST_RUNS

# metric -> ordered list of stat-key aliases (first match wins)
SCALAR_ALIASES = {
    "simTicks": ["simTicks", "sim_ticks"],
    "simSeconds": ["simSeconds", "sim_seconds"],
    "simInsts": ["simInsts", "sim_insts"],
    "simOps": ["simOps", "sim_ops"],
    "numCycles": ["system.cpu.numCycles"],
    "ipc": [
        "system.cpu.ipc",
        "system.cpu.ipc_total",
        "system.cpu.commit.ipc",
    ],
    "cpi": ["system.cpu.cpi", "system.cpu.cpi_total"],
    # auxiliary (optional) metrics - empty if the CPU model lacks them
    "branchPredCondPredicted": ["system.cpu.branchPred.condPredicted"],
    "branchPredCondIncorrect": ["system.cpu.branchPred.condIncorrect"],
    "commitBranches": ["system.cpu.commit.branches"],
    "commitFunctionCalls": [
        "system.cpu.commit.functionCalls",
        "system.cpu.commitStats0.numFunctionCalls",
    ],
    "numBranches": [
        "system.cpu.executeStats0.numBranches",
        "system.cpu.commitStats0.numBranches",
    ],
    "numMemRefs": [
        "system.cpu.executeStats0.numMemRefs",
        "system.cpu.commitStats0.numMemRefs",
    ],
}

# cache label -> candidate object paths in the se.py-built system
CACHE_PATHS = {
    "l1i": ["system.cpu.icache"],
    "l1d": ["system.cpu.dcache"],
    "l2": ["system.l2", "system.l2cache"],
}
# hit/miss count aliases inside a cache object ({p} = object path)
CACHE_COUNTS = {
    "hits": ["{p}.overallHits::total", "{p}.demandHits::total",
             "{p}.overall_hits::total", "{p}.demand_hits::total"],
    "misses": ["{p}.overallMisses::total", "{p}.demandMisses::total",
               "{p}.overall_misses::total", "{p}.demand_misses::total"],
    "missRateReported": ["{p}.overallMissRate::total",
                         "{p}.demandMissRate::total",
                         "{p}.overall_miss_rate::total",
                         "{p}.demand_miss_rate::total"],
}

STAT_LINE = re.compile(r"^([\w.:+\-]+)\s+([-+0-9.eEnaif]+)")


def parse_stats(path):
    """Return {stat_key: float} for one stats.txt."""
    stats = {}
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            m = STAT_LINE.match(line)
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            try:
                stats[key] = float(val)
            except ValueError:
                continue  # 'nan'/'inf' handled by float(); anything else skipped
    return stats


def first_alias(stats, aliases):
    """Return (value, key) for the first alias present, else (None, None)."""
    for key in aliases:
        if key in stats:
            return stats[key], key
    return None, None


warnings = []


def warn(msg):
    warnings.append(msg)
    print(f"WARNING: {msg}", file=sys.stderr)


def extract_run(run):
    """Extract all metrics for one run directory. Empty string = missing."""
    stats_path = os.path.join(RAW_DIR, run, "stats.txt")
    row = {"run": run}
    if not os.path.isfile(stats_path):
        warn(f"{run}: stats.txt not found at {stats_path}")
        return row
    stats = parse_stats(stats_path)
    if not stats:
        warn(f"{run}: stats.txt is empty (simulation may have failed)")
        return row

    for metric, aliases in SCALAR_ALIASES.items():
        val, key = first_alias(stats, aliases)
        if val is None:
            row[metric] = ""
            row[f"{metric}__key"] = ""
        else:
            row[metric] = repr(val)
            row[f"{metric}__key"] = key

    # IPC fallback: compute from instruction and cycle counts if absent
    if row.get("ipc", "") == "":
        insts, ikey = first_alias(stats, SCALAR_ALIASES["simInsts"])
        cycles, ckey = first_alias(stats, SCALAR_ALIASES["numCycles"])
        if insts is not None and cycles not in (None, 0):
            row["ipc"] = repr(insts / cycles)
            row["ipc__key"] = f"computed:{ikey}/{ckey}"
        else:
            warn(f"{run}: IPC not found and could not be computed")

    # caches: counts first, rates derived from counts
    for label, paths in CACHE_PATHS.items():
        found_path = None
        for p in paths:
            if any(k.startswith(p + ".") for k in stats):
                found_path = p
                break
        if found_path is None:
            for fld in ("hits", "misses", "hitRate", "missRate"):
                row[f"{label}_{fld}"] = ""
                row[f"{label}_{fld}__key"] = ""
            continue

        vals = {}
        for fld, patterns in CACHE_COUNTS.items():
            aliases = [pat.format(p=found_path) for pat in patterns]
            v, k = first_alias(stats, aliases)
            vals[fld] = (v, k)

        hits, hits_key = vals["hits"]
        misses, misses_key = vals["misses"]
        rep_rate, rep_key = vals["missRateReported"]

        row[f"{label}_hits"] = "" if hits is None else repr(hits)
        row[f"{label}_hits__key"] = hits_key or ""
        row[f"{label}_misses"] = "" if misses is None else repr(misses)
        row[f"{label}_misses__key"] = misses_key or ""

        if hits is not None and misses is not None and (hits + misses) > 0:
            row[f"{label}_hitRate"] = repr(hits / (hits + misses))
            row[f"{label}_hitRate__key"] = (
                f"computed:{hits_key}/({hits_key}+{misses_key})"
            )
            row[f"{label}_missRate"] = repr(misses / (hits + misses))
            row[f"{label}_missRate__key"] = (
                f"computed:{misses_key}/({hits_key}+{misses_key})"
            )
            if rep_rate is not None:
                # cross-check against the rate gem5 itself reports
                if abs(rep_rate - misses / (hits + misses)) > 1e-6:
                    warn(f"{run}: {label} computed miss rate differs from "
                         f"reported {rep_key}={rep_rate}")
        else:
            row[f"{label}_hitRate"] = ""
            row[f"{label}_hitRate__key"] = ""
            row[f"{label}_missRate"] = "" if rep_rate is None else repr(rep_rate)
            row[f"{label}_missRate__key"] = rep_key or ""
            warn(f"{run}: {label} hit/miss counts incomplete")

    return row


def write_csv(path, rows, columns):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {path}")


def parse_config_ini(path):
    """Minimal INI parser (gem5 config.ini has duplicate-free sections)."""
    sections = {}
    current = None
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1]
                sections[current] = {}
            elif "=" in line and current is not None:
                k, _, v = line.partition("=")
                sections[current][k.strip()] = v.strip()
    return sections


def config_parameters():
    """Q2: clock domain / memory mode / memory size from runtime config.ini."""
    rows = []
    for run in LIST_RUNS + MATRIX_RUNS:
        ini = os.path.join(RAW_DIR, run, "config.ini")
        if not os.path.isfile(ini):
            warn(f"{run}: config.ini missing")
            continue
        sec = parse_config_ini(ini)
        entry = {"run": run}
        entry["mem_mode"] = sec.get("system", {}).get("mem_mode", "")
        entry["mem_ranges"] = sec.get("system", {}).get("mem_ranges", "")
        entry["cache_line_size"] = sec.get("system", {}).get(
            "cache_line_size", "")
        entry["clk_domain_clock_ticks"] = sec.get(
            "system.clk_domain", {}).get("clock", "")
        entry["cpu_clk_domain_clock_ticks"] = sec.get(
            "system.cpu_clk_domain", {}).get("clock", "")
        entry["cpu_type"] = sec.get("system.cpu", {}).get("type", "")
        entry["mem_ctrl_type"] = (
            sec.get("system.mem_ctrl", {}).get("type", "")
            or sec.get("system.mem_ctrls", {}).get("type", ""))
        # memory latency if SimpleMemory
        entry["simple_mem_latency"] = (
            sec.get("system.mem_ctrl", {}).get("latency", "")
            or sec.get("system.mem_ctrls", {}).get("latency", ""))
        # cache geometry (present only in cache runs)
        for label, secname in (("l1i", "system.cpu.icache"),
                               ("l1d", "system.cpu.dcache"),
                               ("l2", "system.l2")):
            entry[f"{label}_size"] = sec.get(secname, {}).get("size", "")
            entry[f"{label}_assoc"] = sec.get(secname, {}).get("assoc", "")
        rows.append(entry)
    cols = ["run", "cpu_type", "mem_mode", "mem_ranges", "cache_line_size",
            "clk_domain_clock_ticks", "cpu_clk_domain_clock_ticks",
            "mem_ctrl_type", "simple_mem_latency",
            "l1i_size", "l1i_assoc", "l1d_size", "l1d_assoc",
            "l2_size", "l2_assoc"]
    write_csv(os.path.join(RESULTS_DIR, "config_parameters.csv"), rows, cols)


def main():
    rows = {run: extract_run(run) for run in ALL_RUNS}

    # full summary (all metrics + source keys)
    all_cols = ["run"]
    seen = set(all_cols)
    for r in rows.values():
        for c in r:
            if c not in seen:
                seen.add(c)
                all_cols.append(c)
    write_csv(os.path.join(RESULTS_DIR, "summary.csv"),
              [rows[r] for r in ALL_RUNS], all_cols)

    matrix_cols = ["run", "ipc", "ipc__key", "simTicks", "simTicks__key",
                   "simSeconds", "simInsts", "numCycles",
                   "l1i_hits", "l1i_misses", "l1i_hitRate", "l1i_missRate",
                   "l1d_hits", "l1d_misses", "l1d_hitRate", "l1d_missRate",
                   "l2_hits", "l2_misses", "l2_hitRate", "l2_missRate"]
    write_csv(os.path.join(RESULTS_DIR, "matrix_results.csv"),
              [rows[r] for r in MATRIX_RUNS], matrix_cols)

    list_cols = ["run", "ipc", "ipc__key", "simSeconds", "simSeconds__key",
                 "simTicks", "simInsts", "simOps", "numCycles",
                 "branchPredCondPredicted", "branchPredCondIncorrect",
                 "commitBranches", "commitFunctionCalls", "numBranches",
                 "numMemRefs"]
    write_csv(os.path.join(RESULTS_DIR, "linked_list_results.csv"),
              [rows[r] for r in LIST_RUNS], list_cols)

    config_parameters()

    if warnings:
        print(f"\nextract_stats.py finished with {len(warnings)} warning(s).",
              file=sys.stderr)
    else:
        print("\nextract_stats.py finished with no warnings.")


if __name__ == "__main__":
    main()
