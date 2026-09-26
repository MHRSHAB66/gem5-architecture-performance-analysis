#!/usr/bin/env bash
# package.sh - build the final submission archive
# ACA Project 3 - Mehrdad Sheikhabbasi (40131025)
#
# Refuses to package unless validate_results.py passes and the report
# PDF exists. Produces ACA_Project3_40131025.zip whose single root
# folder is ACA_Project3_40131025/, then verifies it with `unzip -l`
# into results/logs/package_validation.log.

set -eu
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
NAME="ACA_Project3_40131025"
ZIP="${PROJECT_ROOT}/${NAME}.zip"

cd "${PROJECT_ROOT}"

echo "== gate 1: validation =="
python3 scripts/validate_results.py > /dev/null || {
    echo "ERROR: validation failed - not packaging." >&2; exit 1; }
echo "validation OK"

echo "== gate 2: report PDF =="
[ -s report.pdf ] || {
    echo "ERROR: report.pdf missing - not packaging." >&2; exit 1; }
head -c4 report.pdf | grep -q "%PDF" || {
    echo "ERROR: report.pdf is not a valid PDF." >&2; exit 1; }
echo "report OK"

echo "== gate 3: all stats.txt present =="
for run in matrix_no_cache_naive matrix_no_cache_tiled matrix_cache_naive \
           matrix_cache_tiled list_recursive_atomic list_recursive_o3 \
           list_iterative_atomic list_iterative_o3; do
    [ -s "results/raw/${run}/stats.txt" ] || {
        echo "ERROR: results/raw/${run}/stats.txt missing." >&2; exit 1; }
done
echo "stats OK"

echo "== cleaning transient files =="
find . -name '*.o' -delete
find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
rm -f report/main.aux report/main.log report/main.out report/main.toc \
      report/main.xdv report/texput.log

echo "== building ${ZIP} =="
rm -f "${ZIP}"
STAGE="$(mktemp -d)"
trap 'rm -rf "${STAGE}"' EXIT
mkdir "${STAGE}/${NAME}"

# Copy project contents — NO README.md; report.pdf goes to the root of the ZIP folder
cp Makefile "${STAGE}/${NAME}/"
cp report.pdf "${STAGE}/${NAME}/"         # report PDF at top level as report.pdf
cp -r src bin configs scripts results report "${STAGE}/${NAME}/"

# Remove ZIP self-reference
rm -f "${STAGE}/${NAME}/${NAME}.zip"
# Remove compiled PDF dragged in by cp -r report/ (root-level report.pdf is the copy)
rm -f "${STAGE}/${NAME}/report/main.pdf"
# No README files in the final archive
find "${STAGE}/${NAME}" -name "README.md" -delete

( cd "${STAGE}" && zip -qr "${ZIP}" "${NAME}" )

echo "== verifying archive =="
mkdir -p results/logs
unzip -l "${ZIP}" | tee results/logs/package_validation.log
echo
echo "package.sh: wrote ${ZIP}"
