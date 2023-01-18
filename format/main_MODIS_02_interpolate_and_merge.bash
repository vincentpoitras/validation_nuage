###########################################################################
#  Environnement                                                          #
###########################################################################
module load utils/cdo                           &> /dev/null
module load python3/miniconda3 python3/python3  &> /dev/null
source activate base_plus                       &> /dev/null


###########################################################################
#  Input parameters                                                       #
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
#  Configuration file /  directories paths                                #
###########################################################################
config=$working_directory/../config.yml

# Read configuration file
args_cdf="'$config', 'MODIS NetCDF'"     # For MODIS I/O data
args_gem="'$config', 'GEM5  NetCDF'"     # For a "source file" for the remapping (target_domain)
args_dom="'$config', 'domain'"           # "Label" in the path for the remapped data
dir_cdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_cdf);")
dir_gem=$(python -c "import yamlmanip; yamlmanip.extract_value($args_gem);")
domain=$( python -c "import yamlmanip; yamlmanip.extract_value($args_dom);")


# Replace the template MXD06_L2 by MOD06_L2 or MYD06_L2
dir_cdf=${dir_cdf/MXD06_L2/$dataset}

# Input and output directory
diri=$dir_cdf/original
diro=$dir_cdf/$domain

[ -d $diro ] || mkdir -p $diro


# "Source file" for the remapping (any file in the gem duirectory is ok)
target_domain=($(ls $dir_gem/*/dm*.nc))



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
#                                  Main loops                             #
###########################################################################
# Loop over date range (datei..datef) with 1-hour increment
# Subloop over time range (hour-30min .. hour+25 min) with 5-min increment
# Example:
#	[2014-01-05T12:00]: 2014-01-05T11:30 2014-01-05T11:35 ... 2014-01-05T12:20 2014-01-05T12:25
#       [2014-01-05T13:00]: 2014-01-05T12:30 2014-01-05T12:35 ... 2014-01-05T13:20 2014-01-05T13:25
#       [2014-01-05T14:00]: 2014-01-05T13:30 2014-01-05T13:35 ... 2014-01-05T14:20 2014-01-05T14:25
#       ...
date=$datei
while [ $date -le $datef ]; do

	YYYY=${date:0:4}
        YYYYMMDD=${date:0:8}
        HHMM=${date:8:4}
	output_file=$diro/$YYYY/MXD06_L2_${YYYYMMDD}_${HHMM}.nc
        output_file=${output_file/MXD06_L2/$dataset}	
	missing_timestep=0 # If any of the 6 5-min files ismissing, this will be set to 1 to print a warning
	echo $output_file
	cdo -info $output_file &> /dev/null && file_is_readable=1 || file_is_readable=0 # 0 --> file don't exist OR exist but corrupted
	if [ $overwrite -eq 1 ] || [ $file_is_readable -eq 0 ] ; then
		subhour_datei=$(r.date $date -30M)  #eg date = 2014-01-05T12:00 --> initial subhour date = 2014-01-05T11:30
        	subhour_datef=$(r.date $date +25M)  #eg date = 2014-01-05T12:00 --> final   subhour date = 2014-01-05T12:25
        	subhour_datei=${subhour_datei:0:12}
		subhour_datef=${subhour_datef:0:12}
        	subhour_date=$subhour_datei

		files_to_merge=''  # List (constructed in the loop) of temporary files (after interpolation) to merge
		while [ $subhour_date -le $subhour_datef ]; do
		
			# subhour_date time variables
			subhour_YYYY=${subhour_date:0:4}    # subhour_YYYY != YYYY for the 1st steps of YYYY01 
                	subhour_YYYYMMDD=${subhour_date:0:8}
                	subhour_HHMM=${subhour_date:8:4}

			# Subhour input and temporary files (after interpolation, before merging)
			subhour_output_tmp=$diro/$subhour_YYYY/tmp
			[ -d $subhour_output_tmp ] || mkdir -p $subhour_output_tmp
                	subhour_filei=$diri/$subhour_YYYY/${dataset}_${subhour_YYYYMMDD}_${subhour_HHMM}.nc
                	subhour_filet=$subhour_output_tmp/${dataset}_${subhour_YYYYMMDD}_${subhour_HHMM}.nc.tmp
                        
			# Remove the temporary file (if subhour_filet already exist)
			[ -f $subhour_filet ] && rm $subhour_filet

			# Remapping the fields (if subhour_filei exist)
                	if [ -f $subhour_filei ]; then
                		cdo -S remapbil,$target_domain $subhour_filei $subhour_filet &> /dev/null
                        	files_to_merge="$files_to_merge $subhour_filet"
				subhour_filei_exist=1
			else
				#echo "[Warning] $subhour_filei should exist and does not."
				subhour_filei_exist=0
				missing_timestep=1		
		
                	fi
			echo "   $subhour_filei $subhour_filei_exist"

			# Subhour_date increment
        		newdate=$(r.date $subhour_date +5M)
        		subhour_date=${newdate:0:12}
		done

	
		if [ -z $files_to_merge ]; then
			echo -e "[WARNING] [WARNING] Missing timesteps (ALL). $output_file was not created\n"
		else
			# Merging 5-min interpolated files into a single 1-hour file (hh-1:30,35,40,45,50,55, hh:00,05,10,15,20,25)	
			message=$(python aux_MODIS_merge_subhour_files.py "$output_file $files_to_merge")
			[ $missing_timestep -eq 1 ] && warning=" [WARNING] Missing timestep(s). " || warning=""
			str1="Created"
        		str2="Created + deleted (no data inside the domain)"
			if [[ "$message" == "$str1" ]] || [[ "$message" == "$str2" ]]; then
	       			echo -e "$warning $output_file $message\n"
        		else
 	       			echo "[ERROR] A problem occured when treating $output_file."
	       			echo "[ERROR] Exit"
	      			exit
			fi	       
			rm $files_to_merge
		fi
	else
		echo -e "$output_file already exist (skip) \n"
 	fi


        # Date increment
        newdate=$(r.date $date +1H)
        date=${newdate:0:12}

done

