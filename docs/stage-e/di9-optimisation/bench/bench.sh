#!/bin/zsh
# LABS-1.056 step 5: controlled before/after benchmarks, run alone. Versions: base (8663cb2 code), o1 (144be5b),
# o2 (92da365 = O-1 + O-2). Two passes in opposite version order, plus fresh-process repeats. Every step records its
# window, the number of sleep events in it (pmset) and the power source; a step with sleep events is invalid.
#   zsh bench.sh [pass...]    (default: A B R)
SP=<scratch>/opt
OUT=$SP/bench
PR=$SP/bench-probes
mkdir -p $OUT $PR
cd <projects>/typedb-semantic-world-model || exit 1
for p in stage_e_scale stage_e_di9_instrumented stage_e_core03_selective; do cp probes/$p.py $PR/; done
typeset -A WT
WT=(base <projects>/wm-entry-wt o1 <projects>/wm-o1-wt o2 <projects>/wm-o2-wt)
DBS=(wm-probe-scale-worlds-1 wm-probe-scale-worlds-5 wm-probe-scale-worlds-10 wm-probe-scale-perspectives-5 wm-probe-scale-perspectives-10)
step() {   # step NAME command...
  local s=$(date -u '+%Y-%m-%d %H:%M:%S')
  "$@"; local rc=$?
  local e=$(date -u '+%Y-%m-%d %H:%M:%S')
  local z=$(zsh $SP/slept.sh "$s" "$e" | wc -l | tr -d ' ')
  echo "$s .. $e rc=$rc sleep-events=$z $(pmset -g batt | grep -o "'.*'") :: $STEP" >> $OUT/status.txt
}
run_version() {   # run_version PASS VERSION
  local P=$1 V=$2 W=${WT[$2]}
  local R="uv run --project $W --offline python -I"
  for k in 1 5 10; do
    STEP="$P $V core03-$k"; step ${=R} $PR/stage_e_core03_selective.py $W --scale $k --db wm-probe-core03-$k --reuse --keep \
      --out $OUT/$P-$V-core03-$k.json > /dev/null 2> $OUT/$P-$V-core03-$k.err
  done
  for db in $DBS; do
    STEP="$P $V read $db"; step ${=R} $PR/stage_e_scale.py $W --read --n 5 --db $db --out $OUT/$P-$V-read-$db.json \
      --answers $OUT/$P-$V-answers-$db.json > /dev/null 2> $OUT/$P-$V-read-$db.err
  done
  STEP="$P $V instrumented"; step ${=R} $PR/stage_e_di9_instrumented.py $W --dbs ${(j:,:)DBS} --n 7 \
    --out $OUT/$P-$V-instrumented.json > /dev/null 2> $OUT/$P-$V-instrumented.err
}
echo "$(date -u '+%Y-%m-%d %H:%M:%S') start; containers $(~/.docker/bin/docker ps -q | wc -l | tr -d ' ')" >> $OUT/status.txt
if (( $# )); then PASSES=($@); else PASSES=(A B R); fi
for P in $PASSES; do
  case $P in
    A) for V in base o1 o2; do run_version A $V; done ;;
    B) for V in o2 o1 base; do run_version B $V; done ;;
    R) for i in 1 2 3; do for V in base o2; do
         W=${WT[$V]}
         STEP="R$i $V repeat"; step uv run --project $W --offline python -I $PR/stage_e_di9_instrumented.py $W \
           --dbs wm-probe-scale-worlds-1,wm-probe-scale-worlds-10,wm-probe-scale-perspectives-10 --readers parts,where,value_at,occurrence \
           --n 5 --out $OUT/R$i-$V-repeat.json > /dev/null 2> $OUT/R$i-$V-repeat.err
         for k in 1 10; do
           STEP="R$i $V core03-$k"; step uv run --project $W --offline python -I $PR/stage_e_core03_selective.py $W --scale $k \
             --db wm-probe-core03-$k --reuse --keep --out $OUT/R$i-$V-core03-$k.json > /dev/null 2> $OUT/R$i-$V-core03-$k.err
         done
       done; done ;;
  esac
done
echo "$(date -u '+%Y-%m-%d %H:%M:%S') DONE" >> $OUT/status.txt
