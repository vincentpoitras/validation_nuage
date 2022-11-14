#!/bin/bash

# Le script python fstd2nc est utilisé pour convertir les fichier fst --> NetCDF
#
# Référence: https://pypi.org/project/fstd2nc
#
#
#
# Comment lancé le script
# 	Interactif : ./GEM5_fstd2nc.bash 201401
# 	Ordonnaceur: YYYYMM=201401; soumet $(pwd)/GEM5_fstd2nc.bash -args $YYYYMM -jn format_GEM5_${YYYYMM} -t 43200
#
# Note:
#	[1] Pour formater le pas de temps "0" (qui peut contenir des valeurs initiales, mais surtout des champs geophysiques statiques)
#           il suffit de mettre en argument step0: ./GEM5_fstd2nc.bash step0
#       [2] Si on relance le script, les fichiers de sortie vont simplement être écrasés       
#	[3] Le script python fstd2nc est utilisé au lieu du plus conventionnel cdf2rpn car ce dernier
#  	    ne garde pas les coefficient de pression a et b (p=a+bLOG(ps/pref)). Ceux-ci sont nécessaires
#           pour calculer les niveaux de pression.


# Paramètres  passés au scripts
YYYYMM=$1


DIRI=/pampa/poitras/DATA/GEM5/Samples
DIRO=/pampa/poitras/DATA/GEM5/Samples_NetCDF

[ -d $DIRO ] || mkdir -p $DIRO


module load python3/miniconda3 python3/python3 python3/python-rpn >& /dev/null
source activate base_plus                                         >& /dev/null

dirs=$(ls $DIRI)
for dir in $dirs; do
	echo $dir
	if [[ $dir == *"$YYYYMM"* ]]; then
		diri=$DIRI/$dir
		diro=$DIRO/$dir
		[ ! -f $diro ] && mkdir -p $diro
		files=$(ls $diri)
		for file in $files; do
        		filei=$diri/${file}
        		fileo=$diro/${file}.nc
	        	[ -f $fileo ] && rm $fileo	
			python -m  fstd2nc --nc-format NETCDF4 --zlib --keep-LA-LO $filei $fileo >& /dev/null
			echo $fileo
     		done
	fi        
done






