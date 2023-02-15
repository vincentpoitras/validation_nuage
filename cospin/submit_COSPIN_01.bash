#!/bin/bash

# Wrapper to launch the bash script main_COSPIN_01.py
#	1 task = 1 month

###########################################################################
#                               Environnement                             #
###########################################################################
module load python3/miniconda3 python3/python3  &> /dev/null
source activate base_plus                       &> /dev/null



###########################################################################
#                               Input paramters                           #
###########################################################################
if [ $# -ne 5 ]; then
	echo "USAGE:   ./submit_COSPIN_01.bash YYYYMMi YYYYMMf dataset   overwrite submission_type"
	echo "EXAMPLE: ./submit_COSPIN_01.bash 201401  201402  CALIPSO   false     scheduler"
	echo "EXAMPLE: ./submit_COSPIN_01.bash 201401  201402  MYOD06_L2 false     scheduler"
	echo "EXAMPLE: ./submit_COSPIN_01.bash 201401  201402  ALL_STEPS false     interactive"
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
# Auxiliary script                                                        #
###########################################################################
# python script used to do basic manipulations on yaml files
yamlmanip=$working_directory/../yamlmanip.py
if [ -f $yamlmanip ]; then
        ln -sf ../yamlmanip.py
else
        echo "[ERROR] $working_directory/../yamlmanip.py should exist and does not"
        echo "[ERROR] Exit"
        exit
fi


netcdf4_extra=$working_directory/../netcdf4_extra.py
if [ -f $netcdf4_extra ]; then
        ln -sf ../netcdf4_extra.py
else
        echo "[ERROR] $working_directory/../netcdf4_extra.py should exist and does not"
        echo "[ERROR] Exit"
        exit
fi


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


# Check if the config file is readable
args="'$config'"
config_is_readable=$(python -c "import yamlmanip; yamlmanip.check_if_readable($args);")
if [[ $config_is_readable == no ]]; then
        echo "[ERROR] Unable to read the config file: $working_directory/../config.yml"
        echo "[ERROR] Exit"
        exit
fi



###########################################################################
#  Sanity check 2: YYYYMMi and YYYYMMf                                    #
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
#  Sanity check 3: Overwrite                                              #
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
		echo "ERROR: Accepted answer are [y/n] (lower case)"
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
#  Sanity check 4: Data list                                              #
###########################################################################
# Check if 
#     * Input parameter for dataset is allowed
#     * File lists are existing (for each year) (skip for dataset=ALL_STEPS)


# Check if the dataset is one of the accepted values
if   [[ $dataset == MOD06_L2  ]] || [[ $dataset == MYD06_L2 ]] || [[ $dataset == MCD06_L2 ]]; then DATASET=MODIS;
elif [[ $dataset == CALIPSO   ]]                                                            ; then DATASET=CALIPSO;
elif [[ $dataset == ALL_STEPS ]]                                                            ; then DATASET=ALL_STEPS;
else 
	echo "[ERROR] datase=$dataset"
	echo "[ERROR] Accepted entries are [MOD06_L2/MYD06_L2/MCD06_L2/CALIPSO/ALL_STEPS] (case sensitive)"
        echo "[ERROR] Exit"
	exit	
fi

# Check if the list of file exists
if [[ $DATASET != ALL_STEPS ]]; then
	args_list="'$config', '$DATASET list'"
	args_dom="'$config', 'domain'"
	dir_list=$(python -c "import yamlmanip; yamlmanip.extract_value($args_list);")
	domain=$( python -c "import yamlmanip; yamlmanip.extract_value($args_dom);")
	[[ $DATASET == MODIS ]] && dir_list=${dir_list/MXD06_L2/$dataset}
	dir_list=$dir_list/$domain
	YYYYi=${YYYYMMi:0:4}
	YYYYf=${YYYYMMf:0:4}
	for YYYY in $(seq $YYYYi $YYYYf); do
		file_list=$dir_list/${YYYY}.txt
		if ! [ -f $file_list ]; then
			echo    "[ERROR] $file_list should exist and does not"
			echo -n "[ERROR] Make sure that you have run: "
			[[ $DATASET == CALIPSO ]] && echo " ../format/submit_CALIPSO_02_makefilelist.bash for the corresponding year"
			[[ $DATASET == MODIS   ]] && echo " ../format/submit_MODIS_04_makefilelist.bash for the corresponding year and dataset"
			echo "[ERROR] Exit"
			exit
		fi
	done
fi
	 	
	
###########################################################################
#  Sanity check 5: Output directory                                       #
###########################################################################
# Check if we are allowed to create the output directories
args_cospin="'$config', 'COSP2 input'"
dir_cospin=$(python -c "import yamlmanip; yamlmanip.extract_value($args_cospin);")

[ -d $dir_cospin ] || mkdir -p $dir_cospin
if ! [ -d $dir_cospin ]; then
	echo "[ERROR] Unable to create $dir_cospin"
	echo "[ERROR] Exit"
	exit
fi


###########################################################################
#  Script submission                                                      #
###########################################################################
script=$working_directory/wrapper_COSPIN_01.bash


YYYYMM=$YYYYMMi
while [ $YYYYMM -le $YYYYMMf ]; do
	jn=COSPIN_$YYYYMM	
	args="$working_directory $YYYYMM $dataset $overwrite"

	if [[ $submission_type == scheduler ]]; then
		soumet $script -args $args -jn $jn -cm 20G #-t 36000
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
