"""Per-step FV3 'ENG Deficit (W/m**2)' (= TE lost in the fixer window; negative = dycore created TE) from run outs.
usage: eng.py <runs dir>"""
import sys, re, os
import numpy as np
R = sys.argv[1]
def eng(c):
    v = [float(l.split('=')[-1]) for l in open(os.path.join(R, c, 'out'), errors='replace') if 'ENG Deficit' in l]
    return np.array(v)
h = {c: eng(c) for c in ('h_d1', 'h_d0', 'h_d05', 'h_x1', 'h_x16', 'h_x17', 'h_nod', 'h_r0', 'h_x8')}
print('1 h cases, created TE per step (W m-2) = -ENG; steps 1..5')
for c, v in h.items():
    print(f'  {c:6s}', ' '.join(f'{-x:+.7f}' for x in v))
d = lambda a, b: -(h[a] - h[b])     # TE created in a minus in b
H0 = d('h_d1', 'h_d0'); Hx = d('h_x1', 'h_d0'); Hy = d('h_x17', 'h_d0'); Hh = d('h_d05', 'h_d0'); H16 = d('h_x16', 'h_d0')
K = d('h_d0', 'h_nod')
s = lambda v: ' '.join(f'{x:+.7f}' for x in v)
print('applied heat, unfixed      H0 = d1 - d0  :', s(H0))
print('applied heat, bit 1        Hx = x1 - d0  :', s(Hx))
print('ratio H0/Hx (D1 factor)                  :', ' '.join(f'{x:.4f}' for x in H0 / Hx))
print('linearity  (d05-d0)/(d1-d0)              :', ' '.join(f'{x:.4f}' for x in Hh / H0))
print('applied heat, bits 1+16    Hy = x17 - d0 :', s(Hy))
print('bit 16 changes estimate by Hy/Hx - 1     :', ' '.join(f'{x:+.4f}' for x in Hy / Hx - 1))
print('bit 16 alone (unfixed D1): H16/H0 - 1    :', ' '.join(f'{x:+.4f}' for x in H16 / H0 - 1))
print('damping TE change  K = d0 - nod (-KE removed + dA):', s(K))
print('step-1 closure: Hy + K (=dA if Hy = KE removed):', f'{Hy[0]+K[0]:+.7f}', ' Hx + K:', f'{Hx[0]+K[0]:+.7f}', ' H0 + K:', f'{H0[0]+K[0]:+.7f}')
print('Rayleigh net (d1 - r0)                   :', s(d('h_d1', 'h_r0')))
print('Rayleigh net with bit 8 (x8 - r0)        :', s(d('h_x8', 'h_r0')))
D = {c: eng(c) for c in ('d_d1', 'd_x1', 'd_d0')}
print('24 h cases (na_init 1), mean created TE over 120 steps, and 3-hourly blocks:')
for c, v in D.items():
    print(f'  {c:5s} n={len(v)} mean {-v.mean():+.5f}  blocks', ' '.join(f'{-x:+.3f}' for x in v.reshape(8, -1).mean(1)))
print(f'  D1 term (d1 - x1) 24 h mean {-(D["d_d1"]-D["d_x1"]).mean():+.5f}; applied unfixed (d1 - d0) {-(D["d_d1"]-D["d_d0"]).mean():+.5f};'
      f' bit-1 applied (x1 - d0) {-(D["d_x1"]-D["d_d0"]).mean():+.5f}; ratio {(D["d_d1"]-D["d_d0"]).mean()/(D["d_x1"]-D["d_d0"]).mean():.4f}')
