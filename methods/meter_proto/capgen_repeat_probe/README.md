# capgen-v1: a repeated probe scheme with optional, run-time-active arrays

This is the test behind the claim in [`../../meter_design.md`](../../meter_design.md) that one budget-check scheme can
appear several times in a group, with its storage allocated only when the meter is on.

## Result

Run on ccpp-framework `feature/capgen-v1` @1959c303, with gfortran 16.2, OpenMPI and `-fcheck=all`:

| Case | Result |
|---|---|
| Meter on, 1 OpenMP thread | 3 probes per column; both segment changes exact |
| Meter on, 4 OpenMP threads (dynamic schedule over 4 chunks) | same |
| Meter off: arrays unallocated, passed as absent | runs; `wet_step` applied twice |
| Known-bad: 2 slots for 3 probes | fails, `budget_probe: more probes than slots`, `STOP 1` |

What the generated cap (`ccpp_budget_suite_physics_cap.F90`) does:
- **Each occurrence gets its own pointer** (`budget_col_p`, `budget_col_2_p`, `budget_col_3_p`). The pointers are
  locals of `physics_run`, so they are thread-safe.
- **The active flag is tested per occurrence.** Each pointer is associated with the chunk slice when `active` is
  true, and nullified otherwise. When off, the cost per probe is two branches and two `nullify` calls.

## Constraints found

- **Host arrays passed as optional arguments need the `TARGET` attribute.** The cap reaches them through pointers.
- **Scheme array dimensions must use `horizontal_dimension`.** capgen-v1 rejects `horizontal_loop_extent` in a
  dimension, and the cap slices to `lb:ub` itself. A scheme that needs the column count takes `size(q, 1)`.

## Reproduce

1. Clone `NCAR/ccpp-framework` at `feature/capgen-v1`.
2. Make a work directory beside it containing:
   - `capgen` → `../ccpp-framework/capgen` (a symlink);
   - `e2e/cmake/`, copied from `end-to-end-tests/cmake`;
   - `e2e/CMakeLists.txt` = `CMakeLists_top.txt` from this folder;
   - `e2e/budget/`, holding the remaining files from this folder, with `CMakeLists_test.txt` renamed to
     `CMakeLists.txt`.
3. Build and run:

   ```
   cmake ../e2e -DCMAKE_Fortran_COMPILER=gfortran && make && OMP_NUM_THREADS=4 ./budget/test_budget.x
   ```
