#!/usr/bin/env python3
"""check_pm.py <diffA> <stripA> <dirA> <diffB> <stripB> <dirB> : do two unified diffs carry the same + and - lines?
Per file (path after stripping, prefixed with dir), compares the multisets of added and removed lines.
Prints SAME or the per-file differences; exit 0 if same, 1 otherwise."""
import sys
from collections import Counter
from pathlib import PurePosixPath


def parse(path, strip, d):
    out = {}
    cur = None
    for l in open(path, encoding="utf-8", errors="surrogateescape").read().split("\n"):
        if l.startswith("+++ "):
            p = l[4:].split("\t")[0].strip()
            parts = PurePosixPath(p).parts[int(strip):]
            rel = str(PurePosixPath(d, *parts)) if d != "." else str(PurePosixPath(*parts))
            cur = out.setdefault(rel, [Counter(), Counter()])
        elif l.startswith("--- ") or l.startswith("diff ") or l.startswith("@@"):
            continue
        elif cur is not None and l.startswith("+"):
            cur[0][l[1:]] += 1
        elif cur is not None and l.startswith("-"):
            cur[1][l[1:]] += 1
    return out


a = parse(*sys.argv[1:4])
b = parse(*sys.argv[4:7])
bad = 0
for f in sorted(set(a) | set(b)):
    pa, ma = a.get(f, [Counter(), Counter()])
    pb, mb = b.get(f, [Counter(), Counter()])
    if pa == pb and ma == mb:
        continue
    bad += 1
    print(f"  {f}: +A-B {sum((pa - pb).values())} +B-A {sum((pb - pa).values())} "
          f"-A-B {sum((ma - mb).values())} -B-A {sum((mb - ma).values())}")
    for k in list((pa - pb) + (pb - pa))[:3]:
        print("     +", k[:100])
    for k in list((ma - mb) + (mb - ma))[:3]:
        print("     -", k[:100])
print("SAME" if not bad else f"DIFFERENT in {bad} file(s)")
sys.exit(1 if bad else 0)
