#!/bin/bash

# info: vincent.poitras@ec.gc.ca
# date: 2023-06
# description: "wrapper" pour lancer les script main_MODIS_vs_CALIPSO_03_figures.py
#              C'est plus simple de soumettre un "wrapper" à travers l'ordonnanceur que le script python directement


###########################################################################
#                               Environnement                             #
###########################################################################
module load python3/miniconda3 python3/python3  &> /dev/null
source activate base_plus                       &> /dev/null


###########################################################################
#  Input parameters                                                       #
###########################################################################
working_directory=$1
YYYYi=$2
YYYYf=$3
period=$4
dataset=$5
layerdef_MODIS=$6
layerdef_CALIPSO=$7
window=$8
overwrite=$9


###########################################################################
# Script launch                                                          #
###########################################################################
script=$working_directory/main_MODIS_vs_CALIPSO_03_figures.py
args="$working_directory $YYYYi $YYYYf $period $dataset $layerdef_MODIS $layerdef_CALIPSO $window $overwrite"

python $script $args






