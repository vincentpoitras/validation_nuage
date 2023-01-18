#!/bin/bash

# info: vincent.poitras@ec.gc.ca
#
# Wrapper to launch the bash script main_CALIPSO_01_format.bash
# Each task corresponds to a month (YYYYMM)
# Task may be submitted interactively or through the scheduler
 
###########################################################################
#                               Environnement                             #
###########################################################################
module load python3/miniconda3 python3/python3  &> /dev/null
source activate base_plus                       &> /dev/null



###########################################################################
#                               Input paramters                           #
###########################################################################

if [ $# -ne 4 ]; then
	echo "USAGE:   ./submit_CALIPSO_01_format.bash YYYYi YYYYf overwrite submission_type"
	echo "EXAMPLE: ./submit_CALIPSO_01_format.bash 2014  2014  false     scheduler"
	echo "EXAMPLE: ./submit_CALIPSO_01_format.bash 2014  2015  true      interactive"
	echo "Exit"
	exit
fi

YYYYi=$1
YYYYf=$2
overwrite=$3
submission_type=$4
working_directory=$(pwd)


###########################################################################
# Auxiliary script                                                        #
###########################################################################
# python script used to do basic manipulations on yaml files
if [ -f $yamlmanip ]; then
	ln -sf ../yamlmanip.py 
else
	echo "[ERROR] $working_directory/../yamlmanip.py should exist and does not"
	echo "[ERROR] Exit"
	exit
fi





###########################################################################
# Sanity check 1: Configuration file                                      #
###########################################################################
# Check whether the files exist + is readable

config=$working_directory/../config.yml
if [ ! -f $config ]; then
	echo "ERROR: Configuration file $config not found"
	echo "ERROR: Exit"
	exit
fi

args="'$config'"
config_is_readable=$(python -c "import yamlmanip; yamlmanip.check_if_readable($args);")

if [[ $config_is_readable == no ]]; then
	echo "[ERROR] Unable to read the config file: $working_directory/../config.yml"
	echo "[ERROR] Exit"
	exit
fi



###########################################################################
# Sanity check 2: YYYYi and YYYYf                                     #
###########################################################################
# Check if YYYYi and YYYYf are 4 digit integers
# Check if YYYYi <= YYYYf 

keys='YYYYi YYYYf'
for key in $keys; do
	YYYY=${!key}
	if [ ${#YYYY} -ne 4 ] || [[ ! $YYYY =~ ^[0-9]+$ ]]; then
		echo "ERROR: $key=$YYYY must be a 4-digits integer"
	       	echo "ERROR: Exit"
		exit
	fi
done	

if [ $YYYYi -gt $YYYYf ]; then
        echo "ERROR: YYYYi=$YYYYi, YYYYf=$YYYYf"
        echo "ERROR: We must have YYYYi <= YYYYf"
        echo "ERROR: Exit"
        exit

fi


###########################################################################
# Sanity check 3: Overwrite                                               #
###########################################################################
# Check if overwirte is true or false
# If overwrite is set to true, double check with the user 
if [[ $overwrite == true ]]; then
	echo "Overwrite $dataset data in the range $YYYYMMi $YYYYMMf [y/n]"
	read answer
	if [[ $answer == y ]]; then
		echo Continue
	elif [[ $answer == n ]]; then
 		echo Abort 
		exit
	else
		echo "ERROR: Accepted answer are lower [y/n] (lower case)"
		echo "ERROR: Exit"
		exit
	fi		
elif [[ ! $overwrite == false ]]; then
	echo "ERROR: overwrite=$overwrite."
	echo "ERROR: Accepted values are [true/false] (lower case)"
	echo "ERROR: Exit"
	exit
fi


###########################################################################
#  Sanity check 4: Input directories                                      #
###########################################################################
# Check if annual imput directories exist

# Read configuration file
args_hdf="'$config', 'CALIPSO hdf'"
dir_hdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_hdf);")

for YYYY in $(seq $YYYYi $YYYYf); do        
	# Check directory existence
	diri=$dir_hdf/${YYYY}
        if [ ! -d $diri ]; then
                echo "[ERROR]: $diri should exist and does not"
                echo "[ERROR]: Please check if ../download/main_CALIPSO_01_download.bash was previously ran"
                echo "[ERROR]: Exit"
                exit
        fi
done


###########################################################################
# Script submission                                                       #
###########################################################################
script=$working_directory/main_CALIPSO_01_format.bash


for YYYY in $(seq $YYYYi $YYYYf); do

	args="$working_directory $YYYY $overwrite"

	if [[ $submission_type == scheduler ]]; then
		soumet $script -args $args -jn CALIPSO_format_$YYYY #-t 111600
	elif [[ $submission_type == interactive ]]; then
		$script $args 
	else
		echo "ERROR: submission_type=$submission_type"
		echo "ERROR: Accepted values [scheduler/interactive]"
		echo "ERROR: Exit"
		exit
	fi
done


