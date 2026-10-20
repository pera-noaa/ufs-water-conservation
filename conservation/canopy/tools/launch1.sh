#!/bin/bash
# start the m1 build queue and the run queue (lists 1, 2) in the background
C=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/canopy; cd $C
nohup tools/buildq_b.sh m1:m1 > logs/buildq3.txt 2>&1 &
nohup bash -c "tools/runq3.sh runs/list1.txt; tools/runq3.sh runs/list2.txt" > logs/runq2.txt 2>&1 &
