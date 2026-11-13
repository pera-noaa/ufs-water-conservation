#!/usr/bin/env python3
"""Fix B for TEMPO's CCPP driver: mp_tempo_run converts to mixing ratios and back with the input (host-basis) humidity
in both directions, as diff 02 does for mp_thompson.F90. Usage: python3 apply_tempo_b_patch.py <ccpp-physics dir>
The driver returns tendencies (new - old)/dtp. Converting back with /(1+qv) puts the new values per (dry air + new
vapour), while the host applies them to a state per (dry air + old vapour) and FV3 rebuilds mass with the old
thickness: net condensation creates water, net evaporation removes it. Only mp_tempo_run is changed; mp_tempo_init's
aerosol conversion (no vapour change there) is left alone."""
import sys
from pathlib import Path

f = Path(sys.argv[1]) / "physics/MP/TEMPO/mp_tempo.F90"
s = f.read_text()
i = s.index("subroutine mp_tempo_run")
head, run = s[:i], s[i:]

fwd_old = "         qv = new_spechum/(1.0_kind_phys-new_spechum)\n"
back_old = "         new_spechum = qv/(1.0_kind_phys+qv)\n"
for t in (fwd_old, back_old):
    if run.count(t) != 1:
        sys.exit(f"ABORT: {t.strip()!r} found {run.count(t)} times in mp_tempo_run")
a = run.index(fwd_old)
a_end = run.index("\n\n", run.index("if (convert_dry_rho) then", a))
b = run.index(back_old)
b_end = run.index("dspechum = (new_spechum - spechum)/dtp", b)
fwd, back = run[a:a_end], run[b:b_end]
nf, nb = fwd.count("/(1.0_kind_phys-new_spechum)"), back.count("/(1.0_kind_phys+qv)")
if (nf, nb) != (13, 13):
    sys.exit(f"ABORT: expected 13 forward and 13 backward conversions, found {nf}, {nb}")
fwd = ("         ! convert with the input (host-basis) humidity in both directions, so the host's mass rebuild is exact\n"
       + fwd.replace("/(1.0_kind_phys-new_spechum)", "/(1.0_kind_phys-spechum)"))
back = back.replace("new_spechum = qv/(1.0_kind_phys+qv)", "new_spechum = qv*(1.0_kind_phys-spechum)") \
           .replace("/(1.0_kind_phys+qv)", "*(1.0_kind_phys-spechum)")
run = run[:a] + fwd + run[a_end:b] + back + run[b_end:]
f.write_text(head + run)
print(f"patched {f.name} (B for TEMPO: {nf} forward, {nb} backward conversions)")
