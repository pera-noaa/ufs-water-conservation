#!/bin/bash
#SBATCH -A co2 -p service -n 1 -t 08:00:00 -J mp_rt_plain
#SBATCH -o /work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/logs/rt_plain.%j.log
set -x
rsync -a --exclude='/tests/*.exe' --exclude='/tests/build_*' --exclude='/tests/logs/log_*' --exclude='/tests/run_dir' --exclude='/build/' --exclude='/tests/modules.fv3_*' /work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1/rt_sxd5/ /work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/src_plain/
echo "COPY_DONE $(date -Is)"
export MACHINE_ID=hercules
export PATH=$(echo "$PATH" | tr ":" "\n" | grep -v -i conda | paste -sd:)
unset PYTHONPATH
export dprefix=/work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/rt_plain
mkdir -p ${dprefix}/stmp
cd /work2/noaa/co2/ash/ufs-chem-v1/upstream/meterproto/src_plain/tests
./rt.sh -a co2 -k -n "control_p8 intel"
echo "=== RT_EXIT rc=$? ==="
