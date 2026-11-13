#!/bin/bash
# usage: cmptree.sh <treeA> <treeB> [out] : diff -rq of two ufs-weather-model source trees, excluding git metadata,
# build dirs, executables, compile logs/modules, patch backups/rejects; prints count, writes the list to <out>
A=${1:?A}; B=${2:?B}; O=${3:-/dev/stdout}
diff -rq --no-dereference \
  -x .git -x 'build_*' -x '*.exe' -x 'compile_*_time.log' -x 'modules.fv3_*' -x '*.orig' -x '*.rej' -x '__pycache__' \
  "$A" "$B" > "$O"
echo "differences: $(grep -c . "$O" 2>/dev/null || true)"
