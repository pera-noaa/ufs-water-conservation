# Red-team of open replies, 26 Oct 2026

Threads read 26 Oct ~22 UTC: ccpp-physics #401, #403, #405, #406 (#404, #407, WM #3404 have no comments).

## Who is arguing what, and why

| Person | Position | Why they hold it |
|---|---|---|
| Jongil Han (EMC, SAMF author; designed the TVD method, NCAR#753/#754, 2021) | #405 is wrong: the subtraction exists so `dellaq(kb)` and `dellaq(jmin+1)` stay zero, and "we confirmed moisture and tracer mass conservations" | His argument stops at layer `kb`. He checks the rule he designed (no change at or below `kb`), which holds, and assumes the flux form makes the rest conserve. Conservation and positivity were TVD's selling points in #753, so "TVD leaks water" challenges his design. GFS v17 is near operational, so any SAMF answer change costs him. On #401 he changed his mind within a day once we ran *his* proposed test and showed the result in *his* terms. |
| Lisa Bengtsson (PSL; CA scheme) | #401: which application? does it affect `progsigma = .true.` (operational, GFS v17 coupled)? asked for a convective-precipitation plot from `hafs_global_1nest_atm` with and without the fix. #403: don't silently override namelist settings; don't claim skill not shown | Guards operational and near-operational configurations and wants claims sized to the evidence. **Her 23 Oct request for a plot on #401 is unanswered (3+ days).** |
| Dom Heinzeller (climbfuji; CCPP lead, merged #754) | #406 content OK; asks that comments in this and other AI-generated PRs be rewritten to sound human, "so reviewers have confidence a person looked at the changes" | A trust problem, not a technical one. Dense, table-heavy, symbol-heavy replies make it worse, and he will see the #405 reply. |
| Ruiyu Sun (EMC) | approved #406 three times (16:17, 20:55, 21:12; no new commits) | Supportive; no action needed. |

## `reply_405_1.md`: weaknesses

1. **It argues in a frame Han didn't use.** He reasoned layer by layer; the reply answers with a column sum. Han's own step 1, carried one layer up to `kb+1`, shows the leak in two lines of his notation: the updraft term adds `eta(kb)·qcko(kb) = eta·qo(kb)`, and the TVD divergence removes `flxtvd(kb) = eta·tem1` (code: `tem2 = -eta(i,k-1)*qcko(i,k-1)`, `factor = g/dp`, d9b70feb L2405–2421). → `reply_405_2.md`.
2. **Name clash.** "`tem1 - tem2`" (updraft term) and "`tem1(kb)`" (TVD face value) are different Fortran variables with the same name. Han would read it as sloppy.
3. **Overstated:** "zero only where `phkp = 1`" — it is also zero where `qo(kb) = q1(kb+1)`.
4. **Ignores his evidence claim.** It doesn't ask *how* he confirmed conservation, or show why a global check would miss it: 0.014 mm/day globally, 0.8 % of convective rain, against 88 % / 99 % of column-steps visibly wrong.
5. **His likely next objection is unanswered:** the fix puts an unlimited `qo(kb)` on the one face, so does it break positive-definiteness (TVD's purpose)? Borrowing frequency is unchanged (97 vs 104 of about 330k deep column-steps; proposal L117).
6. **Numbers don't visibly match the PR description:** deep 0.56 % and shallow 2.12 % vs the description's 0.8 %. Combined they are 0.805 % (7.01e12 / 8.70e14 kg), so they agree, but the reply never says so (fixed in v2 by quoting 0.8 %).
7. **`-no-fma` sentence:** true but off-topic, and it invites a compiler sidebar. v2 drops the bit-identity claim; the meter agreement (4e-15) is the evidence. Details in `reply_405_1.evidence.txt` if asked.
8. **Length/tone:** 484 words, bold headers, numbered derivation, against a 6-line comment. v2 is about 360 words, in plain prose apart from the table.
9. **"Before #754" can read as "your change broke it"** to the TVD author. v2 keeps the fact but anchors it on `dellah`, which is his own exact treatment.

Still true in both versions and checked: `qcko(kb) = qo(kb)`; `dellah` uses `dv3h = heo(kb)` with `hcko(kb) = heo(kb)`; the in-model identity holds to 4e-15 kg/m² in 2.1 M column-steps, with and without FMA; PR #405 brings it to the same level.

## `reply_403_2.md`

Substance holds: a flux form conserves on any surface if its face fluxes are mass-weighted, and sigma vs z is an accuracy question. Short and plain. Risks:
- The thread has moved to Lisa's CA/cold-pool points. A reply on diffusion is still on-topic for the PR but will sit between Han and Lisa.
- "making it optional is fine for us": consistent with Lisa's "be explicit" point only if it is a namelist option that defaults off. Optionally say so.

## Open items this surfaced (not drafts yet)

- **Lisa, #401 (23 Oct):** convective-precipitation plot, `hafs_global_1nest_atm`, with and without the fix. **Done 27 Oct** ([comment](https://github.com/ufs-community/ccpp-physics/issues/401#issuecomment-6433041952), `reply_401_lisa.posted.md`; figures `hafs_samf/cnvplot/`): 10 members per set, 0–18 h, both `progsigma`.
- **climbfuji, #406:** rewrite AI-sounding code comments in #405/#406/#407. **Done 27 Oct**: folded into the fix commits and force-pushed (`POSTING.md`, 25–27 Oct); reply `reply_406_climbfuji.md`.
- **Han, #405 (26 Oct):** disagrees. **Answered 27 Oct** with `reply_405_3.md` (slide-8 check numbers below).

## Where Han's group "confirmed conservation" (searched 26 Oct)

| Source | What it says | Does it test what #405 is about? |
|---|---|---|
| NCAR/ccpp-physics#753, `TVD.pdf` slide 8 (Convection parameterization meeting, 13 Aug 2021; Han, Yang, Montuoro, Li, Sun) | Eq. (1)+(2)+(3); "Subtract the double counting change rates of the variable at updraft and downdraft boundaries"; "Check conservation after implementing numerical discretization as ∫∂φ/∂t dz = (−w'φ')top − (−w'φ')bot": **central differencing ~1e-17 for TKE; TVD 1e-5–1e-2 for TKE** | Yes, and it shows a TVD residual 12–15 orders above rounding. TKE only; units not stated. Slide 10 blames residual negatives on "divergence of parcel flux [term (3)] and vertically unequal grid sizes", which is where the `kb` mismatch sits. |
| NCEP Office Note 506 (Han et al. 2022, doi 10.25923/5051-3r70) | Eq. (9c) as above. "Conserving the column integrated total tracer mass" refers only to the negative-tracer borrowing, Eqs. (10)–(11), which conserves by construction. No column budget of the TVD transport, no cloud-base treatment. Tests: TKE min/max tables, 6-day forecast skill (ccab07 vs ccab92). | No. |
| NCAR/ccpp-physics#754 | MJO and jet-stream diagnostics only (Diagnostics_ufsp6_ufsp7_ufsp7tvd). | No. |

No documented check on moisture. "We confirmed moisture and tracer mass conservations" most likely means slide 8 (TKE) and/or the borrowing, which conserves by construction. Ruiyu Sun is a co-author of ON506 and of the slides (and approved #406).

Local copies: scratchpad `hanpdf/on506.{pdf,txt}`, `hanpdf/tvd753.{pdf,txt}`, `hanpdf/slide-08.png`.

`reply_405_3.md` (372 words) restates the argument in his terms: Eq. (9c) terms (2) and (3) at the `kb` interface, his steps 1) and 2) carried to `kb+1`, and his slide-8 check applied to water. The TKE check has since been run (sa1chk5, job 10283521). On develop, TKE and ozone column residuals are 6.4e-3/3.6e-3 and 2.5e-3/3.0e-4 of the gross transport (deep/shallow), equal to the kb/jmin formula to 2e-14. With the PR they are 1e-16 to 3e-15. The reply now quotes these numbers.
