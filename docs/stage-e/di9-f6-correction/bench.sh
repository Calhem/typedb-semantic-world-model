#!/bin/zsh
# LABS-1.058 step 6: end-to-end before/after benchmarks of the F6 correction, run alone. Versions: o3 (4ce7933, the
# single query) and f6 (the two-step lookup). Passes A (o3, f6) and B (f6, o3), then fresh-process repeats R1-R5
# alternating the order. Every step records its window, the sleep events in it (pmset) and the power source; a step
# with sleep events is invalid and is repeated.     zsh bench.sh [pass...]   (default: A B R)
SP=<scratch>/opt
OUT=$SP/f6c/bench
PR=$SP/f6c/probes
mkdir -p $OUT $PR
cd <projects>/typedb-semantic-world-model || exit 1
for p in stage_e_scale stage_e_di9_instrumented stage_e_core03_selective; do cp probes/$p.py $PR/; done
typeset -A WT
WT=(o3 <projects>/wm-o3-wt f6 <projects>/wm-f6-wt)
DBS=(wm-probe-scale-worlds-1 wm-probe-scale-worlds-5 wm-probe-scale-worlds-10 wm-probe-scale-perspectives-5 wm-probe-scale-perspectives-10)
step() {   # step command...   (STEP names it)
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
    A) for V in o3 f6; do run_version A $V; done ;;
    B) for V in f6 o3; do run_version B $V; done ;;
    R) for i in 1 2 3 4 5; do
         if (( i % 2 )); then VS=(o3 f6); else VS=(f6 o3); fi
         for V in $VS; do
           W=${WT[$V]}
           STEP="R$i $V repeat"; step uv run --project $W --offline python -I $PR/stage_e_di9_instrumented.py $W \
             --dbs wm-probe-scale-worlds-1,wm-probe-scale-worlds-10,wm-probe-scale-perspectives-10 --readers parts,where,value_at,occurrence \
             --n 5 --out $OUT/R$i-$V-repeat.json > /dev/null 2> $OUT/R$i-$V-repeat.err
           for k in 1 10; do
             STEP="R$i $V core03-$k"; step uv run --project $W --offline python -I $PR/stage_e_core03_selective.py $W --scale $k \
               --db wm-probe-core03-$k --reuse --keep --out $OUT/R$i-$V-core03-$k.json > /dev/null 2> $OUT/R$i-$V-core03-$k.err
           done
         done
       done ;;
  esac
done
echo "$(date -u '+%Y-%m-%d %H:%M:%S') DONE" >> $OUT/status.txt
