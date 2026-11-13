#!/usr/bin/env python3
"""Test-only hook (apply after instrument_tm.py): as the tracer agent's testhook_uniform_reset.py (at the first
atmosphere_dynamics call pt_udry = 1e-6*(1 - sum water), pt_umoist = 1e-6), but skipped when env TRDYN_NORESET is set
(end-to-end runs that keep the IC). Usage: testhook_uniform_reset_env.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90"
s = f.read_text()
a1 = "   type(time_type) :: atmos_time\n"
a2 = "   tm_iu = max(get_tracer_index(MODEL_ATMOS, 'pt_umoist'), 0)\n"
for a in (a1, a2):
    if s.count(a) != 1:
        sys.exit(f"ABORT {s.count(a)} matches {a!r}")
s = s.replace(a1, a1 + "   logical, save :: tm_first = .true.\n   integer :: tm_k, tm_j, tm_i, tm_nr\n")
s = s.replace(a2, a2 + """   if (tm_first) then   ! TEST HOOK: exact uniform test tracers after the IC remap
     call get_environment_variable('TRDYN_NORESET', length=tm_nr)
     if (tm_nr == 0) then
     do tm_k = 1, npz
       do tm_j = jsc, jec
         do tm_i = isc, iec
           if (tm_iud > 0) Atm(n)%q(tm_i,tm_j,tm_k,tm_iud) = 1.d-6*(1.d0 - sum(Atm(n)%q(tm_i,tm_j,tm_k,1:Atm(n)%flagstruct%nwat)))
           if (tm_iu > 0) Atm(n)%q(tm_i,tm_j,tm_k,tm_iu) = 1.d-6
         enddo
       enddo
     enddo
     if (tm_iud > 0) call mpp_update_domains(Atm(n)%q(:,:,:,tm_iud), Atm(n)%domain)
     if (tm_iu > 0) call mpp_update_domains(Atm(n)%q(:,:,:,tm_iu), Atm(n)%domain)
     endif
     tm_first = .false.
   endif
""")
f.write_text(s)
print("uniform reset hook (env TRDYN_NORESET skips)", f)
