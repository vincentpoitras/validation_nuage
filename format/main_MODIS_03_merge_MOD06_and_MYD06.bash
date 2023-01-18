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
overwrite=$3

# Reset overwrite value: true --> 1, false --> 0 
[[ $overwrite == true ]] && overwrite=1 || overwrite=0



###########################################################################
#                         Scripts called in the main loop                 #
###########################################################################
# When a MOD adn MYD files exist for the same time step, MCD is created
# by averaging them
average_two_files=$working_directory/aux_MODIS_average_two_files.py



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
date=$datei
a=0
while [ $date -le $datef ]; do
	YYYY=${date:0:4}
        YYYYMMDD=${date:0:8}
        HHMM=${date:8:4}

	file_template=$dir_cdf/$domain/$YYYY/MXD06_L2_${YYYYMMDD}_${HHMM}.nc
	file_MOD=${file_template//MXD06_L2/MOD06_L2}
	file_MYD=${file_template//MXD06_L2/MYD06_L2}
	file_MCD=${file_template//MXD06_L2/MCD06_L2}

	# Create output output directory (if not already existing)
	output_directory=${file_MCD%/*}
	[ -d $output_directory ] || mkdir -p $output_directory

	# Monitoring/debug: 1 file exist, 0 file does not exist
	[ -f $file_MOD ] && echo $file_MOD 1 || echo $file_MOD 0
	[ -f $file_MYD ] && echo $file_MYD 1 || echo $file_MYD 0


	# Check if the output_file is readable (exist + not corrupted)
	cdo -info $file_MCD &> /dev/null && file_is_readable=1 || file_is_readable=0

	# Check if the file is a symlink (saferto redo it, in case MYD or MOD was missing when the link was created, but it is now available)
	[ -L $file_MCD ] && file_is_symlink=1 || file_is_symlink=0
	

	if [ $overwrite -eq 1 ] || [ $file_is_readable -eq 0 ] || [ $file_is_symlink -eq 1 ]; then
		if   [ -f $file_MOD ] && [ -f $file_MYD ]; then 
                	python $average_two_files $file_MOD $file_MYD $file_MCD &> /dev/null
                	echo $file_MCD was created merging MOD06_L2 and MYD06_L2 data

        	elif [ -f $file_MOD ]                    ; then
	        	ln -sf $file_MOD $file_MCD
			echo $file_MCD was created as a symlink to MOD06_L2 file
        	elif [ -f $file_MYD ]                    ; then
			ln -sf $file_MYD $file_MCD
			echo $file_MCD was created as a symlink to MYD06_L2 file
        	else
                	echo "$file_MCD was not created (there is no data inside the domain)"
        	fi
	else
		echo $file_MCD already exists, is readable and not a symlink [overwrite=false]
	fi
        echo


        # Date increment
        newdate=$(r.date $date +1H)
        date=${newdate:0:12}

done


