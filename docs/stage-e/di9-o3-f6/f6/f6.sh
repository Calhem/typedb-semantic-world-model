#!/bin/zsh
# LABS-1.057: F6 supersession formulations, run alone from the O-3 worktree; two passes (order reversed in pass 2)
SP=<scratch>/opt; OUT=$SP/f6; mkdir -p $OUT
WT=<projects>/wm-o3-wt; cd $WT
step() { local s=$(date -u '+%Y-%m-%d %H:%M:%S'); "$@" > /dev/null 2> $OUT/$NAME.err; local rc=$?
  local e=$(date -u '+%Y-%m-%d %H:%M:%S')
  echo "$s .. $e rc=$rc sleep-events=$(zsh $SP/slept.sh "$s" "$e" | wc -l | tr -d ' ') $(pmset -g batt | grep -o "'.*'") :: $NAME" >> $OUT/status.txt; }
R="uv run --offline python -I probes/stage_e_f6_supersession.py ."
JOBS=("core03-1 --db wm-probe-core03-1 --core03 1" "core03-5 --db wm-probe-core03-5 --core03 5" "core03-10 --db wm-probe-core03-10 --core03 10"
      "where-worlds-1 --db wm-probe-scale-worlds-1 --where" "where-worlds-10 --db wm-probe-scale-worlds-10 --where")
for P in 1 2; do
  if [[ $P == 2 ]]; then JOBS=(${(Oa)JOBS}); fi
  for j in $JOBS; do
    args=(${=j}); NAME=p$P-${args[1]}
    step ${=R} ${args[2,-1]} --questions 60 --n 5 --out $OUT/$NAME.json
  done
done
echo DONE >> $OUT/status.txt
