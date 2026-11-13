#!/usr/bin/env python3
"""mynnred offline replay of MYNN moisture_check + the theta tendency on dumped real columns.

usage: replay_mc.py <col file>...
For each column: replays moisture_check (logic transcribed from module_bl_mynn.F90) on the dumped pre-call state,
checks it reproduces the model's own outputs (thl after, Dqv..Dqs, Dth), then forms Dth the 01b way (scratch copy)
and the frame-P energy of MYNN's tendencies, cp*exner*Dth + hvap*Dqv - hfus*(Dqi+Dqs), both ways (J m-2 per step).
"""
import sys
import numpy as np

CP, XLV, XLF = 1004.6, 2.5e6, 3.3358e5


def moisture_check(kte, delt, dp, exner, qv, qc, qi, qs, th, dqv, dqc, dqi, dqs, xlvcp, xlscp):
    qv, qc, qi, qs, th = (a.copy() for a in (qv, qc, qi, qs, th))
    dqv, dqc, dqi, dqs = (a.copy() for a in (dqv, dqc, dqi, dqs))
    qvmin, qcmin, qimin = 1e-20, 0.0, 0.0
    dqv2 = 0.0
    for k in range(kte - 1, -1, -1):
        dqc2 = max(0.0, qcmin - qc[k]); dqi2 = max(0.0, qimin - qi[k]); dqs2 = max(0.0, qimin - qs[k])
        dqc[k] += dqc2 / delt; dqi[k] += dqi2 / delt; dqs[k] += dqs2 / delt
        dqv[k] -= (dqc2 + dqi2 + dqs2) / delt
        qc[k] += dqc2; qi[k] += dqi2; qs[k] += dqs2
        qv[k] = qv[k] - dqc2 - dqi2 - dqs2
        th[k] = th[k] + xlvcp / exner[k] * dqc2 + xlscp / exner[k] * (dqi2 + dqs2)
        dqv2 = max(0.0, qvmin - qv[k])
        dqv[k] += dqv2 / delt
        qv[k] += dqv2
        if k != 0:
            qv[k - 1] = qv[k - 1] - dqv2 * dp[k] / dp[k - 1]
            dqv[k - 1] = dqv[k - 1] - dqv2 * dp[k] / dp[k - 1] / delt
        qv[k] = max(qv[k], qvmin); qc[k] = max(qc[k], qcmin); qi[k] = max(qi[k], qimin); qs[k] = max(qs[k], qimin)
    if dqv2 > 1e-20:
        msk = qv > 2.0 * qvmin
        ssum = np.sum(qv[msk] * dp[msk])
        aa = dqv2 * dp[0] / max(1e-20, ssum)
        if aa < 0.5:
            dum = aa * qv[msk]
            qv[msk] -= dum
            dqv[msk] -= dum / delt
    return qv, qc, qi, qs, th, dqv, dqc, dqi, dqs


def dth_of(thl, sqc2, sqi2, th, exner, delt, flag_qi, xlvcp, xlscp):
    if flag_qi:
        return (thl + xlvcp / exner * sqc2 + xlscp / exner * sqi2 - th) / delt
    return (thl + xlvcp / exner * sqc2 - th) / delt


def rel(a, b):
    s = np.max(np.abs(b))
    return np.max(np.abs(a - b)) / s if s > 0 else np.max(np.abs(a - b))


tot = np.zeros(6)
for fn in sys.argv[1:]:
    with open(fn) as f:
        h = f.readline().split()
    kte, delt, flag_qi, ncall, xlvcp, xlscp = int(h[7]), float(h[8]), h[9] == "T", int(h[10]), float(h[11]), float(h[12])
    d = np.loadtxt(fn, comments='#')
    (exner, rho, dz, delp, th, thl0, thl1, sqv, sqc, sqi, sqs, sqv0, sqc0, sqi0, sqs0, sqv2, sqc2, sqi2, sqs2,
     dqv0, dqc0, dqi0, dqs0, dqv, dqc, dqi, dqs, dth) = d[:, 1:].T
    m = rho * dz
    # replay, unfixed (thl passed)
    qv_, qc_, qi_, qs_, th_, dqv_, dqc_, dqi_, dqs_ = moisture_check(kte, delt, delp, exner, sqv0, sqc0, sqi0, sqs0,
                                                                     thl0, dqv0, dqc0, dqi0, dqs0, xlvcp, xlscp)
    dth_u = dth_of(th_, qc_, qi_, th, exner, delt, flag_qi, xlvcp, xlscp)
    chk = [rel(th_, thl1), rel(qv_, sqv2), rel(qc_, sqc2), rel(qi_, sqi2), rel(qs_, sqs2), rel(dqv_, dqv),
           rel(dqc_, dqc), rel(dqi_, dqi), rel(dqs_, dqs), rel(dth_u, dth)]
    # 01b: scratch copy -> thl unchanged
    dth_f = dth_of(thl0, qc_, qi_, th, exner, delt, flag_qi, xlvcp, xlscp)
    # no fill at all (reference: the pre-fill tendencies)
    fc, fi, fs = np.maximum(0, -sqc0), np.maximum(0, -sqi0), np.maximum(0, -sqs0)
    E = lambda dthx: np.sum(m * (CP * exner * dthx + XLV * dqv_ - XLF * (dqi_ + dqs_))) * delt
    # frame-P energy of the fill alone: the tendency difference with/without the fill
    E_fill_u = np.sum(m * (CP * exner * (dth_u - dth_of(thl0, sqc0, sqi0, th, exner, delt, flag_qi, xlvcp, xlscp))
                           + XLV * (dqv_ - dqv0) - XLF * (dqi_ - dqi0 + dqs_ - dqs0))) * delt
    E_fill_f = np.sum(m * (CP * exner * (dth_f - dth_of(thl0, sqc0, sqi0, th, exner, delt, flag_qi, xlvcp, xlscp))
                           + XLV * (dqv_ - dqv0) - XLF * (dqi_ - dqi0 + dqs_ - dqs0))) * delt
    Lfill = np.sum(m * (XLV * fc + (XLV + XLF) * (fi + fs)))
    print(f"{fn.split('/')[-1]}: kte={kte} flag_qi={flag_qi} fill c/i/s (kg m-2) {np.sum(m*fc):.3e}/{np.sum(m*fi):.3e}/"
          f"{np.sum(m*fs):.3e}  replay max rel err {max(chk):.1e}")
    print(f"   fill energy (J m-2/step): unfixed {E_fill_u:.6e}  01b {E_fill_f:.6e}  L*fill {Lfill:.6e}  "
          f"unfixed/(L*fill) {E_fill_u/Lfill if Lfill else float('nan'):.12f}")
    tot += [np.sum(m * fc), np.sum(m * fi), np.sum(m * fs), E_fill_u, E_fill_f, Lfill]
print("TOTAL fill c/i/s %.4e %.4e %.4e  E_fill unfixed %.6e 01b %.6e  L*fill %.6e" % tuple(tot))
