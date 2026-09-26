#!/usr/bin/env bash
# run_linked_list.sh - Question 1: CPU model comparison
#
# Runs linked_list_recursive and linked_list_iterative with both
# AtomicSimpleCPU and DerivO3CPU. Everything else (binary flags, clock,
# memory type/size, cache geometry) is IDENTICAL across the four runs -
# the CPU model and the algorithm are the only variables.
#
# Caches are enabled for both CPU models so the comparison is fair:
# DerivO3CPU is meant to be used with caches, and using the same cache
# flags for AtomicSimpleCPU keeps every other parameter equal.

set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"
require_gem5

common_flags=(
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

run_gem5 list_recursive_atomic \
    "${SE_PY}" -c "${BIN_DIR}/linked_list_recursive" \
    --cpu-type=AtomicSimpleCPU "${common_flags[@]}"

run_gem5 list_recursive_o3 \
    "${SE_PY}" -c "${BIN_DIR}/linked_list_recursive" \
    --cpu-type=DerivO3CPU "${common_flags[@]}"

run_gem5 list_iterative_atomic \
    "${SE_PY}" -c "${BIN_DIR}/linked_list_iterative" \
    --cpu-type=AtomicSimpleCPU "${common_flags[@]}"

run_gem5 list_iterative_o3 \
    "${SE_PY}" -c "${BIN_DIR}/linked_list_iterative" \
    --cpu-type=DerivO3CPU "${common_flags[@]}"

echo "run_linked_list.sh: done"
