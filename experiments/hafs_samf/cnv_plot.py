"""cnv_plot.py <hafs_exp dir> <out dir>: hafs_global_1nest_atm convective precipitation (cprat_ave, run mean since
start), develop vs Han's xlamue floor (F) and 2a95266 (B), 48 h members (consv_te = 1, 0.999, ...).
Both progsigma settings 0-18 h, 10 members, from the q_*_S reruns (develop with progsigma false crashes from 19.4 h).
Writes cnv_maps.png, cnv_zonal.png and cnv_summary.txt. Faded: |Welch t| <= 2.1 (two-sided 5 %, 12-18 dof)."""
import glob
import os
import sys
import numpy as np
import netCDF4
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap

H, O = sys.argv[1], sys.argv[2]
SETS = [("T", "progsigma = .true., 0–18 h", ("devP2ps_S", "devFps_S", "devBps_S"), 18),
        ("F", "progsigma = .false. (RT), 0–18 h", ("devP2_S", "devF_S", "devB_S"), 18)]
NAMES = ("develop", "xlamue floor", "2a95266")
COL = ("#2a78d6", "#eb6834", "#1baf7a")
FILES = {"glb": "sfcf0%02d.nc", "nest": "sfc.nest02.f0%02d.nc"}
INK, MUTED, GRID = "#1f1f1e", "#6b6b67", "#d9d8d4"
SEQ = ListedColormap(["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
SEQ_LEV = [0, 0.5, 1, 2, 5, 10, 20, 50, 200]
DIV = LinearSegmentedColormap.from_list("div", ["#8f1d1c", "#e34948", "#f0efec", "#3987e5", "#104281"])


def load(g, dom, hr, mem):
    cp, tp = [], []
    for m in mem:
        with netCDF4.Dataset(f"{H}/q_{g}{m}/{FILES[dom] % hr}") as d:
            cp.append(d["cprat_ave"][0].astype(np.float64).filled(np.nan) * 86400.0)
            tp.append(d["prate_ave"][0].astype(np.float64).filled(np.nan) * 86400.0)
            geo = (d["lat"][:].astype(np.float64), d["lon"][:].astype(np.float64),
                   d["land"][0].astype(np.float64).filled(np.nan))
    return np.array(cp), np.array(tp), geo


def welch_t(a, b):
    se = np.sqrt(a.var(0, ddof=1) / len(a) + b.var(0, ddof=1) / len(b))
    with np.errstate(invalid="ignore", divide="ignore"):
        return (b.mean(0) - a.mean(0)) / se, se


def wmean(x, w):
    ok = np.isfinite(x)
    return (x[ok] * w[ok]).sum() / w[ok].sum()


def geo_plot(lat, lon, dom):
    lon = np.where(lon > 180, lon - 360, lon)
    if dom == "glb":
        k = np.argsort(lon[0])
        return lat[:, k], lon[:, k], k
    return lat, lon, slice(None)


data, out = {}, []
for s, lab, groups, hr in SETS:
    mem = sorted({os.path.basename(d)[len(f"q_{groups[0]}"):] for d in glob.glob(f"{H}/q_{groups[0]}[0-9]*")}, reverse=True)
    mem = [m for m in mem if all(os.path.exists(f"{H}/q_{g}{m}/{FILES['nest'] % hr}") for g in groups)]
    assert len(mem) == 10, (s, mem)
    out.append(f"== {lab}: members consv_te = {', '.join('0.' + m if m != '1000' else '1' for m in mem)}")
    for dom in FILES:
        cps, tps = [], []
        for g in groups:
            cp, tp, geo = load(g, dom, hr, mem)
            cps.append(cp); tps.append(tp)
        lat, lon, land = geo
        w = np.cos(np.deg2rad(lat))
        data[s, dom] = (cps, geo)
        dname = "global" if dom == "glb" else "nest (0.25°, 90° × 80° around Laura)"
        out.append(f"  {dname}:")
        for i, g in enumerate(groups):
            gm = np.array([wmean(c, w) for c in cps[i]])
            gt = np.array([wmean(c, w) for c in tps[i]])
            line = (f"    {NAMES[i]:13s} convective {gm.mean():.4f} ± {gm.std(ddof=1) / np.sqrt(len(gm)):.4f} mm/day"
                    f" (members {gm.min():.4f}–{gm.max():.4f}), total {gt.mean():.4f}, convective share {gm.mean() / gt.mean():.1%}")
            if i:
                g0 = np.array([wmean(c, w) for c in cps[0]])
                t, _ = welch_t(cps[0], cps[i])
                sig = np.isfinite(t) & (np.abs(t) > 2.1)
                fin = np.isfinite(t)
                d = gm.mean() - g0.mean()
                se = np.sqrt(gm.var(ddof=1) / len(gm) + g0.var(ddof=1) / len(g0))
                line += (f"\n      minus develop: {d:+.4f} mm/day ({d / g0.mean():+.2%}), t = {d / se:+.1f};"
                         f" area with |t| > 2.1: {(w * sig).sum() / (w * fin).sum():.1%} (5 % by chance);"
                         f" rms of the mean difference {np.sqrt(wmean((cps[i].mean(0) - cps[0].mean(0)) ** 2, w)):.3f} mm/day")
            out.append(line)
        # null: split develop members in two halves, the same statistic, for the area fraction by chance with these fields
        a, b = cps[0][0::2], cps[0][1::2]
        t, _ = welch_t(a, b)
        fin = np.isfinite(t)
        out.append(f"    develop half vs half (null): area with |t| > 2.1 {(w * (np.abs(t) > 2.1) * fin).sum() / (w * fin).sum():.1%},"
                   f" rms mean difference {np.sqrt(wmean((b.mean(0) - a.mean(0)) ** 2, w)):.3f} mm/day")
open(f"{O}/cnv_summary.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))

plt.rcParams.update({"font.size": 8, "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": GRID, "font.family": "DejaVu Sans"})
_, (nlat, nlon, _) = data["T", "nest"]
nok = np.isfinite(data["T", "nest"][0][0][0])
nlon = np.where(nlon > 180, nlon - 360, nlon)
AR = {"glb": 360 / 130, "nest": np.ptp(nlon[nok]) / np.ptp(nlat[nok])}
fig = plt.figure(figsize=(13.5, 10.4), facecolor="#fcfcfb")
gs = fig.add_gridspec(5, 3, height_ratios=[1 / AR["glb"], 1 / AR["nest"], 1 / AR["glb"], 1 / AR["nest"], 0.035],
                      hspace=0.06, wspace=0.02, left=0.035, right=0.995, top=0.95, bottom=0.045)
L = 4
row = 0
for s, lab, groups, hr in SETS:
    for dom in FILES:
        cps, (lat, lon, land) = data[s, dom]
        plat, plon, k = geo_plot(lat, lon, dom)
        w = np.cos(np.deg2rad(lat))
        for j in range(3):
            ax = fig.add_subplot(gs[row, j], facecolor="#fcfcfb")
            if j == 0:
                f = cps[0].mean(0)
                im0 = ax.pcolormesh(plon, plat, f[:, k], cmap=SEQ, norm=BoundaryNorm(SEQ_LEV, SEQ.N), shading="auto",
                                    rasterized=True)
                txt = f"{wmean(f, w):.2f} mm/day"
            else:
                t, _ = welch_t(cps[0], cps[j])
                d = cps[j].mean(0) - cps[0].mean(0)
                sig = np.isfinite(t) & (np.abs(t) > 2.1)
                ax.pcolormesh(plon, plat, np.where(sig, np.nan, d)[:, k], cmap=DIV, vmin=-L, vmax=L, shading="auto",
                              alpha=0.3, rasterized=True)
                im1 = ax.pcolormesh(plon, plat, np.where(sig, d, np.nan)[:, k], cmap=DIV, vmin=-L, vmax=L,
                                    shading="auto", rasterized=True)
                txt = f"{wmean(d, w) / wmean(cps[0].mean(0), w):+.2%}"
            ax.contour(plon, plat, np.where(land == 1, 1.0, 0.0)[:, k], levels=[0.5], colors=MUTED, linewidths=0.4)
            if dom == "glb":
                ax.set_xlim(-180, 180); ax.set_ylim(-65, 65)
            else:
                ok = np.isfinite(cps[0][0])
                ax.set_xlim(plon[ok].min(), plon[ok].max()); ax.set_ylim(plat[ok].min(), plat[ok].max())
            ax.set_aspect("equal", adjustable="box")
            ax.set_xticks([]); ax.set_yticks([])
            ax.text(0.01, 0.02, txt, transform=ax.transAxes, fontsize=8.5, color=INK,
                    bbox=dict(boxstyle="square,pad=0.2", fc="#fcfcfb", ec="none", alpha=0.85))
            if row == 0:
                ax.set_title(("develop, ensemble mean", f"{NAMES[1]} − develop", f"{NAMES[2]} − develop")[j],
                             fontsize=10, loc="left")
            if j == 0:
                ax.set_ylabel(f"progsigma {lab.split('=')[1].split(',')[0].strip()}  {'global' if dom == 'glb' else 'nest'}"
                              f"\n0–{hr} h, {len(cps[0])} members", fontsize=8.5)
        row += 1
cax = fig.add_subplot(gs[4, 0])
cb = fig.colorbar(im0, cax=cax, orientation="horizontal", ticks=SEQ_LEV[:-1])
cb.ax.set_xticklabels(["0", "0.5", "1", "2", "5", "10", "20", "50"])
cb.set_label("convective precipitation, mm/day", fontsize=8)
cax = fig.add_subplot(gs[4, 1:])
fig.colorbar(im1, cax=cax, orientation="horizontal", extend="both").set_label(
    "difference, mm/day (faded: |t| < 2.1 against the member spread)", fontsize=8)
fig.suptitle("hafs_global_1nest_atm convective precipitation: develop vs the #401 fix", x=0.035, y=0.99, ha="left",
             fontsize=11, fontweight="bold")
fig.savefig(f"{O}/cnv_maps.png", dpi=120, facecolor=fig.get_facecolor())

fig, axs = plt.subplots(1, 3, figsize=(13.5, 3.6), facecolor="#fcfcfb", gridspec_kw={"width_ratios": [1.2, 1.2, 1]})
for a, (s, lab, groups, hr) in zip(axs[:2], SETS):
    cps, (lat, lon, land) = data[s, "glb"]
    la = lat[:, 0]
    z = [np.nanmean(c, axis=2) for c in cps]
    for j in (1, 2):
        d = z[j].mean(0) - z[0].mean(0)
        se = np.sqrt(z[j].var(0, ddof=1) / len(z[j]) + z[0].var(0, ddof=1) / len(z[0]))
        a.fill_between(la, d - 2 * se, d + 2 * se, color=COL[j], alpha=0.18, lw=0)
        a.plot(la, d, color=COL[j], lw=2, label=f"{NAMES[j]} − develop")
    a.axhline(0, color=MUTED, lw=0.8)
    a.set_xlim(-90, 90); a.set_xlabel("latitude"); a.set_ylabel("zonal-mean difference, mm/day")
    a.set_title(f"{lab}: zonal mean, ±2 SE bands", loc="left", fontsize=8.5)
    a.grid(color=GRID, lw=0.5); a.legend(frameon=False, fontsize=7.5)
    for sp in ("top", "right"):
        a.spines[sp].set_visible(False)
a = axs[2]
xt = []
for si, (s, lab, groups, hr) in enumerate(SETS):
    cps, (lat, lon, land) = data[s, "glb"]
    w = np.cos(np.deg2rad(lat))
    g0 = np.array([wmean(c, w) for c in cps[0]]).mean()
    for j in range(3):
        gm = 100 * (np.array([wmean(c, w) for c in cps[j]]) / g0 - 1)
        x = si * 4 + j
        a.scatter(np.full(len(gm), x) + np.linspace(-0.2, 0.2, len(gm)), gm, s=22, color=COL[j],
                  edgecolor="#fcfcfb", lw=1, zorder=3, label=NAMES[j] if si == 0 else None)
        a.plot([x - 0.3, x + 0.3], [gm.mean()] * 2, color=INK, lw=1.2, zorder=4)
    xt.append((si * 4 + 1, lab.split(",")[0] + f"\n0–{hr} h"))
a.axhline(0, color=MUTED, lw=0.8)
a.set_xticks([x for x, _ in xt], [l for _, l in xt])
a.set_xlim(-0.8, 6.8)
a.set_ylabel("global-mean convective precipitation,\n% from develop's mean")
a.set_title("each member; bar = mean", loc="left", fontsize=8.5)
a.grid(axis="y", color=GRID, lw=0.5); a.legend(frameon=False, fontsize=7.5, loc="upper left")
for sp in ("top", "right"):
    a.spines[sp].set_visible(False)
fig.tight_layout()
fig.savefig(f"{O}/cnv_zonal.png", dpi=110, facecolor=fig.get_facecolor())
print("wrote", O)
