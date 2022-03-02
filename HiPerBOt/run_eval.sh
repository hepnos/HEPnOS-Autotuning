#!/bin/bash

datasets=( "lulesh4_exec" "hypre" "mm" "openAtom" "kripke_exec" "kripke" "kripke_raja" )

for i in "${datasets[@]}"
do
  python configselection.py $i
done
