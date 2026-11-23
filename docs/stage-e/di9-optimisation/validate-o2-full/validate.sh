#!/bin/zsh
# LABS-1.056: correctness validation of one increment from its worktree.
#   zsh validate.sh <worktree> <label> <runs>
# suite (4 configurations x runs, serial) || snapshots of the kept upgraded and fresh reference databases, diffed with
# S7/S8 (main 8663cb2) and S5/S6 || 398 views on both || E1 revised.
WT=$1; L=$2; RUNS=${3:-1}
SP=<scratch>
OUT=$SP/opt/validate-$L
mkdir -p $OUT
cd $WT || exit 1
R="uv run --offline python -I"
log() { echo "$(date +%H:%M:%S) $*" >> $OUT/status.txt; }
log "start $(git rev-parse --short HEAD)"
(
  for run in $(seq 1 $RUNS); do for sel in 1 0; do for prof in 0 1; do
    WM_SELECTIVE=$sel WM_PROFILES=$prof uv run --offline python -m pytest -q -p no:cacheprovider tests > $OUT/suite-run$run-sel$sel-prof$prof.log 2>&1
    echo "run$run-sel$sel-prof$prof rc=$? $(tail -1 $OUT/suite-run$run-sel$sel-prof$prof.log)" >> $OUT/suite-summary.txt
  done; done; done
  log "suite done"
) &
(
  ${=R} probes/pre_e_b_snapshot.py $WT --db wm-probe-pre-e-mp-u --out $OUT/snap-up.json > $OUT/snap-up.log 2>&1
  log "snap-up rc=$?"
) &
(
  ${=R} probes/pre_e_b_snapshot.py $WT --db wm-probe-stage-e --out $OUT/snap-fresh.json > $OUT/snap-fresh.log 2>&1
  log "snap-fresh rc=$?"
) &
${=R} probes/pre_e_d_impact.py $WT --db wm-probe-pre-e-mp-u --compare probes/pre_e_d_occurrence_baseline.json.gz > $OUT/views-up.out.txt 2>&1
log "views-up rc=$?"
${=R} probes/pre_e_d_impact.py $WT --db wm-probe-stage-e --compare probes/pre_e_d_occurrence_baseline.json.gz > $OUT/views-fresh.out.txt 2>&1
log "views-fresh rc=$?"
uv run --offline python -m evaluation.run --revised --out $OUT/e1-revised > $OUT/e1-revised.log 2>&1
log "e1 revised rc=$?"
wait
B=$SP/baselines
${=R} probes/pre_e_b_diff.py $B/S7-main-up.json $OUT/snap-up.json > $OUT/diff-S7-up.out.txt 2>&1
${=R} probes/pre_e_b_diff.py $SP/mp/S5-v3-up.json $OUT/snap-up.json > $OUT/diff-S5-up.out.txt 2>&1
${=R} probes/pre_e_b_diff.py $B/S8-main-fresh.json $OUT/snap-fresh.json > $OUT/diff-S8-fresh.out.txt 2>&1
log "suite: $(cat $OUT/suite-summary.txt | tr '\n' ';')"
log DONE
