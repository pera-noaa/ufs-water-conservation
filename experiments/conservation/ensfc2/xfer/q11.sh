#!/bin/bash
until broker run --timeout 60 hercules -- "grep -q TREE_DONE /work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2/logs/tree_mopt10.log" < /dev/null; do sleep 30; done
/Users/pera/Documents/ash-code/ufs-chem-v1/conservation/ensfc2/xfer/runqueue.sh /Users/pera/Documents/ash-code/ufs-chem-v1/conservation/ensfc2/xfer/q11.txt
