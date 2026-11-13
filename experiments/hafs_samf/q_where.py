# q_where.py <run dir>...: dbg4 events and DBGETA columns by domain (MPI ranks 0-239 parent C96, 240-359 nest: 180 compute PEs, 2 ranks each, only even ranks print) and by hour,
# using rank 0's "fcstRUN phase 1, n_atmsteps = N" lines as the clock (dt 90 s: 40 steps per hour)
import sys, re, collections
for d in sys.argv[1:]:
    step = 0; ev = collections.Counter(); et = collections.Counter(); big = collections.Counter(); tk = collections.Counter()
    for line in open(d + "/out", errors="replace"):
        m = re.match(r"\s*(\d+):\s*(\S+)", line)
        if not m: continue
        r, tag = int(m.group(1)), m.group(2)
        if tag == "PASS:" and "fcstRUN phase 1" in line:
            step = int(re.search(r"n_atmsteps =\s*(\d+)", line).group(1)); continue
        dom = "parent" if r < 240 else ("nest" if r < 360 else "other")
        h = step // 40
        if tag == "DBGSAMF":
            f = line.split(); ev[(dom, h)] += 1
            if abs(float(f[8])) > 20: big[(dom, h)] += 1
        elif tag == "DBGETA": et[(dom, h)] += 1
        elif tag == "DBGTKE": tk[(dom, h)] += 1
    print(d.rstrip("/").split("/")[-1], "last step", step)
    for dom in ("parent", "nest", "other"):
        print(f"  {dom:6s} events/h", [ev[(dom, h)] for h in range(7)], ">20K", [big[(dom, h)] for h in range(7)],
              "eta>1.2/h", [et[(dom, h)] for h in range(7)], "capped/h", [tk[(dom, h)] for h in range(7)])
