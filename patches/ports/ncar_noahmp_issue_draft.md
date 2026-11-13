# Draft issue for NCAR/noahmp (not posted)

Ready to paste. Line numbers are NCAR/noahmp `master` @1a6225b (2026-10-02).

---

**Title:** Thin snow and canopy water below a threshold are set to zero and the water is discarded

**Body:**

### Description

Noah-MP zeroes small amounts of canopy water and of snow without passing the water anywhere, so it leaves the land
water balance. We found and measured both in the CCPP port of Noah-MP used by UFS (`module_sf_noahmplsm.F90` in
ufs-community/ccpp-physics, the v4-style code), and the same logic is in v5:

| | v5 (`master` @1a6225b) | What happens |
|---|---|---|
| Canopy water and ice | `src/CanopyHydrologyMod.F90` L92 (`CanopyLiqWater <= 1.0e-06`), L101 (`CanopyIce <= 1.0e-6`) | set to 0 after evaporation and frost/dew; the water goes nowhere |
| Snow without layers | `src/SnowWaterMainMod.F90` L176 and `src/SnowpackHydrologyMod.F90` L96 (`SnowWaterEquiv <= 1.0e-6`, `SnowDepth <= 1.0e-6` or `1.0e-8`); glacier versions in `SnowWaterMainGlacierMod.F90` L176 and `SnowpackHydrologyGlacierMod.F90` L106 | set to 0; the water goes nowhere |

### What we measured (UFS, CCPP copy)

In-model meters in a C96 UFS forecast (`control_p8_ugwpv1`, 24 h, 1.77 million land column-steps), with Noah-MP's own
water check (`errwat`) accumulated every step:

- **Canopy:** light rain or snow intercepted by the canopy often leaves at or below 1e-6 mm after evaporation and
  dew, so it vanished on about 5 % of land column-steps. The deleted water (0.0141 mm summed over the run) equalled
  the whole remaining water-check error in every snow state, to 1 part in 10⁴: about 4 × 10⁻⁷ of the precipitation
  falling on land. The CCPP copy uses the same 1e-6 thresholds as v5.
- **Snow:** the CCPP copy truncates at 1e-3 mm. Ice dripping off a frosted canopy reaches snow-free ground as about
  1e-4 mm per step and was deleted every step: −15.6 mm over the run, 0.009 % of global precipitation. v5's 1e-6 mm
  threshold lets that drip accumulate instead, so v5 should lose much less, only when thin snow melts or sublimates
  through the threshold. We have not measured v5.

Each event is small, below Noah-MP's water-balance error check, but the loss is one-signed, so it accumulates.

### Solution

Fixes we tested in the CCPP copy (`errwat` then sums to −1.2 × 10⁻⁸ mm over the run, i.e. rounding):

- **Canopy:** return the truncated liquid and ice from the canopy routine and add them to the rain and snowfall
  reaching the ground (the ice at the fresh-snow density). Nothing changes phase, so no latent heat is created. (We
  first tried adding it to canopy evaporation instead; that closes the water but leaves its latent heat unpaid.)
- **Snow:** when snow without layers is zeroed, add it to the top soil layer as ice, as the code already does with
  excess sublimation of thin snow. The glacier routines have no soil below the pack, so there we book it as runoff:
  surface runoff in the glacier snow-water routine, glacier flow (with the existing snow-cap overflow) at the end of
  the glacier driver.

The equivalent v5 changes are in `CanopyHydrologyMod` (and where its output feeds the ground water input) and in the
four snow routines above. We're happy to adapt and test them for v5 if that is useful. The CCPP versions are
ufs-community/ccpp-physics fixes NM5, NM6 and NM7 (diffs available).

### Also: negative transpiration heat condenses no water

`src/CanopyHydrologyMod.F90` L75 and L81 take `Transpiration = max(HeatLatentTransp/ConstLatHeat…, 0)`. When the
energy solve returns a negative transpiration heat flux (vapour condensing through the stomatal pathway), that latent
heat warms the canopy but no water condenses, so the water and the latent heat flux disagree. This is energy–water
consistency, not a water leak. In the CCPP copy (same logic in `canwater`), `HeatLatentTransp < 0` on 13 % of land
column-steps, and Noah-MP's latent energy exceeded its water's by 0.024 W/m² per land column. Counting the condensation
as canopy dew (`DewCanopyLiq`, or `FrostCanopyIce` on a frozen canopy) took that to 0.0013 W/m² (the canopy evaporation
cap) and added about 8e-4 mm/day of canopy dew over land; the energy solution is unchanged.

### Related

- The same code is in NOAA-EMC/noahmp (`src/module_sf_noahmplsm.F90`), where we have prepared the CCPP fixes (NM5, NM6, NM7) as well.

*Found with the help of an AI coding assistant (Claude); confirmed by building and running the model with in-model
water meters.*

---
