#!/usr/bin/env python3
"""Round-3 closure summary from a metered run's ESG lines (full precision). Usage: es2_check.py <out> [dt=720]"""
import sys
from collections import defaultdict
HV, HF = 2.5e6, 3.3358e5
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
st = defaultdict(lambda: [0.0] * 421)
for line in open(sys.argv[1], errors="replace"):
    if "ESG " not in line:
        continue
    p = line[line.index("ESG "):].split()
    k, s = int(p[1]), int(p[2])
    for j, v in enumerate(p[3:13]):
        st[k][10 * (s - 1) + j + 1] = float(v)
ks = sorted(st); n = len(ks)
G = [sum(st[k][i] for k in ks) for i in range(421)]
A = G[170] / n; W = 1.0 / (A * n * dt); W2 = 1.0 / (A * n)
g = lambda i: G[i] * W
q = lambda i: G[i] * W2
L = lambda f: g(f - 4)            # soil esb(5:59)
E = lambda k: L(22 + k)           # soil esl(k), k <= 30
dH, fsa, fira, fsh, LH, pah, Pf = L(6), L(8), L(9), L(10), L(11), L(12), L(17)
eflxb, lheat, Eic, Eig = E(14), E(24), E(22), E(23)
B = fsa - fira - fsh - LH + pah + eflxb + lheat - HF * Pf + HF * (Eic + Eig)
R = dH - B
bnd = g(261) + g(262) + g(263) + g(264)
evc = -(g(271) + g(272))
print(f"steps {n}")
print(f"SOIL  R = dH - B (energy fluxes only)            {R:+.6e}")
print(f"      booked water/air enthalpy at its T (soil+gw) {bnd:+.6e}  evaporated-ice content {evc:+.6e}")
print(f"      R3 = R - booked                              {R - bnd - evc:+.6e}")
print(f"        R_E (energy column, Kirchhoff)             {E(5) + E(6) - E(29) - eflxb:+.6e}")
print(f"        R_S -(canhs+erreng)                        {-E(11) - E(13):+.6e}")
print(f"        R_P precipitation segment                  {E(3) + E(4) + HF * E(28):+.6e}")
print(f"        snowwater segment dHs/dHl                  {g(183):+.6e} / {g(184):+.6e}")
print(f"        new snow layer content                     {E(25):+.6e}   PAH clipped {E(18):+.6e}")
print(f"        soilwater+gw residual after booking        {g(187) + g(189) - bnd:+.6e}")
pst = g(273) + g(274) + E(25)
print(f"        precipitation stored in snow at layer T    {pst:+.6e} (snowfall {g(273):+.3e}, rain {g(274):+.3e}, new layer {E(25):+.3e})")
print(f"      R3' = R3 - precipitation stored in snow      {R - bnd - evc - pst:+.6e}")
r3p = R - bnd - evc - pst
print(f"        canopy melt/freeze latent returned as soil heat (internal, counted by B via lheat) {E(19):+.6e}")
print(f"        hfus x ice deficit: frozen-ground (NM11 returns; B over-books) {g(275):+.6e}, snowh2o (not returned) {g(276):+.6e}")
print(f"      R_final = R3' - E19 + d65 + d66                {r3p - E(19) + g(275) + g(276):+.6e}")
print(f"GLAC  residual (exported ice sensible heat)        {g(55 + 7 - 4 + 0) - 0:+.6e}" if False else "", end="")
print(f"AQUIFER groundwater dHs {g(189):+.6e} - exchange {g(221):+.6e} - subsurface {g(222):+.6e} - watmin {g(223):+.6e}"
      f" = {g(189) - g(221) - g(222) - g(223):+.6e}; pore air (gw) {g(224):+.6e}; diff {g(189) - g(221) - g(222) - g(223) - g(224):+.3e}")
print(f"EV    booked {g(270):+.6e} applied {q(307):+.6e} diff {q(307) - g(270):+.3e}")
print(f"LW    applied {q(302):+.6e}  booked land {q(303):+.6e} ice {q(304):+.6e} water {q(305):+.6e} rad {q(306):+.6e}"
      f"  booked-rad-applied {q(303) + q(304) + q(305) - q(306) - q(302):+.3e}")
print(f"PH    host-frozen hfus*m {g(207):+.6e} applied {g(209):+.6e} diff {g(209) - g(207):+.3e}")
print(f"      land frozen received soil {HF*Pf:+.6e} (host srflag {HF*L(57):+.6e}) diff {HF*(Pf - L(57)):+.3e}")
gl = lambda f: g(55 + f - 4)
print(f"      glacier received {HF*gl(17):+.6e} host {HF*gl(57):+.6e} diff {HF*(gl(17) - gl(57)):+.3e}")
print(f"SW    land-only cells fsa {g(236):+.6e} atm {g(232):+.6e} diff {g(236) - g(232):+.3e}; soil fsa {g(235):+.6e} A {g(233):+.6e}")
I = lambda f: g(110 + f - 59)
print(f"ICE   ice3lay residual {I(65) - I(67) - I(68):+.3e}; snow-ice dH {I(83):+.3e}")
print(f"CONV  disagreement: fraction of convective column-steps {G[285]/max(G[284],1e-300):.4f}; mass T1-snow/host-rain "
      f"{g(282):.4e}, T1-rain/host-snow {g(283):.4e} of {g(281):.4e} kg m-2 s-1 -> hfus x net {HF*(g(282)-g(283)):+.4e} W m-2")
# ---------------------------------------------------------------- round 4
if any(G[i] != 0.0 for i in list(range(311, 332)) + [308]):
    print("== round 4")
    r3p = R - bnd - evc - pst
    r4 = r3p - E(19) + g(275) + g(276) - g(321) - g(322) - g(325)
    print(f"SOIL  R3' {r3p:+.6e}; EP heat {g(321):+.6e}, LW2 kept {g(322):+.6e}, AIR1 kept {g(325):+.6e}")
    print(f"      R_final4 = R3' - E19 + d65 + d66 - EP - LW2 - AIR1 = {r4:+.6e}")
    print(f"      snow-bottom outflow content (internal to soil / runoff export) {g(326):+.6e}")
    print(f"      R_final4' = R_final4 + snow-bottom outflow (only its runoff part is a boundary flux) = {r4 + g(326):+.6e}")
    print(f"      EP: target {g(323):+.6e} = PAH {L(12):+.6e} + stored {g(324):+.6e} + applied {g(321):+.6e} "
          f"(diff {g(323) - L(12) - g(324) - g(321):+.3e})")
    gres = dH_g = None
    gL = lambda f: g(55 + f - 4)
    gE = lambda k: gL(22 + k)
    Bg = gL(8) - gL(9) - gL(10) - gE(1) + gE(3) - HF * gL(17) + HF * (gL(14) + gL(16))
    Rg = gL(6) - Bg
    print(f"GLAC  R {Rg:+.6e}; reset content change (glacier flow, booked) {g(311):+.6e}; EP {g(312):+.6e}; LW2 {g(313):+.6e}")
    print(f"      R_final = R - reset - EP - LW2 = {Rg - g(311) - g(312) - g(313):+.6e}")
    print(f"      EP: target {g(315):+.6e} = stored {g(316):+.6e} + applied {g(312):+.6e} (diff {g(315) - g(316) - g(312):+.3e})")
    print(f"EV    applied {q(307):+.6e} = soil {g(270):+.6e} + glacier {g(314):+.6e} (diff {q(307) - g(270) - g(314):+.3e})")
    print(f"LW2   cells kept by land {q(308):+.6e} vs soil+glacier kept {g(322) + g(313):+.6e} (diff {q(308) - g(322) - g(313):+.3e})")
    print(f"      LW applied to lowest layer {q(302):+.6e}; booked - rad - land kept - applied {q(303) + q(304) + q(305) - q(306) - q(308) - q(302):+.3e}")
    print(f"ICE   EP heat {g(331):+.6e}; post-ice3lay dH {I(66):+.6e} (diff {I(66) - g(331):+.3e})")
