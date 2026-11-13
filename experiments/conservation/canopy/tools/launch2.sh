#!/bin/bash
# submit the compile check when fewer than 2 of my c_/cr_ jobs are queued
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy
nohup bash -c "while [ \$(squeue -h -u \$USER -o %j | grep -c '^c_\|^cr_') -ge 2 ]; do sleep 20; done; sbatch $C/tools/chk.sbatch" > $C/logs/chk_submit.txt 2>&1 &
