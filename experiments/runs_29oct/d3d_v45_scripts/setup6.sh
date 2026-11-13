#!/bin/bash
# setup6.sh: #403 variants 4/5 = Jongil's diff3d (#429 @8460b55b) / FV3 delp (4) or / physics mass (5); rebuild r14d3d4;
# runs v4, v5 and a v3 rerun (gate: bitwise = d3d_v3_3d)
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; C=$U/cons/upchk; T=$U/cons/energy/runs/tmpl; D=$U/cons/r14_d3d; M=$U/cons/r14_mlm
source $C/arms.sh
S=$D/src/ufs-weather-model/UFSATM/fv3/atmos_cubed_sphere
FD=$S/model/dyn_core.F90; FA=$S/driver/UFS/atmosphere.F90
[ -e $D/logs/dyn_core.F90.r14c ] && { echo ABORT; exit 1; }
[ -e $D/logs/PREREG_v45.md ] || { echo "ABORT: no prereg"; exit 1; }
cp -p $FD $D/logs/dyn_core.F90.r14c; cp -p $FA $D/logs/atmosphere.F90.r14c
/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I $D/bin/apply_d3d45.py $FD $FA || exit 1
diff $D/logs/atmosphere.F90.r14c $FA; diff $D/logs/dyn_core.F90.r14c $FD | grep -c '^>'
mk() { local name=$1 v=$2 dst=$D/runs/$1
  [ -e $dst ] && { echo ABORT; exit 1; }
  rsync -a --exclude=fv3.exe.ctl64 --exclude=fv3.exe --exclude=out --exclude=err --exclude='*.nc' --exclude=RESTART --exclude=budget_by_scheme.txt $T/ $dst/
  mkdir -p $dst/RESTART; for f in $T/*.nc; do [ -L "$f" ] && cp -P "$f" $dst/; done
  cp -p $D/runs/d3d_v2_3d/{input.nml,model_configure,job_card} $dst/
  sed -i "s|r14d3d.exe|r14d3d4.exe|g; s|UPCHK_D3D=2|UPCHK_D3D=$v|; s|r14d_d3d_v2_3d|r14d_$name|" $dst/job_card
  grep "UPCHK_D3D=$v" $dst/job_card >/dev/null && grep r14d3d4.exe $dst/job_card >/dev/null || { echo ABORT jc; exit 1; }; }
mk d3d_v4_3d 4
mk d3d_v5_3d 5
mk d3d_v3_3d_b4 3
sed "s|r14d3d3.exe|r14d3d4.exe|; s|r14d_build3|r14d_build4|; s|build3\.|build4.|" $D/bin/build3.sbatch > $D/bin/build4.sbatch
b=$(sbatch --parsable $D/bin/build4.sbatch)
j1=$(cd $D/runs/d3d_v4_3d && sbatch --parsable --dependency=afterok:$b job_card)
j2=$(cd $D/runs/d3d_v5_3d && sbatch --parsable --dependency=afterok:$b job_card)
j3=$(cd $D/runs/d3d_v3_3d_b4 && sbatch --parsable --dependency=afterok:$b job_card)
echo "build4 $b d3d_v4_3d $j1 d3d_v5_3d $j2 d3d_v3_3d_b4 $j3" | tee -a $M/logs/jobs.txt
