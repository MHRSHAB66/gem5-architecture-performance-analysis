#!/usr/bin/env bash
# common.sh - shared helpers for all run scripts
# ACA Project 3 - Mehrdad Sheikhabbasi (40131025)
#
# Resolves the project root relative to this file so every script can be
# invoked from any working directory. GEM5_ROOT may be overridden via the
# environment; it defaults to ~/gem5.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GEM5_ROOT="${GEM5_ROOT:-$HOME/gem5}"
GEM5_BIN="${GEM5_ROOT}/build/X86/gem5.opt"
SE_PY="${GEM5_ROOT}/configs/deprecated/example/se.py"

BIN_DIR="${PROJECT_ROOT}/bin"
RAW_DIR="${PROJECT_ROOT}/results/raw"
LOG_DIR="${PROJECT_ROOT}/results/logs"

mkdir -p "${RAW_DIR}" "${LOG_DIR}"

# Parameters kept IDENTICAL across every run (only the variable under
# study - algorithm or CPU model - may differ between compared runs).
CPU_CLOCK="2GHz"
SYS_CLOCK="1GHz"
MEM_TYPE="SimpleMemory"
MEM_SIZE="512MB"
L1I_SIZE="32kB"
L1D_SIZE="32kB"
L2_SIZE="256kB"
L1I_ASSOC=4
L1D_ASSOC=4
L2_ASSOC=8
CACHELINE=64

require_gem5() {
    if [ ! -x "${GEM5_BIN}" ]; then
        echo "ERROR: gem5 binary not found/executable at ${GEM5_BIN}" >&2
        echo "       set GEM5_ROOT to your gem5 checkout." >&2
        exit 1
    fi
}

# run_gem5 <run-name> <gem5 args...>
# Runs gem5 with -d results/raw/<run-name>, tees the console log to
# results/logs/<run-name>.log and stores the exact command in command.txt.
run_gem5() {
    local name="$1"; shift
    local outdir="${RAW_DIR}/${name}"
    mkdir -p "${outdir}"
    local cmd=("${GEM5_BIN}" -d "${outdir}" "$@")
    printf '%q ' "${cmd[@]}" > "${outdir}/command.txt"
    echo >> "${outdir}/command.txt"
    echo "==== RUN ${name} ===="
    echo "CMD: ${cmd[*]}"
    if "${cmd[@]}" 2> >(tee "${outdir}/simerr" >&2) \
                   | tee "${LOG_DIR}/${name}.log"; then
        # program stdout is interleaved in the gem5 console log (SE mode
        # writes guest stdout to gem5's stdout); keep a copy as simout
        cp "${LOG_DIR}/${name}.log" "${outdir}/simout"
        echo "==== RUN ${name}: OK ===="
    else
        echo "==== RUN ${name}: FAILED (exit $?) ====" >&2
        return 1
    fi
}
