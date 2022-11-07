#!/bin/bash
########################################################################################################
# AIM   : Download GEM files of a given year stored on narval 
# To download step0       : ./GEM_download.bash step0
# To download a whole year: ./GEM_download.bash 2014
# NOTE : Except for step0, it is strongly adviced to perform the download through the scheduler, e.g.
#        YYYY=2014; soumet GEM_download.bash -args $YYYY -jn GEM_download_${YYYY} -t 17280'
########################################################################################################

# Input parameter (specified during the submission)
YYYY=$1

if [ $# -eq 0 ]; then
	echo '[ERROR] Input parameter for year (YYYY) must be specified'
	echo '[ERROR] Examples:'
        echo '[ERROR]    Interactive: ./GEM_download.bash 2014'
	echo '[ERROR]    Scheduler  : YYYY=2014; soumet GEM_download.bash -args $YYYY -jn GEM_download_${YYYY} -t 17280'
	echo '[ERROR] Exit'
	exit
fi

# Source (on narval) and destination (on pampa) (edit these paths if necessary)
src=/home/poitras/projects/rrg-laprise/poitras/gem/Output/GEM5/COSP2/Cascades_CORDEX/CLASS/COSP2_NAM-11m_ERA5_GEM5_CLASS_NEWVEG_newP3-SCPF_SN_Lakes/Samples/*${YYYY}*
dst=/pampa/poitras/DATA/GEM5/Samples/.

# Download
rsync -rLtv --exclude="Restarts" --exclude="Pilots" poitras@narval.computecanada.ca:$src $dst
