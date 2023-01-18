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

if [ $# -ne 3 ]; then
	echo "USAGE:   ./submit_CALIPSO_02_makefilelist.bash YYYYi YYYYf submission_type"
	echo "EXAMPLE: ./submit_CALIPSO_02_makefilelist.bash 2014  2014  scheduler"
	echo "EXAMPLE: ./submit_CALIPSO_02_makefilelist.bash 2014  2015  interactive"
	echo "Exit"
	exit
fi

YYYYi=$1
YYYYf=$2
submission_type=$3
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
#  Sanity check 3: Input directories                                      #
###########################################################################
# Check if annual imput directories exist

# Read configuration file
args_cdf="'$config', 'CALIPSO NetCDF'"
dir_cdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_cdf);")

for YYYY in $(seq $YYYYi $YYYYf); do        
	# Check directory existence
	diri=$dir_cdf/${YYYY}
        if [ ! -d $diri ]; then
                echo "[ERROR]: $diri should exist and does not"
                echo "[ERROR]: Please check if main_CALIPSO_01_format.bash was previously ran"
                echo "[ERROR]: Exit"
                exit
        fi
done


###########################################################################
#  Overwite checkup                                                       #
###########################################################################
# If the output file already exist, we ask to the user if we should 
# continue and overwrite the file


# Read configuration file
args_list="'$config', 'CALIPSO list'"
args_dom=" '$config', 'domain'"
dir_list=$(python -c "import yamlmanip; yamlmanip.extract_value($args_list);")
dom=$(     python -c "import yamlmanip; yamlmanip.extract_value($args_dom );")

for YYYY in $(seq $YYYYi $YYYYf); do
	file=$dir_list/$dom/${YYYY}.txt
	if [ -f $file ]; then
		echo "File $file already exists."
		echo "Do you want to overwrite it? [YES/no]"
		read answer

	        if [[ $answer == YES ]]; then
        	        echo Continue
			rm $file
	        elif [[ $answer == no ]]; then
        	        echo Abort 
                	exit
       	 	else
                	echo "ERROR: Accepted answer are [YES/no]"
                	echo "ERROR: Exit"
                	exit
		fi
        fi
done





###########################################################################
# Script submission                                                       #
###########################################################################
script=$working_directory/main_CALIPSO_02_makefilelist.bash


for YYYY in $(seq $YYYYi $YYYYf); do

	args="$working_directory $YYYY $overwrite"

	if [[ $submission_type == scheduler ]]; then
		soumet $script -args $args -jn CALIPSO_makefilelist_$YYYY #-t 111600
	elif [[ $submission_type == interactive ]]; then
		$script $args 
	else
		echo "ERROR: submission_type=$submission_type"
		echo "ERROR: Accepted values [scheduler/interactive]"
		echo "ERROR: Exit"
		exit
	fi
done


