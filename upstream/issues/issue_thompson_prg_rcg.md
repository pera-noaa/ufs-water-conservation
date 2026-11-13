<!-- DRAFT 12 Nov 2026, not posted. New issue on ufs-community/ccpp-physics, promised in the #406 L3171 thread
     (4556955726: "that's outside this PR, so I'll open a separate issue for it").
     done = issue filed with the mechanism, the fix form, and an offer; no runs before filing (it is a code-reading
     finding, and whether to fix is the owner's call).
     Code: pera-noaa/ccpp-physics pr1-thompson abd89364 (= #406 head), module_mp_thompson.F90:
       L2826-2829 below freezing prg_rcg = table, capped at rr/dt, prr_rcg = -prg_rcg; L2834-2836 above freezing
       prr_rcg = tcg_racg capped at rg/dt, prg_rcg = -prr_rcg.
       Rain check L3160-3170 (sump has +prr_rcg; scales prr_rcg L3169). Graupel check L3186-3196 (sump = prg_gde
       - prg_ihm - prr_gml + prg_rcg; other graupel gains prg_scw/rfz/gcw/rci/rcs are not in it). Re-enforce
       L3201-3203 cuts both to the smaller magnitude. Update L4310-4311: qg1d <= R1 -> 0 (creates water).
     Not measured. Above-freezing mirror: rain sinks in the rain check are -prg_rfz - pri_rfz - prr_rci, mostly
     freezing terms, so it rarely binds there.
     Title: "Thompson: graupel gain from rain collection is cut after the graupel check" -->

@AndersJensen-NOAA As mentioned in #406. In `module_mp_thompson.F90` (line numbers as of #406's head):

Below freezing, rain collected by graupel freezes onto it: `prg_rcg = −prr_rcg` (L2826–2829). The rain check can scale `prr_rcg` down (L3169), but the graupel check (L3186–3196) still counts the unscaled `prg_rcg` as a gain. Only afterwards does the Re-enforce block cut `prg_rcg` to the scaled rain loss (L3201–3203). If graupel was being depleted by sublimation or ice multiplication and passed its check only because of that gain, it ends the step below zero, and L4311 sets it to zero, which creates water. Above freezing the same pattern runs the other way (the rain gain is checked, then cut), but the rain check has few sinks there.

The fix is the one #406 makes for rain-snow: below freezing, set `prg_rcg = −prr_rcg` right after the rain check, before the graupel check. It changes answers only where the rain check limits rain collected by graupel below freezing.

I found this by reading the code and haven't measured how often it fires. I can open the PR, and measure it in `control_p8`, if you'd like it fixed.
