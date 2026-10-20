#!/bin/bash
# usage: nohup buildq.sh name:tree[:suites] ... & ; submits builds keeping <= 2 of my jobs queued, copies exe to exe/
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy
for spec in "$@"; do
  n=${spec%%:*}; r=${spec#*:}; t=${r%%:*}; s=""; [ "$r" != "$t" ] && s=${r#*:}
  while [ "$(squeue -h -u $USER -o %j | grep -c '^c_\|^cr_')" -ge 2 ]; do sleep 60; done
  sbatch -J c_$n --export=NONE,SRC=$C/$t/ufs-weather-model,SUITES=${s:-FV3_GFS_v17_p8_ugwpv1} $C/tools/build64.sbatch
done
while [ "$(squeue -h -u $USER -o %j | grep -c '^c_')" -ge 1 ]; do sleep 60; done
for spec in "$@"; do n=${spec%%:*}; r=${spec#*:}; t=${r%%:*}
  cp $C/$t/ufs-weather-model/tests/fv3_c_$n.exe $C/exe/ 2>/dev/null && echo "exe c_$n ok" || echo "exe c_$n MISSING"
done
echo BUILDQ DONE
