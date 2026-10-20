"""Parse wrapped 'TX step v(1:100)' records (the Fortran record wraps mid-number; continuation lines carry the rank
prefix '  0: ' only). Returns {step: [100 floats]}."""
import re
def read_tx(path, n=100):
    TX, buf, step = {}, None, None
    for line in open(path, errors='replace'):
        line = line.rstrip('\n')
        if buf is not None:
            buf += re.sub(r'^\s*\d+: ', '', line, count=1)
            toks = buf.split()
            if len(toks) >= n:
                TX[step] = [float(x) for x in toks[:n]]
                buf = None
            continue
        m = re.search(r'\bTX +(\d+) (.*)$', line)
        if m:
            step, buf = int(m.group(1)), m.group(2)
            toks = buf.split()
            if len(toks) >= n:
                TX[step] = [float(x) for x in toks[:n]]; buf = None
    return TX
