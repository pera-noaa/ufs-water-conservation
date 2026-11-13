#!/usr/bin/env python3
"""Fix A' in SAMF deep: kb/jmin face of the TVD flux and the double-count subtraction both use qo/ctro (v1 or ufs/dev tree, A applied or not).
Usage: python3 apply_samf_a2_patch.py <samfdeepcnv.f | ufs_model.fd | ccpp-physics checkout>
For water and every convectively transported tracer, at the face k == kb the updraft part (eta) of flxtvd carries qo(kb)
(ctro(kb)) instead of the TVD-limited tem1, and at k == jmin the downdraft part (edto*etad) carries qo(jmin); the
double-count subtraction at kb and jmin+1 uses the same qo/ctro (which is fix A). Layer kb is then unchanged and kb+1
loses eta*qo(kb), as in dellah (aup = 0 for k <= kb) and as the shallow scheme already does with fix A. Shallow is not
touched. Every anchor must match exactly once, else nothing is written; a tree that already has A' is left unchanged."""
import re
import sys
from pathlib import Path

MARK = "! cloud-base face: "


def locate(arg):
    p = Path(arg)
    if p.is_file():
        return p
    for rel in ("FV3/ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f", "ccpp/physics/physics/CONV/SAMF/samfdeepcnv.f",
                "physics/CONV/SAMF/samfdeepcnv.f", "CONV/SAMF/samfdeepcnv.f"):
        if (p / rel).is_file():
            return p / rel
    sys.exit(f"ABORT: no samfdeepcnv.f under {arg}")


def wrap72(line):
    """Split a fixed-form statement line longer than 72 columns at a ' * ' into a continuation line."""
    if len(line) <= 72:
        return [line]
    cut = line.rfind(" * ", 0, 70)
    if cut < 10:
        sys.exit(f"ABORT: cannot wrap {line!r}")
    pad = re.match(r"     &( *)", line).group(1)
    return [line[:cut], "     &" + pad + line[cut + 1:]]


def patch_block(s, start, q):
    """Patch one TVD block whose subtraction comment starts at index start; q is qo(i,k) or ctro(i,k,n)."""
    head, tail = s[:start], s[start:]
    # the subtraction block runs from the comment to the first blank '!' line after the kb branch
    m = re.match(r"! subtract the double counting change rates at jmin\+1 & kb beforehand\n!\n"
                 r"(?P<body>(?: +if\(k == jmin\(i\)\) then\n.*?\n +endif\n +if\(k == kb\(i\)\) then\n.*?\n +endif\n))",
                 tail, re.S)
    if not m:
        sys.exit("ABORT: subtraction block not recognised")
    body = m.group("body")
    nt = body.count("tem1")
    if nt not in (0, 2):
        sys.exit(f"ABORT: expected 0 (A applied) or 2 (unpatched) tem1 in the subtraction block, found {nt}")
    if nt == 2:
        new = []
        for ln in body.split("\n"):
            new.extend(wrap72(ln.replace("tem1", q)) if "tem1" in ln else [ln])
        body = "\n".join(new)
    elif body.count(q) != 2:
        sys.exit(f"ABORT: subtraction block uses neither tem1 nor {q}")
    # insert the face correction just before the subtraction comment; indentation from the 'if(k == jmin' line
    ind = re.match(r" +", body).group(0)
    fix = (f"!\n{MARK}the updraft (downdraft) part of the flux at\n"
           f"! kb (jmin) carries {q.split('(')[0]}, as dellah does; layer kb is unchanged\n!\n"
           f"{ind}if(k == kb(i)) flxtvd(i,k) = flxtvd(i,k)\n"
           f"     &{' ' * (len(ind) - 3)}+ eta(i,k) * ({q} - tem1)\n"
           f"{ind}if(k == jmin(i)) flxtvd(i,k) = flxtvd(i,k)\n"
           f"     &{' ' * (len(ind) - 3)}- edto(i) * etad(i,k) * ({q} - tem1)\n")
    for ln in fix.split("\n"):
        if len(ln) > 72 and not ln.startswith("!"):
            sys.exit(f"ABORT: line too long: {ln!r}")
    # the '!' line that precedes the comment stays in place; the correction goes before it
    if not head.endswith("!\n"):
        sys.exit("ABORT: no '!' line before the subtraction comment")
    head = head[:-2] + fix
    return head + "!\n" + tail[:m.start("body")] + body + tail[m.end("body"):]


def main():
    path = locate(sys.argv[1])
    s = path.read_text()
    if MARK in s:
        print(f"already has A': {path}")
        return
    anchors = [m.start() for m in re.finditer(r"! subtract the double counting change rates at jmin\+1 & kb beforehand\n", s)]
    if len(anchors) != 2:
        sys.exit(f"ABORT: expected 2 subtraction blocks (water, tracers), found {len(anchors)}")
    # tracer block first so the water block's offset stays valid
    s = patch_block(s, anchors[1], "ctro(i,k,n)")
    s = patch_block(s, anchors[0], "qo(i,k)")
    if s.count(MARK) != 2:
        sys.exit("ABORT: marker count")
    path.with_suffix(path.suffix + ".preA2").write_text(path.read_text())
    path.write_text(s)
    print(f"A' applied: {path}")


if __name__ == "__main__":
    main()
