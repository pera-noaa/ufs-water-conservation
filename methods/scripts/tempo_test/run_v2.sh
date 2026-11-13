#!/bin/bash
# run.sh <tag> <args...>: run the closure test of build <tag> in the run directory with its version's tables
R=/private/tmp/claude-33310/-Users-pera-Documents-ash-code-tm5-zoom/ec8c50fd-c8e3-44ff-8b44-bb076a72dd87/scratchpad/tempo_round2
tag=$1; shift; v=${tag%%_*}; [ $v = 2856696 ] && v=c62699f
cd $R/run/$v && $R/build/$tag/wct "$@" 2>&1 | grep -v "^ *tempo_init\|^ *tempo_\|table" | sed "s/^/$tag /"
