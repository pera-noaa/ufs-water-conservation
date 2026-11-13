<!-- POSTED 12 Nov 2026: https://github.com/ufs-community/ccpp-physics/pull/414#issuecomment-6833781177. Reply on ufs-community/ccpp-physics#414 to JongilHan66's 3 Nov comment 6608271814 (his shallow
     xlamue form: max(xlamue, xlamx) for k <= kbcon, min(xlamue, xlamx) above). That code is in #403 (62485fc1, 3 Nov),
     which re-implements #405, #408 and #414. Decision (12 Nov): #414 stays deep-only; shallow is not needed for the #401
     crashes (../shal_xlamue_414.md: no shallow step > 4 K, all shallow variants within consv_te noise in control_p8),
     and adding it would rerun package 1's RT. -->

@JongilHan66 Sorry for the slow reply. Your shallow form (floor at and below cloud base, cap above) is already in #403 (62485fc1), so I'll leave shallow to #403 and keep this PR to the deep floor that stops the #401 crashes. If you'd rather have it here too, I'll add your lines exactly as they are in #403.
