#!/usr/bin/env python3
"""TEST ONLY: if env TRSAMF_NPC is set, GFS_PBL_generic_post discards the PBL tendency of the chemistry tracers
(they are then not PBL-mixed, everything else unchanged). Usage: hook_npc_env.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE/GFS_PBL_generic_post.F90"
s = f.read_text()
a = "                ten_q(i,k,n) = dvdftra(i,k,k1)\n"
for x in (a,):
    if s.count(x) != 1:
        sys.exit(f"ABORT {s.count(x)} {x!r}")
s = s.replace(a, a + "                if (trsamf_npc) ten_q(i,k,n) = 0.0_kind_phys  ! TEST HOOK\n")
# declare + read env once, right after the first executable-free point: use the 'if (trans_aero) then' of the ten_q block
a2 = "        if (trans_aero) then\n          ! Set kk if chemistry-aerosol tracers are diffused\n"
if s.count(a2) != 1:
    sys.exit(f"ABORT a2 {s.count(a2)}")
s = s.replace(a2, "        call get_environment_variable('TRSAMF_NPC', length=trsamf_len)  ! TEST HOOK\n"
              "        trsamf_npc = trsamf_len > 0\n" + a2)
a3 = "      implicit none\n"
i = s.index("subroutine GFS_PBL_generic_post_run")
j = s.index(a3, i)
s = s[:j] + a3 + "      logical :: trsamf_npc  ! TEST HOOK\n      integer :: trsamf_len\n" + s[j + len(a3):]
f.write_text(s)
print("npc hook", f)
