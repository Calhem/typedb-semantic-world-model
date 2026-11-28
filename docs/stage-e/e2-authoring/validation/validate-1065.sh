#!/bin/zsh
WT=<path>
SP=<scratch>
OUT=$SP/opt/validate-1065; mkdir -p $OUT; cd $WT || exit 1
log() { echo "$(date +%H:%M:%S) $*" >> $OUT/status.txt; }
log "start $(git rev-parse --short HEAD)"
uv run --offline python -I probes/src_semantics_unchanged.py 5ded39a > $OUT/src-unchanged.txt 2>&1; log "src unchanged vs 5ded39a rc=$?"
git diff --stat d06316c HEAD -- src schema docs/architecture > $OUT/baseline-diff.txt 2>&1; log "baseline diff lines=$(wc -l < $OUT/baseline-diff.txt)"
uv run --offline python -m pytest -q -p no:cacheprovider tests/test_zz_e2_decisions.py tests/test_zz_e2_harness.py tests/test_zz_e2_evidence_roles.py > $OUT/harness-tests.log 2>&1; log "harness tests rc=$? $(tail -1 $OUT/harness-tests.log)"
uv run --offline python scripts/e2_corpus_check.py --quiet > $OUT/corpus-check.txt 2>&1; log "corpus check rc=$? $(tail -1 $OUT/corpus-check.txt)"
uv run --offline python -m evaluation.check --load > $OUT/e1-check.log 2>&1; log "e1 check rc=$? $(tail -1 $OUT/e1-check.log)"
uv run --offline python -m evaluation.run --out $OUT/e1-original > $OUT/e1-original.log 2>&1; log "e1 original rc=$? $(tail -1 $OUT/e1-original.log)"
uv run --offline python -m evaluation.run --revised --out $OUT/e1-revised > $OUT/e1-revised.log 2>&1; log "e1 revised rc=$? $(tail -1 $OUT/e1-revised.log)"
uv run --offline python -I $SP/opt/e1-compare.py $OUT/e1-original/results.json $SP/opt/e1-original-main/results.json > $OUT/e1-compare-original.txt 2>&1; log "e1 compare original rc=$?"
uv run --offline python -I $SP/opt/e1-compare.py $OUT/e1-revised/results.json $SP/opt/validate-di19/e1-revised/results.json > $OUT/e1-compare-revised.txt 2>&1; log "e1 compare revised rc=$?"
log DONE
