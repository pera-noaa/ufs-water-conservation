"""Summarise DBGSA1 lines: sa1_sum.py <v0.dbg.txt> [<v1.dbg.txt>]"""
import re, sys
def load(p):
    D = {"DBGSA1DD": [], "DBGSA1SD": []}; C = {"DBGSA1DC": [], "DBGSA1SC": []}
    for l in open(p):
        m = re.search(r"(DBGSA1[DS][DC])\s+(.*)", l)
        if not m: continue
        v = [float(x) for x in m.group(2).split()]
        (D if m.group(1).endswith("D") and len(v) == 13 else C)[m.group(1)].append(v)
    return D, C
for p in sys.argv[1:]:
    D, C = load(p)
    print(f"== {p}")
    for tag, name in (("DBGSA1DD", "deep"), ("DBGSA1SD", "shallow")):
        rows = D[tag]
        if not rows: print(f"  {name}: no lines"); continue
        s = [sum(r[j] for r in rows) for j in range(13)]
        mx6 = max(r[5] for r in rows); mx7 = max(r[6] for r in rows)
        n = s[0]; R, P, absdiff, rain, absR = s[1], s[2], s[3], s[4], s[10]
        print(f"  {name}: {int(n)} column-steps with rain ({len(rows)} lines)")
        print(f"    rain {rain:.4e} kg; created R {R:+.4e} kg = {100*R/rain:+.4f} % of rain; predicted P {P:+.4e} kg")
        print(f"    sum|R| {absR:.4e} kg ({100*absR/rain:.4f} % of rain); sum|R-P| {absdiff:.3e} kg = {absdiff/max(absR,1e-300):.2e} of sum|R|")
        print(f"    max|R-P| per column {mx6:.3e} kg/m2; max|R| {mx7:.3e} kg/m2")
        print(f"    phi(kb): =0 {int(s[7])} ({100*s[7]/n:.1f} %), (0,0.999) {int(s[8])} ({100*s[8]/n:.1f} %), >=0.999 {int(s[9])} ({100*s[9]/n:.1f} %)")
        print(f"    columns with |R| > 0.1 % of their rain: {int(s[11])} ({100*s[11]/n:.1f} %); kb term at phi=0: {s[12]:+.4e} kg ({100*s[12]/max(P,1e-300):.0f} % of P)")
    for tag in ("DBGSA1DC", "DBGSA1SC"):
        for v in C[tag][:6]:
            print(f"  {tag} kb={int(v[0])} {'jmin' if 'D' in tag[6] else 'ktcon'}={int(v[1])} phi={v[2]:.3f} q(kb)={v[3]:.5e} q(kb+1)={v[4]:.5e} qo(kb)={v[5]:.5e} tem1={v[6]:.5e} eta={v[7]:.3f} xmb={v[8]:.4e} dt={v[9]:.0f} rain={v[10]:.4e} R={v[11]:+.4e} P={v[12]:+.4e} Pkb={v[13]:+.4e}")
