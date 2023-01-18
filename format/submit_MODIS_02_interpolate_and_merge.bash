#!/bin/bash

# Wrapper to launch the bash script MODIS_02_interpolate.bash
# This bash script:
# 	

###########################################################################
#                               Environnement                             #
###########################################################################
module load python3/miniconda3 python3/python3  &> /dev/null
source activate base_plus                       &> /dev/null



###########################################################################
#                               Input paramters                           #
###########################################################################

if [ $# -ne 5 ]; then
	echo "USAGE:   ./submit_MODIS_02_interpolate_and_merge.bash YYYYMMi YYYYMMf dataset  overwrite submission_type"
	echo "EXAMPLE: ./submit_MODIS_02_interpolate_and_merge.bash 201401  201402  MOD06_L2 false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_02_interpolate_and_merge.bash 201401  201512  MOD06_L2 true      interactive"
	echo "Exit"
	exit
fi

YYYYMMi=$1
YYYYMMf=$2
dataset=$3
overwrite=$4
submission_type=$5
working_directory=$(pwd)


###########################################################################
#  Sanity check 1: Configuration file                                     #
###########################################################################
# Check if the configuration file exist
config=$working_directory/../config.yml
if [ ! -f $config ]; then
	echo "ERROR: Configuration file $config not found"
	echo "ERROR: Exit"
	exit
fi

###########################################################################
#  Sanity check 2: dataset                                                #
###########################################################################
# Check if the datset key is either MOD06_L2 or MYD06_L2
if [[ $dataset != MOD06_L2 ]] && [[ $dataset != MYD06_L2 ]]; then
        echo "ERROR: dataset=$dataset"
	echo "ERROR: Accecpted values [MOD06_L2/MYD06_L2]"
        echo "ERROR: Exit"
        exit
fi


###########################################################################
#  Sanity check 3: YYYYMMi and YYYYMMf                                    #
###########################################################################
# Check if YYYYMMi and YYYYMMf are 6 digit integers
# Check if YYYYMMi <= YYYYMMf
keys='YYYYMMi YYYYMMf'
for key in $keys; do
	YYYYMM=${!key}
	if [ ${#YYYYMM} -ne 6 ] || [[ ! $YYYYMM =~ ^[0-9]+$ ]]; then
		echo "ERROR: $key=$YYYYMM must be a 6-digits integer"
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
#  Sanity check 4: Overwrite                                              #
###########################################################################
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
#  Sanity check 5: Input directories                                      #
###########################################################################
# Check if the input directories exist (for each year involved)
#     * Range YYYYi to YYYYf
#     * YYYYi-1
# Individual files may still missing, but that will be checked in the main script


# Read configuration file
args_cdf="'$config', 'MODIS NetCDF'"
args_dom="'$config', 'domain'"
dir_cdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_cdf);")
domain=$( python -c "import yamlmanip; yamlmanip.extract_value($args_dom);")



# INPUT DIRECTORIES: Check range YYYYi to YYYYi
YYYYi=${YYYYMMi:0:4}
YYYYf=${YYYYMMf:0:4}
for YYYY in $(seq $YYYYi $YYYYf); do
	#Input directory
	diri=$dir_cdf/original/$YYYY
	diri=${diri/MXD06_L2/$dataset}
	if [ ! -d $diri ]; then
        	echo "[ERROR]: $diri should exist and does not"
        	echo "[ERROR]: Please check if MODIS_01_format.bash was previously ran"
        	echo "[ERROR]: Exit"
		exit
	fi
done


# INPUT DIRECTORIES: Check YYYY-1  (if MMi == 01)
MMi=${YYYYMMi:4:2}
if [[ $MMi == 01 ]]; then
	YYYYim1=$((YYYYi-1))
	diri=$dir_cdf/original/$YYYYim1
	diri=${diri/MXD06_L2/$dataset}	
	if [ ! -d $diri ]; then 
                echo "[ERROR]: $diri should exist and does not"
		echo "[ERROR]: For 1st hourly file to produce ${YYYYMMi}0100, 6 timesteps are extracted from the previous year:"
                echo "[ERROR]: ${YYYYim1}1231 @ 23:30,23:35,23:40,:23:45,23:50,23:55)"
                echo "[ERROR]: Please check if MODIS_01_format.bash was previously ran"
                echo "[ERROR]: Exit"
                exit
	fi
fi
	
	 	
	
# OUTPUT directories
# TODO: check if we have the right to create them



###########################################################################
#  Script submission                                                      #
###########################################################################
script=$working_directory/main_MODIS_02_interpolate_and_merge.bash

YYYYMM=$YYYYMMi
while [ $YYYYMM -le $YYYYMMf ]; do
	
	args="$working_directory $YYYYMM $dataset $overwrite"

	if [[ $submission_type == scheduler ]]; then
		soumet $script -args $args -jn MODIS_interpolate_and_merge_${dataset}_$YYYYMM #-t 54000
	elif [[ $submission_type == interactive ]]; then
		$script $args 
	else
		echo "ERROR: submission_type=$submission_type"
		echo "ERROR: Accepted values [scheduler/interactive]"
		echo "ERROR: Exit"
		exit
	fi

	# Date increment (by 1 month)
	date=${YYYYMM}010000
	newdate=$(r.date $date +31D)
	YYYYMM=${newdate:0:6}
done
