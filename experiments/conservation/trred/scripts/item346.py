#!/usr/bin/env python3
"""Items 3, 4, 6 on dumped columns.
3: one-step TVD violations of o3 and TKE transport: base (mean, nsub=1) vs sub-stepped (mean / donor).
4: patch 03 (all fluxes at the environment dry fraction) vs per-component dry fractions (updraft 1-qcko, downdraft
   1-qrcdo, compensating flux closing the dry-air balance) for pt_ghg / pt_udry; uniform-dry and mass checks.
6: scavenged tracer (fscav>0): column mass removed vs wet_dep booked (model), and replay decomposition.
usage: item346.py <dumpdir> <cfg patched|base> [maxcols]"""
import sys, numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import samfrep as S
d, cfg = sys.argv[1], sys.argv[2]; maxn = int(sys.argv[3]) if len(sys.argv) > 3 else 500
cols = [c for c in S.read_all(d, maxn * 3) if c['rnpos']][:maxn]
c0 = cols[0]; ntr, itc, ntc, ntk = c0['ntr'], c0['itc'], c0['ntc'], c0['ntk']
print('columns', len(cols), 'ntr', ntr, 'itc', itc, 'ntc', ntc, 'ntk', ntk, 'fscav', c0['fscav'])
for n in range(ntr):
    v = c0['qtr'][n][1:20]
    print(f'  tracer {n+1}: k1..19 min {v.min():.4g} max {v.max():.4g}')
P = lambda a: f'median {np.median(a):.3g} p90 {np.percentile(a, 90):.3g} max {np.max(a):.3g}'

def tvd_viol(x0, x1, kt):
    """count cells (k<=kt) whose new value leaves [min,max] of the old 3-point stencil by > 1e-9 relative;
    return count, max relative overshoot, any negative"""
    cnt, mx = 0, 0.0
    for k in range(1, kt + 1):
        lo = min(x0[max(1, k - 1):k + 2]); hi = max(x0[max(1, k - 1):k + 2])
        sc = max(abs(hi), 1e-30)
        o = max(x1[k] - hi, lo - x1[k], 0.0) / sc
        if o > 1e-9:
            cnt += 1; mx = max(mx, o)
    return cnt, mx, bool(np.any(x1[1:kt + 1] < 0))

# item 3: time-step error and vertical oscillation of the one-step (nsub=1) update, o3 / TKE / pt_cnv for reference
def nsc(v):
    v = v[np.abs(v) > 1e-12 * np.max(np.abs(v)) + 1e-300]
    return int(np.sum(np.sign(v[1:]) != np.sign(v[:-1])))
for name, n in (('o3', 1), ('tke', ntk - 2), ('pt_cnv', 4)):
    E, SC, NEG = [], [], []
    for c in cols:
        kt = c['ktcon']; x = c['qtr'][n - 1]
        nsub, cm = S.nsub_of(c, False)
        yb = S.trsub(c, x, 1, 'mean')[0]; ys = S.trsub(c, x, nsub, 'mean')[0]; yp = S.trsub(c, x, S.nsub_of(c, True)[0], 'donor')[0]
        ib, i_s, ip = (yb - x)[1:kt + 1], (ys - x)[1:kt + 1], (yp - x)[1:kt + 1]
        E.append((cm, np.sqrt(np.mean((ib - i_s) ** 2)) / (np.sqrt(np.mean(i_s ** 2)) + 1e-300),
                  np.sqrt(np.mean((ip - i_s) ** 2)) / (np.sqrt(np.mean(i_s ** 2)) + 1e-300)))
        SC.append((nsc(ib), nsc(i_s), nsc(ip)))
        NEG.append((np.any(yb[1:kt + 1] < 0), np.any(ys[1:kt + 1] < 0), np.any(yp[1:kt + 1] < 0)))
    E = np.array(E); SC = np.array(SC); NEG = np.array(NEG)
    for lab, m in (('all', E[:, 0] >= 0), ('C>2', E[:, 0] > 2), ('C<=1', E[:, 0] <= 1)):
        if m.sum() == 0: continue
        print(f'3 {name:6s} {lab:4s} n={m.sum():4d}: rms(incr nsub=1 - incr sub-stepped)/rms(incr sub-stepped) {P(E[m,1])}; '
              f'donor vs mean (both sub-stepped) {P(E[m,2])}; sign changes of incr: base {SC[m,0].mean():.1f} sub {SC[m,1].mean():.1f} p02 {SC[m,2].mean():.1f}; '
              f'cols with negatives base/sub/p02 {NEG[m,0].mean():.3f}/{NEG[m,1].mean():.3f}/{NEG[m,2].mean():.3f}')
# item 4
chem = list(range(itc - 2, itc - 2 + ntc))
for n in chem:
    rr, mm, uu, dlt = [], [], [], []
    for c in cols:
        kt, kb, jmin = c['ktcon'], c['kb'], c['jmin']
        nsub, _ = S.nsub_of(c, True)
        wl = 1.0 - c['q']
        x = c['qtr'][n - 1]
        y3 = S.trsub(c, x, nsub, 'donor', wl=wl)[0]
        wup = np.ones(c['km'] + 1); wdn = np.ones(c['km'] + 1)
        wf = np.ones(c['km'] + 1); wf[1:-1] = 0.5 * (wl[1:-1] + wl[2:])
        wup[:] = wf; wdn[:] = wf
        wup[kb:kt] = 1.0 - c['qcko'][kb:kt]
        wdn[1:jmin + 1] = 1.0 - c['qrcdo'][1:jmin + 1]
        y4 = S.trsub(c, x, nsub, 'donor', wl=wl, wup=wup, wdn=wdn)[0]
        i3 = y3 - x; i4 = y4 - x
        rr.append(np.sqrt(np.mean((i4 - i3)[1:kt + 1] ** 2)) / (np.sqrt(np.mean(i3[1:kt + 1] ** 2)) + 1e-300))
        dp = 1000 * c['dl']
        mm.append(abs(np.sum((y4 - y3)[1:kt + 1] * dp[1:kt + 1])) / (np.sum(np.abs(i3[1:kt + 1]) * dp[1:kt + 1]) + 1e-300))
        e = c['eta'][kb:kt]
        dlt.append(np.sum(e * np.abs(wup[kb:kt] - wf[kb:kt]) / wf[kb:kt]) / np.sum(e))
        u = 1e-6 * wl
        u4 = S.trsub(c, u, nsub, 'donor', wl=wl, wup=wup, wdn=wdn)[0]
        uu.append(np.max(np.abs(u4[1:kt + 1] / wl[1:kt + 1] / 1e-6 - 1)))
    print(f'4 tracer {n}: eta-weighted |w_up-w_env|/w_env {P(dlt)}')
    print(f'4 tracer {n}: rms(incr per-component - incr patch03)/rms(incr patch03) {P(rr)}; column mass diff / gross {P(mm)}; uniform-dry max dev under per-component {max(uu):.2e}')
# item 6
for n in chem:
    j = n - (itc - 2)
    if c0['fscav'][j] == 0:
        continue
    rat, rat_rep, rat_rep_k = [], [], []
    for c in cols:
        kt = c['ktcon']; dp = 1000 * c['dl']
        x = c['qtr'][n - 1]; y = c['new_qtr'][n - 1]
        removed = -np.sum((y - x)[1:kt + 1] * dp[1:kt + 1])
        booked = np.sum(c['wet_dep'][j][1:kt + 1])
        if removed <= 0 and booked <= 0:
            continue
        rat.append(booked / removed if removed > 0 else np.inf)
        nsub, _ = S.nsub_of(c, True)
        dry = cfg == 'patched'
        st = 'donor' if (dry or nsub > 1) and cfg == 'patched' else 'mean'
        ns = nsub if st == 'donor' else 1
        yr, pw = S.trsub(c, x, ns, st, wl=(1 - c['q']) if dry else None, fsc=c['fscav'][j])
        yk, pk = S.trsub(c, x, ns, st, wl=(1 - c['q']) if dry else None, fsc=c['fscav'][j], book_k=True)
        rem_r = -np.sum((yr - x)[1:kt + 1] * dp[1:kt + 1])
        fac = c['xmb'] * c['dt2'] * S.GRAV
        rat_rep.append(np.sum(pw[c['kb'] + 1:kt]) * fac / rem_r)
        rat_rep_k.append(np.sum(pk[c['kb'] + 1:kt]) * fac / rem_r)
    rat = np.array(rat); fin = np.isfinite(rat)
    print(f'6 tracer {n} fscav {c0["fscav"][j]}: cols {len(rat)}; booked wet_dep / mass removed {P(rat[fin])}; min {rat[fin].min():.3g}; '
          f'|ratio-1|>1e-3 in {np.mean(np.abs(rat[fin]-1)>1e-3):.3f}; removed<=0 cols {np.sum(~fin)}')
    print(f'6   replay: booking as coded (eta(k-1)) / replay removed {P(np.array(rat_rep))}; booking with eta(k) (flux-form loss) {P(np.abs(np.array(rat_rep_k)-1))} (|ratio-1|)')
