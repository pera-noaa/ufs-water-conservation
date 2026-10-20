#!/usr/bin/env python3
"""Integrator merge: apply the SAMF hunks of encpl 06 that conflict textually with encnv 01-04 (arg lists, meta tail,
code inserted just before ten_t). Usage: rebase_encpl06.py <tree after `patch` left .rej files>
The added text is taken verbatim from the .rej files; only the anchors change. Removes the .rej/.orig files."""
import re
import sys
from pathlib import Path

d = Path(sys.argv[1]) / "UFSATM/ccpp/physics/physics/CONV/SAMF"


def plus_blocks(rej):
    out = []
    for h in rej.read_text().split("\n@@")[1:]:
        lines = h.split("\n")[1:]
        minus = [l[1:] for l in lines if l.startswith("-")]
        plus = [l[1:] for l in lines if l.startswith("+")]
        out.append((minus, plus))
    return out


for scheme in ("samfdeepcnv", "samfshalcnv"):
    f = d / f"{scheme}.f"
    s = f.read_text()
    for minus, plus in plus_blocks(Path(str(f) + ".rej")):
        if minus:  # argument list: add pflx, samf_kirchhoff ahead of errmsg in the run header
            old = [l for l in s.split("\n") if l.rstrip().endswith("errmsg,errflg)") and l.lstrip().startswith("&")]
            assert len(old) == 1, (scheme, len(old))
            new = old[0].replace("errmsg,errflg)", "pflx,samf_kirchhoff,errmsg,errflg)")
            assert len(new.rstrip()) <= 72
            s = s.replace(old[0], new)
        else:  # code block before the ten_t computation
            anchor = "      ten_t = real((new_t1 - real(t1, kind=conv_wp)) / real(delt,\n"
            assert s.count(anchor) == 1, (scheme, "ten_t anchor")
            s = s.replace(anchor, "\n".join(plus) + "\n" + anchor)
    f.write_text(s)
    m = d / f"{scheme}.meta"
    s = m.read_text()
    (minus, plus), = plus_blocks(Path(str(m) + ".rej"))
    i = s.index(f"  name = {scheme}_run")
    j = s.index("[errmsg]", i)
    s = s[:j] + "\n".join(plus) + "\n" + s[j:]
    m.write_text(s)
for p in list(d.glob("*.rej")) + list(d.glob("*.orig")):
    p.unlink()
print("merged encpl 06 SAMF hunks")
