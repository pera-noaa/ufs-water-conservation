#!/bin/bash
H=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/hafs_exp
until broker run --timeout 60 hercules -- 'squeue -h -u $USER -o "%.40j" | grep -q "devCdt" && exit 1; exit 0' >/dev/null 2>&1; do sleep 120; done
broker run --timeout 900 hercules -- "cd $H; PY=/work2/noaa/co2/miniconda3/envs/tm5/bin/python; \$PY -I q_step.py C_dt45 q_devCdt45_c*; \$PY -I q_step.py C_dt90 \$(ls -d q_devC_c* | head -10); \$PY -I q_step.py C_dt180 q_devCdt180_c*; for g in devCdt45 devCdt180; do e=0; c=0; for d in q_\${g}_c*; do grep -q 'HAS ENDED' \$d/out && e=\$((e+1)); grep -qs FATAL \$d/err && c=\$((c+1)); done; echo \"\$g ended \$e crash \$c\"; done"
