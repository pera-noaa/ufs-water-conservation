#!/bin/bash
#SBATCH -A co2 -p hercules -q batch -N 1 --ntasks-per-node=16 -t 02:30:00
# usage: sbatch -J sc_build_<v> -o build_<v>.%j.log build.sbatch <variant: meter|meterfix> <compile ids...>
set -eu
v=${1:?variant}; shift
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/suites_closure
SRC=/work2/noaa/co2/ash/ufs-chem-v1/upstream/suites/allfix/ufs-weather-model
T=$W/$v/ufs-weather-model
if [ ! -e $T/.instrumented ]; then
  mkdir -p $W/$v
  rsync -a --exclude=/.git/ --exclude='/tests/fv3_*.exe' --exclude='/tests/fail_test_*' --exclude='/tests/logs/' $SRC/ $T/
  /work2/noaa/co2/miniconda3/envs/tm5/bin/python -I $W/instrument_suites.py $T $v
  touch $T/.instrumented
fi
cd $T/tests
export BUILD_JOBS=16
for c in "$@"; do
  case $c in
    atm_dyn32) opt="-DAPP=ATM -DCCPP_SUITES=FV3_GFS_v16,FV3_GFS_v17_p8_mynn,FV3_GFS_v16_gfdlmpv3 -D32BIT=ON" ;;
    rrfs) opt="-DAPP=ATM -DCCPP_SUITES=FV3_RAP,FV3_HRRR,FV3_RRFS_v1beta,FV3_RRFS_v1nssl -D32BIT=ON" ;;
  esac
  ./compile.sh hercules "$opt" ${c}_intel intel > $W/compile_${v}_${c}.log 2>&1
  ls -la $T/tests/fv3_${c}_intel.exe
done
echo BUILD_DONE
