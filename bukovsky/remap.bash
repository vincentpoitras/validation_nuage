#!/bin/bash



###########################################################################
#                               Environnement                             #
###########################################################################
module load utils/cdo                           &> /dev/null
module load python3/miniconda3 python3/python3  &> /dev/null
source activate base_plus                       &> /dev/null





###########################################################################
#                               Configuration file                        #
###########################################################################
# Read configuration file
config=../config.yml
args_GEM5="'$config', 'GEM5 NetCDF'"
args_bukovsky="'$config', 'bukovsky'"
ln -sf ../yamlmanip.py

dir_GEM5=$(      python -c "import yamlmanip; yamlmanip.extract_value($args_GEM5   );")
dir_bukovsky=$( python -c "import yamlmanip; yamlmanip.extract_value($args_bukovsky);")



###########################################################################
#                               REMAP                                     #
###########################################################################


# I/O directories
diri=$dir_bukovsky/original
diro=$dir_bukovsky/remap
[ -d $diro ] || mkdir -p $dir

# target file
target=$dir_GEM5/*step0/pm*


files=$(ls $diri)
for file in $files; do	
	filei=$diri/$file
	fileo=$diro/$file
	cdo -S remapnn,$target $filei $fileo #&> /dev/null
	echo $fileo
done





###########################################################################
#                               SEALAND MASK                              #
###########################################################################
# Sealand mask
sealandmask=$dir_bukovsky/remap/sealandmask.nc
cdo -S expr,'mask=MG>0' -selvar,MG $target $sealandmask





files=$(ls $diri)
for file in $files; do
        fileo=$diro/$file
        filet=$diro/${file}.tmp
	if [[ $file == *ic.nc* ]] || [[ $file == Hudson.nc ]] || [[ $file == GreatLakes.nc ]]; then
		cdo -S setctomiss,0 -mul -mulc,-1 -addc,-1 $sealandmask $fileo $filet && mv $filet $fileo
	else
		cdo -S setctomiss,0 -mul $sealandmask $fileo $filet && mv $filet $fileo 

	fi
        #cdo -S remapnn,$target $filei $fileo #&> /dev/null
        echo $fileo
done

