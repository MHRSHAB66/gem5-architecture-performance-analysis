#!/usr/bin/env bash
# build_workloads.sh - compile all four workloads with IDENTICAL flags
#
# All binaries are statically linked (required for gem5 SE mode) and
# compiled with the exact same flags so compared runs differ only in
# the algorithm.

set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

CFLAGS="-O2 -std=c11 -Wall -Wextra -static"

mkdir -p "${BIN_DIR}"
cd "${PROJECT_ROOT}"

echo "CFLAGS: ${CFLAGS}"
echo "gcc:    $(gcc --version | head -1)"

for w in matrix_naive matrix_tiled linked_list_recursive linked_list_iterative; do
    echo "building bin/${w}"
    # shellcheck disable=SC2086
    gcc ${CFLAGS} -o "bin/${w}" "src/${w}.c"
done

echo
echo "---- native sanity check (host, not gem5) ----"
for w in matrix_naive matrix_tiled linked_list_recursive linked_list_iterative; do
    echo "-- ${w}:"
    "./bin/${w}"
done
echo "build_workloads.sh: done"
