#!/usr/bin/env python3
"""Surface-component energy tables from the 'ESG kdt s v(10)' lines of a metered run.
Usage: es_table.py <out file> [dt=720]   All values W m-2 of GLOBAL area, sums over the metered steps."""
import sys
from collections import defaultdict

HV, HF = 2.5e6, 3.3358e5
fn = sys.argv[1]
dt = float(sys.argv[2]) if len(sys.argv) > 2 else 720.0
steps = defaultdict(lambda: [0.0] * 261)
for line in open(fn, errors="replace"):
    if "ESG " not in line:
        continue
    p = line[line.index("ESG "):].split()
    k, s = int(p[1]), int(p[2])
    for j, v in enumerate(p[3:13]):
        steps[k][10 * (s - 1) + j + 1] = float(v)
ks = sorted(steps)
n = len(ks)
G = [sum(steps[k][i] for k in ks) for i in range(261)]
A = G[170] / n
W = 1.0 / (A * n * dt)      # J (area-summed, step-summed) -> W m-2 global mean


def g(i):
    return G[i] * W


print(f"steps {n} ({ks[0]}..{ks[-1]})  area {A:.6e}  land {G[171]/G[170]:.4f} ice {G[172]/G[170]:.4f} "
      f"water {G[173]/G[170]:.4f}")


def land(o, name):
    # o = 0 soil, 55 glacier; field f of esb(5:59) -> G[o + f - 4]
    def L(f):
        return g(o + f - 4)
    def E(k):  # esl(k) = esb(22 + k)
        return L(22 + k)
    dH, fsa, fira, fsh, LH, pah, ssoil = L(6), L(8), L(9), L(10), L(11), L(12), L(13)
    Em, Pf, Pl = L(14), L(17), L(18)
    print(f"\n== {name}: per-call column budget (W m-2 global; land frame: liquid ref, T - 273.16 K, massless canopy)")
    print(f"  calls/col-steps weight {L(5):.4e}   dH {dH:+.6e}")
    print(f"  SW abs {fsa:+.6e}  LW net up {fira:+.6e}  SH {fsh:+.6e}  LH charged {LH:+.6e}  PAH {pah:+.6e}  "
          f"G {ssoil:+.6e}")
    print(f"  masses (kg m-2 s-1 x area): E {Em:.6e} Pfroz {Pf:.6e} Pliq {Pl:.6e} runsrf {L(15):.6e} drain {L(16):.6e} "
          f"floor {L(19):.6e}  host P {L(53):.6e} MPfroz {L(54):.6e} host-frozen(srflag) {L(57):.6e}")
    if o == 0:
        eflxb, lheat, Eic, Eig = E(14), E(24), E(22), E(23)
        B = fsa - fira - fsh - LH + pah + eflxb + lheat - HF * Pf + HF * (Eic + Eig)
        RP = E(3) + E(4) + HF * E(28)
        RE = E(5) + E(6) - E(29) - eflxb
        RS = -E(11) - E(13)
        RW = E(7) + E(8) + E(9) + E(10) - (lheat - HF * (Pf - E(28)) + HF * (Eic + Eig))
        print(f"  booked B {B:+.6e}   residual R = dH - B {dH - B:+.6e}")
        print(f"   R_P precip_heat {RP:+.3e} | R_E soil/snow column in energy() {RE:+.3e} "
              f"(phase drop -{E(16):.3e}, T->tfrz {-E(17):+.3e}, tsnosoi {E(15):+.3e}) | "
              f"R_S surface -(canhs+erreng) {RS:+.3e} (canhs {E(11):+.3e}, erreng {E(13):+.3e}) | R_W water() {RW:+.3e}")
        print(f"   in R_W: canopy melt-freeze latent {E(19):+.3e}, new snow layer {E(25):+.3e}, "
              f"remainder (moved water's sensible heat etc.) {RW - E(19) - E(25):+.3e}")
        print(f"   canopy storage frame: hcv*dtv(energy) {E(12):+.3e}, hcv*dtv(canwater) {E(20):+.3e}; "
              f"storage-frame R_S {E(12) - E(11) - E(13):+.3e}")
        print(f"   PAH clipped {E(18):+.3e}   dHs/dHl P {E(3):+.2e}/{E(4):+.2e} E {E(5):+.2e}/{E(6):+.2e} "
              f"W {E(7):+.2e}/{E(8):+.2e} T {E(9):+.2e}/{E(10):+.2e}")
        RLH = LH - lheat - HV * Em - HF * (Eic + Eig)
        print(f"  latent: charged - returned - hvap*E - hfus*E_ice = {RLH:+.6e} "
              f"(canopy charged-carried {E(21):+.3e}, of which frozen-canopy transpiration {E(30):+.3e}); "
              f"E_ice canopy {Eic:.3e} ground {Eig:.3e}")
    else:
        fg0, fg1, eflxb = E(1), E(2), E(3)
        B = fsa - fira - fsh - fg0 + eflxb - HF * Pf + HF * (Em + L(16))
        print(f"  booked B (fgev used in the solve, ice vapour, ice runoff) {B:+.6e}   residual {dH - B:+.6e}")
        print(f"  fgev in solve {fg0:+.6e} vs reported {fg1:+.6e} (diff {fg0 - fg1:+.3e}); bottom {eflxb:+.3e}")
        print(f"  latent: reported LH - hsub*E = {LH - (HV + HF) * Em:+.3e}")
    return fsa, -fira, fsh, LH, Em, Pf


ls = land(0, "Noah-MP soil")
lg = land(55, "Noah-MP glacier")

def I(f):  # ice esb(60:84) -> G[110 + f - 59]
    return g(110 + f - 59)
print("\n== sea ice (sfc_sice), per ice area, Winton heat content (liquid at -0.054 C ref)")
print(f"  calls {I(60):.4e}  dH {I(61):+.6e} = snowfall {I(63):+.3e} + clip {I(64):+.3e} + ice3lay {I(65):+.3e} "
      f"+ post {I(66):+.3e}")
print(f"  F used (sum over calls) {I(67):+.6e} = SW {I(69):+.3e} + LW {I(70):+.3e} - SH {I(71):+.3e} - LH {I(72):+.3e}"
      f"; focn {I(68):+.3e}; snowfall mass {I(75):.4e} -> -li*m {-3.34e5*I(75):+.3e}")
print(f"  ice3lay residual dH - F - focn {I(65) - I(67) - I(68):+.6e}; S2 dropped {I(79):+.3e} (n {I(84)*1/W:.0f} wtd)")
print(f"  final fluxes to atmosphere: SH {I(73):+.4e} LH {I(74):+.4e}; LW dn {I(76):+.4e} emit(final T) {I(77):+.4e}; "
      f"cell SW the ice saw {I(78):+.4e}; ice evap mass {I(80):.4e}")
def N(f):  # open water esb(85:109) -> G[135 + f - 84]
    return g(135 + f - 84)
print("\n== open water (NSST), per open-water area")
print(f"  calls {N(85):.4e}  warm-layer dH {N(86):+.4e} (dtm_1p {N(87):+.3e}, adjust/reset {N(88):+.3e}); "
      f"q_warm {N(91):+.3e}")
print(f"  NSST books: SW {N(90):+.4e}, f_nsol {N(89):+.4e} (SH {N(95):+.3e} LH {N(96):+.3e} LWup {N(93):+.3e} "
      f"LWdn {N(94):+.3e} rain {N(92):+.3e}); into ocean {N(90) - N(89):+.4e}")
print(f"  atmosphere gets: SH {N(97):+.4e} LH {N(98):+.4e} (spray SH {N(99):+.3e} LH {N(100):+.3e}); "
      f"LW emit at final tskin {N(101):+.4e}; rain mass {N(102):.4e}")
print(f"  NSST's ocean flux minus the atmosphere-side one (SW - LWnet(old T) - SH - LH): "
      f"{(N(90) - N(89)) - (N(90) + N(94) - N(93) - N(97) - N(98)):+.4e}")
print("\n== hand-off, whole globe (W m-2): atmosphere books (sfc, radiation time) vs components")
swa, lwa, sha, lha = g(161), g(162), g(165), g(166)
sws = ls[0] + lg[0] + I(69) + N(90)
lws = ls[1] + lg[1] + I(70) + (N(94) - N(93))
shs = ls[2] + lg[2] + I(73) + N(97)
lhs = HV * (ls[4] + lg[4]) + I(74) + N(98)
print(f"  SW net : atm {swa:+.6e} (adjsfcnsw {g(163):+.6e})  components {sws:+.6e}  diff {sws - swa:+.4e}")
print(f"  LW net : atm {lwa:+.6e} (adjsfcdlw {g(164):+.6e})  components {lws:+.6e}  diff {lws - lwa:+.4e}")
print(f"  SH     : atm {sha:+.6e}  components {shs:+.6e}  diff {shs - sha:+.4e}")
print(f"  LH     : atm {lha:+.6e}  components (hvap*E land) {lhs:+.6e}  diff {lhs - lha:+.4e}")
print(f"  frozen precip (prev step, MP) over land/ice/water x hfus: {HF*g(174):+.4e} {HF*g(175):+.4e} {HF*g(176):+.4e}; "
      f"surfaces received: land {HF*(ls[5]):+.4e} glacier {HF*lg[5]:+.4e} ice {HF*I(75):+.4e}")
print(f"  total precip mass (prev step) land/ice/water {g(177):.4e} {g(178):.4e} {g(179):.4e}")
if any(G[i] != 0.0 for i in range(180, 200)):
    print("\n== second-layer meters (instrument_es_sfc2.py)")
    print(f"  Noah-MP soil water() by part (dHs/dHl): canwater {g(181):+.3e}/{g(182):+.3e}  snowwater {g(183):+.3e}/"
          f"{g(184):+.3e}  NM11 return {g(185):+.3e}/{g(186):+.3e}  soilwater {g(187):+.3e}/{g(188):+.3e}  "
          f"groundwater {g(189):+.3e}/{g(190):+.3e}")
    print(f"  storage change between calls: soil {g(191):+.4e} (latent {g(192):+.4e})  glacier {g(180):+.4e}  "
          f"sea ice {g(193):+.4e}")
    print(f"  SW (component - cell atmosphere): land {g(194):+.4e} ice {g(195):+.4e} water {g(199):+.4e}")
    print(f"  LW (component - cell atmosphere): land {g(196):+.4e} ice {g(197):+.4e} water(final T) {g(198):+.4e}")
    print(f"  LH components-PBL by cell: land-only {g(154):+.4e} water-only {g(155):+.4e} mixed {g(156):+.4e} "
          f"(ice-containing {g(160):+.4e});  SH: {g(157):+.4e} {g(158):+.4e} {g(159):+.4e}")
    print(f"  sea-ice snow-ice formation (flooding) dH {I(83):+.4e}")
    gl = lambda f: g(55 + f - 4)
    ge = lambda k: gl(22 + k)
    print(f"  glacier: dH energy {ge(4):+.4e} vs ssoil+bottom {ge(5) + ge(3):+.4e} (R_E {ge(4) - ge(5) - ge(3):+.3e}); "
          f"surface residual {ge(6):+.3e}; dH water {ge(7):+.4e} vs -hfus*qsnow {-HF*ge(8):+.4e} + hfus*(E+runsub) "
          f"{HF*(gl(14) + ge(10)):+.4e} (R_W {ge(7) + HF*ge(8) - HF*(gl(14) + ge(10)):+.3e}); dH end {ge(11):+.3e}")
if any(G[i] != 0.0 for i in range(201, 207)):
    print(f"  ice cells: composite evap x rho_ice x hvap {g(201):+.5e} vs PBL dqsfc1 {g(202):+.5e}; "
          f"ice share in composite {g(203):+.5e} vs ice booked {g(204):+.5e}; "
          f"composite hflx x rho_ice x cp {g(205):+.5e} vs PBL dtsfc1 {g(206):+.5e}")
if any(G[i] != 0.0 for i in list(range(221, 237)) + [207, 208]):
    print("\n== round-2 meters (instrument_es_sfc6.py)")
    print(f"  groundwater dHs {g(189):+.5e} = aquifer exchange enthalpy (bottom-layer T) {g(221):+.5e} "
          f"+ subsurface runoff enthalpy {g(222):+.5e} + watmin moves {g(223):+.5e}; "
          f"remainder {g(189) - g(221) - g(222) - g(223):+.3e}")
    print(f"  land SW (soil): A radiation-time albedo {g(233):+.5e}  B current albedo, radiation bands {g(234):+.5e}  "
          f"C Noah-MP fsa {g(235):+.5e}  -> albedo change B-A {g(234) - g(233):+.4e}, split/cosz C-B "
          f"{g(235) - g(234):+.4e}")
    print(f"  land-only cells: A {g(231):+.5e} vs atmosphere net SW {g(232):+.5e} (A-atm {g(231) - g(232):+.3e}); "
          f"fsa {g(236):+.5e} (fsa-atm {g(236) - g(232):+.3e})")
    print(f"  host-frozen convective precipitation: hfus x mass {g(207):+.5e} (mass {g(208):.4e})")
if any(G[i] != 0.0 for i in range(237, 244)):
    CL, CPV = 4185.5, 1846.0
    print("\n== frame F evaporation/precipitation booking (encpl): kg m-2 s-1 K global")
    for nm, a, b in [("land", 237, 238), ("ice", 240, 241), ("water", 242, 243)]:
        print(f"  {nm:5s}: E(Ts-T0) {g(a):+.4e}  E(T1-T0) {g(b):+.4e}  -> Kirchhoff (c_l-cp_v)E(Ts-T0) "
              f"{(CL - CPV) * g(a):+.4e} W m-2, vapour skin->T1 cp_v E(Ts-T1) {CPV * (g(a) - g(b)):+.4e} W m-2")
    print(f"  land precipitation P(T1-T0) {g(239):+.4e} -> c_l P (T1-T0) {CL * g(239):+.4e} W m-2")
