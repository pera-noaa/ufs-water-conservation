# compare driver outputs: variant x vs reference noret (blocks of 6), per flag combo and block size; prints differing fields
import sys, collections
def load(p):
    d, col = {}, None
    for l in open(p):
        f = l.split()
        if f[0] == 'col': col = int(f[1]); continue
        d[(col, f[0])] = f[1:]
    return d
combos = ['none','cp','po','ca','mg','cppo','cpca','all','my','camy','allmy']
print(f"{'variant':6} {'combo':5} " + ' '.join(f'nb={n}' for n in (6,4,2,1)) + '   (differing fields vs noret nb=6)')
for v in ('noret','proto','orig'):
    for c in combos:
        ref = load(f'out/noret.{c}.6.txt'); row = []; bad = set()
        for nb in (6,4,2,1):
            x = load(f'out/{v}.{c}.{nb}.txt')
            diff = [k for k in ref if ref[k] != x.get(k)]
            row.append(len(diff)); bad |= {f'{k[1]}@{k[0]}' for k in diff}
        print(f"{v:6} {c:5} " + ' '.join(f'{n:4}' for n in row) + '   ' + ' '.join(sorted(bad))[:110])
