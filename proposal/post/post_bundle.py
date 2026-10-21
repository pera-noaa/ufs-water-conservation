# post_bundle.py [numbers.json] : render the 0a/0b/0c issue and PR bodies from ../pr_round1_descriptions.md into
# bodies/, in each repository's template order, unwrapped for GitHub; fill "#TBD" and "[RT x]" from numbers.json
# (keys below; missing keys stay "#TBD"), list what is still unfilled, and print the gh commands in posting order.
# Nothing is posted.
import json, pathlib, re, shlex, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = (HERE / "../pr_round1_descriptions.md").read_text()
TPL_WM_CM = (HERE / "wm_cm_only.md").read_text()
NUM = json.loads(pathlib.Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else {}
FORK = "pera-noaa"


def between(s, start, end=None):
    a = s.index(start)
    b = s.index(end, a + len(start)) if end else len(s)
    return s[a:b]


def by_heading(s):
    """{heading line: text under it} for '#'-headings, in order."""
    out, key = {}, None
    for l in s.split("\n"):
        if l.startswith("#"):
            key = l.strip(); out[key] = []
        elif key:
            out[key].append(l)
    return {k: "\n".join(v).strip("\n") for k, v in out.items()}


def unquote(s):
    return "\n".join(l[2:] if l.startswith("> ") else l.lstrip(">") for l in s.split("\n"))


def unwrap(s):
    out, fence = [], False
    for raw in s.split("\n"):
        l = raw.rstrip()
        if l.strip().startswith("```"):
            fence = not fence; out.append(l); continue
        if fence or not l.strip() or l.lstrip().startswith(("|", "<!--", "-->")) or l.startswith("#"):
            out.append(l); continue
        item = bool(re.match(r"\s*([-*]|\d+\.)\s", l))
        prev = out[-1] if out else ""
        if prev.strip() and not prev.lstrip().startswith(("|", "#", "```", "<!--", "-->")) and not item:
            out[-1] = prev + " " + l.strip()
        else:
            out.append(l)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def title_of(sec):
    m = re.search(r"^\*\*Title:\*\* (.+)$", sec, re.M)
    return m.group(1).strip() if m else None


# ---- shared blocks
cc = unquote(between(SRC, "> **Tests Conducted:**", "### 3.1"))
CC = dict(re.findall(r"\*\*(Tests Conducted|Documentation|Issue|Contributors):\*\* (.*?)(?=\n\n\*\*|\Z)", cc.strip(), re.S))
WM_COMMON = between(SRC, "Common to 7a–7e:", "### 7a.")
WM_CQ = between(WM_COMMON, "## Commit Queue Requirements:", "> ### Priority:").split("\n", 1)[1]
WM_Q = by_heading(unquote(between(WM_COMMON, "> ### Priority:")))


def ccpp_pr(sec_start, sec_end, track):
    sec = between(SRC, sec_start, sec_end)
    h = by_heading(sec)
    tests = CC["Tests Conducted"].replace(
        "see this track's ufs-community/ufs-weather-model#TBD ([RT 0b], [RT 0c] or [RT 1d])",
        f"see ufs-community/ufs-weather-model#TBD ([RT {track}])")
    assert f"[RT {track}]" in tests
    body = (f"## Description of Changes:\n{h['## Description of Changes:']}\n\n## Tests Conducted:\n{tests}\n\n"
            f"## Dependencies:\n{h['## Dependencies:']}\n\n## Documentation:\n{CC['Documentation'].replace('none needed', 'None needed')}\n\n"
            f"## Issue (optional):\n{CC['Issue']}\n\n## Contributors (optional):\n{CC['Contributors']}\n")
    return title_of(sec), body


def ufsatm_pr(sec_start, sec_end):
    sec = between(SRC, sec_start, sec_end)
    return sec[sec.index("## Description"):]


def wm_pr(sec_start, sec_end):
    h = by_heading(between(SRC, sec_start, sec_end))
    rtc = "### Regression Test Changes (Please commit test_changes.list):"
    parts = [
        ("## Commit Queue Requirements:", WM_CQ.strip()),
        ("## Description:", h["## Description:"]),
        ("### Commit Message:", h["### Commit Message:"]),
        ("### Priority:", WM_Q["### Priority:"]),
        ("## Git Tracking", ""),
        ("### UFSWM:", h["### UFSWM:"]),
        ("### Sub component Pull Requests:", h["### Sub component Pull Requests:"]),
        ("### UFSWM Blocking Dependencies:", WM_Q["### UFSWM Blocking Dependencies:"]),
        ("### Documentation:", WM_Q["### Documentation:"]),
        ("## Changes", ""),
        (rtc, h[rtc]),
        ("### Input data Changes:", WM_Q["### Input data Changes:"]),
        ("### Subcomponent Branch Changes", WM_Q["### Subcomponent Branch Changes"]),
        ("### Library Changes/Upgrades:", WM_Q["### Library Changes/Upgrades:"]),
    ]
    return "\n\n".join(f"{k}\n{v}" if v else k for k, v in parts) + "\n\n---\n" + TPL_WM_CM


S8 = between(SRC, "## 8. ccpp-physics issue")
S1 = between(SRC, "## 1. ufs-weather-model issue", "## 2. GFDL")

# key, repo, kind, title, head branch, base, body, the keys of its "#TBD"s in order, its [RT x] key
ITEMS = []
ITEMS.append(dict(key="SAMF_ISSUE", repo="ufs-community/ccpp-physics", kind="issue", title=title_of(S8),
                  body="@JongilHan66 @lisa-bengtsson, cc @BinLiu-NOAA\n\n" + S8[S8.index("# Description\n"):],
                  tbd=[]))
ITEMS.append(dict(key="WM_ISSUE", repo="ufs-community/ufs-weather-model", kind="issue", title=title_of(S1),
                  body=S1[S1.index("## Description"):].rsplit("---", 1)[0],
                  tbd=["WM_0b", "WM_0c"]))
for key, start, end, track, head, tbd in [
        ("PR_SAMF", "### 3.1 SAMF", "### 3.2", "0b", "pr1-samf", ["WM_0b", "WM_0b", "WM_ISSUE"]),
        ("PR_NM", "### 3.4 Noah-MP", "### 3.5", "0b", "pr1-noahmp", ["WM_0b", "WM_0b", "WM_ISSUE"]),
        ("PR_GMP", "### 3.6 GFDL MP v3", "### 3.7", "0b", "pr1-gfdlmp", ["WM_0b", "WM_0b", "WM_ISSUE"]),
        ("PR_TH", "### 3.2 Thompson", "### 3.3", "0c", "pr1-thompson", ["WM_0c", "WM_0c", "WM_ISSUE"]),
        ("PR_TP", "### 3.3 TEMPO", "### 3.4", "0c", "pr1-tempo", ["PR_TH", "WM_0c", "WM_0c", "WM_ISSUE"])]:
    t, b = ccpp_pr(start, end, track)
    ITEMS.append(dict(key=key, repo="ufs-community/ccpp-physics", kind="pr", title=t, head=head, base="ufs/dev",
                      body=b, tbd=tbd, rt=f"RT_{track}"))
ITEMS.append(dict(key="ATM_0b", repo="NOAA-EMC/ufsatm", kind="pr", head="pr1-0b", base="develop",
                  title="Round-1 conservation bug fixes, track 0b: SAMF single-precision build fix; update ccpp-physics",
                  body=ufsatm_pr("### 6a.", "### 6b."), tbd=["WM_ISSUE", "WM_0b", "PR_SAMF", "PR_NM", "PR_GMP"]))
ITEMS.append(dict(key="ATM_0c", repo="NOAA-EMC/ufsatm", kind="pr", head="pr1-0c", base="develop",
                  title="Round-1 conservation bug fixes, track 0c: update ccpp-physics (Thompson, TEMPO driver)",
                  body=ufsatm_pr("### 6b.", "### 6c."), tbd=["WM_ISSUE", "WM_0c", "PR_TH", "PR_TP"]))
ITEMS.append(dict(key="WM_0b", repo="ufs-community/ufs-weather-model", kind="pr", head="pr1-0b", base="develop",
                  title="Round-1 conservation bug fixes, track 0b (SAMF, PBL, Noah-MP, GFDL MP v3); update UFSATM",
                  body=wm_pr("### 7a.", "### 7b."),
                  tbd=["WM_ISSUE", "WM_ISSUE", "ATM_0b", "PR_SAMF", "PR_NM", "PR_GMP"], rt="RT_0b"))
ITEMS.append(dict(key="WM_0c", repo="ufs-community/ufs-weather-model", kind="pr", head="pr1-0c", base="develop",
                  title="Round-1 conservation bug fixes, track 0c (Thompson, TEMPO driver); update UFSATM",
                  body=wm_pr("### 7b.", "### 7c."),
                  tbd=["WM_ISSUE", "WM_ISSUE", "ATM_0c", "PR_TH", "PR_TP"], rt="RT_0c"))

out = HERE / "bodies"; out.mkdir(exist_ok=True)
for old in out.glob("*.md"):
    old.unlink()
unfilled = {}
for it in ITEMS:
    b = it["body"]
    n = b.count("#TBD")
    assert n == len(it["tbd"]), (it["key"], n, len(it["tbd"]))
    for k in it["tbd"]:
        b = b.replace("#TBD", f"#{NUM[k]}" if k in NUM else "#\x00TBD", 1)
    b = b.replace("#\x00TBD", "#TBD")
    miss = [k for k in it["tbd"] if k not in NUM]
    rt = it.get("rt")
    if rt:
        tag = f"[RT {rt[3:]}]"
        assert tag in b, (it["key"], tag)
        if rt in NUM:
            b = b.replace(tag, NUM[rt])
        else:
            miss.append(rt)
            if it["repo"].endswith("ufs-weather-model"):   # RT not run: do not tick the RT boxes
                b = re.sub(r"- \[x\] (Run the full Intel\+GNU RT suite|Commit log file|Verify that `test_changes.list`)",
                           r"- [ ] \1", b)
    assert "**To:**" not in b and "[RESULT" not in b
    it["path"] = out / f"{ITEMS.index(it):02d}_{it['key']}.md"
    it["path"].write_text(unwrap(b))
    unfilled[it["key"]] = sorted(set(miss))

print("posting order (nothing is posted by this script):")
for it in ITEMS:
    rel = it["path"].relative_to(HERE)
    if it["kind"] == "issue":
        cmd = f"gh issue create -R {it['repo']} --title {shlex.quote(it['title'])} --body-file {rel}"
    else:
        draft = " --draft" if it["repo"].endswith("ufs-weather-model") and it.get("rt") not in NUM else ""
        cmd = (f"gh pr create -R {it['repo']} --base {it['base']} --head {FORK}:{it['head']}{draft} "
               f"--title {shlex.quote(it['title'])} --body-file {rel}")
    state = "posted #" + str(NUM[it["key"]]) if it["key"] in NUM else cmd
    print(f"{it['key']:10} unfilled: {', '.join(unfilled[it['key']]) or '-'}\n    {state}")
