#!/usr/bin/env bash
# run_all.sh - full reproducible pipeline
#
# environment -> build -> 8 gem5 runs -> stats extraction -> validation
# -> plots -> screenshots. Packaging (scripts/package.sh) is separate on
# purpose: it must only run after validation has been inspected.

set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "${SCRIPT_DIR}/detect_environment.sh"
bash "${SCRIPT_DIR}/build_workloads.sh"
bash "${SCRIPT_DIR}/run_matrix_baseline.sh"
bash "${SCRIPT_DIR}/run_matrix_cache.sh"
bash "${SCRIPT_DIR}/run_linked_list.sh"
python3 "${SCRIPT_DIR}/extract_stats.py"
python3 "${SCRIPT_DIR}/validate_results.py"
python3 "${SCRIPT_DIR}/generate_plots.py"
python3 "${SCRIPT_DIR}/log_to_png.py"

echo "run_all.sh: pipeline complete"
