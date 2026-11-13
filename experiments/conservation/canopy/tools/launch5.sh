#!/bin/bash
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy; cd $C
nohup tools/runq3.sh runs/list4.txt > logs/runq4.txt 2>&1 &
nohup tools/gates.sh > logs/gates.txt 2>&1 &
