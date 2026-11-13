"""wm_template_fix.py TEMPLATE BODY...: replace each body's Commit Queue block with the live template's, ticked; add What's Missing."""
import re, sys
tpl = open(sys.argv[1]).read()
cq = tpl[tpl.index("- [ ] This PR addresses"):tpl.index("**NOTE:**")].rstrip() + "\n"
miss = tpl[tpl.index("## What's Missing?"):tpl.index("---\n<!-- STOP")]
TICK = ["This PR addresses a relevant WM issue", "Run the full Intel+GNU RT suite", "Commit log file w/full results",
        "Verify that `test_changes.list`", "Yes. [Generative AI tool", "Fill out all sections"]
out = []
for ln in cq.split("\n"):
    if any(t in ln for t in TICK):
        ln = ln.replace("- [ ]", "- [x]", 1)
    ln = ln.replace("[Generative AI tool (insert name, if any)]", "Claude Opus 5.5 (Anthropic)")
    out.append(ln)
cq = "\n".join(out)
for p in sys.argv[2:]:
    b = open(p).read()
    head = "## Commit Queue Requirements:\n"
    i = b.index(head) + len(head); j = b.index("\n## Description:")
    b = b[:i] + cq + b[j:]
    if "## What's Missing?" not in b:
        k = b.index("---\n<!-- STOP")
        b = b[:k] + miss + b[k:]
    open(p, "w").write(b)
    print(p, "ok")
