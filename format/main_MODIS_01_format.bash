#!/bin/bash

# info: poitras.vincent@uqam.ca
# date: 2022/02/21
# aim : [1] Convert hdf data to Netcdf4
#	[2] Set variables attributes (they are originally defined in the global attributes)
#
#############################################################################################



###########################################################################
#                               Environnement                             #
###########################################################################
module load python3/miniconda3 python3/python3  &> /dev/null
source activate base_plus			&> /dev/null



###########################################################################
#                               Input parameters                          #
###########################################################################
working_directory=$1
YYYYMM=$2
dataset=$3
overwrite=$4

# Reset overwrite value: true --> 1, false --> 0 
[[ $overwrite == true ]] && overwrite=1 || overwrite=0


###########################################################################
#  Moving to the working directory                                        #
###########################################################################
cd $working_directory


###########################################################################
#                         Scripts called in the main loop                 #
###########################################################################
# Transform date format: YYYYMMDD --> YYYYJJJ
#  e.g  20140101 --> 2014001, 20141231 --> 2014365, 20080229 --> 2008060, etc
MMDD2JJJ=$working_directory/aux_MODIS_MMDD2JJJ.py  

# Convert hdf to NetCDF
h4tonccf_nc4=$working_directory/h4tonccf_nc4

# Compress files and remove "duplicated" fields created by h4tonccf_nc
format_python=$working_directory/aux_MODIS_format.py



###########################################################################
#                    Configuration file / path to directories             #
###########################################################################
config=$working_directory/../config.yml

YYYY=${YYYYMM:0:4}

# Read configuration file
args_hdf="'$config', 'MODIS hdf'"
args_cdf="'$config', 'MODIS NetCDF'"
dir_hdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_hdf);")
dir_cdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_cdf);")/original


# Replace the template MXD06_L2 by MOD06_L2 or MYD06_L2
dir_hdf=${dir_hdf/MXD06_L2/$dataset}
dir_cdf=${dir_cdf/MXD06_L2/$dataset}


# Add the YYYY subdirectory
YYYY=${YYYYMM:0:4}
dir_hdf=$dir_hdf/$YYYY
dir_cdf=$dir_cdf/$YYYY

# Create the directories if they don't already exist
[ -d $dir_hdf ] || mkdir -p $dir_hdf
[ -d $dir_cdf ] || mkdir -p $dir_cdf



###########################################################################
#                               datei and datef                           #
###########################################################################
# In the main loop, we will perform a loop from datei to datef
# Files are availble each 5 min
# datei: First day of the current month (YYYYMM) at 00h00
# datef: Last  day of teh current month (YYYMMM) at 23h55
# Format: YYYYMMDDHHMM

datei=${YYYYMM}010000
YYYYMMp1=$(r.date $datei +31D) # Add 31 days (p1 --> plus ~1 month)
YYYYMMp1=${YYYYMMp1:0:6}010000 # First day of the next    month at 00h00
datef=$(r.date $YYYYMMp1 -5M)  # Last  day of the current month at 23h55
datef=${datef:0:12}            # Keep the 12 first digits to have YYYYMMDDHHMM



###########################################################################
#                                  Main loop                              #
###########################################################################
date=$datei
while [ $date -le $datef ]; do


	# Date and filenames
        YYYYMMDD=${date:0:8}
        HHMM=${date:8:12}
        YYYYJJJ=$(python $MMDD2JJJ $YYYYMMDD)
        filei=$dir_hdf/${dataset}.A${YYYYJJJ}.${HHMM}.*.*.hdf
        filet=$dir_cdf/${dataset}_${YYYYMMDD}_${HHMM}.nc.tmp
        fileo=$dir_cdf/${dataset}_${YYYYMMDD}_${HHMM}.nc


	#Check if the files exist and are readable (not corrupted)
        #  stat=1 : Exist (filei);   Exist + not corruputed (fileo)
        #  stat=0 : Does not exist
        #  stat=-1: Exist + IS corrupted (fileo) 
        [ -f $filei ] && {                                stati=1            ; } || stati=0
        [ -f $fileo ] && { ncinfo $fileo &> /dev/null  && stato=1 || stato=-1; } || stato=0

        if   [ $stato -eq  1 ] && ! [ $overwrite -eq 1 ]; then message="$fileo  already exists and is  readable (skip)"              ; perform_conversion=0;
        elif [ $stato -eq  1 ] &&   [ $overwrite -eq 1 ]; then message="$fileo  already exists and was readable (overwrite)"         ; perform_conversion=1;
        elif [ $stato -eq -1 ] &&   [ $stati     -eq 1 ]; then message="$fileo  already exists but is  CORRUPTED (overwrite)"        ; perform_conversion=1;
        elif [ $stato -eq  0 ] &&   [ $stati     -eq 1 ]; then message="$fileo  has been created"                                    ; perform_conversion=1;
        elif [ $stato -eq  0 ] &&   [ $stati     -eq 0 ]; then message="$fileo  cannot be created. Input file does not exist: $filei"; perform_conversion=0;
        fi

	
	# Performing the actual convertion + formating
        if   [ $perform_conversion -eq  1 ]; then
                [ -f $filet ] &&  rm $filet                                    # Remove filet (if already existing)
                [ -f $fileo ] &&  rm $fileo                                    # Remove fileo (if already existing)

		$h4tonccf_nc4         $filei $filet &> /dev/null               # Convert filei(hdf) --> fileo (nc)
		python $format_python $filet $fileo &> /dev/null  && rm $filet # Compress files and remove "duplicated" fields created by h4tonccf_nc4  
                
		# Check if the conversion have been performed correctly
                [ -f $fileo ] && { ncinfo $fileo &> /dev/null  && stato=1 || stato=-1; } || stato=0
                if [ $stato -ne  1 ]; then
                        message="$fileo  was not created correctly (file will be deleted)"
                        [ -f $fileo ] && rm $fileo
                fi
        fi
        
	echo $message


	# Date increment
        newdate=$(r.date $date +5M)
        date=${newdate:0:12}

done


