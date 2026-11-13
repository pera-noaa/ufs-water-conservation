<!-- POSTED 12 Nov 2026: https://github.com/ufs-community/ccpp-physics/pull/405#issuecomment-6833781836. Reply on ufs-community/ccpp-physics#405 to rhaesung's 29 Oct concern (6504113961: per-PR merges
     break 1:1:1 and can't be guaranteed b4b with the tested combined tree) and gspetro-NOAA's 2 Nov question (6582221397:
     "Is there a reason you can't merge the combined PR into ufs/dev?"); dustinswales agreed 5 Nov (6663503528) if each PR
     is tested on its own. Both unanswered until now.
     Posting this commits us to: (1) one ccpp-physics PR per group from the package branch (--no-ff merge of the PR
     branches, gated on diff = sum of the PRs' diffs; ../POSTING.md procedure); (2) releasing package 1's push, held since
     29 Oct, once they choose the order. Each PR's description carries its own tests (#405 alone: rt_sa1 10314680). -->

@gspetro-NOAA @rhaesung No reason; let's do that. For each group I'll open one ccpp-physics PR from the package branch, which is a merge of the reviewed PR branches with nothing else on it, so `ufs/dev` gets exactly the tree the ufsatm and WM PRs test. The individual PRs stay open as the review record; GitHub marks them merged when the combined one lands. Each one's own test results are in its description.

One question on order: #403 re-implements #405, #408 and #414. If #403 is going in first, we'll check that it covers all three and close them, and package 1 isn't needed. If package 1 goes first, #403 would rebase onto it. Which do you prefer?
