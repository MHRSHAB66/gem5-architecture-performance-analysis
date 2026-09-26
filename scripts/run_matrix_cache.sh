#!/usr/bin/env bash
# run_matrix_cache.sh - Part 1 Step 2: two-level cache hierarchy
#
# Runs matrix_naive and matrix_tiled with the official se.py config:
# TimingSimpleCPU, L1I/L1D 32kB 4-way, unified L2 256kB 8-way, 64B lines,
# SimpleMemory 512MB. Flags verified against gem5 v23.0.0.1 --help.

set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
require_gem5

cache_flags=(
    --cpu-type=TimingSimpleCPU
    --cpu-clock="${CPU_CLOCK}"
    --sys-clock="${SYS_CLOCK}"
    --caches
    --l2cache
    --l1i_size="${L1I_SIZE}"
    --l1d_size="${L1D_SIZE}"
    --l2_size="${L2_SIZE}"
    --l1i_assoc="${L1I_ASSOC}"
    --l1d_assoc="${L1D_ASSOC}"
    --l2_assoc="${L2_ASSOC}"
    --cacheline_size="${CACHELINE}"
    --mem-type="${MEM_TYPE}"
    --mem-size="${MEM_SIZE}"
)

run_gem5 matrix_cache_naive \
    "${SE_PY}" -c "${BIN_DIR}/matrix_naive" "${cache_flags[@]}"

run_gem5 matrix_cache_tiled \
    "${SE_PY}" -c "${BIN_DIR}/matrix_tiled" "${cache_flags[@]}"

echo "run_matrix_cache.sh: done"
