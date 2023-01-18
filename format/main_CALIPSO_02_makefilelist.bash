# info: vincent.poitras@ec.gc.ca
#
# Wrapper to launch the python script aux_CALIPSO_check_if_track_is_inside.py
# This python scripts:
# 	Check all files in the NETCDF directory to verify whether the satellite trajectory pass trough the domain
# 	A list of the relevant file (with the satellite passing over the domain) is produced


###########################################################################
#                               Environnement                             #
###########################################################################
module load python3/miniconda3 python3/python3 >& /dev/null
source activate base_plus                      >& /dev/null


###########################################################################
#  Input parameters                                                       #
###########################################################################
working_directory=$1
YYYY=$2
config=$working_directory/../config.yml


###########################################################################
#  Moving to the working directory                                        #
###########################################################################
cd $working_directory


###########################################################################
# Auxiliary script                                                        #
###########################################################################
check_if_track_is_inside=$working_directory/aux_CALIPSO_check_if_track_is_inside.py


###########################################################################
#                           Executing the python script                   #
###########################################################################
python $check_if_track_is_inside $config $YYYY


