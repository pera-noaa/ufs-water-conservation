import sys
from collections import defaultdict
dt=720.; HF=3.3358e5
st=defaultdict(lambda:[0.0]*421)
for line in open(sys.argv[1],errors="replace"):
    if "ESG " not in line: continue
    p=line[line.index("ESG "):].split(); k,s=int(p[1]),int(p[2])
    for j,v in enumerate(p[3:13]): st[k][10*(s-1)+j+1]=float(v)
ks=sorted(st); n=len(ks); G=[sum(st[k][i] for k in ks) for i in range(421)]
A=G[170]/n; W=1/(A*n*dt); g=lambda i:G[i]*W
gL=lambda f:g(55+f-4); gE=lambda k:gL(22+k)
Bg=gL(8)-gL(9)-gL(10)-gE(1)+gE(3)-HF*gL(17)+HF*(gL(14)+gL(16))
Rg=gL(6)-Bg
print("Rg",Rg,"reset",g(311),"EP",g(312),"LW2",g(313),"EV*dt",g(314),"target",g(315),"stored",g(316),"hsng",g(317))
print("Rg - reset - stored - EP - LW2 =",Rg-g(311)-g(316)-g(312)-g(313))
print(" ... + hsng (sublimated content leaves) =",Rg-g(311)-g(316)-g(312)-g(313)+g(317))
