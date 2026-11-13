<!-- POSTED 12 Nov 2026 after pushing comment-only abd89364 to pr1-thompson (0e22f8c2 -> abd89364): thread replies 4556955042 (L951,
     in climbfuji's thread 4389484787, tagged), 4556955371 (L720), 4556955726 (L3171), 4556956131 (L3206); top-level 6837225987.
     Review re-request via API returned 404 (no permission); the top-level comment tags him. Red-teamed first. Replies on ufs-community/ccpp-physics#406 to AndersJensen-NOAA's
     12 Nov review (CHANGES_REQUESTED, four line comments on 0e22f8c2).
     done = one comment-only commit on pr1-thompson (bitwise unchanged: no code line differs), four thread replies,
     re-request review. L720: his choice between the two options; whichever he picks is bitwise too (dz is never read).
     No move of the rain-snow limit (reply 3).
     Checked (red-team, 12 Nov):
     - mp_gt_driver has one caller, mp_thompson.F90, and all three calls pass dm=dm (L814/L857/L900); the module reads dz
       only in the else branch (L1405), so the driver's dz (L720) is never read. dz1d = dm/rho is recomputed inside the
       dt_inner loop (L1308); t1d/qv1d re-read each inner step. Module rho uses max(1e-10,qv) (L1403), driver doesn't.
     - Below freezing prs_rcs = tmr_racs2 + tcr_sacr2 - tcs_racs1 - tms_sacr1 (L2795); class *1 (massr > 1.5 masss)
       goes to graupel, *2 stays snow (L4747-4795). So -(prr_rcs + prs_rcs) = table prg_rcs (L2799) before the clips
       (L2803-2805) and limiters; after L3206 the three sum to zero below freezing by construction.
     - Moving the limit below the snow check could leave snow negative: it lowers only a positive prs_rcs, which the
       snow check (L3175-3184) uses. The base's prg_rcg line in Re-enforce (L3200-3202) has the same exposure
       (prg_rcg enters the graupel check at L3187, then is cut to |prr_rcg|).
     - FV3 (UFS pin 0492f164, driver/UFS/atmosphere.F90): physics state is dry air + vapour, condensate removed from
       delp and prsi rebuilt (L2235-2262); after physics, tracer mass = input Delta-prsi * returned q (L1660-1664),
       then delp is rebuilt (L1673-1677). So dm = Delta-prsi*(1-spechum)/g IS dry-air mass (red-team finding 9,
       'dm counts condensate', was wrong: checked 12 Nov, no code change).
     - -0.4 %: new_spechum = spechum at entry (driver L601), so the effective change is the back-conversion.

     Comment-only commit (one line each):
       mp_thompson.F90, above L948 new_spechum = qv*(1-spechum):
         ! input spechum: FV3 turns q back into mass with the input layer mass (prsi), so q stays per that mass
       module_mp_thompson.F90 L3171, replacing "! limit the snow gained ...":
         !>  - Rain-snow collection below freezing: snow gains at most the rain lost (before the snow check).
       module_mp_thompson.F90 L3204, replacing "! graupel gains from the limited rain, ice and snow losses":
         ! graupel gets what rain and ice, and rain and snow, net lose, so each collection sums to zero
-->

### L951 (`new_qc*(1 − spechum)`)

Added a comment. After physics, FV3 turns each returned mass fraction back into mass by multiplying by the layer mass physics was given (the input `prsi` difference, dry air plus vapour), and only then rebuilds `delp`. So the mass fractions have to stay relative to that input mass. Converting back with the updated vapour divides by a different mass, which is the −0.4 % in the description.

### L720 (`dm`)

Yes, `dm` is only for `dz1d`, and no, both aren't needed: every call passes `dm`, so the module never reads `dz`. The module recomputes `dz1d = dm/ρ` at each inner step because T and q_v, and so ρ, change between inner steps. I'll make `dz` optional in `mp_gt_driver` and stop passing it (bitwise unchanged), unless you'd rather keep `dz` and drop `dm`, which lets `dz` go stale over the inner steps.

### L3171 (rain-snow limit)

It has to come before the snow check, which sums `prs_rcs`: placed after it, snow would be checked with a gain that is then removed, and could go negative. I've made it a `!>` step like the others so it reads as part of the conservation sequence. The existing `prg_rcg` line in that section has the same exposure for graupel; that's outside this PR, so I'll open a separate issue for it.

### L3206 (graupel from rain-snow)

You're right about the comment; the code holds. Below freezing `prs_rcs` is snow's net change: rain collected onto snow that stays snow (`tmr_racs2 + tcr_sacr2`) minus the snow turned to graupel (`tcs_racs1 + tms_sacr1`). So `−(prr_rcs + prs_rcs)` equals the table `prg_rcs` before the limiters, and after them it keeps the three summing to zero. I've reworded the comment.

### Top-level comment (with the review re-request)

@AndersJensen-NOAA Thanks for the review. COMMIT adds the comment you asked for at L951 and rewords the two at L3171 and L3206; it changes comment lines only, so answers are unchanged. Replies are in each thread.
