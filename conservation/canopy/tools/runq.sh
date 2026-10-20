#!/bin/bash
# usage: nohup runq.sh <list> & ; list lines: name|exe|my gfs_physics_nml switches (k=v,...)|model_configure sed|env K=V|base
# base: "all" (final9 switches, default) or "none"; consv_te=0.999 via switch key consv_te. <= 2 of my cr_ jobs at once.
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy
ALL="$(cat $C/runs/final9_switches.sed)"
while IFS='|' read -r name exe sw mc env base jm; do
  [ -z "$name" ] || [ "${name:0:1}" = "#" ] && continue
  [ -e $C/runs/$name ] && { echo "skip $name (exists)"; continue; }
  until [ -x "$C/exe/$exe" ]; do sleep 60; done
  while [ "$(squeue -h -u $USER -o %j | grep -c '^cr_\|^c_')" -ge 2 ]; do sleep 30; done
  s=""; pre=""; ins=""
  IFS=',' read -ra kv <<< "$sw"
  for x in "${kv[@]}"; do [ -z "$x" ] && continue
    k=${x%%=*}; v=${x#*=}
    if [ "$k" = consv_te ] || [ "${k:0:1}" = "^" ]; then k=${k#^}; pre="${pre:+$pre; }s/^(\s*$k\s*=)[^\n]*$/\1 $v/"; else ins="$ins\n  $k = $v"; fi
  done
  [ -n "$pre" ] && s="$pre"
  [ "${base:-all}" = all ] && s="${s:+$s; }$ALL"
  [ -n "$ins" ] && s="${s:+$s; }s/^(\s*lseaspray\s*=[^\n]*)$/\1$ins/"
  j=$(JOBMIN=$jm $C/tools/mkrun.sh "$name" "$C/exe/$exe" "$s" "$mc" $env 2>&1 | tail -1)
  echo "$(date +%H:%M) $name job $j"
done < "$1"
echo RUNQ DONE
