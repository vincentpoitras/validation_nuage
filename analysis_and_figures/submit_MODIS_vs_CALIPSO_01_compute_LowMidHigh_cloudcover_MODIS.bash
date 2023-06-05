#!/bin/bash

 	


###########################################################################
#                               Input parameters                          #
###########################################################################

if [ $# -ne 5 ]; then
	echo "USAGE:   ./submit_MODIS_vs_CALIPSO_01_compute_LowMidHigh_cloudcover_MODIS.bash YYYYMMi YYYYMMf dataset  overwrite submission_type"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_01_compute_LowMidHigh_cloudcover_MODIS.bash 201401  201512  MYD06_L2 false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_01_compute_LowMidHigh_cloudcover_MODIS.bash 201401  201402  MOD06_L2 false     interactive"
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
#                     Sanity check 1: Configuration file                  #
###########################################################################
# Check wheter the files exist
config=$working_directory/../config.yml
if [ ! -f $config ]; then
	echo "ERROR: Configuration file $config not found"
	echo "ERROR: Exit"
	exit
fi

###########################################################################
#                     Sanity check 2: YYYYMMi and YYYYMMf                 #
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
#                            Sanity check 3: dataset                      #
###########################################################################
# Check if the datset key is either MOD06_L2 or MYD06_L2
if [[ $dataset != MOD06_L2 ]] && [[ $dataset != MYD06_L2 ]] && [[ $dataset != MCD06_L2 ]]; then
        echo "ERROR: dataset=$dataset"
        echo "ERROR: Accecpted values [MOD06_L2/MYD06_L2/MCD06_L2]"
        echo "ERROR: Exit"
        exit
fi



###########################################################################
#                          Sanity check 4: Overwrite                      #
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
#                            Script submission                            #
###########################################################################
script=$working_directory/wrapper_MODIS_vs_CALIPSO_01_compute_LowMidHigh_cloudcover_MODIS.bash

YYYYMM=$YYYYMMi
while [ $YYYYMM -le $YYYYMMf ]; do
	
	args="$working_directory $YYYYMM $dataset $overwrite"

	if [[ $submission_type == scheduler ]]; then
		soumet $script -args $args -jn MODIS_LowMidHigh_cloudcover_$YYYYMM #-t 111600
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


