#!/usr/bin/env python3
"""eml_steps.py <old out> <new out> : old meter EML col 1 at label s (lag of P(s-1)) vs new meter v2 col 1 at label
s-1 (lag of P(s-1)): count of steps, max |difference|, and the new meter's extra last step."""
import sys


def rd(f):
    d = {}
    for line in open(f, errors="ignore"):
        w = line.split()
        if w and w[0].endswith(":") and w[0][:-1].isdigit():
            w = w[1:]
        if len(w) >= 3 and w[0] == "EML":
            try:
                d[int(w[1])] = [float(x) for x in w[2:]]
            except ValueError:
                pass
    return d


o, n = rd(sys.argv[1]), rd(sys.argv[2])
pairs = [(s, o[s][0], n[s - 1][0]) for s in sorted(o) if s - 1 in n and s >= 2]
print(f"paired steps {len(pairs)}, max|old - new| {max(abs(a - b) for _, a, b in pairs):.3e}, "
      f"max|old| {max(abs(a) for _, a, _ in pairs):.3e}")
last = max(n)
print(f"new-only label {last}: {n[last][0]:+.6e} J (lag of the last step's precipitation)")
