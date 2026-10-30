#!/bin/bash
# r14_setup.sh: CP1/FV2 WoFS attribution dirs + run templates (hard links of the rt_w_fv4 RT inputs; configs real copies)
set -euo pipefail
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/r14_1c; P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1
RT=$P/attr/rt_w_fv4/stmp/apera/FV3_RT/rt_390837
mkdir -p $W/exe $W/logs $W/src $W/runs
for t in regional_wofs_tempo regional_wofs; do
  S=$RT/${t}_intel; T=$W/tmpl/$t
  [ -e $T ] && { echo "ABORT: $T exists"; exit 1; }
  mkdir -p $T/RESTART
  for f in $(ls $S); do
    case $f in atmf*|sfcf*|dynf*|phyf*|NATLEV*|PRSLEV*|GFSFLX*|GFSPRS*|*_nccmp.log|err|out|ESMF_Profile*|log.atm.*|logfile.*|PET*|warnfile.*|job_timestamp.txt|RESTART|fv3.exe) continue;;
      input.nml|model_configure|ufs.configure|diag_table|field_table|job_card|fd_ufs.yaml|itag|module-setup.sh) cp -p $S/$f $T/$f;;
      *) cp -al $S/$f $T/$f;;
    esac
  done
  sed -i -e 's/^output_fh: .*/output_fh:               6/' -e 's/^write_dopost: .*/write_dopost:            .false./' $T/model_configure
  cmp -s $S/input.nml $T/input.nml || { echo "GATE input.nml"; exit 1; }
  diff $S/model_configure $T/model_configure | grep '^[<>]' || true
  [ "$(diff $S/model_configure $T/model_configure | grep -c '^>')" = 2 ] || { echo "GATE model_configure: not exactly 2 edits"; exit 1; }
  echo "tmpl $t: $(ls $T | wc -l) entries, real size $(du -sh --apparent-size $T/model_configure | cut -f1) cfg; links ok"
done
echo SETUP_OK
