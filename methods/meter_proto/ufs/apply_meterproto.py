#!/usr/bin/env python3
"""Apply the three budget-meter prototypes to a ufs-weather-model tree (develop, capgen era).
Usage: python3 apply_meterproto.py <ufs-weather-model> [--no-b] [--no-c]
  A  host meter: UFSATM/ccpp/driver/GFS_budget.F90, calls in atmos_model.F90, h2ophys column output in GFS_photochemistry
  B  check schemes ufs_budget_save / samf_prepare_flux_for_budget / ufs_budget_check around SAMF in FV3_GFS_v17_p8_ugwpv1
  C  capgen --post-call-hook MODULE:SUBROUTINE, wired to GFS_budget:budget_post_call_hook
Every anchor must match exactly once, else nothing is written. Run-time switches: &budget_nml budget_meter, budget_hook."""
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1])
do_b = '--no-b' not in sys.argv
do_c = '--no-c' not in sys.argv
here = Path(__file__).resolve().parent
A = root / 'UFSATM'
PH = A / 'ccpp/physics/physics/Interstitials/UFS_SCM_NEPTUNE'
edits = {}


def sub(path, old, new):
    s = edits.get(path) or path.read_text()
    n = s.count(old)
    if n != 1:
        sys.exit(f'ABORT {path.relative_to(root)}: expected 1 match, found {n}: {old.strip()[:70]!r}')
    edits[path] = s.replace(old, new)


# ---- A: host module, atmos_model calls -------------------------------------------------------
am = A / 'fv3/atmos_model.F90'
sub(am, "use CCPP_driver,        only: CCPP_step, ccpp_suite\n",
    "use CCPP_driver,        only: CCPP_step, ccpp_suite\n"
    "use GFS_budget,         only: budget_init, budget_before_physics, budget_after_physics\n")
sub(am, "   if (ierr/=0)  call mpp_error(FATAL, 'Call to CCPP physics_init step failed')\n",
    "   if (ierr/=0)  call mpp_error(FATAL, 'Call to CCPP physics_init step failed')\n"
    "   call budget_init()\n")
sub(am, "      call CCPP_step (step=\"physics\", nblks=Atm_block%nblks, ierr=ierr, dycore='fv3')\n"
        "      if (ierr/=0)  call mpp_error(FATAL, 'Call to CCPP physics step failed')\n",
    "      call budget_before_physics()\n"
    "      call CCPP_step (step=\"physics\", nblks=Atm_block%nblks, ierr=ierr, dycore='fv3')\n"
    "      if (ierr/=0)  call mpp_error(FATAL, 'Call to CCPP physics step failed')\n"
    "      call budget_after_physics(Atm_block)\n")

cm = A / 'ccpp/CMakeLists.txt'
sub(cm, "add_library(${CCPP_TARGET}\n  ${CAPGEN_DEPENDENCIES}\n",
    "add_library(${CCPP_TARGET}\n  ${CAPGEN_DEPENDENCIES}\n  ${HOST_FILES_DIR}/driver/GFS_budget.F90\n")

# Diag arrays (always allocated in the prototype; the design allocates them only when on)
td = A / 'ccpp/data/GFS_typedefs.F90'
NEW = ['budget_h2ophys', 'budget_b_w0', 'budget_b_flux', 'budget_b_dw', 'budget_b_decl']
sub(td, "    real (kind=kind_phys), pointer :: rainc  (:)     => null()   !< convective rain at this time step\n",
    "    real (kind=kind_phys), pointer :: rainc  (:)     => null()   !< convective rain at this time step\n"
    + ''.join(f"    real (kind=kind_phys), pointer :: {v}(:) => null()   !< budget meter (prototype)\n" for v in NEW))
sub(td, "    allocate (Diag%rainc   (IM))\n",
    "    allocate (Diag%rainc   (IM))\n" + ''.join(f"    allocate (Diag%{v} (IM))\n    Diag%{v} = zero\n" for v in NEW))
tm = A / 'ccpp/data/GFS_typedefs.meta'
META = {
    'budget_h2ophys': ('budget_column_water_change_from_photochemistry', 'column water change from h2o photochemistry this step'),
    'budget_b_w0': ('budget_column_water_at_segment_start', 'column water at the start of the checked segment'),
    'budget_b_flux': ('budget_declared_column_water_change_of_segment', 'declared column water change of the checked segment'),
    'budget_b_dw': ('budget_accumulated_column_water_change_of_segment', 'column water change of the checked segment, window sum'),
    'budget_b_decl': ('budget_accumulated_declared_water_change_of_segment', 'declared water change of the checked segment, window sum'),
}
block = ''.join(f"[{v}]\n  standard_name = {std}\n  long_name = {lng}\n  units = kg m-2\n  dimensions = (horizontal_dimension)\n"
                f"  type = real\n  kind = kind_phys\n" for v, (std, lng) in META.items())
sub(tm, "[rainc]\n  standard_name = lwe_thickness_of_convective_precipitation_amount_on_dynamics_timestep\n"
        "  long_name = convective rain at this time step\n  units = m\n  dimensions = (horizontal_dimension)\n"
        "  type = real\n  kind = kind_phys\n",
    "[rainc]\n  standard_name = lwe_thickness_of_convective_precipitation_amount_on_dynamics_timestep\n"
    "  long_name = convective rain at this time step\n  units = m\n  dimensions = (horizontal_dimension)\n"
    "  type = real\n  kind = kind_phys\n" + block)

# h2ophys column change (answer-neutral: writes only the new array)
pf = PH / 'GFS_photochemistry.F90'
sub(pf, "       do3_dt_temp, do3_dt_ohoz, dqv_dt_prd, dqv_dt_qvmx, errmsg, errflg)\n",
    "       do3_dt_temp, do3_dt_ohoz, dqv_dt_prd, dqv_dt_qvmx, prsi, budget_h2ophys, errmsg, errflg)\n")
sub(pf, "    real(kind=kind_phys), intent(in), dimension(:,:,:) :: &\n         gq0             ! tracer concentration\n",
    "    real(kind=kind_phys), intent(in), dimension(:,:,:) :: &\n         gq0             ! tracer concentration\n"
    "    real(kind=kind_phys), intent(in), dimension(:,:) :: prsi          ! interface pressure (Pa)\n"
    "    real(kind=kind_phys), intent(inout), dimension(:) :: budget_h2ophys ! column water change (kg m-2)\n")
sub(pf, "           ten_q(i,k,ntqv) = (h2o0(i,k) - init_h2o0(i,k))/dtp\n         end do\n       end do\n    endif\n",
    "           ten_q(i,k,ntqv) = (h2o0(i,k) - init_h2o0(i,k))/dtp\n         end do\n       end do\n"
    "       do i=1, im\n         budget_h2ophys(i) = 0.\n         do k=1, levs\n"
    "           budget_h2ophys(i) = budget_h2ophys(i) + dtp*ten_q(i,k,ntqv)*(prsi(i,k) - prsi(i,k+1))*con_1ovg\n"
    "         end do\n       end do\n    else\n       budget_h2ophys(1:im) = 0.\n    endif\n")
pm = PH / 'GFS_photochemistry.meta'
sub(pm, "  intent = inout\n  optional = True\n[errmsg]\n", "  intent = inout\n  optional = True\n[prsi]\n  standard_name = air_pressure_at_interface\n  long_name = air pressure at model layer interfaces\n"
    "  units = Pa\n  dimensions = (horizontal_loop_extent,vertical_interface_dimension)\n  type = real\n  kind = kind_phys\n"
    "  intent = in\n[budget_h2ophys]\n  standard_name = budget_column_water_change_from_photochemistry\n"
    "  long_name = column water change from h2o photochemistry this step\n  units = kg m-2\n"
    "  dimensions = (horizontal_loop_extent)\n  type = real\n  kind = kind_phys\n  intent = inout\n[errmsg]\n")

# ---- B: check schemes around SAMF ------------------------------------------------------------
if do_b:
    for f in ['ufs_budget_common.F90', 'ufs_budget_save.F90', 'ufs_budget_save.meta', 'ufs_budget_check.F90',
              'ufs_budget_check.meta', 'samf_prepare_flux_for_budget.F90', 'samf_prepare_flux_for_budget.meta']:
        if (PH / f).exists():
            sys.exit(f'ABORT {f} already exists')
    sub(cm, '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/GFS_SCNV_generic_post.meta"\n',
        '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/GFS_SCNV_generic_post.meta"\n'
        '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/ufs_budget_save.meta"\n'
        '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/ufs_budget_check.meta"\n'
        '  "${SCHEME_FILES_DIR}/Interstitials/UFS_SCM_NEPTUNE/samf_prepare_flux_for_budget.meta"\n')
    sx = A / 'ccpp/suites/suite_FV3_GFS_v17_p8_ugwpv1.xml'
    sub(sx, "      <scheme>GFS_suite_interstitial_3</scheme>\n",
        "      <scheme>ufs_budget_save</scheme>\n      <scheme>GFS_suite_interstitial_3</scheme>\n")
    sub(sx, "      <scheme>GFS_suite_interstitial_4</scheme>\n",
        "      <scheme>GFS_suite_interstitial_4</scheme>\n      <scheme>samf_prepare_flux_for_budget</scheme>\n"
        "      <scheme>ufs_budget_check</scheme>\n")
    meta_args = {'w0': 'budget_b_w0', 'flux': 'budget_b_flux', 'dw': 'budget_b_dw', 'decl': 'budget_b_decl'}

# ---- C: capgen per-call hook -------------------------------------------------------------------
if do_c:
    cg = A / 'cmake/ccpp_capgen.cmake'
    sub(cg, "  set(oneValueArgs HOST_NAME OUTPUT_ROOT VERBOSITY KIND_SPECS)\n",
        "  set(oneValueArgs HOST_NAME OUTPUT_ROOT VERBOSITY KIND_SPECS POST_CALL_HOOK)\n")
    sub(cg, "  if(arg_TRACE)\n    list(APPEND CCPP_CAPGEN_CMD_LIST \"--trace\")\n  endif()\n",
        "  if(arg_TRACE)\n    list(APPEND CCPP_CAPGEN_CMD_LIST \"--trace\")\n  endif()\n\n"
        "  if(DEFINED arg_POST_CALL_HOOK)\n    list(APPEND CCPP_CAPGEN_CMD_LIST \"--post-call-hook\" \"${arg_POST_CALL_HOOK}\")\n  endif()\n")
    sub(cm, "            KIND_SPECS \"${CCPP_KINDS}\")\n",
        "            KIND_SPECS \"${CCPP_KINDS}\"\n            POST_CALL_HOOK \"GFS_budget:budget_post_call_hook\")\n")
    cp = A / 'ccpp/framework/capgen/ccpp_capgen.py'
    sub(cp, "    parser.add_argument(\n        '--trace',\n",
        "    parser.add_argument(\n        '--post-call-hook',\n        default=None,\n        metavar='MODULE:SUBROUTINE',\n"
        "        help=(\"After every scheme run call, emit `call SUBROUTINE(suite, group, scheme, lb, ub, \"\n"
        "              \"thread, errmsg, errflg)` (with `use MODULE`) in the group caps.\"),\n    )\n"
        "    parser.add_argument(\n        '--trace',\n")
    sub(cp, "    trace: bool = False,\n    return_state: bool = False,\n):\n",
        "    trace: bool = False,\n    return_state: bool = False,\n    post_call_hook: Optional[str] = None,\n):\n")
    sub(cp, "        # Group caps\n        for resolved_group in suite_res.groups:\n",
        "        # Group caps\n        from generator import group_cap as _gc\n        _gc.set_post_call_hook(post_call_hook)\n"
        "        for resolved_group in suite_res.groups:\n")
    sub(cp, "            trace=args.trace,\n        )\n    except CCPPError as exc:\n",
        "            trace=args.trace,\n            post_call_hook=args.post_call_hook,\n        )\n    except CCPPError as exc:\n")
    gp = A / 'ccpp/framework/capgen/generator/group_cap.py'
    sub(gp, "def _emit_phase_items(\n",
        "_POST_CALL_HOOK = None   # (module, subroutine) or None\n_HOOK_CTX = None         # (suite, group, lb, ub, thread)\n\n\n"
        "def set_post_call_hook(spec):\n    \"\"\"Set the per-call hook from 'MODULE:SUBROUTINE' (None disables it).\"\"\"\n"
        "    global _POST_CALL_HOOK\n    _POST_CALL_HOOK = tuple(spec.split(':', 1)) if spec else None\n\n\n"
        "def _emit_phase_items(\n")
    sub(gp, "    if errflg_arg is not None:\n        lines.append('{}if ({} /= 0) return'.format(indent, _call_arg_expr(errflg_arg)))\n",
        "    if errflg_arg is not None:\n        lines.append('{}if ({} /= 0) return'.format(indent, _call_arg_expr(errflg_arg)))\n"
        "    if _POST_CALL_HOOK and _HOOK_CTX and phase == 'run' and errflg_local and errmsg_local:\n"
        "        s, g, lb, ub, th = _HOOK_CTX\n"
        "        lines.append(\"{}call {}('{}', '{}', '{}', {}, {}, {}, {}, {})\".format(\n"
        "            indent, _POST_CALL_HOOK[1], s, g, resolved_call.scheme_name, lb, ub, th, errmsg_local, errflg_local))\n"
        "        lines.append('{}if ({} /= 0) return'.format(indent, errflg_local))\n")
    sub(gp, "    # ---- scheme calls ---------------------------------------------------\n",
        "    # ---- scheme calls ---------------------------------------------------\n"
        "    global _HOOK_CTX\n"
        "    _lb = _ctrl_local(host_dict, 'horizontal_loop_begin')\n"
        "    _ub = _ctrl_local(host_dict, 'horizontal_loop_end')\n"
        "    _th = _ctrl_local(host_dict, 'thread_number')\n"
        "    _HOOK_CTX = (suite_name, group_name, _lb, _ub, _th) if (_lb and _ub and _th) else None\n")
    sub(gp, "    if ctrl_local_names:\n        lines.append('{}subroutine {}( &'.format(_INDENT, sub_name))\n",
        "    _hook_use = ('{}  use {}, only: {}'.format(_INDENT, *_POST_CALL_HOOK)\n"
        "                 if (_POST_CALL_HOOK and phase == 'run') else None)\n"
        "    if ctrl_local_names:\n        lines.append('{}subroutine {}( &'.format(_INDENT, sub_name))\n")
    sub(gp, "    # ---- dummy argument declarations ------------------------------------\n",
        "    if _hook_use:\n        lines.append(_hook_use)\n\n"
        "    # ---- dummy argument declarations ------------------------------------\n")

# ---- write ---------------------------------------------------------------------------------------
for p, s in edits.items():
    p.with_suffix(p.suffix + '.preMP').write_text(p.read_text())
    p.write_text(s)
shutil.copy(here / 'GFS_budget.F90', A / 'ccpp/driver/GFS_budget.F90')
if do_b:
    for f in ['ufs_budget_common.F90', 'ufs_budget_save.F90', 'ufs_budget_save.meta', 'ufs_budget_check.F90',
              'ufs_budget_check.meta', 'samf_prepare_flux_for_budget.F90', 'samf_prepare_flux_for_budget.meta']:
        shutil.copy(here / f, PH / f)
print(f'applied: A{" B" if do_b else ""}{" C" if do_c else ""}; {len(edits)} files edited')
