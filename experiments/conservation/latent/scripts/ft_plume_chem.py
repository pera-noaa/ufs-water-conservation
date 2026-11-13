#!/usr/bin/env python3
"""Run-dir edit for the F3 borrowing test: make pt_plume a chemistry tracer and keep the chemistry tracers contiguous
(order ... pt_cnv, pt_umoist, pt_plume, pt_ghg, pt_udry). usage: ft_plume_chem.py <rundir>"""
import sys
from pathlib import Path
p = Path(sys.argv[1]) / "field_table"
assert not p.is_symlink()
s = p.read_text()
blocks = {}
for name in ("pt_plume", "pt_umoist"):
    i = s.index(f' "TRACER", "atmos_mod", "{name}"')
    j = s.index("/\n", i) + 2
    blocks[name] = s[i:j]
assert s.index(blocks["pt_plume"]) + len(blocks["pt_plume"]) == s.index(blocks["pt_umoist"])
chem = blocks["pt_plume"].replace('           "units",        "kg/kg"\n',
                                  '           "units",        "kg/kg"\n       "tracer_usage", "chemistry"\n', 1)
assert chem != blocks["pt_plume"]
s = s.replace(blocks["pt_plume"] + blocks["pt_umoist"], blocks["pt_umoist"] + chem)
p.write_text(s)
print("pt_plume -> chemistry, after pt_umoist")
