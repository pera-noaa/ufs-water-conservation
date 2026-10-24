# q_sum.py <tag> <stats file> <eta file>: one summary line from the q_stats and q_eta tables of an ensemble
import sys
tag, sf, ef = sys.argv[1:4]
L = [l.split() for l in open(sf) if l.strip() and l.split()[0].startswith("q_")]
E = [l.split() for l in open(ef) if l.strip() and l.split()[0].startswith("q_")]
n = len(L); cr = sum(int(x[2]) for x in L); fin = [x for x in L if x[1] == "1"]
deep = [int(x[4]) for x in fin] or [0]; c5 = sum(int(x[6]) for x in L)
mdt = sorted(float(x[8]) for x in fin) or [0]; mcfl = max([float(x[9]) for x in L] or [0]); pr = [float(x[-1]) for x in fin]
cols = sum(int(x[1]) for x in E); e12 = sum(int(x[2]) for x in E); t2 = sum(int(x[3]) for x in E)
neg = sum(max(int(x[4]), 0) for x in E); cap = sum(max(int(x[5]), 0) for x in E); mx = max([float(x[9]) for x in E] or [0])
m = sum(pr) / len(pr) if pr else float("nan")
print(f"{tag:11s} crash {cr}/{n} | >4K/mem {min(deep)}-{max(deep)} cfl>5 {c5} | step med {mdt[len(mdt)//2]:5.1f} max {mdt[-1]:5.1f} K cfl {mcfl:5.1f} | "
      f"eta>1.2 {e12} max {mx:6.1f} eta<=0 {neg} | tke>2 {100*t2/max(cols,1):4.1f}% capped {cap} | prate {m:.4f}")
