#!/bin/bash
# sv_setup.sh <P|A|A1|F|B>: survey of SAMF configurations with rt.sh (-l sv.conf -k -e) against develop's baselines.
# P: develop with the print-only dbg4 + dbgeta2 (every test must PASS: the prints change nothing);
# A: the same plus the issue's option A (a test that PASSes is one where A never binds); A1: option A only where eta > 1;
# F: Han's floor, xlamue >= 0.001*clamt (= xlamud) in deep (clam_deep = 0.1 in all 12, so = q_fix.sh's F).
# B: Christian Boyer's 2a95266 (Han's PR for #401) as is: floor 0.001*clamt replacing crtlame in deep and shallow,
#    fent1/fent2 from min(qeso ratio, 1) (boyer_2a95266.patch).
# GFS v16 and v17 at C48-C384 (dt 225-1200 s) and five HAFS configurations (dt 90-180 s).
set -eu
V=$1
P=/work2/noaa/co2/ash/ufs-chem-v1/upstream/pr1; H=$P/hafs_exp; R=$P/sv_$V
case $V in P) OFF=23 ;; A) OFF=24 ;; A1) OFF=25 ;; F) OFF=26 ;; B) OFF=27 ;; *) echo "variant?"; exit 1 ;; esac
[ -e "$R" ] && { echo "$R exists"; exit 1; }
rsync -a --exclude 'build_*' --exclude '/tests/*.exe' --exclude '/tests/logs/log_hercules/' $P/ufs-weather-model/ $R/
PH=$R/UFSATM/ccpp/physics; d=$PH/physics/CONV/SAMF; f=$d/samfdeepcnv.f; s=$d/samfshalcnv.f
[ "$(git -C $R rev-parse --short=8 HEAD)" = f1d68949 ] && [ -z "$(git -C $PH status --porcelain -- physics/CONV/SAMF)" ] || { echo "GATE: not pristine develop"; exit 1; }
if [ $V = A ] || [ $V = A1 ]; then
  o=optD.f; [ $V = A1 ] && o=optA1.f
  [ "$(grep -c 'xmbmax(i) = dp / (real(grav, kind=conv_wp)' $f)" = 1 ] || { echo "GATE: anchor A"; exit 1; }
  awk -v s=$H/$o '{print} /xmbmax\(i\) = dp \/ \(real\(grav, kind=conv_wp\)/{g=1} g==1 && /^      enddo/{while((getline l < s)>0) print l; g=2}' $f > $f.new && mv $f.new $f
fi
if [ $V = F ]; then
  c='^            xlamue(i,k) = max(xlamue(i,k), crtlame)$'
  [ "$(grep -c "$c" $f)" = 1 ] || { echo "GATE: anchor F"; exit 1; }
  sed -i "s/$c/            xlamue(i,k) = max(xlamue(i,k), crtlame,\n     \&                      0.001_conv_wp * clamt(i))/" $f
  [ "$(grep -c '^     &                      0.001_conv_wp \* clamt(i))$' $f)" = 1 ] || { echo "GATE: F not applied"; exit 1; }
  [ -z "$(git -C $PH diff -U0 -- physics/CONV/SAMF/samfdeepcnv.f | grep '^+[^+]' | cut -c2- | awk 'length($0)>72')" ] || { echo "GATE: column 72"; exit 1; }
fi
if [ $V = B ]; then
  git -C $PH apply $H/boyer_2a95266.patch || { echo "GATE: patch"; exit 1; }
  [ "$(git -C $PH diff --numstat -- physics/CONV/SAMF | awk '{a+=$1; d+=$2} END {print a" "d}')" = "9 5" ] || { echo "GATE: B diff size"; exit 1; }
fi
git -C $PH diff -- physics/CONV/SAMF > $P/sv_$V.diff
awk -v s=$H/dbg4_deep.f -v e=$H/dbgeta2_deep.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; while((getline l < e)>0) print l; done=1} {print}' $f > $f.new && mv $f.new $f
awk -v s=$H/dbg4_shal.f 'done==0 && /^! Negative moisture is set to zero after borrowing/{while((getline l < s)>0) print l; done=1} {print}' $s > $s.new && mv $s.new $s
echo "sv_$V: SAMF diff deep +$(git -C $PH diff --numstat -- physics/CONV/SAMF/samfdeepcnv.f | cut -f1) shal +$(git -C $PH diff --numstat -- physics/CONV/SAMF/samfshalcnv.f | cut -f1); option-A lines $(grep -c 'option D\|option A1' $f)"
cd $R/tests
{ sed -n '/^COMPILE | atm_dyn32 |/p' rt.conf
  for t in control_c48 control_c48.v2.sfc control_stochy control_p8 control_c192 control_c384 control_c384gdas; do grep -m1 "^RUN | *$t *|" rt.conf; done
  echo
  sed -n '/^COMPILE | hafsw |/p' rt.conf
  for t in hafs_regional_atm hafs_regional_atm_thompson_gfdlsf hafs_regional_1nest_atm hafs_global_1nest_atm hafs_global_storm_following_1nest_atm; do grep -m1 "^RUN | *$t *|" rt.conf; done
} > sv.conf
[ "$(grep -c '^COMPILE' sv.conf)" = 2 ] && [ "$(grep -c '^RUN' sv.conf)" = 12 ] || { echo "GATE: sv.conf"; cat sv.conf; exit 1; }
sed -i 's/\$(( \$(id -u) + 1500 ))/$(( $(id -u) + 1500 + ${ECF_OFF:-0} ))/' rt.sh
[ "$(grep -c 'ECF_OFF' rt.sh)" -ge 1 ] || { echo "GATE: ECF_OFF"; exit 1; }
cat > $P/sv_$V.sbatch <<EOF
#!/bin/bash
#SBATCH -A lpdm -p service -n 1 -t 08:00:00 -J ufs_sv_$V
#SBATCH --mem=64G
#SBATCH -o $P/sv_$V.%j.log
# survey $V: rt.sh -l sv.conf -k -e vs develop baselines
set -x
export MACHINE_ID=hercules
# --mem above is for this driver's cgroup (Lustre EIO); do not export it to the test jobs' srun
unset SLURM_MEM_PER_NODE SLURM_MEM_PER_CPU SLURM_MEM_PER_GPU
export ECF_OFF=$OFF
export PATH=\$(echo "\$PATH" | tr ":" "\n" | grep -v -i conda | paste -sd:)
unset PYTHONPATH
export dprefix=$P/sv_${V}_run
mkdir -p \${dprefix}/stmp
cd $R/tests
grep -m1 "BL_DATE=" bl_date.conf
./rt.sh -a lpdm -e -k -l sv.conf
echo "=== RT_EXIT rc=\$? ==="
EOF
j=$(sbatch --parsable $P/sv_$V.sbatch); echo "SURVEY $V SUBMITTED $j"
