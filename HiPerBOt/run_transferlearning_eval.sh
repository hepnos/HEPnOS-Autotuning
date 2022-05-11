#!/bin/bash

#datasets=( "KRIPKE.L0" "HYPRE" )
datasets=( "DH_surrogate" "DH_surrogate2" )
for i in "${datasets[@]}"
do
  python transferlearning.py $i
done
