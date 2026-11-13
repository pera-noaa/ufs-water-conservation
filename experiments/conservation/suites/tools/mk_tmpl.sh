#!/bin/bash
# mk_tmpl.sh : $S/tmpl/<test> from $U/suites/wb/orig_<test> (copied, outputs excluded), 24 h, passive tracers pt_u/pt_s
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; S=$U/cons/suites
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
mkdir -p $S/tmpl $S/ic
[ -e $S/ic/gfs_data.tile6.nc ] || $PY $S/tools/make_ic2.py $U/suites/wb/orig_rap_control/INPUT $S/ic
for t in control_p8_mynn control_iovr4_gfdlmpv3 rap_control; do
  src=$U/suites/wb/orig_$t; dst=$S/tmpl/$t
  [ -e "$dst" ] && { echo "skip $t (exists)"; continue; }
  rsync -a --exclude='atmf*' --exclude='sfcf*' --exclude='PET*' --exclude=ESMF_Profile.summary --exclude=err \
    --exclude=out --exclude=job_timestamp.txt --exclude='log.atm.*' --exclude='logfile.*' --exclude='warnfile.*' \
    --exclude='RESTART/*' --exclude='GFS*.Grb*' --exclude='*.nc_nccmp.log' --exclude=fv3.exe --exclude='atmos_4xdaily*' \
    --exclude='budget*' --exclude='meter_report*' "$src/" "$dst/"
  cd "$dst"
  [ -n "$(find . -maxdepth 2 -type l)" ] && { echo "ABORT: symlinks in $dst"; exit 1; }
  for b in 1 2 3 4 5 6; do cp -p $S/ic/gfs_data.tile$b.nc INPUT/gfs_data.tile$b.nc; done
  TR=' "TRACER", "atmos_mod", "pt_u"
           "longname",     "uniform passive tracer (moist mixing ratio 1e-6)"
           "units",        "kg/kg"
       "profile_type", "fixed", "surface_value=0.0" /
 "TRACER", "atmos_mod", "pt_s"
           "longname",     "structured passive tracer"
           "units",        "kg/kg"
       "profile_type", "fixed", "surface_value=0.0" /'
  $PY - "$TR" <<'PYEOF'
import sys, re
tr = sys.argv[1] + "\n"
s = open('field_table').read()
i = s.find(' "TRACER", "atmos_mod", "cld_amt"')
s = s[:i] + tr + s[i:] if i >= 0 else s.rstrip('\n') + '\n' + tr
open('field_table', 'w').write(s)
names = [m.group(1) for l in s.splitlines() if not l.lstrip().startswith('#')
         for m in [re.search(r'"TRACER",\s*"atmos_mod",\s*"([^"]+)"', l)] if m]
open('sm_env', 'w').write(f"export SM_NTU={names.index('pt_u')+1} SM_NTS={names.index('pt_s')+1}\n")
print(len(names), names)
PYEOF
  sed -i -E 's/^(\s*max_output_fields\s*=\s*).*/\1600/' input.nml
  sed -i -E 's/^(nhours_fcst:\s+).*/\124/' model_configure
  grep -q zstandard_level model_configure && sed -i -E 's/^(zstandard_level:\s+).*/\10/' model_configure
  echo "$t: $(cat sm_env) $(grep -E '^(nhours_fcst|dt_atmos)' model_configure | tr -s ' ' | tr '\n' ' ')"
done
