#!/usr/bin/env python3
"""Per-window in-model meter report from WBM (MYNN) / WBG (GFDL MP v3) lines in RUNDIR/out (instrument_suites.py).
Sums the cumulative per-rank lines over ranks at equal kdt; window HHa-HHb = steps (HHa*3600/dt, HHb*3600/dt]. kg/m2.
Usage: meter_report.py <rundir> [...]   (WB_WINDOW, WB_END as in water_budget_by_scheme.py)"""
import os, re, sys
from collections import defaultdict
WIN, END = int(os.environ.get("WB_WINDOW", 6)), int(os.environ.get("WB_END", 24))
for rd in sys.argv[1:]:
    dt = int(re.search(r"dt_atmos:\s*(\d+)", open(f"{rd}/model_configure").read()).group(1))
    S = {"WBM": defaultdict(lambda: None), "WBG": defaultdict(lambda: None)}
    cnt = {"WBM": defaultdict(int), "WBG": defaultdict(int)}
    for ln in open(f"{rd}/out", errors="replace"):
        m = re.match(r"\s*\d+:\s*(WBM|WBG)\s+(-?\d+)\s+(.*)", ln)
        if not m:
            continue
        tag, k, vals = m.group(1), int(m.group(2)), [float(x) for x in m.group(3).split()]
        S[tag][k] = vals if S[tag][k] is None else [a + b for a, b in zip(S[tag][k], vals)]
        cnt[tag][k] += 1
    print(f"\n### {rd}  dt={dt}")
    for tag in ("WBM", "WBG"):
        if not S[tag]:
            continue
        nr = sorted(set(cnt[tag].values()))
        print(f"{tag}: steps {min(S[tag])}..{max(S[tag])}, ranks per step {nr}")
        for fh in range(WIN, END + 1, WIN):
            k1, k2 = (fh - WIN) * 3600 // dt, fh * 3600 // dt
            if k1 == 0:
                k1 = None
            a, b = (S[tag][k1] if k1 else None), S[tag].get(k2)
            if b is None or (k1 and a is None):
                print(f"  {fh-WIN:3d}-{fh:3d}: missing steps {k1},{k2}"); continue
            a = a or [0.0] * len(b)
            d = [y - x for x, y in zip(a, b)]
            ns = k2 - (k1 or 0)
            A = d[-1] / ns
            v = [x / A for x in d[:-1]]
            if tag == "WBM":
                h, E, Sf, F, pre, post, Eh = v
                print(f"  {fh-WIN:3d}-{fh:3d}: dW_host {h:+.5f} E(qfx) {E:.5f} | R_mynn=dW_host-E {h-E:+.5f} ({100*(h-E)/E:+.3f}% E) = "
                      f"surface (S-qfx) {Sf-E:+.5f} + interior (pre-S) {pre-Sf:+.5f} + moisture_check {post-pre:+.5f} + weights (host-post) {h-post:+.5f}"
                      f" | check F-qfx {F-E:+.2e} | E_host_rho-E {Eh-E:+.5f}")
            else:
                h, mfr, Praw, P, wat = v
                print(f"  {fh-WIN:3d}-{fh:3d}: dW_host {h:+.5f} P {P:.5f} | R_mp_host=dW_host+P {h+P:+.5f} ({100*(h+P)/P:+.3f}% Pls) = "
                      f"own frame (dW_mp+P_raw) {mfr+Praw:+.5f} + frame (host-mp) {h-mfr:+.5f} + rainmin (P-P_raw) {P-Praw:+.2e} | settled cloud water {wat:.2e}")
