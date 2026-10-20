import sys
rows=[]
for line in open(sys.argv[1], errors="replace"):
    if "EPC " not in line: continue
    p=line[line.index("EPC "):].split()
    v=[float(x) for x in p[3:]]; rows.append((int(p[1]),int(p[2]),v))
# drop the layerless-snow melt false positives: soil layer 1, ice and liquid unchanged, layer reset to tfrz
keep=[r for r in rows if not (r[1]==1 and r[2][3]==r[2][4] and r[2][5]==r[2][6])]
print("all",len(rows),"kept",len(keep))
import collections
c=collections.Counter((r[1], int(r[2][8])) for r in keep); print("by (layer, imelt):", c.most_common(10))
keep.sort(key=lambda r: abs(r[2][0]), reverse=True)
for r in keep[:12]:
    print(r[0], r[1], " ".join(f"{x:+.6e}" for x in r[2]))
print("sum dH kept", sum(r[2][0] for r in keep))
