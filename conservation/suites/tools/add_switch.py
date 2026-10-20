"""add_switch.py <name> <standard_name> <comment> : add a logical gfs_physics_nml switch (default .false.) to
work/data/GFS_typedefs.F90/.meta next to samf_kirchhoff."""
import sys
from pathlib import Path
name, std, com = sys.argv[1:4]
f = Path('work/data/GFS_typedefs.F90'); s = f.read_text()
def sub(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
sub("    logical              :: samf_kirchhoff  !< SAMF latent heat of condensation L_v(T) of the host energy frame\n",
    "    logical              :: samf_kirchhoff  !< SAMF latent heat of condensation L_v(T) of the host energy frame\n"
    f"    logical              :: {name:15s} !< {com}\n")
sub("    logical              :: samf_kirchhoff = .false.            !< SAMF latent heat of condensation L_v(T) of the host energy frame\n",
    "    logical              :: samf_kirchhoff = .false.            !< SAMF latent heat of condensation L_v(T) of the host energy frame\n"
    f"    logical              :: {name} = .false. !< {com}\n")
sub("thompson_kirchhoff, samf_kirchhoff, thompson_frame_heat,",
    f"thompson_kirchhoff, samf_kirchhoff, thompson_frame_heat, {name},")
sub("    Model%samf_kirchhoff = samf_kirchhoff\n", f"    Model%samf_kirchhoff = samf_kirchhoff\n    Model%{name} = {name}\n")
f.write_text(s)
m = Path('work/data/GFS_typedefs.meta'); t = m.read_text()
a = "[samf_kirchhoff]\n  standard_name = flag_for_samf_kirchhoff_latent_heat\n"
assert t.count(a) == 1
t = t.replace(a, f"[{name}]\n  standard_name = {std}\n  long_name = {com}\n  units = flag\n  dimensions = ()\n  type = logical\n" + a)
m.write_text(t)
print("switch", name, "added")
