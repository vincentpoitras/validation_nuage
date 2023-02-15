#!/bin/bash




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
