#!/bin/bash
# usage: to_v17p8.sh <run dir> : switch a control_p8_ugwpv1 namelist to FV3_GFS_v17_p8 (unified_ugwp with UGWP v0 +
# GSL small-scale drag, as default_vars.sh export for atmaero_control_p8)
set -euo pipefail
cd ${1:?}
sed -i -E "s/^(\s*ccpp_suite\s*=\s*).*/\1'FV3_GFS_v17_p8'/; s/^(\s*do_ugwp_v0\s*=\s*).*/\1.true./; s/^(\s*do_ugwp_v1\s*=\s*).*/\1.false./; s/^(\s*do_gsl_drag_ls_bl\s*=\s*).*/\1.false./; s/^(\s*do_gsl_drag_tofd\s*=\s*).*/\1.false./; s/^(\s*knob_ugwp_version\s*=\s*).*/\10/; s/^!\s*launch_level\s*=.*/  launch_level      = 54/" input.nml
grep -E "^\s*(ccpp_suite|do_ugwp_v0|do_ugwp_v1|do_gsl_drag_ls_bl|do_gsl_drag_ss|do_gsl_drag_tofd|gwd_opt|knob_ugwp_version|launch_level)\s*=" input.nml | tr -s ' ' | tr '\n' ' '; echo
# UGWP v0 namelist: v1-only knobs hidden (HIDE_UGWPV1), dokdis/ndx4lh as default_vars.sh v0 export
sed -i -E 's/^(\s*knob_ugwp_(palaunch|nslope|lzmax|lzmin|lzstar|taumin|tauamp|lhmet|orosolv)\s*=)/!\1/; s/^(\s*knob_ugwp_dokdis\s*=\s*).*/\11/; s/^(\s*knob_ugwp_ndx4lh\s*=\s*).*/\11/' input.nml
sed -n '/cires_ugwp_nml/,/^\//p' input.nml | grep -v "^ *!" | tr -s ' ' | tr '\n' ' '; echo
