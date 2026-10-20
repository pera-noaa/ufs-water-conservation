#!/bin/bash
# usage: land14_impacts.sh : land-set impacts for full14 (NM10r A/B, noise pair, all-on vs ctl64)
E=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/energy; P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python; cd $E/runs
echo "-- NM10r A/B (gB14x_off -> gB14_off)"; $P -I ../tools/imp_land14.py gB14x_off gB14_off
echo "-- noise (ctl64 -> ctlc999)"; $P -I ../tools/imp_land14.py ctl64 ctlc999
echo "-- full14 all-on vs ctl64"; $P -I ../tools/imp_land14.py ctl64 rs14_S
