#!/bin/bash
# trdyn run dirs. usage: mkruns.sh A|B|C
set -euo pipefail
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn; M="bash $W/bin/make_rundir.sh"
DC=$W/dc/tests/fv3_dc.exe; DY=$W/dy/tests/fv3_dy.exe
export OUTFH="0 6 12 18 24"
case ${1:?} in
A)  # class c, uniform tracers reset at the first dynamics call (IC excluded)
  $M c0 $DC
  $M o0 $DY
  NML="dry_tracer_adv=.true." $M a1 $DY ;;
B)  # end-to-end (no reset): unfixed dycore + moist IC / dry IC only / both fixes (writes 12 h restart) / both on 4x6
  $M n0 $DY TRDYN_NORESET=1
  ICD=$W/ic_d NML="dry_tracer_ic=.true." $M i1 $DY TRDYN_NORESET=1
  ICD=$W/ic_d NML="dry_tracer_adv=.true. dry_tracer_ic=.true." RSTI=12 $M e2 $DY TRDYN_NORESET=1
  ICD=$W/ic_d NML="dry_tracer_adv=.true. dry_tracer_ic=.true." LAYOUT=4,6 $M e2L $DY TRDYN_NORESET=1 ;;
C)  # warm start of e2 from its 12 h restart
  ICD=$W/ic_d NML="dry_tracer_adv=.true. dry_tracer_ic=.true." $M e2R $DY TRDYN_NORESET=1
  bash $W/bin/mk_warm.sh e2R e2 ;;
esac
