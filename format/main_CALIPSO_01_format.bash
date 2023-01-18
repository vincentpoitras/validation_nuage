# info: vincent.poitras@ec.gc.ca
#
# aim : [1] Convert hdf data to Netcdf4 (using h4tonccf_nc4)
#	[2] Fix the "valid_range attribute problem"
#           They are initialy specify by a string made of 2 number separated by a triple dot ...
#           This is replaced by a more standard array
#           If it is not done, other scripts will crash later
#
#	h4tonccf_nc4: http://hdfeos.org/software/h4cflib.php


###########################################################################
#                               Environement                              #
###########################################################################
module load python3/miniconda3 python3/python3 
source activate base_plus                      


###########################################################################
#  Input parameters                                                       #
###########################################################################
working_directory=$1
YYYY=$2
overwrite=$3

# Reset overwrite value: true --> 1, false --> 0 
[[ $overwrite == true ]] && overwrite=1 || overwrite=0


###########################################################################
#  Moving to the working directory                                        #
###########################################################################
cd $working_directory


###########################################################################
# Auxiliary script                                                        #
###########################################################################
h4tonccf_nc4=$working_directory/h4tonccf_nc4
format_attributes=$working_directory/aux_CALIPSO_format_attributes.py


###########################################################################
# Reading the configuration file                                          #
###########################################################################
# Reading the path for the
#       * Input  directory (contains original hdf files)                [dir_hdf]
#       * Output directory (will contain newly converted NetCDF files ) [dir_cdf]

config='../config.yml'
args_hdf="'$config', 'CALIPSO  hdf'"
args_cdf="'$config', 'CALIPSO  NetCDF'"
dir_hdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_hdf);")
dir_cdf=$(python -c "import yamlmanip; yamlmanip.extract_value($args_cdf);")


###########################################################################
# I/O directories                                                         #
###########################################################################
# Complete path with year subdirectory
dir_hdf=$dir_hdf/$YYYY
dir_cdf=$dir_cdf/$YYYY

# Create the output directory (if not existing)
[ -d $dir_cdf ] || mkdir -p $dir_cdf

# Check if I/O directories exists
[ -d $dir_hdf ] || { echo "[ERROR] Input  directory $dir_hdf should exist and does not. Exit" exit; }
[ -d $dir_cdf ] || { echo "[ERROR] Unabale to create output directory $dir_cdf. Exit" exit; }


###########################################################################
# Main loop                                                               #
###########################################################################
files=$(ls $dir_hdf | grep -F '.hdf')  # <-- Selec hdf-file in the input directory

for file in $files; do

	# Complete path to the files
	file_hdf=$dir_hdf/$file
	file_cdf=$dir_cdf/${file/.hdf/.nc}

	# Check if file_cdf is readable (already exist + not corrupted)
        [ -f $file_cdf ] && file_exist=1 || file_exist=0
        if [ $file_exist -eq 1 ]; then
        	ncinfo $file_cdf &> /dev/null && file_is_readable=1 || file_is_readable=0
        else
        	file_is_readable=0
        fi

	# Create the file (if requiered)
        if [ $file_is_readable -eq 0 ] || [ $overwrite -eq 1 ]; then

		# STEP 1: Remove the output file (if already existing)
        	[ -f $file_cdf ] && rm $file_cdf

		# STEP 2: Convert the file (hdf --> NetCDF4)
		$h4tonccf_nc4 $file_hdf $file_cdf &> /dev/null 

		# STEP 3: Fix the attributes
		python $format_attributes $file_cdf 
        	
		echo $file_cdf was created
	else
		 echo "$file_cdf already exists and is not corrupted (overwite=false)"
	fi
done	


