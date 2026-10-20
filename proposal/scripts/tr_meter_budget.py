#!/usr/bin/env python3
"""Passive-tracer mass budget from the TRP (physics) and PTM (dycore) meters of instrument_tr.py.
Usage: python3 tr_meter_budget.py <RUNDIR> [<RUNDIR> ...]     (TR_SNAP=0 skips the atmf snapshot check; TR_NMAX=n stops at step n)
Sums the srun-labelled 'TRP kdt m ...' and 'PTM n m ...' lines over ranks (both cumulative through step n) and prints,
per tracer, every piece as kg and as a fraction of the tracer's global mass M, the per-step statistics (mean, std,
share of positive steps, largest step) and the drift extrapolated to a year (x 365 d / run length). Closure checks:
  physics: whole - (PBL + deep + shallow) = 0;   hand-off: PTM physics change (9) - TRP whole = 0
  dycore:  M(n) - M(n-1) = fv_dynamics + subgrid + statein frame + physics + write back + fv_update_phys + gaps
  fv_dynamics = (dyn_core+tracer_2d) + Lagrangian_to_Eulerian + rest;  L2E = remap own frame + fillz + frame switch
and, unless TR_SNAP=0, the meter's M against the tracer mass in atmfHHH (q*dpres/(1-condensate)/g*area)."""
import glob
import os
import re
import sys
from collections import defaultdict

import numpy as np

G = 9.80665
NAMES = {1: "trpa (profile)", 2: "trpb (3-D IC)"}


def lines(rd, tag, nv):
    acc, cnt = defaultdict(lambda: np.zeros(nv)), defaultdict(int)
    pat = re.compile(rf"\s*\d+:\s+{tag}\s+(\d+)\s+(\d)\s+(.*)")
    for ln in open(f"{rd}/out", errors="replace"):
        m = pat.match(ln)
        if m:
            v = np.array([float(x) for x in m.group(3).split()])
            if v.size != nv:
                sys.exit(f"ABORT {tag}: {v.size} values, expected {nv}: {ln[:80]}")
            acc[(int(m.group(1)), int(m.group(2)))] += v
            cnt[(int(m.group(1)), int(m.group(2)))] += 1
    if not acc:
        sys.exit(f"ABORT: no {tag} lines in {rd}/out")
    ranks = max(cnt.values())
    keys = sorted(k for k in acc if cnt[k] == ranks)
    steps = sorted({k[0] for k in keys})
    arr = np.array([[acc[(s, m)] for m in (1, 2)] for s in steps])   # (step, tracer, value)
    return np.array(steps), arr, ranks


def stats(x, M):
    x = np.asarray(x) / M
    return f"mean {x.mean():+.2e} sd {x.std():.2e} pos {np.mean(x > 0):4.0%} max|.| {np.abs(x).max():.2e}"


def snapshot(rd, steps_per_h):
    from netCDF4 import Dataset
    A = {}
    for t in range(1, 7):
        a = np.asarray(Dataset(glob.glob(f"{rd}/INPUT/C*_grid.tile{t}.nc")[0])["area"][:], float)
        A[t] = a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]
    cond = ["clwmr", "icmr", "rwmr", "snmr", "grle"]
    out = {}
    for f in sorted(glob.glob(f"{rd}/atmf???.tile1.nc")):
        fh = int(f[-12:-9])
        s = np.zeros(2)
        for t in range(1, 7):
            d = Dataset(f"{rd}/atmf{fh:03d}.tile{t}.nc")
            dp = np.asarray(d["dpres"][:], float).squeeze() / (1.0 - sum(np.asarray(d[c][:], float).squeeze() for c in cond))
            for m, v in enumerate(("trpa", "trpb")):
                s[m] += ((np.asarray(d[v][:], float).squeeze() * dp).sum(0) / G * A[t]).sum()
        out[max(1, round(fh * steps_per_h))] = s
    return out


def run(rd):
    dt = int(re.search(r"dt_atmos\s*[:=]\s*(\d+)", open(f"{rd}/model_configure").read()).group(1))
    kp, P, rp = lines(rd, "TRP", 13)
    kd, D, rdn = lines(rd, "PTM", 15)
    nmax = int(os.environ.get("TR_NMAX", 0))      # truncate (e.g. before a crash)
    if nmax:
        P, kp, D, kd = P[kp <= nmax], kp[kp <= nmax], D[kd <= nmax], kd[kd <= nmax]
    nd = kd[-1]
    hours = nd * dt / 3600.0
    yr = 365.0 * 24.0 / hours
    print(f"\n### {rd}  (dt {dt} s; physics steps {kp[0]}-{kp[-1]} on {rp} ranks; dycore steps {kd[0]}-{nd} on {rdn} ranks;"
          f" {hours:g} h; per year = x {yr:.1f})")
    if not np.array_equal(kp, np.arange(1, kp[-1] + 1)) or not np.array_equal(kd, np.arange(1, nd + 1)):
        sys.exit("ABORT: missing steps in the meter series")
    snap = snapshot(rd, 3600.0 / dt) if os.environ.get("TR_SNAP", "1") != "0" else {}
    for m in (0, 1):
        p, d = P[:, m, :], D[:, m, :]
        Mt = d[:, 14]                                  # mass after each step's update
        M0 = d[0, 14] - (d[0, 0] + d[0, 6] + d[0, 7] + d[0, 8] + d[0, 9] + d[0, 10])   # before step 1
        M = M0
        dp_ = np.diff(np.r_[np.zeros((1, 13)), p], axis=0)    # per step
        dd = np.diff(np.r_[np.zeros((1, 15)), d], axis=0)
        dd[:, 14] = np.diff(np.r_[M0, Mt])
        print(f"\n  {NAMES[m+1]}: M = {M:.9e} kg at the start; M(end) - M(start) = {Mt[-1]-M:+.3e} kg = {(Mt[-1]-M)/M:+.3e}"
              f" -> {(Mt[-1]-M)/M*yr*100:+.2e} %/yr")
        print("  physics (kg over the run, / M, %/yr; sum|col| and sum|layer| / M)")
        for lab, b in (("whole physics", 0), ("PBL (stateout_update)", 3), ("SAMF deep", 6), ("SAMF shallow", 9)):
            t = p[-1, b]
            print(f"    {lab:24s} {t:+.4e} {t/M:+.3e} {t/M*yr*100:+.2e} %/yr | col {p[-1,b+1]/M:.2e} layer {p[-1,b+2]/M:.2e}"
                  f" | per step {stats(dp_[:, b], M)}")
        res = p[-1, 0] - p[-1, 3] - p[-1, 6] - p[-1, 9]
        print(f"    closure whole - (PBL+deep+shallow) = {res:+.3e} kg ({res/M:+.1e});  hand-off PTM(9) - TRP whole ="
              f" {d[-1,8]-p[-1,0]:+.3e} kg;  physics-frame mass / M - 1 at step 1 = {dp_[0,12]/M-1:+.2e}")
        print("  dycore (kg over the run, / M, %/yr | per step)")
        rest = d[-1, 0] - d[-1, 1] - d[-1, 3]
        frame = d[-1, 3] - d[-1, 4] - d[-1, 5]
        for lab, t, s in (("fv_dynamics", d[-1, 0], dd[:, 0]),
                          ("  dyn_core+tracer_2d", d[-1, 1], dd[:, 1]),
                          ("    tracer_2d own frame", d[-1, 2], dd[:, 2]),
                          ("    delp vs dp2 frame", d[-1, 1] - d[-1, 2], dd[:, 1] - dd[:, 2]),
                          ("  Lagrangian_to_Eulerian", d[-1, 3], dd[:, 3]),
                          ("    remap own frame", d[-1, 4], dd[:, 4]),
                          ("    fillz", d[-1, 5], dd[:, 5]),
                          ("    delp vs pe frame", frame, dd[:, 3] - dd[:, 4] - dd[:, 5]),
                          ("  rest of fv_dynamics", rest, dd[:, 0] - dd[:, 1] - dd[:, 3]),
                          ("fv_subgrid_z", d[-1, 6], dd[:, 6]),
                          ("statein frame", d[-1, 7], dd[:, 7]),
                          ("physics (update)", d[-1, 8], dd[:, 8]),
                          ("write back", d[-1, 9], dd[:, 9]),
                          ("fv_update_phys", d[-1, 10], dd[:, 10]),
                          ("gaps", d[-1, 11], dd[:, 11])):
            print(f"    {lab:26s} {t:+.4e} {t/M:+.3e} {t/M*yr*100:+.2e} %/yr | {stats(s, M)}")
        print(f"    remap sum|col| {d[-1,12]/M:.2e}, fillz sum|col| {d[-1,13]/M:.2e} (/ M, whole run)")
        clo = dd[:, 14] - (dd[:, 0] + dd[:, 6] + dd[:, 7] + dd[:, 8] + dd[:, 9] + dd[:, 10] + dd[:, 11])
        print(f"    closure per step: max |dM - pieces| = {np.abs(clo[1:]).max():.2e} kg ({np.abs(clo[1:]).max()/M:.1e})")
        dyn = d[-1, 0] + d[-1, 6] + d[-1, 7] + d[-1, 9] + d[-1, 10] + d[-1, 11]
        print(f"    dycore + hand-off (all but physics) {dyn:+.4e} {dyn/M:+.3e} {dyn/M*yr*100:+.2e} %/yr")
        if 1 in snap:
            for k, s in sorted(snap.items()):
                if k <= nd:
                    print(f"    snapshot after step {k:4d}: atmf mass / meter mass - 1 = {s[m]/Mt[k-1]-1:+.4e};"
                          f" change since step 1: atmf {s[m]/snap[1][m]-1:+.3e}, meter {Mt[k-1]/Mt[0]-1:+.3e}")


for rd in sys.argv[1:]:
    run(rd)
