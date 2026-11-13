#!/usr/bin/env python3
"""port_eb_phys2.py <in instrument_eb_phys2.py> <out> : port of the physics energy meter to trees without our
precipitation-flux exports (pflx_dc/sc/mpl/mpi): drops those arguments and their S_cross (em_sxp) calls; skips the prebuild config when the tree has none (capgen only).
EMS columns 13-14 (S_cross) then lack the precipitation part; columns 1-12 (dE, F, residuals, water) are unchanged."""
import sys
s = open(sys.argv[1]).read()
reps = [
    ('             ("pflx_dc", "precipitation_mass_through_layer_bottom_from_deep_convection")],', '             ],'),
    ('             ("pflx_sc", "precipitation_mass_through_layer_bottom_from_shallow_convection")],', '             ],'),
    ('              ("pflx_mpl", "liquid_precipitation_mass_through_layer_bottom_from_microphysics"),\n'
     '              ("pflx_mpi", "frozen_precipitation_mass_through_layer_bottom_from_microphysics")] + PH1ARG,',
     '              ] + PH1ARG,'),
    ('       call em_sxp(8, j0+i, levs, pflx_dc(i,:), 4185.5d0, tgrs(i,:))\\n', ''),
    ('       call em_sxp(9, j0+i, levs, pflx_sc(i,:), 4185.5d0, tgrs(i,:))\\n', ''),
    ('                  "       call em_sxp(11, j0+i, levs, pflx_mpl(i,:), 4185.5d0, tgrs(i,:))\\n"\n'
     '                  "       call em_sxp(11, j0+i, levs, pflx_mpi(i,:), 1972.d0, tgrs(i,:))\\n"\n', ''),
    ('c = cfg.read_text()\nif "em_p01" not in c:', 'c = cfg.read_text() if cfg.exists() else "em_p01"\nif "em_p01" not in c:'),
]
for a, b in reps:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(sys.argv[2], "w").write(s)
print("ported", sys.argv[2])
