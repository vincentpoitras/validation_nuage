#!/bin/bash

# info: vincent.poitras@ec.gc.ca
# date: 2023-06
# description: "wrapper" pour lancer les script main_MODIS_vs_CALIPSO_02_common_track_monthly_mean.py
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
YYYYMM=$2
dataset=$3
layerdef_MODIS=$4
layerdef_CALIPSO=$5
overwrite=$6


###########################################################################
# Script launch                                                          #
###########################################################################
script=$working_directory/main_MODIS_vs_CALIPSO_02_common_track_monthly_mean.py
args="$working_directory $YYYYMM $dataset $layerdef_MODIS $layerdef_CALIPSO $overwrite"

python $script $args






