import matplotlib.pyplot as     plt
import numpy             as     np
import pandas            as     pd
import yaml
import sys
import os
import netCDF4
import warnings

from aux_CALIPSO         import extract_domain_coord
from aux_CALIPSO         import extract_satellite_track
from aux_grid_projection import convert_latlon_to_domain_indices
warnings.filterwarnings("ignore")


#################################################################################################################
### FUNCTIONS ###################################################################################################
#################################################################################################################
def create_dataframe(dirlist, YYYYMM):
    ''' Create a dataframe containg only the files of YYYYMM '''
    YYYY =     str(YYYYMM[0:4])
    MM   = int(str(YYYYMM[4:6]))

    filelist   = dirlist + '/' + YYYY + '.txt'
    df         = pd.read_csv(filelist,delimiter='\s+', header=None)
    df.columns = ['file', 'ndata', 'ti', 'tf', 'date', 'MM', 'date_gem', 't_gem']
    df         = df[   np.isin(df['MM'], MM)  ].reset_index(drop=True)
    return df



def convert_calipso_data_in_2D(ncfile, varname, domain, coord_domain, dim):

    # Extract the part of the track that is INSIDE the domain
    track = extract_satellite_track(ncfile, coord_domain, showtrack=False)


    indices = convert_latlon_to_domain_indices(track, domain)

    ds      = netCDF4.Dataset(ncfile,'r')
    data    = ds[varname][track['index']]

    data_sum  = np.ones(dim) * 0
    data_n    = np.ones(dim) * 0
    for i in range(len(indices['i'])):
        I = indices['i'][i]
        J = indices['j'][i]
        data_sum[I, J] = data_sum[I, J] + data[i]
        data_n[  I, J] = data_n[  I, J] + 1
    return data_sum/data_n


def create_outputfile(ncfileo, ncfile_template, monthly_data_sum_CALIPSO, monthly_data_sum_MODIS, monthly_data_n):
    nco = netCDF4.Dataset(ncfileo        , 'w')
    nct = netCDF4.Dataset(ncfile_template, 'r')

    # Copying global attributes
    nco.setncatts(nct.__dict__)

    # Creating dimensions
    dimnames = [ dim for dim in nct.dimensions ]
    for dimname in dimnames:
        #print(dimname)
        dimension = nct.dimensions[dimname]
        nco.createDimension(dimname, (len(dimension) if not dimension.isunlimited() else None))
    
    # Creating + copying 'old' variables
    varnames = [ var for var in nct.variables ]
    for varname in varnames:
        if varname in [ 'lon', 'lat', 'rlon', 'rlat', 'rotated_pole' ]:
            variable = nct[varname]
            x = nco.createVariable(varname, variable.datatype, variable.dimensions, zlib=True, complevel=4)
            nco[varname].setncatts(variable.__dict__)
            nco[varname][:] = nct[varname][:]

    # Creating + copying 'new' variables
    variable = nct['lon']
    for varname in monthly_data_n:
        varname_MODIS   = varname + '_sum_MODIS'
        varname_CALIPSO = varname + '_sum_CALIPSO'
        varname_n       = varname + '_n'
        x = nco.createVariable(varname_MODIS  , variable.datatype, variable.dimensions, zlib=True, complevel=4)
        x = nco.createVariable(varname_CALIPSO, variable.datatype, variable.dimensions, zlib=True, complevel=4)
        x = nco.createVariable(varname_n      , variable.datatype, variable.dimensions, zlib=True, complevel=4)
        nco[varname_MODIS  ][:] = monthly_data_sum_MODIS  [varname][:]
        nco[varname_CALIPSO][:] = monthly_data_sum_CALIPSO[varname][:]
        nco[varname_n      ][:] = monthly_data_n          [varname][:]




#################################################################################################################
### MAIN ########################################################################################################
#################################################################################################################


#########################################################################
# Input arguments                                                       #
#########################################################################
working_directory =     sys.argv[1]
YYYYMM            =     sys.argv[2]
dataset           =     sys.argv[3]
layerdef_MODIS    =     sys.argv[4]
layerdef_CALIPSO  =     sys.argv[5]
overwrite         =     sys.argv[6].lower()

YYYY = int(str(YYYYMM[0:4]))
MM   = int(str(YYYYMM[4:6]))


#########################################################################
# Configuration file (yml)                                              #
#########################################################################
yml_file = working_directory + '/../config.yml'
stream = open(yml_file,'r')
config = yaml.safe_load(stream)

domain          = config['domain'        ]
dirlist_CALIPSO = config['CALIPSO'       ]['list'  ]                             + '/' + domain                          
dirlist_MODIS   = config['MODIS'         ]['list'  ].replace('MXD06_L2',dataset) + '/' + domain
dirout          = config['CALIPSOvsMODIS']['NetCDF'] + '/CALIPSO_' + layerdef_CALIPSO + '_' + dataset + '_' + layerdef_MODIS  + '/' + domain

if not os.path.exists(dirout): os.makedirs(dirout)
#########################################################################
# Selecting files to treat                                              #
#########################################################################

''' Create a dataframe containing YYYYMM files '''
df_CALIPSO = create_dataframe(dirlist_CALIPSO, YYYYMM)
df_MODIS   = create_dataframe(dirlist_MODIS  , YYYYMM)



''' Selecting files with common date (and hour) '''
df_MODIS   = df_MODIS  [   np.isin(df_MODIS  ['date'], df_CALIPSO['date'])  ].reset_index(drop=True)
df_CALIPSO = df_CALIPSO[   np.isin(df_CALIPSO['date'], df_MODIS  ['date'])  ].reset_index(drop=True)


#########################################################################
# Loop over all files                                                   #
#########################################################################
'''
Loop 1: Over all files of YYYYMM (selected in the previous step)
Loop 2: Over all layers
        t: Total cloud cover 
        h: High  cloud cover
        m: Mid   cloud cover
        l: Low   cloud cover

NOTE: In loop 1, for a given date, the trajectory might be split into 2 CALIPSO files: 
      D(day) and Z (night). For this reason we are doing the loop over CALIPSO file
      and find the correspondig MODIS file (with the same date).
'''

# Empty dictionnaries (will be filled with data from each levels ("varnames"))
monthly_data_sum_CALIPSO = {}
monthly_data_sum_MODIS   = {}
monthly_data_n           = {}


for iCAL in range(len(df_CALIPSO['file'])):
    iMOD = df_MODIS.index[df_MODIS['date'] == df_CALIPSO['date'][iCAL]][0]

    
    ncfile_MODIS   = df_MODIS  ['file'][iMOD].replace('NetCDF','NetCDF_LowMidHigh').replace(domain,domain+'/'+layerdef_MODIS)  # Mal codé ici (à modifier ...) Compliqué, en plus  
    ncfile_CALIPSO = df_CALIPSO['file'][iCAL].replace('NetCDF','NetCDF_LowMidHigh/'+layerdef_CALIPSO)  # Si qqn enlève NetCDF du chemin dans le fichier yaml, tout va planter...
    

    print(df_CALIPSO['date'][iCAL], ncfile_CALIPSO)
    print(df_MODIS  ['date'][iMOD], ncfile_MODIS  )


    # Extract the domain coordinates from the 2D ncfile (MODIS). This will be used to select the portion of CALIPSO track that is inside the domain
    if iCAL == 0:  domain_coord  = extract_domain_coord(ncfile_MODIS)
        

    ds_CALIPSO = netCDF4.Dataset(ncfile_CALIPSO,'r')
    ds_MODIS   = netCDF4.Dataset(ncfile_MODIS  ,'r')
    
    for varname in ['Tot_cloud_cover', 'High_cloud_cover', 'Mid_cloud_cover', 'Low_cloud_cover' ]:

        # MODIS -- Read varname in dataset 
        data_MODIS    = np.array(ds_MODIS[varname][:])
        missing_value = ds_MODIS[varname].getncattr('missing_value') 
        mask_MODIS    = np.where(data_MODIS == missing_value, 0, 1)
        data_MODIS    = data_MODIS * mask_MODIS
        
        # CALIPSO -- Read varname in dataset + fomrat 1D --> 2D
        dim          = data_MODIS.shape
        data_CALIPSO = convert_calipso_data_in_2D(ncfile_CALIPSO, varname, domain, domain_coord, dim)
        mask_CALIPSO = np.where(np.isnan(data_CALIPSO), 0, 1           )
        data_CALIPSO = np.where(np.isnan(data_CALIPSO), 0, data_CALIPSO)

        
        # Masking non-common data
        mask         = mask_MODIS   * mask_CALIPSO
        data_CALIPSO = data_CALIPSO * mask
        data_MODIS   = data_MODIS   * mask
       
    
        # Initialisation of monthly value 
        if iCAL == 0:
            monthly_data_sum_CALIPSO[varname] = 0*data_CALIPSO
            monthly_data_sum_MODIS  [varname] = 0*data_MODIS
            monthly_data_n          [varname] = 0*mask
            print(varname)

        
        # Monthly values
        monthly_data_sum_CALIPSO[varname] += data_CALIPSO
        monthly_data_sum_MODIS  [varname] += data_MODIS
        monthly_data_n          [varname] += mask 


        #plt.imshow(data_MODIS)
        #plt.show()
        
    print('')

# Create outputfile
ncfile_template = ncfile_MODIS 
ncfileo         = dirout + '/' + YYYYMM + '.nc' 

create_outputfile(ncfileo, ncfile_template, monthly_data_sum_CALIPSO, monthly_data_sum_MODIS, monthly_data_n)
print(ncfileo)


exit()












