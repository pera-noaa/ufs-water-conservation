"""D2: replicate d_sw's heat lines (one cell, 4 edges) with random winds and compare with KE differences of
compute_total_energy's D-grid cell KE. u0 = wind before damping, a = divergence-damping increment (enters via ke),
b = vorticity-damping increment (u += vt). Code: fy = u0 + a (u after ke-gradient), ub = a + b."""
import numpy as np
rng = np.random.default_rng(1)
def KE(u1, u2, v1, v2, rsin2, cosa):
    return 0.25 * rsin2 * (u1**2 + u2**2 + v1**2 + v2**2 - (u1 + u2) * (v1 + v2) * cosa)
worst = {}
for n in range(10000):
    cosa = rng.uniform(-0.5, 0.5); rsin2 = 1. / (1. - cosa**2)
    u0 = rng.normal(0, 10, 4); a = rng.normal(0, 0.5, 4); b = rng.normal(0, 0.2, 4)   # edges: u(j), u(j+1), v(i), v(i+1)
    uf = u0 + a + b
    fy = u0 + a; ub = a + b                       # code's fy/fx and ub/vb at the heat lines
    u2, du2, v2, dv2 = fy[0] + fy[1], ub[0] + ub[1], fy[2] + fy[3], ub[2] + ub[3]
    gsum = np.sum(fy * ub)
    code = -0.25 * rsin2 * (np.sum(ub**2) + 2. * gsum - cosa * (u2 * dv2 + v2 * du2 + du2 * dv2))
    # fv3tally bit 16
    uf1, uf2, vf1, vf2 = uf
    fix = -0.25 * rsin2 * (-np.sum(ub**2) + 2. * np.sum(uf * ub) - cosa * ((uf1 + uf2) * dv2 + (vf1 + vf2) * du2 - du2 * dv2))
    removed = KE(*u0, rsin2, cosa) - KE(*uf, rsin2, cosa)
    code_id = KE(*(u0 + a), rsin2, cosa) - KE(*(u0 + 2 * a + b), rsin2, cosa)   # fv3tally's reading of the code
    for k, v in (('code - KE(u0+a)+KE(u0+2a+b)', code - code_id), ('fix - removed', fix - removed)):
        worst[k] = max(worst.get(k, 0.), abs(v) / max(abs(removed), 1e-12))
    worst.setdefault('rel', []).append((code - removed) / removed if abs(removed) > 1 else np.nan)
for k in ('code - KE(u0+a)+KE(u0+2a+b)', 'fix - removed'):
    print(f'max relative |{k}| = {worst[k]:.2e}')
print('code - removed = -2*a.d term (algebra): checked numerically above; mean rel (|removed|>1):',
      f"{np.nanmean(worst['rel']):.3e}")
