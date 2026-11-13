#!/bin/bash
# share401.sh: a self-contained copy of two run directories for ccpp-physics#401 (develop, and the 24 fixes that crash),
# with executables, inputs, logs and the source diffs; history/restart output and PET logs left out. Private (group co2).
set -eu
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; H=$P/hafs_exp; S=/work2/noaa/co2/ash/share/ccpp401
[ -e $S ] && { echo "$S exists"; exit 1; }
mkdir -p $S
for pair in develop:q_dev_c1000:q/dev crash_24fixes:q_t1a_c1000:q/t1a; do
  IFS=: read name run tree <<< "$pair"
  rsync -a --exclude '*.nc' --exclude 'PET*.ESMF_LogFile' --exclude 'RESTART/' $H/$run/ $S/$name/
  cp -a $H/$run/INPUT/. $S/$name/INPUT/
  git -C $P/$tree/UFSATM/ccpp/physics diff d9b70feba915022424b35aa0ab33535b9b8c6571 -- . > $S/$name/ccpp-physics.diff
  echo "$name: ccpp-physics $(git -C $P/$tree/UFSATM/ccpp/physics rev-parse --short HEAD) (diff vs ufs/dev d9b70feb, includes the print-only DBGSAMF block), ufsatm $(git -C $P/$tree/UFSATM rev-parse --short HEAD), noahmp $(git -C $P/$tree/NOAHMP-interface/noahmp rev-parse --short HEAD), WM $(git -C $P/$tree rev-parse --short HEAD)" >> $S/versions.txt
done
cp $H/dbg4_deep.f $H/dbg4_shal.f $S/
cat > $S/README.txt <<'TXT'
ccpp-physics#401: hafs_global_1nest_atm, Hercules, Intel (rt.sh compile "hafsw": -DAPP=HAFSW -DMOVING_NEST=ON
-DCCPP_SUITES=FV3_HAFS_v1_gfdlmp_tedmf,... -D32BIT=ON), 6 h, 6 nodes, about 2.5 min.

develop/        ufs-weather-model develop f1d68949 + the print-only DBGSAMF block (dbg4_deep.f, dbg4_shal.f), consv_te = 1.
                Runs to 6 h; out has the DBGSAMF lines (one per layer heated > 4 K in one step).
crash_24fixes/  the same plus our 24 water/energy fixes (ccpp-physics.diff), consv_te = 1.
                Stops with "compute_qs: saturation vapor pressure table overflow" (err).

Each directory has fv3.exe, INPUT/, the namelists, field_table, model_configure, diag_table, ufs.configure, job_card
(SBATCH account lpdm; change it), out, err and log.atm.f*. History and restart files are left out.
versions.txt has the source hashes.
TXT
du -sh $S | cut -f1; ls $S $S/develop | head -40 | tr '\n' ' '
