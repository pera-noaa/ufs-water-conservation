#!/bin/bash
# early.sh : first look at g_off (vs full12 rs12_S) and m_on (master budget + EML)
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/preclag
Y=/work2/noaa/co2/miniconda3/envs/tm5/bin/python; T=$E/tools; cd $P/runs
tail -2 g_off/out | cut -c1-120; tail -2 m_on/out | cut -c1-120
for f in atmf024 sfcf024 RESTART/20210323.060000.sfc_data RESTART/20210323.060000.phy_data; do echo "g_off vs rs12_S $f: $($Y -I $T/cmp_allvars.py g_off $E/runs/rs12_S $f 1 2>&1 | head -1)"; done
grep -o "sfc_precip_t1_carry *= *[.a-z]*" m_on/input.nml
$Y -I ../tools/frameF_table_pl.py m_on/out 720 --ep1
