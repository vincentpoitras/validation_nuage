#!/bin/bash

#########################################################################################################################################################################################
# DATASET : MOD06_L2 (Terra) and MYD06_L2 (aqua)
# INFO    : https://atmosphere-imager.gsfc.nasa.gov/products/cloud
# DOWNLOAD: https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61
#
# How to launch this script
#	Scheduler  : dataset=MYD06_L2; YYYY=2015; dddi=334; dddf=365; soumet MODIS_download.bash -args $dataset $YYYY $dddi $dddf -jn ${dataset}_download_${YYYY}_${dddi}-${dddf} -t 86400 
#       Interactive: ./MODIS_download.bash MYD06_L2 2015 334 365 
#
# Notes
#	[1] Download estimate time (for 3 month): ~2 weeks
#       [2] The downloading is very inefficient since we should dowload individualy each file
#           There is a file each 5 min --> 288 / day
#           wget must (re)*connect several time before to complete succesfuly a download
#           For future usage, we may explore wheter lftp is more efficient (it would allow to dowload an entire "folder" (each day ~ a folder with 288 files)
#       [3] The authorization key maybe generated on the website

##########################################################################################################################################################################################


# Input parameters
dataset=$1    # MOD06_L2 (Terra) or MYD06_L2
YYYY=$2       # 4-digit year
dddi=$3       # first day of the range (1-366) DON'T add leading 0
dddf=$4       # last  day of the range (1-366) DON'T add leading 0

#Output directory (EDIT IF NECESSARY)
output_directory=/pampa/poitras/DATA/MODIS/$dataset/hdf/$YYYY

# Authorization key may be generated if you log to the websitesite (EDIT IF NECESSARY)
url=https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/$dataset/YYYY/DDD/
authorization_key=dmluY2VudHBvaXRyYXM6Y0c5cGRISmhjeTUyYVc1alpXNTBRSFZ4WVcwdVkyRT06MTY1MTc3MDM3ODo0MDZjNGM3Yzc3MzY4OWYyYmFjYzk3ZjM2NjJlMTQ2MjE2ZWVmMmU5 



######################################################################################################################################################
# Checking input parameters
if [ $# -ne 4 ]; then
        echo '[ERROR] Incorrect number of arguments has been specified'
	echo '[ERROR] Examples (to download Aqua data for the whole month of December 2015):'
        echo '[ERROR]    Interactive: ./MODIS_download.bash MYD06_L2 2015 334 365'
        echo '[ERROR]    Scheduler  : dataset=MYD06_L2; YYYY=2015; dddi=334; dddf=365;' 
	echo '                        soumet MODIS_download.bash -args $dataset $YYYY $dddi $dddf -jn ${dataset}_download_${YYYY}_${dddi}-${dddf} -t 864000'
        echo '[ERROR] Exit'
        exit
fi

if [ $dddf -lt $dddi ]; then
	echo "[ERROR] $dddf < $dddi"
	echo '[ERROR] dddf must be larger or equal to dddi'
	echo '[ERROR] Exit'
	exit
fi

if [[ $dataset != "MOD06_L2" ]] && [[ $dataset != "MYD06_L2" ]]; then
	echo "[ERROR] dataset=$dataset"
	echo '[ERROR] dataset must be MOD06_L2 or MYD06_L2';
	echo '[ERROR] Exit'
	exit
fi



# Output directory
output_directory=/pampa/poitras/DATA/MODIS/$dataset/hdf/$YYYY
[ -d $output_directory ] || mkdir -p $output_directory


# Actual download
# A loop is performed over the day
# If we relaunch thsi script and have already 288/day, the day will be skipped
NDATA=288
for ddd in `seq $dddi $dddf`; do
	DDD=$(printf "%03d" $ddd)
	ndata=$(ls -l $output_directory/*A$YYYY$DDD* | wc -l ) || ndata=0
	echo $DDD $ndata
	if [ $ndata -lt $NDATA ]; then
		URL=${url/YYYY/$YYYY}
                URL=${URL/DDD/$DDD}
		wget -e robots=off -m -np -R .html,.tmp -nH --cut-dirs=6  $URL --header "Authorization: Bearer $authorization_key" -P $output_directory &> /dev/null	
	fi
done


 
