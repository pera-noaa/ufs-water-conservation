# tketrace4.py <out> <rank> <ii> : TKE (tracer 8, level 21) per step, paired by print order, not by DBGCOL clock.
# Per rank and step the order is DBGTKP (PBL) -> DBGTKI (before convection) -> DBGTKM (end of physics, carries kdt).
import sys, re
out, rank, ii = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
pat = re.compile(r"^\s*(\d+):\s*(DBGTK[PIM])\s+(.*)$")
nan = float("nan"); pend = {}; rows = []
with open(out, errors="replace") as f:
    for line in f:
        m = pat.match(line)
        if not m or int(m.group(1)) != rank: continue
        tag, r = m.group(2), m.group(3).split()
        if tag == "DBGTKP" and int(r[0]) == ii and int(r[1]) == 21: pend.update(pin=float(r[3]), pout=float(r[5]))
        elif tag == "DBGTKI" and int(r[0]) == ii: pend["i3"] = float(r[4])
        elif tag == "DBGTKM" and int(r[1]) == ii:
            rows.append((int(r[0]), pend.get("pin", nan), pend.get("pout", nan), pend.get("i3", nan), float(r[5]))); pend = {}
print(f"rank {rank} ii {ii}, level 21; nan = stage not printed")
print(f"{'kdt':>5} {'PBL in':>8} {'PBL out':>8} {'pre-conv':>8} {'end phys':>8} | {'GWD..I3':>8} {'conv+MP':>8} {'dycore':>8}")
prev = (None, nan)
for k, pin, pout, i3, mp in rows:
    dyc = pin - prev[1] if prev[0] == k - 1 else nan
    print(f"{k:5d} {pin:8.2f} {pout:8.2f} {i3:8.2f} {mp:8.2f} | {i3-pout:8.2f} {mp-i3:8.2f} {dyc:8.2f}")
    prev = (k, mp)
