# info: vincent.poitras@ec.gc.ca
#
# Ce script convertit tous les fichiers fst d'un répertoir mensuel en fichier NetCDF
#
# Le script python fstd2nc est utilisé pour la conversion fst --> NetCDF
# Référence: https://pypi.org/project/fstd2nc
#
# La conversion va avoir lieu si une des 3 conditions suivantes est remplies
#	* Le fichier n'existe pas
#	* Le fichier existe mais est corrompu
#       * overwrite = true
#
# L'argument d'entrée YYYYMM, peut prendre comme valeur
#	* step0
#	* Une date à 6 chiffre (année + mois)

###########################################################################
#                               Environement                              #
###########################################################################
module load python3/miniconda3 python3/python3 python3/python-rpn >& /dev/null  # python
source activate base_plus                                         >& /dev/null  # python + ncinfo


###########################################################################
#  Input parameters                                                       #
###########################################################################
working_directory=$1
YYYYMM=$2
overwrite=$3

# Reset overwrite value: true --> 1, false --> 0 
[[ $overwrite == true ]] && overwrite=1 || overwrite=0


###########################################################################
#  Moving to the working directory                                        #
###########################################################################
cd $working_directory


###########################################################################
# Reading the configuration file                                          #
###########################################################################
# Reading the path for the
# 	* Input  directory (contains original fst files)                [DIRI]
#	* Output directory (will contain newly converted NetCDF files ) [DIRO]

config='../config.yml'
args_DIRI="'$config', 'GEM5  fst'"
args_DIRO="'$config', 'GEM5  NetCDF'"     
DIRI=$(python -c "import yamlmanip; yamlmanip.extract_value($args_DIRI);")
DIRO=$(python -c "import yamlmanip; yamlmanip.extract_value($args_DIRO);")


###########################################################################
# I/O directories                                                         #
###########################################################################

# Create the output directory (if not existing)
[ -d $DIRO ] || mkdir -p $DIRO

# Check if I/O directories exists
[ -d $DIRI ] || { echo "[ERROR] Input  directory $DIRI should exist and does not. Exit" exit; }
[ -d $DIRO ] || { echo "[ERROR] Unabale to create output directory $DIRO. Exit" exit; } 



###########################################################################
# Main loop over the content of the desired monthly directory (YYYYMM)    #
###########################################################################

dirs=$(ls $DIRI)
for dir in $dirs; do                                  # <-- Loop over all subdirectories, BUT
	if [[ $dir == *"$YYYYMM"* ]]; then            # <-- We are treating only the directory containing the desired YYYYMM

		# Desired I/O subdirectories
		diri=$DIRI/$dir
		diro=$DIRO/$dir
		[ ! -f $diro ] && mkdir -p $diro

		# Loop over all files contained in the desired subdirectories
		files=$(ls $diri)
		for file in $files; do
        		filei=$diri/${file}
        		fileo=$diro/${file}.nc
			
			# Check if file is readable (elready xist + not corrupted)
			[ -f $fileo ] && file_exist=1 || file_exist=0
			if [ $file_exist -eq 1 ]; then
				ncinfo $fileo &> /dev/null && file_is_readable=1 || file_is_readable=0
			else
				file_is_readable=0
			fi
			
			if [ $file_is_readable -eq 0 ] || [ $overwrite -eq 1 ]; then
	        		[ -f $fileo ] && rm $fileo	
				python -m  fstd2nc --nc-format NETCDF4 --zlib --keep-LA-LO $filei $fileo >& /dev/null
				echo $fileo was created
			else
				echo "$fileo exist and is not corrupted (overwite=false)"
			fi
     		done
	fi        
done






