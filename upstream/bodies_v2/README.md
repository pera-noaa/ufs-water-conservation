# Unposted bodies

Only bodies not yet posted are kept here. Posted text is in `../posted/`; older drafts are in `../_superseded/`.

| File | Item | Waits on |
|---|---|---|
| `14_ATM_sxs.md` | NOAA-EMC/ufsatm#1156 body with #408 (package 1) | user's go-ahead; Lisa's early-return answer on #408 |
| `15_WM_sxs.md` | ufs-community/ufs-weather-model#3408 body with #408 (package 1) | same |

The ufsatm and WM PRs cite each other: post the ufsatm PR, then the WM PR with its number, then edit the ufsatm body to
fill the WM number. Before posting, `grep -n 'TBD\|\[RT' <file>` must print only the numbers still to come.
