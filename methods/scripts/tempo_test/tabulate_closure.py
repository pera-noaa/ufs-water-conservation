import re, sys
rows={}; cur=None
for line in open(sys.argv[1]):
    m=re.match(r"(\S+) dt=\s*([\d.]+) steps=\s*(\d+) semi=\s*(\d) P=\s*(\S+) sum_res=\s*(\S+) sum_abs=\s*(\S+) mean_step=\s*(\S+) max_step=\s*(\S+) first=\s*(\S+) last=\s*(\S+) res/P=\s*(\S+)",line)
    if m:
        tag,dt,st,semi,P,sres,sabs,mean,mx,first,last,rp=m.groups()
        cur=(tag,dt,semi); rows[cur]=dict(P=float(P),sres=float(sres),mean=float(mean),mx=float(mx),rp=float(rp))
    elif "P rain" in line and cur: rows[cur]["pc"]=[float(x) for x in line.split("=")[1].split()]
cfg=[(dt,se) for dt in ("20.0","60.0") for se in "01"]
for v in ["c62699f","2856696","881614f","9adf9ef"]:
    print(f"== {v}: res/P [20s std, 20s semi, 60s std, 60s semi] | mean residual per step (kg/m2) | max |step| (kg/m2)")
    for s in ["o0","o1","o2","o3","n1","n2","n3"]:
        r=[rows[(f"{v}_{s}",dt,se)] for dt,se in cfg]
        print(f"  {s:3s} "+" ".join(f"{x['rp']:9.1e}" for x in r)+" | "+" ".join(f"{x['mean']:9.1e}" for x in r)+" | "+" ".join(f"{x['mx']:8.1e}" for x in r))
print("\nprecipitation change new - old, final commits (n3 - o3), whole run; and relative")
for v in ["c62699f","2856696","881614f","9adf9ef"]:
    out=[]
    for dt,se in cfg:
        a=dict(P=sum(rows[(f"{v}_o3",dt,se)]['pc'])); b=dict(P=sum(rows[(f"{v}_n3",dt,se)]['pc']))
        out.append(f"{b['P']-a['P']:+9.2e} ({(b['P']-a['P'])/a['P']:+8.1e})")
    print(f"  {v} " + "  ".join(out))
