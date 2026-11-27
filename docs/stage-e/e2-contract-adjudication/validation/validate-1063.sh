#!/bin/zsh
# LABS-1.061 (E2 harness): validation of one increment from its worktree.
#   zsh validate-e2h.sh <worktree> <runs>
# E1 original and revised against the committed results (only meta may differ), E1 format check with every fixture
# loaded, then the suite in 4 configurations x runs (serial; never two pytest runs at once).
WT=$1; RUNS=${2:-1}
SP=<scratch>
OUT=$SP/opt/validate-1063
mkdir -p $OUT
cd $WT || exit 1
log() { echo "$(date +%H:%M:%S) $*" >> $OUT/status.txt; }
log "start $(git rev-parse --short HEAD)"
uv run --offline python -m evaluation.check --load > $OUT/e1-check.log 2>&1
log "e1 check rc=$? $(tail -1 $OUT/e1-check.log)"
uv run --offline python -m evaluation.run --out $OUT/e1-original > $OUT/e1-original.log 2>&1
log "e1 original rc=$? $(tail -1 $OUT/e1-original.log)"
uv run --offline python -m evaluation.run --revised --out $OUT/e1-revised > $OUT/e1-revised.log 2>&1
log "e1 revised rc=$? $(tail -1 $OUT/e1-revised.log)"
uv run --offline python -I $SP/opt/e1-compare.py $OUT/e1-original/results.json $WT/benchmark/e1/results/results.json $SP/opt/e1-original-main/results.json > $OUT/e1-compare-original.txt 2>&1
log "e1 compare original rc=$?"
uv run --offline python -I $SP/opt/e1-compare.py $OUT/e1-revised/results.json $WT/benchmark/e1/results-revised/results.json > $OUT/e1-compare-revised.txt 2>&1
log "e1 compare revised rc=$?"
for run in $(seq 1 $RUNS); do for sel in 1 0; do for prof in 0 1; do
  WM_SELECTIVE=$sel WM_PROFILES=$prof uv run --offline python -m pytest -q -p no:cacheprovider tests > $OUT/suite-run$run-sel$sel-prof$prof.log 2>&1
  echo "run$run-sel$sel-prof$prof rc=$? $(tail -1 $OUT/suite-run$run-sel$sel-prof$prof.log)" >> $OUT/suite-summary.txt
done; done; done
log "suite done"
log "DONE"
uv run --offline python -I probes/src_semantics_unchanged.py main > $OUT/src-unchanged.txt 2>&1
log "src semantics unchanged vs main rc=$?"
uv run --offline python -m evaluation.e2.reader_docs --check > $OUT/reader-docs-check.txt 2>&1
log "reader docs check rc=$?"
log "DONE2"
