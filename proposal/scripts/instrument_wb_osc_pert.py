#!/usr/bin/env python3
"""Add a run-time temperature perturbation to a metered samfdeepcnv.f (instrument_wb_ka.py output): t1 *= 1+OSC_PEPS at step OSC_PK.
Usage: python3 instrument_wb_osc_pert.py <samfdeepcnv.f>   (rewritten in place)
Env at run time: OSC_PK (step; unset = never), OSC_PLON, OSC_PLAT (deg; every column within 0.6 deg in both), OSC_PEPS
(default 1e-6). Applied at entry, before the scheme reads t1, to all levels. With OSC_PK unset nothing changes.
Every anchor must match exactly once, else nothing is written."""
import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text()
if "wka_kdt" not in s or "osc_pk" in s:
    sys.exit("ABORT: not a metered samfdeepcnv.f, or already perturbed")
R = [
    ("      integer, save :: wka_kdt = -1\n",
     "      integer, save :: wka_kdt = -1\n"
     "      integer, save :: osc_pk = -2\n"
     "      real(kind=8), save :: osc_plo = 0.d0, osc_pla = 0.d0\n"
     "      real(kind=8), save :: osc_pe = 1.d-6\n"),
    ("      logical wka_box(im)\n", "      logical wka_box(im)\n      character(len=32) osc_env\n"),
    ("\n      dt2 = delt\n",
     "\n      if(osc_pk < -1) then\n"
     "        osc_pk = -1\n"
     "        call get_environment_variable('OSC_PK', osc_env)\n"
     "        if(len_trim(osc_env) > 0) read(osc_env,*) osc_pk\n"
     "        call get_environment_variable('OSC_PLON', osc_env)\n"
     "        if(len_trim(osc_env) > 0) read(osc_env,*) osc_plo\n"
     "        call get_environment_variable('OSC_PLAT', osc_env)\n"
     "        if(len_trim(osc_env) > 0) read(osc_env,*) osc_pla\n"
     "        call get_environment_variable('OSC_PEPS', osc_env)\n"
     "        if(len_trim(osc_env) > 0) read(osc_env,*) osc_pe\n"
     "        write(*,'(a,i8,3es14.6)') 'OSC_PERT ', osc_pk, osc_plo,\n"
     "     &    osc_pla, osc_pe\n"
     "      endif\n"
     "      if(kdt == osc_pk) then\n"
     "        do i = 1, im\n"
     "          if(abs(xlon(i)*57.2957795-osc_plo) < 0.6 .and.\n"
     "     &       abs(xlat(i)*57.2957795-osc_pla) < 0.6) then\n"
     "            do k = 1, km\n"
     "              t1(i,k) = t1(i,k) * (1.d0 + osc_pe)\n"
     "            enddo\n"
     "            write(*,'(a,i7,2f9.3,es14.6)') 'OSC_PERTD ', kdt,\n"
     "     &        xlon(i)*57.2957795, xlat(i)*57.2957795, t1(i,1)\n"
     "          endif\n"
     "        enddo\n"
     "      endif\n"
     "      dt2 = delt\n"),
]
for a, b in R:
    if s.count(a) != 1:
        sys.exit(f"ABORT: expected 1 match, found {s.count(a)}: {a.strip()[:60]!r}")
    s = s.replace(a, b)
for ln in s.split("\n"):
    if len(ln) > 72 and not ln.startswith(("!", "c", "C")) and "osc" in ln:
        sys.exit(f"ABORT: line > 72 columns: {ln!r}")
p.write_text(s)
print(f"perturbation hook added: {p}")
