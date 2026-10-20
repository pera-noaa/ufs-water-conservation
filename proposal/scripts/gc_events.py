#!/usr/bin/env python3
"""Tabulate WBGC-flagged columns (|R|>1e-8) with their gcycle changes and the Thompson WBGCT layers: gc_events.py <rundir>."""
import re
import sys

out = f"{sys.argv[1]}/out"
NM = ("lat lon slmsk fice landfrac lakefrac oceanfrac hice tisfc tsfc weasd snowd tsfco zorli slmsk_cp fice_cp dry icy "
      "wet lake frland hice_cp evap evap_w evap_l evap_i slmsk_post fice_post rain rainc s31 s32").split()
ev, A, P, S, T = [], {}, {}, {}, {}
last_t = {}
for line in open(out, errors="replace"):
    m = re.match(r"\s*(\d+):\s+(WBGC|WBGCA|WBGCP|WBGCS|WBGCT|WBGCTS)\s+(.*)", line)
    if not m:
        continue
    r, tag, rest = int(m.group(1)), m.group(2), m.group(3).split()
    if tag == "WBGCT":   # printed inside Thompson, before the column's WBGC line at physics_post
        last_t.setdefault(r, []).append([float(x) for x in rest])
        continue
    if tag == "WBGCTS":
        last_t[r][-1].append([float(x) for x in rest])
        continue
    k, j = int(rest[0]), int(rest[1])
    key = (k, r, j)
    if tag == "WBGC":
        R = float(rest[2])
        if abs(R) > 1e-8:
            ev.append((key, [float(x) for x in rest[2:]]))
    elif tag == "WBGCA":
        A[key] = dict(zip(NM, map(float, rest[2:])))
    elif tag == "WBGCP":
        P[key] = dict(zip(NM, map(float, rest[2:])))
    elif tag == "WBGCS":
        S.setdefault(key, []).append((rest[2], float(rest[3]), float(rest[4])))
    if tag == "WBGC" and r in last_t:
        T[(k, r)] = last_t.pop(r)
print("kdt rank col | R  E_add  P (kg/m2) | lat lon | fice prev->now | tisfc prev->now | tsfc | evap_i prev->now")
for key, (R, E, H, Pp) in ev:
    a, p = A[key], P[key]
    print(f"{key[0]:5d} {key[1]:3d} {key[2]:4d} | {R:.3e} {E:.3e} {Pp:.3e} | {a['lat']:.2f}N {a['lon']-360:.2f}E | "
          f"{p['fice']:.4f}->{a['fice']:.4f} | {p['tisfc']:.1f}->{a['tisfc']:.1f} | {a['tsfc']:.1f} | "
          f"{p['evap_i']:.2e}->{a['evap_i']:.2e}")
    for st in S.get(key, []):
        print(f"        stage {st[0]:28s} dW(gq0) {st[1]:+.4e}  dW(qgrs) {st[2]:+.4e}")
    for t in [t for t in T.get(key[:2], []) if abs(t[6] - R) < 1e-6 * max(abs(R), 1e-12)]:
        k, temp, p_, rdz, qv, dqv, clip = t[:7]
        print(f"        Thompson k={int(k)} T={temp:.1f} p={p_/100:.0f}hPa rho*dz={rdz:.2f} qv={qv:.3e} clip={clip:.3e} kg/m2")
        for sp in t[7:]:
            nm = "qv qc qi qr qs qg".split()[int(sp[1]) - 1]
            if any(abs(x) > 1e-9 for x in sp[2:]):
                print(f"          {nm}: q={sp[2]:+.3e} a={sp[3]:+.3e} b={sp[4]:+.3e} c(sed+melt)={sp[5]:+.3e} x(R1->qv)={sp[6]:+.3e}")
