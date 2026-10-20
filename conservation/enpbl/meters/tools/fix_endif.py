#!/usr/bin/env python3
"""one-off: drop the duplicated ENDIF after the B&B block (usage: fix_endif.py <satmedmfvdifq.F>...)"""
import sys
for p in sys.argv[1:]:
    s = open(p).read()
    a = s.index("dtend(i,k,idtend)+dspq(i,k)*delt")
    old = "          endif\n        endif\n      endif\n      endif\n"
    b = s.index(old, a)
    assert b - a < 200
    s = s[:b] + "          endif\n        endif\n      endif\n" + s[b + len(old):]
    open(p, "w").write(s)
    print("fixed", p)
