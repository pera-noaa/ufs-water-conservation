import sys
from collections import defaultdict
HF=3.3358e5; dt=720.
st=defaultdict(lambda:[0.0]*421)
for line in open(sys.argv[1],errors="replace"):
    if "ESG " not in line: continue
    p=line[line.index("ESG "):].split(); k,s=int(p[1]),int(p[2])
    for j,v in enumerate(p[3:13]): st[k][10*(s-1)+j+1]=float(v)
ks=sorted(st); A=sum(st[k][170] for k in ks)/len(ks)
tot=0; tote=0
for k in ks:
    G=st[k]; W=1/(A*dt*len(ks)); g=lambda i:G[i]*W
    L=lambda f:g(f-4); E=lambda q:L(22+q)
    B=L(8)-L(9)-L(10)-L(11)+L(12)+E(14)+E(24)-HF*L(17)+HF*(E(22)+E(23))
    R=L(6)-B
    bnd=g(261)+g(262)+g(263)+g(264); evc=-(g(271)+g(272)); pst=g(273)+g(274)+E(25)
    r=R-bnd-evc-pst-E(19)+g(275)+g(276)-g(321)-g(322)-g(325)+g(326)
    re=E(5)+E(6)-E(29)-E(14)
    tot+=r; tote+=re
    if abs(r)>1e-12 or abs(re)>1e-12: print(k, f"r {r:+.3e} R_E {re:+.3e}")
print("total r", tot, "R_E", tote)
