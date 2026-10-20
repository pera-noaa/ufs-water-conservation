#!/bin/bash
# usage: make_canon.sh : canonical series from the replay. Steps that applied at -F0 keep their source diff verbatim;
# rebased (patch -F0 + integrator re-anchor) and script steps get the regenerated pre->post diff (-p1 at the tree root).
# Writes $R/patches/NN_label.diff + $R/patches/series.txt (file dir level class-of-origin source md5), checks the
# + and - lines of each rebased diff against its source.
set -uo pipefail
R=/work2/noaa/co2/ash/ufs-chem-v1/upstream/cons/replay
E=$R/../energy; A=$E/accepted; S2=$R/../ensfc2/patches; SRC=$R/src; TL=$R/tools/energy_tools
P=/work2/noaa/co2/miniconda3/envs/tm5/bin/python
O=${OUT:-$R/patches}; rm -rf "${O:?}"; mkdir -p $O; S=$O/series.txt; : > $S
cat ${RECIPES:-$R/tools/recipe_[a-e].txt} | while read -r line; do
  [[ -z "$line" || "$line" == \#* || "$line" == CMP* ]] && continue
  line=$(eval echo "$line"); set -- $line; nl=$1; m=$2
  res=$(awk -F'\t' -v n=$nl '$1==n{print $3}' $R/logs/replay${WTAG:-}.tsv | tail -1)
  if [[ $m == P || ( $m == PR && $res == clean ) ]]; then
    cp -p $5 $O/$nl.diff; printf "%s\t%s\t%s\t%s\t%s\n" "$nl.diff" "$3" "$4" "verbatim($res)" "$5" >> $S
  else
    cp -p $R/work${WTAG:-}/regen/$nl.diff $O/$nl.diff
    if [ $m = PR ]; then
      chk=$($P -I $R/tools/check_pm.py $O/$nl.diff 1 . $5 $4 $3 | tail -1)
      printf "%s\t.\t1\t%s\t%s\n" "$nl.diff" "rebased(+/- vs source: $chk)" "$5" >> $S
    elif [ $m = M ]; then
      printf "%s\t.\t1\t%s\t%s\n" "$nl.diff" "composed(-F$3, $res)" "${*:4}" >> $S
    else
      printf "%s\t.\t1\t%s\t%s\n" "$nl.diff" "script($res)" "$*" >> $S
    fi
  fi
done
cut -f1,4 $S | column -t -s$'\t'
