#!/bin/bash

# info: vincent.poitras@ec.gc.ca
#
# Wrapper to launch the bash script main_GEM5_01_format.bash
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
	echo "USAGE:   ./submit_GEM5_01_format.bash YYYYMMi YYYYMMf overwrite submission_type"
	echo "EXAMPLE: ./submit_GEM5_01_format.bash 201401  201412  false     scheduler"
	echo "EXAMPLE: ./submit_GEM5_01_format.bash 201401  201512  true      interactive"
	echo "EXAMPLE: ./submit_GEM5_01_format.bash 0       0       true      interactive"
	echo "NOTE: the latter case stand for step0"
	echo "Exit"
	exit
fi

YYYYMMi=$1
YYYYMMf=$2
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
# Sanity check 2: YYYYMMi and YYYYMMf                                     #
###########################################################################
# Check if YYYYMMi and YYYYMMf are 6 digit integers
# Check if YYYYMMi <= YYYYMMf 



keys='YYYYMMi YYYYMMf'
for key in $keys; do
	YYYYMM=${!key}
	[ $YYYYMM -eq 0 ] && break
	if [ ${#YYYYMM} -ne 6 ] || [[ ! $YYYYMM =~ ^[0-9]+$ ]]; then
		echo "ERROR: $key=$YYYYMM must be a 6-digits integer (or set to 0 for step0)"
	       	echo "ERROR: Exit"
		exit
	fi
done	

if [ $YYYYMMi -gt $YYYYMMf ]; then
        echo "ERROR: YYYYMMi=$YYYYMMi, YYYYMMf=$YYYYMMf"
	echo "ERROR: We must have YYYYMMi <= YYYYMMf"
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
# Check if monthly input directories exist

# Read configuration file
args_fst="'$config', 'GEM5 fst'"
dir_fst=$(python -c "import yamlmanip; yamlmanip.extract_value($args_fst);")


YYYYMM=$YYYYMMi
while [ $YYYYMM -le $YYYYMMf ]; do
 
	# Check directory existence
	[ $YYYYMM -eq 0 ] && diri=$dir_fst/*_step0 || diri=$dir_fst/*_${YYYYMM}
        if [ ! -d $diri ]; then
                echo "[ERROR]: $diri should exist and does not"
                echo "[ERROR]: Please check if ../download/main_GEM5_01_download.bash was previously ran"
                echo "[ERROR]: Exit"
                exit
        fi
	
	[ $YYYYMM -eq 0 ] && break

	# Date increment (by 1 month)
        date=${YYYYMM}010000
        newdate=$(r.date $date +31D)
        YYYYMM=${newdate:0:6}
done



###########################################################################
# Script submission                                                       #
###########################################################################
script=$working_directory/main_GEM5_01_format.bash


YYYYMM=$YYYYMMi
while [ $YYYYMM -le $YYYYMMf ]; do
	
	[ $YYYYMM -eq 0 ] && yyyymm=step0 || yyyymm=$YYYYMM 
	args="$working_directory $yyyymm $overwrite"		

	if [[ $submission_type == scheduler ]]; then
		soumet $script -args $args -jn GEM5_format_$YYYYMM #-t 111600
	elif [[ $submission_type == interactive ]]; then
		$script $args 
	else
		echo "ERROR: submission_type=$submission_type"
		echo "ERROR: Accepted values [scheduler/interactive]"
		echo "ERROR: Exit"
		exit
	fi


	[ $YYYYMM -eq 0 ] && break
		
	# Date increment (by 1 month)
	date=${YYYYMM}010000
	newdate=$(r.date $date +31D)
	YYYYMM=${newdate:0:6}
done


