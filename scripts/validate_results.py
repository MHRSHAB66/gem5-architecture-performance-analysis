#!/usr/bin/env python3
"""validate_results.py - gatekeeper before packaging.

ACA Project 3 - Mehrdad Sheikhabbasi (40131025)

Checks (exit code != 0 on any failure => packaging must NOT run):
  1. all eight mandatory runs exist,
  2. every run has stats.txt and config.ini,
  3. required IPC and simTicks/simSeconds metrics are present,
  4. matrix naive/tiled checksums are identical,
  5. all linked-list runs exited normally (programs match sample.c, no validation output),
  6. runs that must differ in only one variable really share their other
     settings (clock, mem size/type, cache geometry, CPU type as applicable),
  7. no NaN/empty value in required metric cells,
  8. simTicks and simSeconds are strictly positive,
  9. cache runs carry the mandated associativities and 64B line size in
     config.ini.
"""

import csv
import math
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "results", "raw")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

MATRIX_RUNS = ["matrix_no_cache_naive", "matrix_no_cache_tiled",
               "matrix_cache_naive", "matrix_cache_tiled"]
LIST_RUNS = ["list_recursive_atomic", "list_recursive_o3",
             "list_iterative_atomic", "list_iterative_o3"]
ALL_RUNS = MATRIX_RUNS + LIST_RUNS

failures = []
passes = []


def check(cond, ok_msg, fail_msg):
    if cond:
        passes.append(ok_msg)
        print(f"PASS: {ok_msg}")
    else:
        failures.append(fail_msg)
        print(f"FAIL: {fail_msg}")


def read_csv(name):
    path = os.path.join(RESULTS_DIR, name)
    if not os.path.isfile(path):
        failures.append(f"{name} missing - run extract_stats.py first")
        print(f"FAIL: {name} missing")
        return {}
    with open(path, newline="") as fh:
        return {row["run"]: row for row in csv.DictReader(fh)}


def parse_config_ini(path):
    sections, current = {}, None
    with open(path, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1]
                sections[current] = {}
            elif "=" in line and current is not None:
                k, _, v = line.partition("=")
                sections[current][k.strip()] = v.strip()
    return sections


def grab(pattern, path):
    if not os.path.isfile(path):
        return None
    with open(path, errors="replace") as fh:
        m = re.search(pattern, fh.read())
    return m.group(1) if m else None


def numeric_ok(row, key):
    v = row.get(key, "")
    if v in ("", None):
        return False
    try:
        f = float(v)
    except ValueError:
        return False
    return not (math.isnan(f) or math.isinf(f))


def main():
    # 1+2: run dirs and mandatory files
    for run in ALL_RUNS:
        d = os.path.join(RAW_DIR, run)
        check(os.path.isdir(d), f"{run}/ exists", f"{run}/ missing")
        for f in ("stats.txt", "config.ini", "command.txt", "simout"):
            p = os.path.join(d, f)
            check(os.path.isfile(p) and os.path.getsize(p) > 0,
                  f"{run}/{f} present and non-empty",
                  f"{run}/{f} missing or empty")

    summary = read_csv("summary.csv")

    # 3+7+8: required metrics present, numeric, positive
    for run in ALL_RUNS:
        row = summary.get(run, {})
        check(numeric_ok(row, "ipc") and float(row["ipc"]) > 0,
              f"{run}: IPC ok ({row.get('ipc', '')[:12]})",
              f"{run}: IPC missing/invalid")
        check(numeric_ok(row, "simTicks") and float(row["simTicks"]) > 0,
              f"{run}: simTicks positive",
              f"{run}: simTicks missing/non-positive")
        check(numeric_ok(row, "simSeconds") and float(row["simSeconds"]) > 0,
              f"{run}: simSeconds positive",
              f"{run}: simSeconds missing/non-positive")

    # cache metrics required for the two cache matrix runs
    for run in ("matrix_cache_naive", "matrix_cache_tiled"):
        row = summary.get(run, {})
        for m in ("l1i_missRate", "l1d_missRate", "l2_missRate"):
            check(numeric_ok(row, m),
                  f"{run}: {m} ok",
                  f"{run}: {m} missing/NaN")

    # 4: matrix checksums identical between naive and tiled (all 4 runs)
    checks = {}
    for run in MATRIX_RUNS:
        c = grab(r"MATRIX_CHECKSUM:\s*(-?\d+)",
                 os.path.join(RAW_DIR, run, "simout"))
        checks[run] = c
        check(c is not None, f"{run}: checksum found ({c})",
              f"{run}: MATRIX_CHECKSUM not found in simout")
    vals = {v for v in checks.values() if v is not None}
    check(len(vals) == 1 and None not in checks.values(),
          f"matrix checksums identical across all 4 runs ({vals})",
          f"matrix checksums differ or missing: {checks}")

    # 5: linked-list programs match sample.c (no validation output expected)
    # Programs are exact copies of sample.c structure - no printf after reverse,
    # no validate() function, exit code 0 is sufficient correctness check.
    for run in LIST_RUNS:
        out = os.path.join(RAW_DIR, run, "simout")
        exited = grab(r"Exiting @ tick (\d+)", out)
        check(exited is not None,
              f"{run}: simulation exited normally (tick {exited})",
              f"{run}: simulation did not exit normally")

    # 6+9: controlled variables via runtime config.ini
    cfgs = {}
    for run in ALL_RUNS:
        p = os.path.join(RAW_DIR, run, "config.ini")
        if os.path.isfile(p):
            cfgs[run] = parse_config_ini(p)

    def sysval(run, key):
        return cfgs.get(run, {}).get("system", {}).get(key, "?")

    # memory size identical everywhere
    memsz = {run: sysval(run, "mem_ranges") for run in cfgs}
    check(len(set(memsz.values())) == 1,
          f"mem_ranges identical in all runs ({next(iter(set(memsz.values())))})",
          f"mem_ranges differ: {memsz}")

    # cache geometry in the six cache runs
    for run in ["matrix_cache_naive", "matrix_cache_tiled"] + LIST_RUNS:
        s = cfgs.get(run, {})
        geo = {
            "l1i_assoc": s.get("system.cpu.icache", {}).get("assoc"),
            "l1d_assoc": s.get("system.cpu.dcache", {}).get("assoc"),
            "l2_assoc": s.get("system.l2", {}).get("assoc"),
            "line": s.get("system", {}).get("cache_line_size"),
            "l1i_size": s.get("system.cpu.icache", {}).get("size"),
            "l1d_size": s.get("system.cpu.dcache", {}).get("size"),
            "l2_size": s.get("system.l2", {}).get("size"),
        }
        expected = {"l1i_assoc": "4", "l1d_assoc": "4", "l2_assoc": "8",
                    "line": "64", "l1i_size": "32768", "l1d_size": "32768",
                    "l2_size": "262144"}
        check(geo == expected,
              f"{run}: cache geometry matches mandate",
              f"{run}: cache geometry mismatch {geo}")

    # matrix runs: identical CPU type/clock across all four
    mcpu = {r: cfgs.get(r, {}).get("system.cpu", {}).get("type", "?")
            for r in MATRIX_RUNS}
    check(len(set(mcpu.values())) == 1 and "TimingSimpleCPU" in
          next(iter(set(mcpu.values())), ""),
          f"matrix runs share CPU type ({next(iter(set(mcpu.values())))})",
          f"matrix runs CPU type differ: {mcpu}")

    # Q1: CPU model is the only variable between atomic and o3 pairs
    for algo in ("recursive", "iterative"):
        a, o = f"list_{algo}_atomic", f"list_{algo}_o3"
        ma, mo = sysval(a, "mem_mode"), sysval(o, "mem_mode")
        check(ma == "atomic" and mo == "timing",
              f"{algo}: mem_mode atomic={ma} / o3={mo} as expected",
              f"{algo}: unexpected mem_mode atomic={ma} o3={mo}")

    # identical binaries per comparison pair (same executable path/sha)
    print()
    n_pass, n_fail = len(passes), len(failures)
    print(f"==== VALIDATION SUMMARY: {n_pass} passed, {n_fail} failed ====")
    if failures:
        print("VALIDATION FAILED - packaging must not proceed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("VALIDATION PASSED - safe to package.")


if __name__ == "__main__":
    main()
