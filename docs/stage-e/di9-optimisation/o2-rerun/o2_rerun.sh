#!/bin/zsh
# LABS-1.056: rerun O-2's alternatives on AC power, two passes (database order reversed in pass 2)
SP=<scratch>/opt; OUT=$SP/o2-rerun; mkdir -p $OUT
cd <projects>/typedb-semantic-world-model
DBS=(wm-probe-core03-1 wm-probe-core03-5 wm-probe-core03-10 wm-probe-core03-1-mixed wm-probe-core03-5-mixed wm-probe-core03-10-mixed wm-probe-scale-worlds-1 wm-probe-scale-worlds-10 wm-probe-scale-perspectives-10)
for P in 1 2; do
  if [[ $P == 2 ]]; then DBS=(${(Oa)DBS}); fi
  for db in $DBS; do
    s=$(date -u '+%Y-%m-%d %H:%M:%S')
    uv run --offline python -I $SP/code-o2/stage_e_o1_bounds.py $SP/code-o2 --knob o2 --db $db --n 5 --out $OUT/p$P-$db.json > /dev/null 2> $OUT/p$P-$db.err
    rc=$?; e=$(date -u '+%Y-%m-%d %H:%M:%S'); z=$(zsh $SP/slept.sh "$s" "$e" | wc -l | tr -d ' ')
    echo "$s .. $e pass $P $db rc=$rc sleep-events=$z $(pmset -g batt | grep -o "'.*'")" >> $OUT/status.txt
  done
done
echo DONE >> $OUT/status.txt
