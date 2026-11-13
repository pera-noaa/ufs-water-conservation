**Title:** Snow layer heat: conserve energy when snow layers merge, divide or vanish

**Base:** NCAR/noahmp `develop` (57b9373) ← pera-noaa/noahmp `snow-layer-heat`

---

**Bug.** Three routines change the heat content of the snowpack without a matching flux.

1. `SnowLayerCombine`: a layer with ≤ 0.1 kg/m² of ice is merged into its neighbour, and the neighbour keeps its own temperature. When the last layer melts out, or the pack falls below 2.5 cm, the heat of the removed layers is dropped.
2. `SnowThermalProperty`: `HeatCapacVolSnow` is built from the capped volume fractions `SnowIceVol` and `SnowLiqWaterVol`, so liquid beyond the pore space has no heat capacity.
3. `SnowLayerWaterCombo` (used by `SnowLayerCombine` and `SnowLayerDivide`): the enthalpy multiplies `ConstHeatCapacIce` and `ConstHeatCapacWater`, which are per m³, by layer masses in kg/m², so sensible heat is weighted about 1000 times too heavily against latent heat. When the combined enthalpy is between 0 and `ConstLatHeatFusion`·liquid, the temperature is set to freezing, which does not match that enthalpy.

**Fix.** One commit each:

1. Merge the two layers' heat with per-mass heat capacities and set the merged temperature from it. Pass the heat of removed layers to the top soil layer, or glacier ice on glacier points, through `HeatCapacSoilSnow(1)`.
2. Compute `HeatCapacVolSnow` from the ice and liquid mass. Where the caps do not bind, the result is unchanged.
3. Use per-mass heat capacities in one expression, `T = Tfrz + (H − Lf·liquid)/C`, as CTSM's `Combo` does (`src/biogeophys/SnowHydrologyMod.F90`). Liquid below freezing is left to the phase-change routine.

This changes snow and soil temperatures wherever layers merge, divide or vanish.

**Testing.** Standalone tests of the actual routines (gfortran 16.2, double precision, `-fcheck=all -ffpe-trap=invalid,zero,overflow`). Each test checks the enthalpy of the snow layers, ponded melt and the top soil layer before and after the call (J/m²; heat capacity in J/m²/K for case 7):

| Case | Routine | Change on `develop` | Change with this PR |
|---|---|---|---|
| 1. Thin top layer merges into the layer below | `SnowLayerCombine` | +913 | −1 × 10⁻⁹ |
| 2. Thin bottom layer merges into the layer above | `SnowLayerCombine` | −15,457 | 3 × 10⁻¹⁰ |
| 3. Last layer melts out | `SnowLayerCombine` | +2,174 | −2 × 10⁻⁹ |
| 4. Pack thinner than 2.5 cm loses its layers | `SnowLayerCombine` | +74,535 | 6 × 10⁻⁹ |
| 5. Layers combined by thickness, with liquid | `SnowLayerCombine` → `SnowLayerWaterCombo` | +1,393 | −5 × 10⁻¹⁰ |
| 6. Partly frozen combination | `SnowLayerWaterCombo` | +542 | 5 × 10⁻¹⁰ |
| 7. Heat capacity, liquid above the pore space | `SnowThermalProperty` | −57,043 (of 175,101) | 0 |

Each commit fixes its own cases (1–4, 7, and 5–6). In single precision the residuals with this PR are at most 3 J/m², the rounding of a soil temperature near 270 K. I have not run HRLDAS or WRF with this branch.

The same fixes, for the UFS copy of Noah-MP, are in ufs-community/ccpp-physics#410. There, in a 24 h C96 run, they reduced Noah-MP's soil energy residual from 3.9 × 10⁻⁴ to 4.3 × 10⁻⁸ W/m² (measured together with a later fix for thin snow).

@cenlinhe @barlage

<details><summary>Test program</summary>

```fortran
! Standalone checks of Noah-MP v5 snow layer heat: enthalpy of snow + ponding + top layer before and after each call
program test_snow_heat
  use Machine
  use ConstantDefineMod
  use NoahmpVarType
  use SnowLayerCombineMod
  use SnowLayerWaterComboMod
  use SnowThermalPropertyMod
  implicit none
  type(noahmp_type) :: nm
  integer :: nfail
  real(kind=kind_noahmp) :: h0, h1, tol
  real(kind=kind_noahmp) :: d1, l1, i1, t1
  tol = 1.0e-6
  nfail = 0
  call setup(nm)

  ! 1: thin top layer (ice <= 0.1) merges into the layer below
  call state(nm, -3, [0.01,0.10,0.20], [0.05,20.,30.], [0.,0.,0.], [260.,268.,271.])
  call check('merge into the layer below')
  ! 2: thin bottom layer merges into the layer above
  call state(nm, -2, [0.,0.10,0.02], [0.,10.,0.05], [0.,0.,0.5], [0.,265.,272.])
  call check('bottom layer merges up')
  ! 3: the last layer vanishes; its heat goes to the top soil layer
  call state(nm, -1, [0.,0.,0.03], [0.,0.,0.08], [0.,0.,0.02], [0.,0.,265.])
  call check('last layer vanishes')
  ! 4: pack thinner than 2.5 cm loses its layers
  call state(nm, -2, [0.,0.01,0.01], [0.,2.,2.], [0.,0.,0.], [0.,262.,268.])
  call check('thin pack loses its layers')
  ! 5: thin top layer combined by thickness, with liquid in both layers
  call state(nm, -3, [0.01,0.10,0.20], [3.,20.,30.], [1.,0.5,0.], [273.16,270.,271.])
  call check('thickness combination')

  ! 6: SnowLayerWaterCombo alone, enthalpy between 0 and Lf*liquid
  d1 = 0.05; l1 = 1.0; i1 = 5.0; t1 = ConstFreezePoint
  h0 = enth(i1,l1,t1) + enth(5.0_kind_noahmp,0.0_kind_noahmp,272.0_kind_noahmp)
  call SnowLayerWaterCombo(d1, l1, i1, t1, 0.05_kind_noahmp, 0.0_kind_noahmp, 5.0_kind_noahmp, 272.0_kind_noahmp)
  h1 = enth(i1,l1,t1)
  call report('combo, partly frozen', h0, h1)

  ! 7: SnowThermalProperty: liquid above the pore space still has heat capacity
  call state(nm, -1, [0.,0.,0.05], [0.,0.,40.], [0.,0.,20.], [0.,0.,273.])
  call SnowThermalProperty(nm)
  h0 = ConstHeatCapacIce/ConstDensityIce*40.0 + ConstHeatCapacWater/ConstDensityWater*20.0
  h1 = nm%energy%state%HeatCapacVolSnow(0)*0.05
  call report('heat capacity from mass [J/m2/K]', h0, h1)

  if (nfail > 0) then
     print '(a,i0,a)', 'FAIL: ', nfail, ' case(s)'
  else
     print '(a)', 'PASS: all cases'
  endif

contains

  function enth(ice, liq, t) result(h)
    real(kind=kind_noahmp), intent(in) :: ice, liq, t
    real(kind=kind_noahmp) :: h
    h = (ConstHeatCapacIce/ConstDensityIce*ice + ConstHeatCapacWater/ConstDensityWater*liq)*(t-ConstFreezePoint) &
        + ConstLatHeatFusion*liq
  end function enth

  function total(nm) result(h)
    type(noahmp_type), intent(in) :: nm
    real(kind=kind_noahmp) :: h
    integer :: j
    h = 0.0
    do j = nm%config%domain%NumSnowLayerNeg+1, 0
       h = h + enth(nm%water%state%SnowIce(j), nm%water%state%SnowLiqWater(j), nm%energy%state%TemperatureSoilSnow(j))
    enddo
    h = h + ConstLatHeatFusion*(nm%water%state%PondSfcThinSnwComb + nm%water%state%PondSfcThinSnwTrans)
    h = h + nm%energy%state%HeatCapacSoilSnow(1)*nm%config%domain%ThicknessSnowSoilLayer(1) &
            *(nm%energy%state%TemperatureSoilSnow(1)-ConstFreezePoint)
  end function total

  subroutine check(name)
    character(len=*), intent(in) :: name
    h0 = total(nm)
    call SnowLayerCombine(nm)
    h1 = total(nm)
    call report(name, h0, h1)
  end subroutine check

  subroutine report(name, a, b)
    character(len=*), intent(in) :: name
    real(kind=kind_noahmp), intent(in) :: a, b
    character(len=4) :: v
    v = 'ok'
    if (abs(b-a) > tol*max(1.0,abs(a))) then
       v = 'FAIL'; nfail = nfail + 1
    endif
    print '(a4,1x,a36,2es16.8,es11.2)', v, name, a, b, b-a
  end subroutine report

  subroutine setup(nm)
    type(noahmp_type), intent(inout) :: nm
    nm%config%domain%NumSnowLayerMax = 3
    nm%config%domain%NumSoilLayer    = 4
    nm%config%nmlist%OptSnowAlbedo   = 1
    nm%config%nmlist%OptSnowThermConduct = 1
    allocate(nm%config%domain%ThicknessSnowSoilLayer(-2:4), nm%energy%state%TemperatureSoilSnow(-2:4))
    allocate(nm%energy%state%HeatCapacSoilSnow(-2:4), nm%energy%state%HeatCapacVolSnow(-2:0))
    allocate(nm%energy%state%ThermConductSnow(-2:0))
    allocate(nm%water%state%SnowIce(-2:0), nm%water%state%SnowLiqWater(-2:0), nm%water%state%SnowRadius(-2:0))
    allocate(nm%water%state%SnowIceVol(-2:0), nm%water%state%SnowLiqWaterVol(-2:0), nm%water%state%SnowEffPorosity(-2:0))
    allocate(nm%water%state%MassBChydropho(-2:0), nm%water%state%MassBChydrophi(-2:0))
    allocate(nm%water%state%MassOChydropho(-2:0), nm%water%state%MassOChydrophi(-2:0))
    allocate(nm%water%state%MassDust1(-2:0), nm%water%state%MassDust2(-2:0), nm%water%state%MassDust3(-2:0))
    allocate(nm%water%state%MassDust4(-2:0), nm%water%state%MassDust5(-2:0))
    allocate(nm%water%state%SoilLiqWater(1:4), nm%water%state%SoilIce(1:4))
  end subroutine setup

  subroutine state(nm, nneg, dz, ice, liq, t)
    type(noahmp_type), intent(inout) :: nm
    integer, intent(in) :: nneg
    real, intent(in) :: dz(3), ice(3), liq(3), t(3)
    nm%config%domain%NumSnowLayerNeg = nneg
    nm%config%domain%ThicknessSnowSoilLayer(-2:0) = dz
    nm%config%domain%ThicknessSnowSoilLayer(1:4)  = [0.1, 0.3, 0.6, 1.0]
    nm%water%state%SnowIce      = ice
    nm%water%state%SnowLiqWater = liq
    nm%energy%state%TemperatureSoilSnow(-2:0) = t
    nm%energy%state%TemperatureSoilSnow(1:4)  = [271.0, 272.0, 274.0, 276.0]
    nm%energy%state%HeatCapacSoilSnow(1:4)    = 2.2e6
    nm%water%state%SoilLiqWater = 0.2
    nm%water%state%SoilIce      = 0.05
    nm%water%state%SnowRadius   = 100.0
    nm%water%state%SnowWaterEquiv = sum(ice) + sum(liq)
    nm%water%state%SnowDepth      = sum(dz)
    nm%water%state%PondSfcThinSnwComb  = 0.0
    nm%water%state%PondSfcThinSnwTrans = 0.0
  end subroutine state

end program test_snow_heat
```

Built against `utility/Machine.F90` and `src/` `ConstantDefineMod`, the `*VarType` modules, `SnowLayerWaterComboMod`, `SnowLayerCombineMod` and `SnowThermalPropertyMod`, with `-cpp -DDOUBLE_PREC -fdefault-real-8`.
</details>

AI-assisted: Claude Opus 5.5; reviewed by author (trailer on every commit). Part of a water-conservation project for UFS physics (NOAA GML / CIRES).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
