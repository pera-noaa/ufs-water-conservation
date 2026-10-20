"""Offline replay of SAMF-deep tracer/qv transport on dumped columns (trred dump_deep.py records).
Arrays are 1-based (index 0 unused) to mirror the Fortran. Port of samfdeep_trsub (patch 02/03) plus switches:
  start = 'mean' (ctro(kb), SA1 face; base code), 'donor' (patch 02: c(kb), c(jmin+1)), 'int' (use given interface
  array cto_in instead of the arithmetic mean, e.g. qv's own qo; SA1 face).
  wdry: None (moist) or per-layer dry fraction wl (patch 03); wcomp: optional per-component dry fractions (item 4)."""
import numpy as np, glob, os

NARR = ['eta', 'etad', 'xlamue', 'xlamud', 'zi', 'dl', 'delp', 'c0t', 'q', 'q1', 'qoi', 'dellaq', 'qcko', 'qrcko',
        'qcdo', 'qrcdo', 'new_q1']
HK = ['magic', 'km', 'ntr', 'ntc', 'itc', 'ntk', 'kb', 'jmin', 'ktcon', 'kbcon', 'kmax', 'kd94', 'rnpos', 'i', 'nn', 'cnt']


def read_dump(path):
    """yield dict per column"""
    b = open(path, 'rb').read()
    p = 0
    while p < len(b):
        h = np.frombuffer(b, '<i4', 16, p); p += 64
        assert h[0] == 20261017, (path, p)
        d = dict(zip(HK, (int(x) for x in h)))
        r = np.frombuffer(b, '<f8', 8, p); p += 64
        d.update(xmb=r[0], edto=r[1], xlamdet=r[2], dt2=r[3], rn=r[4])
        km, ntr, ntc = d['km'], d['ntr'], d['ntc']
        d['fscav'] = np.frombuffer(b, '<f8', ntc, p).copy(); p += 8 * ntc
        a = np.frombuffer(b, '<f8', km * len(NARR), p).reshape(len(NARR), km); p += 8 * km * len(NARR)
        for j, n in enumerate(NARR):
            d[n] = np.concatenate(([0.], a[j]))          # 1-based
        t = np.frombuffer(b, '<f8', 2 * km * ntr, p).reshape(2, ntr, km); p += 16 * km * ntr
        d['qtr'] = np.concatenate((np.zeros((ntr, 1)), t[0]), axis=1)
        d['new_qtr'] = np.concatenate((np.zeros((ntr, 1)), t[1]), axis=1)
        if ntc > 0:
            t = np.frombuffer(b, '<f8', 2 * km * ntc, p).reshape(2, ntc, km); p += 16 * km * ntc
            d['chem_pw'] = np.concatenate((np.zeros((ntc, 1)), t[0]), axis=1)
            d['wet_dep'] = np.concatenate((np.zeros((ntc, 1)), t[1]), axis=1)
        yield d


def read_all(d, maxn=None):
    out = []
    for f in sorted(glob.glob(os.path.join(d, 'deep_*.bin'))):
        for c in read_dump(f):
            out.append(c)
            if maxn and len(out) >= maxn:
                return out
    return out


GRAV = 9.80665
CQ = 1.0


def nsub_of(c, trsrc, cmax=0.5):
    kb, jmin, ktcon = c['kb'], c['jmin'], c['ktcon']
    eta, etad, edto, xmb, dt2, dl = c['eta'], c['etad'], c['edto'], c['xmb'], c['dt2'], c['dl']
    trcm = 0.0
    for k in range(1, ktcon):
        tem = 0.0
        if k >= kb: tem = eta[k]
        if k <= jmin: tem = tem - edto * etad[k]
        kk = k + 1 if tem > 0 else k
        trcm = max(trcm, abs(tem) * xmb * dt2 * GRAV / (1000.0 * dl[kk]))
    if trsrc:
        trcm = max(trcm, eta[kb] * xmb * dt2 * GRAV / (1000.0 * dl[kb]),
                   edto * etad[jmin] * xmb * dt2 * GRAV / (1000.0 * dl[jmin + 1]))
    return max(1, int(np.ceil(trcm / cmax))), trcm


def trsub(c, x, nsub, start='mean', wl=None, fsc=0.0, upd=True, cto_in=None, wup=None, wdn=None,
          return_parts=False, book_k=False):
    """one column, one tracer (moist q in x, 1-based). Returns new x, trpw. Mirrors samfdeep_trsub.
    wup/wdn (item 4): per-level dry fractions of updraft/downdraft air; then the compensating flux carries the
    dry-air balance so that the net dry flux through every face is zero."""
    km = c['km']; km1 = km - 1
    kb, jmin, ktcon, kmax = c['kb'], c['jmin'], c['ktcon'], c['kmax']
    eta, etad, edto, xlamue, xlamdet, zi, dl, xmb, dt2, c0t = (c['eta'], c['etad'], c['edto'], c['xlamue'],
                                                             c['xlamdet'], c['zi'], c['dl'], c['xmb'], c['dt2'], c['c0t'])
    trsrc = start == 'donor'
    rns = 1.0 / nsub; dts = dt2 * rns
    ctr = x.copy()
    trpw = np.zeros(km + 1)
    wc = np.ones(km + 1); wf = np.ones(km + 1)
    if wl is not None:
        wc[1:kmax + 1] = wl[1:kmax + 1]
        for k in range(1, min(kmax, km1) + 1):
            wf[k] = 0.5 * (wl[k] + wl[k + 1])
    wu = wf.copy(); wd = wf.copy(); wcm = wf.copy()
    if wup is not None:
        wu = wup.copy(); wd = wdn.copy()
        for k in range(1, km1 + 1):
            tem = (eta[k] if k >= kb else 0.0) - (edto * etad[k] if k <= jmin else 0.0)
            num = (eta[k] * wu[k] if k >= kb else 0.0) - (edto * etad[k] * wd[k] if k <= jmin else 0.0)
            wcm[k] = num / tem if abs(tem) > 0 else wf[k]
    for it in range(nsub):
        cc = np.zeros(km + 1); cto = np.zeros(km + 1); eck = np.zeros(km + 1); erk = np.zeros(km + 1)
        ecd = np.zeros(km + 1); dd = np.zeros(km + 1)
        cc[1:kmax + 1] = ctr[1:kmax + 1] / wc[1:kmax + 1]
        cto[1:kmax + 1] = cc[1:kmax + 1]
        for k in range(1, km1 + 1):
            if k <= kmax - 1:
                cto[k] = 0.5 * (cc[k] + cc[k + 1])
        if cto_in is not None:          # e.g. qv's interface values (only meaningful for the first sub-step)
            cto[1:kmax] = cto_in[1:kmax]
        if start == 'upper':            # qv's rule without the saturation term: interface k = layer k+1
            cto[1:kmax] = cc[2:kmax + 1]
        eck[kb] = cc[kb] if trsrc else cto[kb]
        erk[kb] = eck[kb]
        if upd:
            for k in range(kb + 1, min(kmax - 1, km1) + 1):
                dz = zi[k] - zi[k - 1]
                tem = CQ * 0.25 * (xlamue[k] + xlamue[k - 1]) * dz
                eck[k] = ((1.0 - tem) * eck[k - 1] + tem * (cto[k] + cto[k - 1])) / (1.0 + tem)
                erk[k] = eck[k]
                if fsc != 0.0:
                    chc = fsc * eck[k]
                    tem = chc / (1.0 + c0t[k] * dz)
                    kk = k if book_k else k - 1
                    trpw[k] += c0t[k] * dz * tem * eta[kk] * wu[kk] * rns
                    eck[k] = tem + eck[k] - chc
        ecd[jmin] = cc[jmin + 1] if trsrc else cto[jmin]
        for k in range(jmin - 1, 0, -1):
            dz = zi[k + 1] - zi[k]
            tem = CQ * 0.5 * xlamdet * dz
            ecd[k] = ((1.0 - tem) * ecd[k + 1] + tem * (cto[k] + cto[k + 1])) / (1.0 + tem)
        dp = 1000.0 * dl[1]
        dd[1] = edto * etad[1] * ecd[1] * wd[1] * GRAV / dp
        for k in range(2, km1 + 1):
            if k < ktcon:
                aup = 0.0 if k <= kb else 1.0
                adw = 0.0 if k > jmin else 1.0
                dp = 1000.0 * dl[k]
                tem1 = -eta[k] * erk[k] * wu[k]
                tem2 = -eta[k - 1] * eck[k - 1] * wu[k - 1]
                ptem1 = -etad[k] * ecd[k] * wd[k]
                ptem2 = -etad[k - 1] * ecd[k - 1] * wd[k - 1]
                dd[k] += (aup * (tem1 - tem2) - adw * edto * (ptem1 - ptem2)) * GRAV / dp
        dp = 1000.0 * dl[ktcon]
        dd[ktcon] = eta[ktcon - 1] * eck[ktcon - 1] * wu[ktcon - 1] * GRAV / dp
        ed = np.zeros(km + 1); flx = np.zeros(km + 1)
        for k in range(1, km1 + 1):
            if k <= ktcon:
                ed[k] = cc[k] - cc[k + 1]
        if cc[1] >= 0:
            ed[0] = max(0.0, 2.0 * cc[1] - cc[2]) - cc[1]
        else:
            ed[0] = min(0.0, 2.0 * cc[1] - cc[2]) - cc[1]
        for k in range(1, km1 + 1):
            if k < ktcon:
                tem = 0.0
                if k >= kb: tem = eta[k]
                if k <= jmin: tem = tem - edto * etad[k]
                if tem > 0:
                    rr = ed[k + 1] / ed[k] if abs(ed[k]) > 1e-22 else 0.0
                    ph = (rr + abs(rr)) / (1.0 + abs(rr))
                    t1 = cc[k + 1] + ph * (cto[k] - cc[k + 1])
                    flx[k] = tem * t1
                elif tem < 0:
                    rr = ed[k - 1] / ed[k] if abs(ed[k]) > 1e-22 else 0.0
                    ph = (rr + abs(rr)) / (1.0 + abs(rr))
                    t1 = cc[k] + ph * (cto[k] - cc[k])
                    flx[k] = tem * t1
                else:
                    t1 = cto[k]; flx[k] = 0.0
                if not trsrc:
                    if k == kb: flx[k] += eta[k] * (cto[k] - t1) * (wu[k] / wcm[k])
                    if k == jmin: flx[k] -= edto * etad[k] * (cto[k] - t1) * (wd[k] / wcm[k])
                flx[k] *= wcm[k]
                if k == jmin:
                    dp = 1000.0 * dl[k + 1]
                    dd[k + 1] -= edto * etad[k] * ecd[k] * wd[k] * GRAV / dp
                if k == kb:
                    dp = 1000.0 * dl[k]
                    dd[k] -= eta[k] * eck[k] * wu[k] * GRAV / dp
        for k in range(1, km1 + 1):
            if k <= ktcon:
                dp = 1000.0 * dl[k]
                dd[k] += (flx[k] - flx[k - 1]) * GRAV / dp
        for k in range(1, min(ktcon, kmax) + 1):
            ctr[k] += dd[k] * xmb * dts
    if return_parts:
        return ctr, trpw, dict(eck=eck, ecd=ecd, cto=cto, cc=cc)
    return ctr, trpw


def dellaq_replay(c):
    """qv della per unit xmb as samfdeepcnv (SA1 base), from dumped qcko/qrcko/qcdo/qrcdo/qoi/q1"""
    km = c['km']; km1 = km - 1
    kb, jmin, ktcon = c['kb'], c['jmin'], c['ktcon']
    eta, etad, edto, dl = c['eta'], c['etad'], c['edto'], c['dl']
    q1, qo, qcko, qrcko, qcdo, qrcdo = c['q1'], c['qoi'], c['qcko'], c['qrcko'], c['qcdo'], c['qrcdo']
    d = np.zeros(km + 1)
    d[1] = edto * etad[1] * GRAV / (1000.0 * dl[1]) * qrcdo[1]
    for k in range(2, km1 + 1):
        if k < ktcon:
            aup = 0.0 if k <= kb else 1.0
            adw = 0.0 if k > jmin else 1.0
            f = GRAV / (1000.0 * dl[k])
            d[k] += (aup * (-eta[k] * qrcko[k] + eta[k - 1] * qcko[k - 1])
                     - adw * edto * (-etad[k] * qrcdo[k] + etad[k - 1] * qcdo[k - 1])) * f
    d[ktcon] = eta[ktcon - 1] * GRAV / (1000.0 * dl[ktcon]) * qcko[ktcon - 1]
    qd = np.zeros(km + 2)
    for k in range(1, km1 + 1):
        if k <= ktcon: qd[k] = q1[k] - q1[k + 1]
    qd[0] = (max(0.0, 2 * q1[1] - q1[2]) - q1[1]) if q1[1] >= 0 else (min(0.0, 2 * q1[1] - q1[2]) - q1[1])
    fl = np.zeros(km + 1)
    for k in range(1, km1 + 1):
        if k < ktcon:
            tem = 0.0
            if k >= kb: tem = eta[k]
            if k <= jmin: tem -= edto * etad[k]
            if tem > 0:
                rr = qd[k + 1] / qd[k] if abs(qd[k]) > 1e-22 else 0.0
                ph = (rr + abs(rr)) / (1 + abs(rr)); t1 = q1[k + 1] + ph * (qo[k] - q1[k + 1]); fl[k] = tem * t1
            elif tem < 0:
                rr = qd[k - 1] / qd[k] if abs(qd[k]) > 1e-22 else 0.0
                ph = (rr + abs(rr)) / (1 + abs(rr)); t1 = q1[k] + ph * (qo[k] - q1[k]); fl[k] = tem * t1
            else:
                t1 = qo[k]; fl[k] = 0.0
            if k == kb: fl[k] += eta[k] * (qo[k] - t1)
            if k == jmin: fl[k] -= edto * etad[k] * (qo[k] - t1)
            if k == jmin: d[k + 1] -= edto * etad[k] * qo[k] * GRAV / (1000.0 * dl[k + 1])
            if k == kb: d[k] -= eta[k] * qo[k] * GRAV / (1000.0 * dl[k])
    for k in range(1, km1 + 1):
        if k <= ktcon:
            d[k] += (fl[k] - fl[k - 1]) * GRAV / (1000.0 * dl[k])
    return d
