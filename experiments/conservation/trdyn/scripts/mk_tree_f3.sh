#!/bin/bash
# F3 gate tree: base + no-fma + latent 01a + 02b + 03b (physics) + tracer hook/meters/TX (trsamf bin) + latent F3 meter
set -euo pipefail
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; W=$U/cons/trdyn; T=$U/cons/tracer; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
S=$U/cons/trsamf/bin; LB=$U/cons/latent/bin
t=${1:?name}
[ -e "$W/$t" ] && { echo "ABORT $W/$t exists"; exit 1; }
rsync -a --exclude=.git --exclude='tests/build_*' --exclude='tests/*.exe' --exclude=tests/run_dir --exclude=tests/logs --exclude='tests/*.log' "$T/base/" "$W/$t/"
$P -I $U/cons/samfinit/tools/nofma.py "$W/$t"
(cd "$W/$t" && patch -p1 -F0 --no-backup-if-mismatch < $LB/01a_F3_samf_scavenging_booking.diff)
(cd "$W/$t/UFSATM/ccpp/physics" && for p in 02b_T1 03b_DRY; do patch -p1 -F0 --no-backup-if-mismatch < $W/patches/${p}_*.diff; done)
$P -I $S/testhook_chem_pbl.py "$W/$t"; $P -I $S/instrument_tm.py "$W/$t" $S/tm_meter.F90; $P -I $S/post_tx.py "$W/$t"
$P -I $LB/meter_f3.py "$W/$t"
echo "TREE_OK $W/$t"
