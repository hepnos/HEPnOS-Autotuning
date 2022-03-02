#!/bin/bash

datasets=( "KRIPKE.L0" "HYPRE" )

for i in "${datasets[@]}"
do
  python transferlearning.py $i
done
