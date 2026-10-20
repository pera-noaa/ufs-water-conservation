#!/bin/bash
until grep -q "QUEUE DONE" /Users/pera/Documents/ash-code/ufs-chem-v1/conservation/ensfc2/xfer/q6.log; do sleep 30; done
/Users/pera/Documents/ash-code/ufs-chem-v1/conservation/ensfc2/xfer/runqueue.sh /Users/pera/Documents/ash-code/ufs-chem-v1/conservation/ensfc2/xfer/q7.txt
