#!/bin/bash
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy; cd $C
nohup tools/runq3.sh runs/list3.txt > logs/runq3.txt 2>&1 &
