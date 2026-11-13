#!/usr/bin/env python3
"""TEST ONLY (apply after instrument_tm.py + testhook_uniform_reset.py): if env TRSAMF_RESET is set, pt_udry is reset to
exactly 1e-6*(1 - sum water) at the end of every atmosphere_dynamics call (after meter point 11), so the physics always
receives an exactly uniform dry ratio; the reset itself shows up in the 'gap H>I' term. Usage: hook_reset_every.py <tree>"""
import sys
from pathlib import Path
f = Path(sys.argv[1]) / "UFSATM/fv3/atmos_cubed_sphere/driver/UFS/atmosphere.F90"
s = f.read_text()
a1 = "   logical, save :: tm_first = .true.\n"
a2 = "   call mpp_clock_end (id_subgridz)\n\n end subroutine atmosphere_dynamics\n"
for a in (a1, a2):
    if s.count(a) != 1:
        sys.exit(f"ABORT {s.count(a)} {a!r}")
s = s.replace(a1, a1 + "   logical, save :: tm_rst_every = .false.\n   integer, save :: tm_rst_init = 0\n   integer :: tm_rst_len\n")
s = s.replace(a2, """   if (tm_rst_init == 0) then   ! TEST HOOK: exact uniform pt_udry before every physics step
     call get_environment_variable('TRSAMF_RESET', length=tm_rst_len)
     tm_rst_every = tm_rst_len > 0
     tm_rst_init = 1
   endif
   if (tm_rst_every .and. tm_iud > 0) then
     do tm_k = 1, npz
       do tm_j = jsc, jec
         do tm_i = isc, iec
           Atm(n)%q(tm_i,tm_j,tm_k,tm_iud) = 1.d-6*(1.d0 - sum(Atm(n)%q(tm_i,tm_j,tm_k,1:Atm(n)%flagstruct%nwat)))
         enddo
       enddo
     enddo
     call mpp_update_domains(Atm(n)%q(:,:,:,tm_iud), Atm(n)%domain)
   endif
""" + a2)
f.write_text(s)
print("reset-every hook", f)
