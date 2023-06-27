#!/bin/bash

 	


###########################################################################
#                               Input parameters                          #
###########################################################################

if [ $# -ne 9 ]; then
	echo "USAGE:   ./submit_MODIS_vs_CALIPSO_03_figures.bash YYYYi YYYYf period dataset(MODIS) layerdef_MODIS     layerdef_CALIPSO window  overwrite submission_type"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_03_figures.bash 2014  2015  annual MYD06_L2       Cloud_Top_Pressure pmax             1       false     scheduler"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_03_figures.bash 2014  2014  01     MCD06_L2       Cloud_Top_Pressure pmax             3       true      interactive"
	echo "EXAMPLE: ./submit_MODIS_vs_CALIPSO_03_figures.bash 2014  2015  DJF    MCD06_L2       Cloud_Top_Pressure pmax             5       false     interactive"
	echo "Allowed values for period: annual, DJF, MAM, JJA, SON, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12"
	echo "window must be an odd number: 1,3,5..."
	echo "Exit"
	exit
fi

YYYYi=$1
YYYYf=$2
period=$3
dataset=$4
layerdef_MODIS=$5
layerdef_CALIPSO=$6
window=$7
overwrite=$8
submission_type=$9
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
#                     Sanity check 3: YYYYi and YYYYf                     #
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
#                     Sanity check 4: period                              #
###########################################################################
allowed_values=("annual" "DJF" "MAM" "JJA" "SON" "1" "2" "3" "4" "5" "6" "7" "8" "9" "10" "11" "12")
value_is_allowed=0
for allowed_value in "${allowed_values[@]}"; do
    if echo "$period" | grep -q "$allowed_value"; then
        value_is_allowed=1
    fi
done

if [ $value_is_allowed -eq 0 ]; then
	echo "ERROR: period=$period"
        echo "ERROR: Allowed values are: ${allowed_values[@]}"
        echo "ERROR: Exit"
        exit


fi

###########################################################################
#                     Sanity check 5: window                              #
###########################################################################

if [ $((window%2)) -eq 0 ]; then
	echo "ERROR: window=$window"
	echo "ERROR: window must be odd"
	echo "ERROR: Exit"
	exit
fi
###########################################################################
#                          Sanity check 6: Overwrite                      #
###########################################################################
# If overwrite is set to true, double check with the user 
if [[ $overwrite == true ]]; then
	echo "Overwrite data[y/n]"
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
script=$working_directory/wrapper_MODIS_vs_CALIPSO_03_figures.bash
	
args="$working_directory $YYYYi $YYYYf $period $dataset $layerdef_MODIS $layerdef_CALIPSO $window $overwrite"
if [[ $submission_type == scheduler ]]; then
	soumet $script -args $args -jn figures_${dataset}_${period}_${window} #-t 111600
elif [[ $submission_type == interactive ]]; then
	$script $args 
else
	echo "ERROR: submission_type=$submission_type"
	echo "ERROR: Accepted values [scheduler/interactive]"
	echo "ERROR: Exit"
	exit
fi



