#!/bin/bash
# Live terminal demo (analysis/ipp1_live_train_fast.py) pinned to one thread per physical core of a 6-core CPU with SMT
# (logical CPUs 0,2,4,6,8,10; change CORES for another CPU). Needs HACKATHON_HOME. The output contains IPP data rows, so it is
# written to $HACKATHON_HOME/out/ (outside the repository), never into git (CON-001).
set -eu
: "${HACKATHON_HOME:?set HACKATHON_HOME to the hackathon folder that holds data/}"
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python}"
CORES="${CORES:-0,2,4,6,8,10}"
mkdir -p "$HACKATHON_HOME/out"
taskset -c "$CORES" "$PY" -u "$DIR/ipp1_live_train_fast.py" 2>&1 | tee "$HACKATHON_HOME/out/live_train_fast_out.txt"
