#!/bin/bash
# usage: nohup mkgate10.sh & : default-off gate trees, both -no-fma (ensfc2 tools/nofma.py):
#   gA = full10 (everything), gB = fx + switchless bug fixes only (R1 TH8 FV2 D3A NM12 latent 01a 02 03, trdyn 02b 04_INLQ,
#   ensfc2 04 05 06 08 09 10); and nth8 = mq10 with TH8 reverse-applied (TH8 separability). <= 2 own builds at a time.
set -uo pipefail
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
A=$E/accepted; S2=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2/patches; NF=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/ensfc2/tools/nofma.py
TH8=$A/23_energy_06_TH8_thompson_count_all_sedimented_precip.diff
cp_tree() { [ -e "$2" ] && { echo "ABORT: $2 exists"; exit 1; }; rsync -a --exclude="ufs-weather-model/tests/build_*" --exclude="ufs-weather-model/tests/*.exe" $1/ $2/; }
apply() {  # apply <tree> <diff> : find base dir and -p level by -F0 dry run (as integrate.sh)
  for b in . UFSATM UFSATM/fv3/atmos_cubed_sphere UFSATM/fv3 UFSATM/ccpp UFSATM/ccpp/physics UFSATM/ccpp/physics/physics; do
    for lev in 1 0 2; do
      if (cd $1/ufs-weather-model/$b && patch -p$lev --dry-run -F0 -s < "$2" >/dev/null 2>&1); then
        (cd $1/ufs-weather-model/$b && patch -p$lev -F0 -s < "$2"); echo "$(basename $1): $(basename $2) -p$lev in $b"; return 0; fi
    done
  done
  echo "ABORT: $(basename $2) does not apply to $1"; exit 1
}
cp_tree $E/full10 $E/gA; $P -I $NF $E/gA/ufs-weather-model
cp_tree $E/fx $E/gB
$P -I $E/tools/apply_fixes_r4.py $E/gB/ufs-weather-model R1 TH8 >/dev/null || { echo "ABORT: R1 TH8"; exit 1; }; echo "gB: R1 TH8 (apply_fixes_r4)"
for d in $A/01_FV2_fv3_statein_consistent_layer_mass.diff $A/03_encnv_D3A.diff $A/07_NM12_noahmp_combine_melt_out.diff \
         $A/12_latent_01a_F3_samf_scavenging_booking.diff $A/14_latent_02_SAMF32_cmake_filter_dependencies.diff \
         $A/15_latent_03_TOPT_process_split_sum_applied_once.diff $A/16_trdyn_02b_T1_samf_tracer_substep.diff \
         $A/18c_trdyn_04_INLQ_inline_q_damping_mass_single_valued.diff \
         $S2/04_sfc_SI1.diff $S2/05_sfc_SI2.diff $S2/06_sfc_NP1.diff $S2/08_sfc_QR1.diff $S2/09_sfc_CMC.diff $S2/10_sfc_FL1.diff; do
  apply $E/gB $d
done
$P -I $NF $E/gB/ufs-weather-model
cp_tree $E/mq10 $E/nth8; (cd $E/nth8/ufs-weather-model && patch -R -p1 -F0 -s < $TH8) || { echo "ABORT: TH8 reverse"; exit 1; }; echo "nth8: TH8 reversed"
cd $E
sbatch -J e_gA --export=NONE,SRC=$E/gA/ufs-weather-model,CLEAN=YES build64.sbatch
sbatch -J e_gB --export=NONE,SRC=$E/gB/ufs-weather-model,CLEAN=YES build64.sbatch
sleep 30; while [ "$(squeue -h -n e_gA,e_gB 2>/dev/null | wc -l)" -ge 2 ]; do sleep 60; done
sbatch -J e_nth8 --export=NONE,SRC=$E/nth8/ufs-weather-model,CLEAN=YES build64.sbatch
echo "TREES SUBMITTED"
