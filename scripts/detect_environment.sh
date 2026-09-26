#!/usr/bin/env bash
# detect_environment.sh - record the simulation environment
# ACA Project 3 - Mehrdad Sheikhabbasi (40131025)
#
# Writes results/environment.txt with gem5 version, toolchain, OS and
# hardware details. Run from anywhere.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

OUT="${PROJECT_ROOT}/results/environment.txt"

require_gem5

{
    echo "==== ACA Project 3 - Environment ===="
    echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo
    echo "---- gem5 ----"
    echo "GEM5_ROOT: ${GEM5_ROOT}"
    echo "GEM5_BIN:  ${GEM5_BIN}"
    echo -n "gem5 git version: "
    git -C "${GEM5_ROOT}" describe --tags --always 2>/dev/null || echo "unknown"
    echo "se.py: ${SE_PY} $( [ -f "${SE_PY}" ] && echo '(present)' || echo '(MISSING)')"
    echo
    echo "---- gem5 build info (first lines of gem5.opt banner) ----"
    "${GEM5_BIN}" --build-info 2>/dev/null | head -20 || true
    echo
    echo "---- OS ----"
    uname -a
    [ -f /etc/os-release ] && grep PRETTY_NAME /etc/os-release
    echo
    echo "---- CPU / RAM ----"
    echo "nproc: $(nproc)"
    grep -m1 'model name' /proc/cpuinfo
    free -h | head -2
    echo
    echo "---- Toolchain ----"
    gcc --version | head -1
    python3 --version
    echo
    echo "---- Fixed simulation parameters (all runs) ----"
    echo "CPU_CLOCK=${CPU_CLOCK}"
    echo "SYS_CLOCK=${SYS_CLOCK}"
    echo "MEM_TYPE=${MEM_TYPE}"
    echo "MEM_SIZE=${MEM_SIZE}"
    echo "L1I=${L1I_SIZE}/${L1I_ASSOC}-way  L1D=${L1D_SIZE}/${L1D_ASSOC}-way  L2=${L2_SIZE}/${L2_ASSOC}-way  line=${CACHELINE}B"
} | tee "${OUT}"

echo
echo "environment written to ${OUT}"
