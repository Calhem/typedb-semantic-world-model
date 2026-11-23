#!/bin/zsh
# slept.sh START END (UTC "YYYY-MM-DD HH:MM:SS"): prints sleep events between them (empty: the machine stayed awake)
pmset -g log | awk -v s="$1" -v e="$2" '{t=$1" "$2} t>=s && t<=e && ($4=="Sleep" || $4=="DarkWake" || ($4=="Wake" && $5=="from"))' | cut -c1-90
