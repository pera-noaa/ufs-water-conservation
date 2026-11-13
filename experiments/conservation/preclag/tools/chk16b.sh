#!/bin/bash
# chk16b.sh : 16b applies where 16 applies (dry run on energy/fx), and its MP_generic_post.meta block equals full12's
set -uo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; E=$U/cons/energy; P=$U/cons/preclag
D=$P/patches/16b_sfc_options_r4_meta_fixed.diff
cd $E/fx && { echo "16  on fx: $(patch -p1 --dry-run -F0 < $U/cons/ensfc2/patches/16_sfc_options_r4.diff | grep -c -i 'fail\|reject')"; echo "16b on fx: $(patch -p1 --dry-run -F0 < $D | grep -c -i 'fail\|reject')"; }
M=ufs-weather-model/UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.meta
awk '/^\+\+\+ .*GFS_MP_generic_post.meta/{f=1;next} f&&/^--- /{f=0} f&&/^\+/{print substr($0,2)}' $D > $P/xfer/16b_meta_added.txt
n=$(wc -l < $P/xfer/16b_meta_added.txt); echo "16b meta added lines: $n"
tail -n $n $E/full12/$M | diff - $P/xfer/16b_meta_added.txt && echo "full12 meta tail == 16b added block"
F=ufs-weather-model/UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_MP_generic_post.F90
grep -c "sfc_precip_enthalpy, con_cliq, tgrs)" $E/full12/$F
