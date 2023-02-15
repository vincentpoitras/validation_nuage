#!/bin/bash

# info: vincent.poitras@ec.gc.ca
# date: 2023-02
# description: "wrapper" pour lancer les cript python main_COSPIN_01.py
#              C,est plus simple de soumettre un "wrapper" à travers l'ordonnanceur que le script python directement


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
overwrite=$4


###########################################################################
# Script launch                                                          #
###########################################################################
script=$working_directory/main_COSPIN_01.py
args="$working_directory $YYYYMM $dataset $overwrite"
python $script $args
