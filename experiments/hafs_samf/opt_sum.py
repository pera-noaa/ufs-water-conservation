# opt_sum.py <q_stats output>: per tree: n, crashes, events (mean, range), cfl>1 total, max dT, max TKE, mean precip; A vs D identity
import sys, re, collections, statistics
T = collections.OrderedDict(); R = {}
for l in open(sys.argv[1]):
    m = re.match(r"\s*q_(\w+?)_c(\d+)\s+(\d)\s+(\d)\s+\|(.*)\|(.*)\|(.*)\|\s*(\S+)", l)
    if not m: continue
    t, v = m.group(1), int(m.group(2))
    d = [float(x) for x in m.group(5).split()]; k = [float(x) for x in m.group(6).split()]
    T.setdefault(t, []).append(dict(v=v, crash=int(m.group(4)), ev=d[0], cfl1=d[1], mx=d[4], cfl=d[5], tke=k[1], p=float(m.group(8))))
    R[(t, v)] = l.split(None, 1)[1]
print(f"{'tree':6} {'n':>3} {'crash':>5} {'ev mean':>8} {'ev range':>10} {'cfl>1':>6} {'max dT':>7} {'max CFL':>7} {'max TKE':>9} {'precip':>7}")
for t, r in T.items():
    ok = [x for x in r if not x['crash']]
    print(f"{t:6} {len(r):>3} {sum(x['crash'] for x in r):>5} {statistics.mean(x['ev'] for x in ok):8.1f} {min(x['ev'] for x in ok):>4.0f}-{max(x['ev'] for x in ok):<4.0f} {sum(x['cfl1'] for x in ok):6.0f} {max(x['mx'] for x in ok):7.1f} {max(x['cfl'] for x in ok):7.1f} {max(x['tke'] for x in ok):9.0f} {statistics.mean(x['p'] for x in ok):7.4f}  crashed {[x['v'] for x in r if x['crash']]}")
for b in ('dev', 't1a'):
    same = sum(R.get((b+'A', v)) == R.get((b+'D', v)) for (t, v) in R if t == b+'A')
    print(f"{b}A vs {b}D identical stat lines: {same} of {len(T.get(b+'A', []))}")
