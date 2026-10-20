#!/usr/bin/env python3
"""Make harness variants of the final tree's Noah-MP LSM and glacier files.

Usage: mkvariants.py <srcdir> <outdir>
Writes <outdir>/{pristine,orig,fix,neg}/{module_sf_noahmplsm.F90,module_sf_noahmp_glacier.F90}.
  pristine: the final tree's files, unchanged
  orig:     + firing meter (records only; no computed value changes)
  fix:      orig + `isnow < -1` (NCAR/noahmp#47) in combine and combine_glacier
  neg:      orig + `isnow < 0` (the alternative floated in #47)
The meter fires where the two conditions differ: isnow_old < -1 and isnow == -1 at j == 0.
"""
import os, sys

src, out = sys.argv[1], sys.argv[2]
L = open(os.path.join(src, 'module_sf_noahmplsm.F90')).read()
G = open(os.path.join(src, 'module_sf_noahmp_glacier.F90')).read()

def once(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new)

LINE_L = '               if (isnow_old < -1) then    ! mb/km: change to isnow\n'
LINE_G = '               if (isnow_old < -1) then\n'
METER = ('               if (allocated(nm12_fire)) then\n'
         '                 if (isnow_old < -1 .and. isnow == -1) then\n'
         '                   nm12_fire(COL) = nm12_fire(COL) + 1\n'
         '                   nm12_liq(COL) = nm12_liq(COL) + snliq(j)\n'
         '                   nm12_ice(COL) = nm12_ice(COL) + snice(j)\n'
         '                   nm12_sneqv(COL) = nm12_sneqv(COL) + sneqv\n'
         '                 end if\n'
         '               end if\n')
DECL = ('  integer, allocatable, public :: nm12_fire(:)\n'
        '  real (kind=kind_phys), allocatable, public :: nm12_liq(:), nm12_ice(:), nm12_sneqv(:)\n')

# LSM: meter arrays in module_sf_noahmplsm, keyed by iloc (= the driver's column index)
Lm = once(L, '  public  :: noahmp_sflx\n', '  public  :: noahmp_sflx\n' + DECL)
Lm = once(Lm, LINE_L, METER.replace('COL', 'iloc') + LINE_L)
# glacier: meter arrays and the current column in noahmp_glacier_globals; set at noahmp_glacier entry
GDECL = DECL.replace('nm12_', 'nm12g_') + '  integer, public :: nm12g_col = 1\n'
gl_hdr = '\nmodule noahmp_glacier_globals\n'
Gm = once(G, gl_hdr, gl_hdr)
i = Gm.index(gl_hdr)
j = Gm.index('  implicit none\n', i) + len('  implicit none\n')
Gm = Gm[:j] + GDECL + Gm[j:]
Gm = once(Gm, LINE_G, METER.replace('nm12_', 'nm12g_').replace('COL', 'nm12g_col') + LINE_G)
# set the column at the first executable statement of noahmp_glacier: before its first 'call atm_glacier'
Gm = once(Gm, '   call atm_glacier', '   nm12g_col = iloc\n   call atm_glacier')

variants = {
    'pristine': (L, G),
    'orig': (Lm, Gm),
    'fix': (Lm.replace(LINE_L, '               if (isnow < -1) then    ! mb/km: change to isnow\n'),
            Gm.replace(LINE_G, '               if (isnow < -1) then\n')),
    'neg': (Lm.replace(LINE_L, '               if (isnow < 0) then    ! mb/km: change to isnow\n'),
            Gm.replace(LINE_G, '               if (isnow < 0) then\n')),
}
for v, (l, g) in variants.items():
    d = os.path.join(out, v)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'module_sf_noahmplsm.F90'), 'w').write(l)
    open(os.path.join(d, 'module_sf_noahmp_glacier.F90'), 'w').write(g)
    print(v, 'written')
