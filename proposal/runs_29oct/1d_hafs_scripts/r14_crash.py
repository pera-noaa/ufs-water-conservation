# r14_crash.py <run dir>... : per member: ended, FATAL signature, last atm step reached (of 240), consv_te
import sys, re
print(f"{'run':>14} {'ended':>5} {'crash':>5} {'qs':>2} {'step':>4} {'consv_te':>8}  first FATAL")
for d in sys.argv[1:]:
    end, step, fatal = 0, -1, ""
    try:
        for l in open(d + "/out", errors="replace"):
            if re.search(r"PROGRAM ufs +HAS ENDED", l): end = 1
            m = re.search(r"fcstRUN phase 2, n_atmsteps = +(\d+)", l)
            if m: step = max(step, int(m.group(1)))
    except OSError:
        print(f"{d.rstrip('/').split('/')[-1]:>14} NO OUT"); continue
    try:
        for l in open(d + "/err", errors="replace"):
            if "FATAL" in l and not fatal: fatal = re.sub(r"\s+", " ", l.strip())[:90]
    except OSError:
        fatal = "NO ERR"
    c = re.search(r"consv_te *= *([0-9.]+)", open(d + "/input.nml").read()).group(1)
    crash = int(bool(fatal) or not end)
    print(f"{d.rstrip('/').split('/')[-1]:>14} {end:>5} {crash:>5} {int('compute_qs' in fatal):>2} {step:>4} {c:>8}  {fatal}")
