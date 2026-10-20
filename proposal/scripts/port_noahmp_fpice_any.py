#!/usr/bin/env python3
"""Noah-MP opt_snf 4/5 (O, UFS diff 19): apply the microphysics' frozen fraction to grid-scale precipitation only;
convective precipitation is snow below freezing (the host's srflag rule), not the grid-scale ratio. The fresh-snow
density is blended by mass. Rain + snow = prcp is unchanged; without convective precipitation the result is
bit-for-bit unchanged. (The canopy wet-fraction change once in O is now an issue, not a fix.)
Works on any v4-style copy (module_sf_noahmplsm.F90/.F, either case, with or without opt_snf 5); aborts unless every
anchor matches once and refuses a second run.
Usage: python3 port_noahmp_fpice_any.py <module_sf_noahmplsm.F90>"""
import re
import sys
from pathlib import Path

p = Path(sys.argv[1])
s = p.read_text()
if re.search(r"\bfpcv\b", s, re.I):
    sys.exit("ABORT: already patched")


def once(pat, what):
    m = list(re.finditer(pat, s, re.I))
    if len(m) != 1:
        sys.exit(f"ABORT {what}: expected 1 match, found {len(m)}")
    return m[0]


up = "PRCP_FROZEN" in s
c = (lambda t: t.upper()) if up else (lambda t: t)

# the grid-scale block: from 'prcp_frozen = ...' through the endif that closes the opt_snf 4/5 test
m = once(r"\n([ \t]*)if *\(opt_snf *== *4[^\n]*\) *then\n([ \t]*)prcp_frozen *= *prcpsnow *\+ *prcpgrpl *\+ *prcphail\n",
         "opt_snf 4 block start")
i = m.group(2).replace("\t", "        ")
start = m.end()
e = list(re.compile(r"\n([ \t]*)endif[ \t]*\n\s*\n[ \t]*rain *= *prcp *\* *\(1\.-fpice\)", re.I).finditer(s, start))
if not e:
    sys.exit("ABORT opt_snf 4 block end: not found")
e = e[0]
q = "prcpconv + prcpshcv"
blk = (f"{i}! the microphysics fraction is for grid-scale precipitation; convective precipitation is snow below freezing\n"
       f"{i}if({q} > 0.) then\n"
       f"{i}  fpcv = 0.0\n"
       f"{i}  if(sfctmp < tfrz) fpcv = 1.0\n"
       f"{i}  if(opt_snf == 4 .and. fpcv > 0. .and. fpice > 0.) bdfall = (bdfall*fpice*prcpnonc + &\n"
       f"{i}         bdfall0*({q})) / (fpice*prcpnonc + {q})\n"
       f"{i}  fpice = fpice + (fpcv - fpice)*({q})/prcp\n"
       f"{i}end if\n")
s = s[:e.start()] + "\n" + c(blk).rstrip("\n") + s[e.start():]
s = s[:m.start(2)] + f"{i}{c('bdfall0 = bdfall')}\n" + s[m.start(2):]

# locals, next to prcp_frozen's declaration in atm
d = once(r"\n([ \t]*real *\(kind=kind_phys\)[ \t]*(?:,[^:\n]*)?::[ \t]*)prcp_frozen\b([^\n]*)\n", "prcp_frozen declaration")
s = (s[:d.end()] + f"{d.group(1)}{c('fpcv')}          !frozen fraction of convective precipitation\n"
     f"{d.group(1)}{c('bdfall0')}       !snow density before the mix [kg/m3]\n" + s[d.end():])
p.write_text(s)
print(f"patched {p}")
