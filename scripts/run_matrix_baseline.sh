#!/usr/bin/env bash
# run_matrix_baseline.sh - Part 1 Step 1: baseline WITHOUT caches
# ACA Project 3 - Mehrdad Sheikhabbasi (40131025)
#
# Runs matrix_naive and matrix_tiled on the custom no-cache SE system
# (configs/no_cache.py): X86TimingSimpleCPU + SimpleMemory, no L1/L2.

set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
require_gem5

NO_CACHE_CFG="${PROJECT_ROOT}/configs/no_cache.py"

run_gem5 matrix_no_cache_naive \
    "${NO_CACHE_CFG}" "${BIN_DIR}/matrix_naive" \
    --cpu-clock "${CPU_CLOCK}" --mem-size "${MEM_SIZE}"

run_gem5 matrix_no_cache_tiled \
    "${NO_CACHE_CFG}" "${BIN_DIR}/matrix_tiled" \
    --cpu-clock "${CPU_CLOCK}" --mem-size "${MEM_SIZE}"

echo "run_matrix_baseline.sh: done"
