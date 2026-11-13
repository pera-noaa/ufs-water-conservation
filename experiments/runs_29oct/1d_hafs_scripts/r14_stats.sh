#!/bin/bash
# r14_stats.sh: crash table (+ the detector on known-crash q_t1a_c1000 and known-finish q_t1a_c999), dbg4 tail stats
U=/work2/noaa/co2/ash/ufs-chem-v1/upstream; P=$U/pr1; R=$P/r14_1d; SC=$P/r14_1d_scripts; H=$P/hafs_exp
PY="/work2/noaa/co2/miniconda3/envs/tm5/bin/python -I"
echo "== detector controls"; $PY $SC/r14_crash.py $H/q_t1a_c1000 $H/q_t1a_c999
for a in a b; do echo "== arm $a"; $PY $SC/r14_crash.py $(ls -d $R/${a}${TAG:-}_c*); done
for a in a b; do echo "== dbg4 $a"; QFH=006 $PY $SC/q_stats.py $(ls -d $R/${a}${TAG:-}_c*); done
sacct -n -X --name=$(for v in $(seq 1000 -1 981); do printf "r14_a${TAG:-}_c$v,r14_b${TAG:-}_c$v,"; done | sed 's/,$//') -S 2026-10-29 -o JobID,JobName%14,State,ExitCode,Elapsed
echo STATS_DONE
