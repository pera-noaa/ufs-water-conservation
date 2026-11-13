#!/usr/bin/env python3
"""Test-only hook (apply after instrument_tm.py): at the first atmosphere_dynamics call set pt_udry to exactly
1e-6*(1 - sum water) and pt_umoist to exactly 1e-6, i.e. after external_ic's remap and adiabatic init.
Usage: testhook_uniform_reset.py <ufs-weather-model tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90"
s = f.read_text()
a1 = "   type(time_type) :: atmos_time\n"
a2 = "   tm_iu = max(get_tracer_index(MODEL_ATMOS, 'pt_umoist'), 0)\n"
for a in (a1, a2):
    if s.count(a) != 1:
        sys.exit(f"ABORT {s.count(a)} matches {a!r}")
s = s.replace(a1, a1 + "   logical, save :: tm_first = .true.\n   integer :: tm_k, tm_j, tm_i\n")
s = s.replace(a2, a2 + """   if (tm_first) then   ! TEST HOOK: exact uniform test tracers after the IC remap
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
     tm_first = .false.
   endif
""")
f.write_text(s)
print("uniform reset hook", f)
