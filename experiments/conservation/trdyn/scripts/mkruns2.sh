#!/bin/bash
# trdyn round 2 run dirs. usage: mkruns2.sh D|B|S|T
set -euo pipefail
W=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/trdyn; M="bash $W/bin/make_rundir.sh"
DC=$W/dc/tests/fv3_dc.exe; D2=$W/dy2/tests/fv3_dy2.exe; DB=$W/dyb/tests/fv3_dyb.exe
N32=$W/n32/tests/fv3_n32.exe; N32C=$W/n32c/tests/fv3_n32c.exe
export OUTFH="0 6 12 18 24"
ZT="z_tracer=.false. nord_tr=2 trdm2=0.05"
case ${1:?} in
D)  # dy2 (02+03+v2), 64-bit metered, uniform reset at first dynamics call
  $M u0 $D2                                              # off, z_tracer=T  (vs c0 of dc)
  NML="dry_tracer_adv=.true." $M a2 $D2                  # on, z_tracer=T (vs a1 of round 1)
  NML="$ZT" $M tc $DC                                    # tracer_2d + damping, unfixed build
  NML="$ZT" $M t0 $D2                                    # same, v2 build, off
  NML="$ZT dry_tracer_adv=.true." $M t1 $D2              # same, on
  NML="inline_q=.true." $M q0 $D2                        # inline_q, off
  NML="inline_q=.true. dry_tracer_adv=.true." $M q1 $D2 ;;  # inline_q, on
T)  # OpenMP 2 threads (ESMF-managed), dry on, z_tracer=T; compare with a2
  NML="dry_tracer_adv=.true." $M h2 $D2 NT=300
  cd $W/rt/h2; sed -i -E 's/^(ATM_petlist_bounds:\s+).*/\10 299/; s/^(ATM_omp_num_threads:\s+).*/\12/' ufs.configure
  grep -E 'ATM_petlist|ATM_omp' ufs.configure ;;
B)  # dyb (02b+03b+v2), 64-bit metered: end-to-end, both switches, dry IC, no reset; plus unfixed-dycore reference
  ICD=$W/ic_d NML="dry_tracer_adv=.true. dry_tracer_ic=.true." $M b2 $DB TRDYN_NORESET=1
  NML="dry_tracer_adv=.true." $M b1 $DB ;;               # reset at first dynamics call (as a1/a2)
S)  # 32-bit (n32: 02b+03b+v2, no meters; n32c: same without v2)
  $M s0c $N32C
  $M s0 $N32
  ICD=$W/ic_d NML="dry_tracer_adv=.true. dry_tracer_ic=.true." $M s2 $N32 ;;
esac
