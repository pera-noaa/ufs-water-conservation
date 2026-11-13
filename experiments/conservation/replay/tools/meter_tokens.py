#!/usr/bin/env python3
"""meter_tokens.py <base tree> <test tree> <changed_files.txt> <series patches dir> <meter diff|file>... : does <test tree>
carry meter code? A meter file that is not a diff (e.g. fv_etally.F90) counts as all-added.
Meter tokens = identifiers (>= 4 chars, case-folded) on the + lines of the meter diffs that occur in none of the base
tree's 60 changed files nor in the file the meter edits. For each token, count occurrences in the test tree's changed
files minus the base's. Also counts getenv calls (test hooks are env-switched). Prints hits; exit 1 if any."""
import re
import sys
from pathlib import Path

base, test, lst, pdir = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
MET = sys.argv[5:]
files = [l.strip() for l in open(lst) if l.strip()]
ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")


def text(root, rel):
    p = root / rel
    return p.read_text(errors="replace").lower() if p.exists() else ""


base_all = "\n".join(text(base, f) for f in files)
base_ids = set(ID.findall(base_all))
tokens = {}
fix_ids = set()
for d in sorted(pdir.glob("*.diff")):
    for l in open(d, errors="replace").read().split("\n"):
        if l.startswith("+") and not l.startswith("+++"):
            fix_ids.update(ID.findall(l.lower()))
for d in MET:
    tgt = None
    lines = open(d, errors="replace").read().split("\n")
    if not d.endswith(".diff"):
        lines = ["+" + l for l in lines]
    for l in lines:
        if l.startswith("+++ "):
            tgt = l[4:].split("\t")[0]
            continue
        if l.startswith("+") and not l.startswith("+++"):
            body = l[1:].split("!")[0] if not l[1:].lstrip().startswith(("c ", "C ")) else ""
            for t in ID.findall(body.lower()):
                if t not in base_ids:
                    tokens.setdefault(t, set()).add(Path(d).name)
test_all = "\n".join(text(test, f) for f in files)
hits = []
for t, src in sorted(tokens.items()):
    n = len(re.findall(r"\b%s\b" % re.escape(t), test_all)) - len(re.findall(r"\b%s\b" % re.escape(t), base_all))
    if n > 0:
        hits.append((t, n, sorted(src)))
ge = test_all.count("getenv") - base_all.count("getenv")
shared = [h for h in hits if h[0] in fix_ids]
own = [h for h in hits if h[0] not in fix_ids]
print(f"meter files: {len(MET)}; tokens new vs base: {len(tokens)}, of which also on + lines of the series "
      f"(fix variables the meters read): {sum(t in fix_ids for t in tokens)}; meter-only tokens: "
      f"{sum(t not in fix_ids for t in tokens)}")
print(f"in test tree: shared fix tokens {len(shared)}, METER-ONLY tokens {len(own)}, new getenv calls {ge}")
for t, n, src in own:
    print(f"  METER-ONLY {t}: {n}  (from {', '.join(src)[:120]})")
sys.exit(1 if own or ge else 0)
