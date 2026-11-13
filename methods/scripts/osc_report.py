#!/usr/bin/env python3
"""Per-step, per-process budget of the lowest layers for one column from instrument_wb_osc_meter.py output (OSM/OSD lines).
Usage: python3 osc_report.py <RUNDIR> [LON LAT] [KDT_FROM KDT_TO] [KD_OFFSET=700] [LAYER=1]
Physics (OSM call n = position in the SDF, see AFTER in instrument_wb_osc_meter.py): process-split changes from the cumulative
dtdt*dtp (radiation after dcyc2t3, PBL incl. surface fluxes after satmedmfvdifq, GWD), time-split changes from gt0 (deep,
shallow SAMF, Thompson, post). Dycore (OSD): pt at entry, after each acoustic (DYN) and remap pass, after fv_subgrid_z and
after the physics update. KD_OFFSET is subtracted from the dycore step (a_step is already absolute after a warm start)."""
import re
import sys
from collections import defaultdict

rd = sys.argv[1]
lon0, lat0 = (float(sys.argv[2]), float(sys.argv[3])) if len(sys.argv) > 3 else (73.262, -12.792)
k0, k1 = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 10**9)
koff = int(sys.argv[6]) if len(sys.argv) > 6 else 700
lay = int(sys.argv[7]) if len(sys.argv) > 7 else 1
lab = re.compile(r"^\s*\d+:\s*")
M = defaultdict(dict)    # kdt -> n -> values
D = defaultdict(dict)    # kdt -> tag(+nm) -> values
for line in open(f"{rd}/out", errors="replace"):
    if "OSM " not in line and "OSD " not in line:
        continue
    line = lab.sub("", line)
    f = line.split()
    try:
        if f[0] == "OSM":
            if abs(float(f[3]) - lon0) < 0.01 and abs(float(f[4]) - lat0) < 0.01:
                M[int(f[1])][int(f[2])] = [float(x) for x in f[5:67]]
        elif f[0] == "OSD":
            if abs(float(f[4]) - lon0) < 0.01 and abs(float(f[5]) - lat0) < 0.01:
                kd = int(f[3]) - koff
                tag = f[1] + (f[2] if f[1] in ("DYN", "REMAP", "PRE_DYN") else "")
                D[kd][tag] = [float(x) for x in f[6:40]]
    except (ValueError, IndexError):
        continue
L = lay - 1
iT, iq, iqc, iqr = 7 * L, 7 * L + 1, 7 * L + 2, 7 * L + 3
idT, idq = 21 + 2 * L, 22 + 2 * L
# dycore layer offsets: ps then per layer 11 values (pt, delp, delz, w, ua, va, u, v, q, qc, qr)
dT, dP, dZ, dW, dUA, dVA, dQ = (1 + 11 * L + j for j in (0, 1, 2, 3, 4, 5, 8))
steps = sorted(k for k in M if k0 <= k <= k1)
print(f"column {lon0} {lat0}, layer {lay}; K. 'ps:' process-split (rad, pbl+sfc, gwd), 'ts:' time-split; dyn = dycore pt change "
      f"in the step (FVEND - ATM_IN), sgz = fv_subgrid_z, upd = physics->dycore update (SU_UPD - SU_IN)")
h = (" kdt  T_dyc_in  dyn     sgz    | Tgrs     rad     pbl     gwd   | deep    shal    thom    post  | phys    upd   | T_out"
     "    | qgrs     dq_pbl    dq_deep   dq_shal   dq_thom   q_out    | qc_out   qr_out  ")
print(h)
for k in steps:
    m, d = M[k], D.get(k, {})
    g = lambda n, i: m[n][i] if n in m else float("nan")
    dd = lambda t, i: d[t][i] if t in d else float("nan")
    rad = g(2, idT)
    pbl = g(12, idT) - g(11, idT)
    gwd = g(14, idT) - g(13, idT)
    deep = g(17, iT) - g(16, iT)
    shal = g(18, iT) - g(17, iT)
    thom = g(21, iT) - g(20, iT)
    post = g(24, iT) - g(21, iT)
    tg = g(1, iT)
    phys = g(24, iT) - tg
    dyn = dd("FVEND", dT) - dd("ATM_IN", dT)
    sgz = dd("ATM_SGZ", dT) - dd("ATM_FVD", dT)
    upd = dd("SU_UPD", dT) - dd("SU_IN", dT)
    qg = g(1, iq)
    print(f"{k:4d} {dd('ATM_IN', dT):8.3f} {dyn:7.3f} {sgz:7.3f} | {tg:8.3f} {rad:7.3f} {pbl:7.3f} {gwd:7.3f} | {deep:7.3f} "
          f"{shal:7.3f} {thom:7.3f} {post:7.3f} | {phys:7.3f} {upd:7.3f} | {dd('SU_UPD', dT):8.3f} | {qg:8.5f} "
          f"{g(13, idq) - g(11, idq):9.2e} {g(17, iq) - g(16, iq):9.2e} {g(18, iq) - g(17, iq):9.2e} {g(21, iq) - g(20, iq):9.2e} "
          f"{g(24, iq):8.5f} | {g(24, iqc):8.2e} {g(24, iqr):8.2e}")
print("\nsurface and layer-1 structure (physics values after GFS_surface_generic_post, call 11; dycore after fv_dynamics)")
print(" kdt  tsfc    tsurf_w  tref    dt_cool  xt       xz     qss      cdq      rb      ustar  wind   evap(kin) heat(kin) "
      "hpbl    dkt1    dz_phii dz_hyd  rho_th  | delp1   delz1    w1      w2      ua1     va1")
for k in steps:
    m, d = M[k], D.get(k, {})
    v = m.get(11)
    if not v:
        continue
    fe = d.get("ATM_FVD", [float("nan")] * 34)
    print(f"{k:4d} {v[37]:7.2f} {v[39]:7.2f} {v[41]:7.2f} {v[44]:8.4f} {v[42]:8.2e} {v[43]:6.2f} {v[46]:8.5f} {v[48]:8.2e} "
          f"{v[49]:7.3f} {v[50]:6.3f} {v[51]:6.2f} {v[55]:9.2e} {v[54]:9.2e} {v[58]:7.1f} {v[59]:7.2f} {v[34]:7.2f} {v[35]:7.2f} "
          f"{v[36]:7.4f} | {fe[2]:7.2f} {fe[3]:8.2f} {fe[4]:7.3f} {fe[15]:7.3f} {fe[5]:7.2f} {fe[6]:7.2f}")
import math
print("\nsea-spray check (sfc_nst lseaspray, layer 1 at physics entry): bulk = cdq*wind*(qss-q1); spray = evap - bulk;"
      " ws10 implied by spray = alps*conlf*ws10**5.4*ru10*bb1*(qs(T1)-q1), ru10 at ws10=30")
print(" kdt  T1      q1       qs(T1)   deficit   evap      bulk      spray     ws10_impl  heat     spray_heat_pred")
for k in steps:
    v = M[k].get(11)
    if not v:
        continue
    T1, q1, p1 = v[27], v[28], v[33]
    es = 611.2 * math.exp(17.67 * (T1 - 273.15) / (T1 - 29.65))
    qs1 = 0.622 * es / (p1 - 0.378 * es)
    bb1 = 1. / (1. + 0.622 * 2.5e6 ** 2 * qs1 / (287.05 * 1004.6 * T1 * T1))
    bulk = v[48] * v[51] * (v[46] - q1)
    spray = v[55] - bulk
    c = 0.75 * 7.2e-9 * 1.026 * bb1 * (qs1 - q1)
    ws = (spray / c) ** (1 / 5.4) if c > 0 and spray > 0 else float("nan")
    print(f"{k:4d} {T1:7.2f} {q1:8.5f} {qs1:8.5f} {qs1 - q1:9.2e} {v[55]:9.2e} {bulk:9.2e} {spray:9.2e} {ws:9.2f} "
          f"{v[54]:9.3f} {-(0.6 / 0.75) * spray * 2.5e6 / 1004.6:9.3f}")
print("\ndycore passes (pt layer, K): ATM_IN DYN1 REMAP1 DYN2 REMAP2 (pt in DYN* is the dycore's internal variable) | w1 after DYN1 DYN2")
for k in steps:
    d = D.get(k, {})
    dd = lambda t, i: d[t][i] if t in d else float("nan")
    print(f"{k:4d} {dd('ATM_IN', dT):8.3f} {dd('DYN1', dT):9.4f} {dd('REMAP1', dT):9.4f} {dd('DYN2', dT):9.4f} {dd('REMAP2', dT):8.3f} | "
          f"{dd('DYN1', dW):8.3f} {dd('DYN2', dW):8.3f} | delz {dd('DYN1', dZ):8.2f} {dd('DYN2', dZ):8.2f}")
