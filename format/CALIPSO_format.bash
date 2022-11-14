#!/bin/bash

# info: poitras.vincent@uqam.ca
#
# aim : [1] Convert hdf data to Netcdf4 (using h4tonccf_nc4)
#	[2] Fix the "valid_range attribute problem"
#           They are initialy specify by a string made of 2 number separated by a triple dot ...
#           This is replaced by a more standard array
#           If it is not done, other scripts will crash later
#
# Comment lancé le script
#       Interactif: ./CALIPSO_format.bash 2014 $(pwd)
#       Ordonaceur: YYYY=2014; soumet $(pwd)/CALIPSO_format.bash -args $YYYY  $(pwd) -jn format_CALIPSO_${YYYY} 
#
#
# Référence:
#	h4tonccf_nc4: http://hdfeos.org/software/h4cflib.php
#############################################################################################

# Environment 
module load python3/miniconda3 python3/python3 #>& /dev/null
source activate base_plus                      #>& /dev/null


# Input paramters
YYYY=$1
script_directory=$2


# Auxilliary scripts
h4tonccf_nc4=$script_directory/h4tonccf_nc4
format_attribute=$script_directory/calipso_fix_attribute_problem.py


# Inputs / Outputs directories
basedirectory=/pampa/poitras/DATA/CALIPSO/CAL_LID_L2_05kmCPro-Standard-V4
dir_hdf_input=$basedirectory/hdf/$YYYY
dir_cdf_output=$basedirectory/NetCDF/$YYYY
[ -d $dir_hdf_input   ] || { echo "ERROR: Input directory $dir_hdf_input does not exist." && exit; }
[ -d $dir_cdf_output  ] || mkdir -p $dir_cdf_output


# Main loop 
files=$(ls $dir_hdf_input | grep -F '.hdf')
for file in $files; do
	file_hdf=$dir_hdf_input/$file
	file_cdf=$dir_cdf_output/${file/.hdf/.nc}

        # Remove th output file if already existing
        [ -f $file_cdf ] && rm $file_cdf

	# Convert the file and fix the attribute
	$h4tonccf_nc4 $file_hdf $file_cdf      &> /dev/null # hdf --> NetCDF4
	python $format_attribute $file_cdf     #&> /dev/null # fix the attribute "problem"	
        echo $file_cdf

done	


