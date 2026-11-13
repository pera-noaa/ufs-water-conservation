#!/bin/bash
# usage: chain_local.sh <dir> metered|plain : emulate the full round-4 tree locally (for anchors and gfortran checks)
L=/Users/pera/Documents/ash-code/ufs-chem-v1/conservation/ensfc2
d=${1:?dir}; kind=${2:-metered}
rm -rf "${d:?}"; mkdir -p $d
if [ $kind = metered ]; then cp -R $L/mfxsrc/UFSATM $L/mfxsrc/cmake $d/; else $L/tools/mkfake.sh $d; fi
mkdir -p $d/UFSATM/ccpp/physics/physics/Radiation/RRTMG; cp $L/fxsrc/Radiation/RRTMG/* $d/UFSATM/ccpp/physics/physics/Radiation/RRTMG/
cd $d
if [ $kind = metered ]; then for m in instrument_es_sfc instrument_es_sfc2 es_static es_icefix instrument_es_sfc3 instrument_es_sfc4 instrument_es_sfc5; do python3 $L/meters/tools/$m.py $d >/dev/null || echo FAIL $m; done; fi
python3 $L/tools/apply_sfc_fixes.py $d SI1 SI2 NP1 >/dev/null || echo FAIL fixes
python3 $L/tools/apply_bugfix.py $d QR1 CMC FL1 >/dev/null || echo FAIL bugfix
(cd UFSATM/ccpp/physics && patch -p1 -s --no-backup-if-mismatch < $L/../nm12/patches/20_NM12_noahmp_combine_melt_out.diff) || echo FAIL nm12
python3 $L/tools/apply_bugfix_r4.py $d SL2 CS1 CB1 >/dev/null || echo FAIL bugfix_r4
python3 $L/tools/apply_options.py $d >/dev/null || echo FAIL options
python3 $L/tools/apply_options_r4.py $d >/dev/null || echo FAIL options_r4
if [ $kind = metered ]; then patch -p1 -s < $L/../encnv/patches/01_D3A.diff; for m in instrument_es2_r3 instrument_es2_r3b instrument_es2_r3c instrument_es2_r3d instrument_es2_r4; do python3 $L/tools/$m.py $d >/dev/null || echo FAIL $m; done; fi
echo CHAIN_DONE
