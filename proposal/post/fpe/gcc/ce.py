"""Compile (and run) condfma.c on Compiler Explorer gcc versions; report the f() loop codegen."""
import json, re, sys, urllib.request
src = open(sys.argv[1]).read()
run_src = src.replace('int\nmain (int argc, char **argv)\n{',
  'int\nmain (int argc, char **argv)\n{\n  printf ("gcc %s, cpu avx512vl=%d\\n", __VERSION__, __builtin_cpu_supports ("avx512vl"));')
assert run_src != src
def ce(cid, opts, code, execute):
    body = {"source": code, "options": {"userArguments": opts,
            "filters": {"execute": execute, "intel": False, "directives": True, "labels": True, "commentOnly": True},
            "compilerOptions": {"executorRequest": execute}, "executeParameters": {"args": [], "stdin": ""}}}
    req = urllib.request.Request(f"https://godbolt.org/api/compiler/{cid}/compile", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Accept": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=120))
for cid in sys.argv[2:]:
    for opts in ["-O3 -mavx512vl -lm", "-O3 -mavx512vl -ffp-contract=off -lm"]:
        r = ce(cid, opts.replace(" -lm", ""), src, False)
        asm = [l["text"] for l in r.get("asm", [])]
        try: i0 = next(i for i, t in enumerate(asm) if t.startswith("f:")); i1 = next(i for i, t in enumerate(asm) if t.startswith("main:"))
        except StopIteration: print(cid, opts, "no asm", r.get("stderr")); continue
        body = asm[i0:i1]
        fma = [t for t in body if re.search(r"\bvfn?m(add|sub)\d+pd", t)]
        print(f"{cid:11s} {opts:38s} fma={len(fma)} masked_fma={sum('{%k' in t for t in fma)} "
              f"blend={sum('vblendm' in t for t in body)} masked_mul={sum(('vmulpd' in t) and ('{%k' in t) for t in body)}")
        if opts.startswith("-O3 -mavx512vl -lm"):
            for t in fma[:2] + [t for t in body if 'vblendm' in t][:1]: print("      ", t.strip())
        e = ce(cid, opts, run_src, True)
        er = e.get("execResult", e)
        out = "".join(x["text"] + "\n" for x in er.get("stdout", [])).strip().replace("\n", " / ")
        print(f"      run: code={er.get('code')} {out} {''.join(x['text'] for x in er.get('stderr', []))[:200]}")
