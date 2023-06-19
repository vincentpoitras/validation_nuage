#!/bin/bash

 	


###########################################################################
#                               Input parameters                          #
###########################################################################

if [ $# -ne 7 ]; then
	echo "USAGE:   ./submit_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash YYYYMMi YYYYMMf dataset(MODIS) layerdef_MODIS     layerdef_CALIPSO  overwrite submission_type"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash 201401  201512  MYD06_L2       Cloud_Top_Pressure pmax               false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash 201401  201512  MYD06_L2       Cloud_Top_Pressure pmax               false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash 201401  201512  MYD06_L2       Cloud_Top_Pressure pmax               false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash 201401  201512  MYD06_L2       Cloud_Top_Pressure pmax               false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash 201401  201512  MYD06_L2       Cloud_Top_Pressure pmax               false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash 201401  201512  MCD06_L2       Cloud_Top_Pressure pmax               true      interactive"
	echo "Exit"
	exit
fi

YYYYMMi=$1
YYYYMMf=$2
dataset=$3
layerdef_MODIS=$4
layerdef_CALIPSO=$5
overwrite=$6
submission_type=$7
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
#	                     Sanity check 2: dataset                      #
###########################################################################
# Check if the datset key is either MOD06_L2 or MYD06_L2
if [[ $dataset != MOD06_L2 ]] && [[ $dataset != MYD06_L2 ]] && [[ $dataset != MCD06_L2 ]]; then
        echo "ERROR: dataset=$dataset"
	echo "ERROR: Accecpted values [MOD06_L2/MYD06_L2/MCD06_L2]"
        echo "ERROR: Exit"
        exit
fi


###########################################################################
#                     Sanity check 3: YYYYMMi and YYYYMMf                 #
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
#               Copy auxiliary file used in an other folder               #
###########################################################################
auxfile=../format/aux_CALIPSO_check_if_track_is_inside.py
if [ -f $auxfile ]; then
	ln -sf $auxfile aux_CALIPSO.py
else
	echo "ERROR: $auxfile should exist and does not"
	echo "ERROR: Exit"
        exit

fi


###########################################################################
#                            Script submission                            #
###########################################################################
script=$working_directory/wrapper_MODIS_vs_CALIPSO_02_common_track_monthly_mean.bash

YYYYMM=$YYYYMMi
while [ $YYYYMM -le $YYYYMMf ]; do
	
	args="$working_directory $YYYYMM $dataset $layerdef_MODIS $layerdef_CALIPSO $overwrite"
	if [[ $submission_type == scheduler ]]; then
		soumet $script -args $args -jn Common_track_${dataset}_$YYYYMM #-t 111600
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


