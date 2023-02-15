# info: poitras.vincent@uqam.ca
# date: 2022/02/18
# aim : convert gem output into cosp input
# Note: A part of this script is adapted from previous work made by Zhipeng Qu.
#       Discussions from our "COSP group" (Faisal Boudala, Mélissa Cholette, Jason Milbrant,Vincent Poitras, Zhipeng Qu)
#       also help to develop this script.

import numpy             as     np
import matplotlib.pyplot as     plt
import pandas            as     pd
from   datetime          import datetime
from dateutil.relativedelta import relativedelta
import yaml
import glob
import netCDF4
import os

from   netcdf4_extra import netcdf4_extract_fields_and_attributes
from   aux_COSPIN_01 import add_time_dimension
from   aux_COSPIN_01 import format_time_for_sunlit
from   aux_COSPIN_01 import sunlit
from   aux_COSPIN_01 import radius_from_cldoppro
from   aux_COSPIN_01 import radius_from_mp_my2
from   aux_COSPIN_01 import cloud_optical_depth_and_emmissivity



#########################################################################
# Input arguments                                                       #
#########################################################################
working_directory =     sys.argv[1]
YYYYMM            =     sys.argv[2]
dataset           =     sys.argv[3]
overwrite         =     sys.argv[4].lower()


#########################################################################
# Configuration file (yml)                                              #
#########################################################################
yml_file = working_directory + '/../config.yml'
stream = open(yml_file,'r')
config = yaml.safe_load(stream)

domain          = config['domain']
dir_GEM5_NetCDF = config['GEM5' ]['NetCDF'] 
dir_COSPIN      = config['COSP2']['input' ]
if   'D06_L2'    in dataset: dir_list = config['MODIS']['list'].replace('MXD06_L2',dataset)
elif 'ALL_STEPS' != dataset: dir_list = config[dataset]['list']
elif 'ALL_STEPS' == dataset: dir_list = 'unset'



#########################################################################
# Dates                                                                 #
#########################################################################
# COSP2 files will be created only for the date between datei and datef
date_object_YYYYMM   = datetime.strptime(YYYYMM, "%Y%m")               
date_object_YYYYMMp1 = date_object_YYYYMM + relativedelta(months = 1)  
YYYYMMp1             = date_object_YYYYMMp1.strftime("%Y%m")           
YYYY                 = date_object_YYYYMM.strftime  ("%Y"  )
datei                = int(YYYYMM   + '010000')  # Adding day, hour and second 
datef                = int(YYYYMMp1 + '010000')  # Adding day, hour and second


#########################################################################
# I/O directories, files and file templates                             #
#########################################################################
output_directory = dir_COSPIN + '/' + str(YYYYMM)                              # Output directory 
file_list        = dir_list + '/' + domain + '/' + YYYY + '.txt' # List        # File containing a list of the timestep with observation 
ncfile_pm0       = glob.glob(dir_GEM5_NetCDF + "/*step0/pm*_00000000p.nc")[0]  # pm file form step 0 (contains MG)
ncfile_dm0       = glob.glob(dir_GEM5_NetCDF + "/*step0/dm*_00000000p.nc")[0]  # dm file from step 0 (contains ME)
pm_template      =           dir_GEM5_NetCDF + "/*YYYYMM/pm*_YYYYMMDDd.nc"     # pm file for other steps (see varlist_pm below)
dm_template      =           dir_GEM5_NetCDF + "/*YYYYMM/dm*_YYYYMMDDd.nc"     # dm file for other steps (see varlist_dm below)

if not os.path.exists(output_directory): os.makedirs(output_directory)






#########################################################################
# Selecting the steps to treat                                          #
#########################################################################
'''
The whole idea of this section is just to have a list of the timestep for which we want to create a COSP2 file.
    [1] Select timestep between datei and datef in the file
    [2] Remove duplicate timestep (if any) --> CALIPSO tracks are splited in a day file and a night file, and they may correspond to teh same date
    [3] If overwrite == false, timestep corresponding to an existing AND readable file will be removed
'''

# [1] Selecting timestep between datei and datef
df         = pd.read_csv(file_list,delimiter='\s+', header=None)
df.columns = ['ncfile', 'ndata', 'ti', 'tf', 'date', 'month', 'date_gem', 't_gem']
df         = df[ df['date'] >= datei].reset_index(drop=True)
df         = df[ df['date'] <= datef].reset_index(drop=True)


#if   'CAL_LID_L2_05kmCPro-Standard-V4' in file_list: df.columns = ['nc_CALIPSO', 'ndata', 'ti', 'tf', 'date', 'month', 'date_gem', 't_gem']
#elif 'MYD06_L2'                        in file_list: df.columns = ['nc_MYD06'  ,                      'date', 'month', 'date_gem', 't_gem']
#elif 'MCD06_L2'                        in file_list: df.columns = ['nc_MCD06'  ,                      'date', 'month', 'date_gem', 't_gem']

# [2] Remove the entry corresponding to the same date 
duplicate_date_indices = [] 
for i in range(len(df['date'])-1):
    if df['date'][i] == df['date'][i+1]:
        duplicate_date_indices.append(i+1)
df.drop(duplicate_date_indices, axis=0, inplace=True)
df = df.reset_index(drop=True)



# [3] Remove from the list file that are already existing (so they will no be overwritten)
#     Exception: corrupted files (unreadable) will be removed and created a second time
if overwrite == 'false':
    existing_file_indices = []
    for i in range(len(df['date_gem'])):
        cospfile = output_directory + '/' + str(df['date'][i]) + '.nc'
        try :
            f = netCDF4.Dataset(cospfile)
            existing_file_indices.append(i)
        except:
            if os.path.isfile(cospfile):
                os.remove(cospfile)

    df.drop(existing_file_indices, axis=0, inplace=True)
    df = df.reset_index(drop=True)


print(df)
print('')



#############################################################################################################################
#                                                     READING INPUT FILE                                                    #
#############################################################################################################################
#   Note: The script "netcdf4_extract_fields_and_attributes" is used to read data and attributes from the ncfiles
#         This scripts was developped for an other project and might be unnecessarily complicated here, but it work perfectly

#print('Reading input data')
 
varlist_pm0 = ['MG']
varlist_dm0 = ['ME']
varlist_pm  = ['FMP', 'FN', 'J8', 'QI_1', 'QI_2', 'QI_3', 'QI_4', 'QI_5', 'QI_6', 'REC', 'REI1', 'LWCI', 'IWCI', 'SS01']
varlist_dm  = ['HU', 'TT','MPQC','MPQR','MPNR', 'GZ', 'P0','leadtime', 'a_1', 'b_1', 'a_2', 'b_2', 'pref' ,'reftime','lon','lat','rlon','rlat' ]


for i in range(len(df['date_gem'])):

    print(df.loc[[i]])
    t_gem      =     df['t_gem'][i]
    YYYYMMDD   = str(df['date_gem'][i])
    YYYYMM     = YYYYMMDD[0:6]
    ncfile_pm = glob.glob(  pm_template.replace('YYYYMMDD',YYYYMMDD).replace('YYYYMM',YYYYMM)  )[0] 
    ncfile_dm = glob.glob(  dm_template.replace('YYYYMMDD',YYYYMMDD).replace('YYYYMM',YYYYMM)  )[0] 
    

    input_data       = {}; 
    input_attributes = {};
    netcdf4_extract_fields_and_attributes(varlist_pm0, ncfile_pm0, input_data, input_attributes); print(ncfile_pm0)
    netcdf4_extract_fields_and_attributes(varlist_dm0, ncfile_dm0, input_data, input_attributes); print(ncfile_dm0)
    netcdf4_extract_fields_and_attributes(varlist_pm , ncfile_pm , input_data, input_attributes); print(ncfile_pm)
    netcdf4_extract_fields_and_attributes(varlist_dm , ncfile_dm , input_data, input_attributes); print(ncfile_pm)


    # Extract dimension size
    XX = input_data['TT'].copy()
    if   len(XX.shape) == 3:        # [      vertical level, lat, lon]
        XX = XX [np.newaxis,:,:,:]  # [time, vertical level, lat, lon]

    ntime = XX.shape[0]
    nlev  = XX.shape[1]
    nlat  = XX.shape[2]
    nlon  = XX.shape[3]

    del XX

    # Adding a time dimension (for single step ncfile)
    #   If the NetCDF file contain only one time step (ntime == 1), there will be no time dimension in the input field
    #   We are adding it because the rest of the script is expecting to have one
    #        [                        ] --> [time,                         ] : time
    #        [                lat, lon] --> [time,                 lat, lon] : P0
    #        [ surfacei_type, lat, lon] --> [time,   surface_type, lat, lon] : J8
    #        [vertical_level, lat, lon] --> [time, vertical_level, lat, lon] : Other variables
    if ntime == 1:
        # variable such as lon, lat etc. are time independent, so they are remoevd from the list below
        varlist = list(set(varlist_pm + varlist_dm) - set(['a_1','b_1','a_2','b_2', 'pref' ,'reftime','lon','lat','rlon','rlat'])) 
        add_time_dimension(varlist,input_data)                                                            
        
    #Script was modified to treat only one time step at the time (because of memory problem)
    varlist = list(set(varlist_pm + varlist_dm) - set(['a_1','b_1','a_2','b_2','pref' ,'reftime','lon','lat','rlon','rlat']))
    ntime = 1

    for var in varlist:
        #print(var,input_data[var].shape) 
        input_data[var] = input_data[var][t_gem]
        #print(var,input_data[var].shape)
    add_time_dimension(varlist,input_data)
  
    #############################################################################################################################
    #                                         Beginning of the computation of output data                                       #
    #############################################################################################################################
    #print('Preparing output data')
    output_data       = {};


    #############################################################################################################################
    #                                         Miscalenous fields that can be directly copied                                    #
    #############################################################################################################################
    # 5 mixing ratio are also directly copied (see the corresponding section below)
    # Note on the lat/lon fields:
    #   As far I understand, only rttov is actually using lat/lon. Otherwise lat/lon is just used as label for the indices,
    #   so there is nothing wrong using a rotated grid with rlat/rlon
    #   But we still to use the "real" lat/lon field to
    #       [1] compute sunlit
    #       [2] use as reference to make sure that everything is correct

    output_data['orography'] = input_data['ME'  ];  ### Topography
    output_data['tca'      ] = input_data['FN'  ];  ### Total cloud fractions
    output_data['cca'      ] = input_data['FMP' ];  ### Implicit cloud fractions
    output_data['q_v'      ] = input_data['HU'  ];  ### Specifi humidity
    output_data['lon'      ] = input_data['rlon'];  ### rotated longitude
    output_data['lat'      ] = input_data['rlat'];  ### rotated latitude
    output_data['longitude'] = input_data['lon' ];  ### 2D longitude
    output_data['latitude' ] = input_data['lat' ];  ### 2D latitude

    input_data.pop('ME'  )
    input_data.pop('FN'  )
    input_data.pop('FMP' )
    input_data.pop('HU'  )
    input_data.pop('rlon')
    input_data.pop('rlat')
    input_data.pop('lon' )
    input_data.pop('lat' )



    #############################################################################################################################
    #                                                Full-level and half-level height                                           #
    #############################################################################################################################
    # Dimensions (multiple step): (time, vertical level, x, y)
    # GZ is given in Decametre
    # We use thermodynamic levels as full height
    # We use momentum      levels as half height
    # Note that the order is "inverted":
    #   nGZ-1 is the 1st level above the ground
    #   0     is the TOA    
    # momentum      levels (half): 1, 3, 5, ...,  nGZ-5, nGZ-3, nGZ-1
    # thermodynamic levels (full): 0, 1, 4, ...,  nGZ-6, nGZ-4, nGZ-2
    # There is no level nGZ (surface, hyb = 1) since this field is equivalent to the topography

    GZ  = 10 * input_data['GZ'] # Dm -> m
    nGZ = len(GZ[0,:,0,0])

    half_level_indices = range(1, nGZ  ,  2) # 1 to nGZ-1
    full_level_indices = range(0, nGZ-1,  2) # 0 to nGZ-2

    half_height = GZ[:,half_level_indices,:,:]
    full_height = GZ[:,full_level_indices,:,:]
    output_data['height']      = full_height;  ### Height_in_full_levels
    output_data['height_half'] = half_height;  ### Height_in_half_levels


    input_data.pop('GZ')
    del GZ, nGZ,  half_height 



    #############################################################################################################################
    #                                                Full-pressure and half-pressure level                                      #
    #############################################################################################################################
    # For half/full levels explanation, see the section on full-level and half-level height above  

    a_x    = 'a_1' if len(input_data['a_1']) > len(input_data['a_2']) else 'a_2'
    b_x    = 'b_1' if len(input_data['b_1']) > len(input_data['b_2']) else 'b_2'

    a    = input_data[ a_x  ]
    b    = input_data[ b_x  ]
    pref = input_data['pref']       # Reference pressure
    ps   = input_data['P0'  ] * 100 # Surface pressure [hPa --> Pa]

    p = np.zeros((ntime,2*nlev,nlat,nlon)) 
    for i in range(2*nlev):
        p[:,i,:,:]  =  np.exp(a[i]+b[i]*np.log(ps/pref))

    p     = p.astype(np.float32)
    phalf = p[:,half_level_indices,:,:]
    pfull = p[:,full_level_indices,:,:]

    output_data['pfull'] = pfull;  ### pressure_in_full_levels
    output_data['phalf'] = phalf;  ### pressure_in_half_levels

    del a, b, pref, ps, p, phalf 
    #print('\t pfull, phalf')


    #############################################################################################################################
    #                                                           Sunlit                                                          #
    #############################################################################################################################
    # We set daylight (sunlit=1) when solar zenith < 90
    lon     = output_data['longitude'] 
    lat     = output_data['latitude' ] 
    time    = input_data['leadtime'  ]
    reftime = input_attributes['reftime']['units'];

    formatted_time        = format_time_for_sunlit(reftime, time)
    output_data['sunlit'] =  sunlit(lon,lat,formatted_time); ### Daypoints 

    del lon, lat 
    #print('\t sunlit')


    #############################################################################################################################
    #                                                           Sea-land mask                                                   #
    #############################################################################################################################
    #   In gem. the sea-land mask varies between 0 (ony sea) and 1 (only land)
    #   COSP requieres a binary mask
    #   To be consistant with cldoppro_mp.F90, we do: mask <= 0.5 --> 0 (only sea), mask > 0.5 --> (only land)

    MG = input_data['MG']
    MG [ MG <= 0.5] = 0
    MG [ MG >  0.5] = 1 
    output_data['landmask'] = MG;  ### Sea-land mask

    del MG
    #print('\t landmask')


    #############################################################################################################################
    #                                                       Skin temperature                                                    #
    #############################################################################################################################
    # GEM output skin temperature over 7 surface fractions:
    # 0: soil, 1: glacier, 2: sea-water, 3: sea-ice, 4: aggregated, 5: urban, 6: lake
    # We are interested in the aggregated value (4)

    J8 = input_data['J8'][:,4,:,:];
    output_data['skt'] = J8;  ### Skin temperature

    del J8
    #print('\t skt')


    #############################################################################################################################
    #                                                         Air temperature                                                   #
    #############################################################################################################################
    #   Converting from celsius to kelvin

    T_abs = input_data['TT'] + 273.15;
    output_data['T_abs'] = T_abs; ### Temperature

    #print('\t T_abs')


    #############################################################################################################################
    #                                                         Mixing ratio                                                      #
    #############################################################################################################################
    # Mixing ratio 1: Data directly copied

    output_data['mr_lsliq' ] = input_data['MPQC'];  ### Mixing ratio: cloud-liquid (large scale)
    output_data['mr_lsrain'] = input_data['MPQR'];  ### Mixing ratio: precip-rain  (large scale)
    output_data['mr_ccliq' ] = input_data['LWCI'];  ### Mixing ratio: cloud-liquid (convective)  [GEM: PBL + 3 convec schemes]
    output_data['mr_ccice' ] = input_data['IWCI'];  ### Mixing ratio: cloud-ice    (convective)  [GEM: PBL + 3 convec schemes]

    # Mixing ratio 2: Decomposition of QI_X: --> cloud-ice  (large scale), precip-snow (large scale) and  precip-graupel (large scale)
    q1 = input_data['QI_1']  #[GEM: small ice crystals   ]
    q2 = input_data['QI_2']  #[GEM: unrimed snow crystals]
    q3 = input_data['QI_3']  #[GEM: lightly rimed snow   ]
    q4 = input_data['QI_4']  #[GEM: graupel              ]
    q5 = input_data['QI_5']  #[GEM: hail                 ]
    q6 = input_data['QI_6']  #[GEM: ice pellet           ]

    MP_CONFIG = 'MPB'
    if   MP_CONFIG == 'MPA':
        output_data['mr_lsice' ] = q1          ;  ### Mixing ratio: cloud-ice      (large scale)
        output_data['mr_lssnow'] = q2 + q3     ;  ### Mixing ratio: precip-snow    (large scale)
        output_data['mr_lsgrpl'] = q4 + q5 + q6;  ### Mixing ratio: precip-graupel (large scale)
    elif MP_CONFIG == 'MPB':
        output_data['mr_lsice' ] = q1 + q2     ;  ### Mixing ratio: cloud-ice      (large scale)
        output_data['mr_lssnow'] = q3          ;  ### Mixing ratio: precip-snow    (large scale)
        output_data['mr_lsgrpl'] = q4 + q5 + q6;  ### Mixing ratio: precip-graupel (large scale)
    elif MP_CONFIG == 'MPC':
        output_data['mr_lsice' ] = (q1 + q2 + q3)/2;  ### Mixing ratio: cloud-ice      (large scale)
        output_data['mr_lssnow'] = (q1 + q2 + q3)/2;  ### Mixing ratio: precip-snow    (large scale)
        output_data['mr_lsgrpl'] = q4 + q5 + q6    ;  ### Mixing ratio: precip-graupel (large scale)




    # Mixing ratio 3: precip-snow  (convective) and precip-rain  (convective) 
    #   We decided to let the convective_cloud_snow  empty for now
    #   Jason will provided a "receipe" for convective_cloud_rain, but untill we have it, we are leaving the field empty
    output_data['mr_ccsnow' ] = input_data['MPQC'] * 0;  ### Mixing ratio: precip-snow  (convective)
    output_data['mr_ccrain' ] = input_data['MPQC'] * 0;  ### Mixing ratio: precip-rain  (convective)


    del q1, q2, q3, q4, q5, q6
    #print('\t Mixing ratios')


    #############################################################################################################################
    #                                                         Effective radius                                                  #
    #############################################################################################################################
    nhydro = 9
    Reff = np.zeros((ntime, nhydro, nlev, nlat, nlon), dtype='float32')

    # Effective radius 1: Data directly copied ( Cloud-liquid(LS), Precip-rain(LS))
    flag_lsliq  = output_data['mr_lsliq' ] > 0
    flag_lsrain = output_data['mr_lsrain'] > 0


    r_lsliq     = input_data['REC' ] * flag_lsliq ;    # Effective radius: cloud-liquid  (large scale)
    r_lsrain    = input_data['SS01'] * flag_lsrain;    # Effective radius: precip-rain   (large scale)

    del flag_lsliq, flag_lsrain

    # Effective radius 2:  cloud-ice (large scale), precip-snow (large scale) and precip-graupel (large scale)
    #   GEM produced actually making difference between cloud-ice, snow or graupel since it is producing a single mixing ratio QTI1  
    #   At each step is diagnostic is done to assign to each griobox a single hydrometeore type category (small ice crystals, unrimed snow crystals, etc.)
    #   QI_1 = QTI1 [flag = small ice crystals], QI_2 = QTI2 [flag = unrimed snow crystals], etc
    #   This decomposition was not conducted for the effective radius (REI1), we will nthe conduct it here
    flag_lsice  = output_data['mr_lsice' ] > 0
    flag_lssnow = output_data['mr_lssnow'] > 0
    flag_lsgrpl = output_data['mr_lsgrpl'] > 0
    r_all     = input_data['REI1'];
    r_lsice   =  r_all * flag_lsice  # Effective radius: cloud-ice      (large scale)
    r_lssnow  =  r_all * flag_lssnow # Effective radius: precip-snow    (large scale)
    r_lsgrpl  =  r_all * flag_lsgrpl # Effective radius: precip-graupel (large scale)

    del r_all, flag_lsice, flag_lssnow, flag_lsgrpl

    # Effective radius 3:
    #   Using the equations in cldoppro_mp.F90 ro compute effective radius of convective cloud hydrometeores
    #   There is 2 options for ice_cloud, but as far I understand the options with a  constant value is used (to check) 
    #   When option ice_constant is chosen, r = 15 micron if mixing ratio > 1e-10, 0-->NaN elswhere
    RGASD        = 0.28705e+3;             # Gas constant for dry air [J K-1 kg-1]
    air_density  = ( pfull/(RGASD*T_abs) ).astype(np.float32)

    r_ccliq = radius_from_cldoppro(air_density, output_data['landmask'], output_data['mr_ccliq'], 'liquid'      ) # Effective radius: cloud-liquid  (convective)
    r_ccice = radius_from_cldoppro(air_density, output_data['landmask'], output_data['mr_ccice'], 'ice_constant') # Effective radius: cloud-ice  (convective)

    # Effective radius 4:
    #   We are setting the effective radius of convective precipitation to zero
    #   For now, we decided to neglect the convective snow
    #   For convective rain, we are waiting for Jason "receipe"
    r_ccrain = r_ccliq * 0
    r_ccsnow = r_ccliq * 0

    # Effective radius 5:
    #   WARNING: The equations/parameter taken from mp_my2, seems to apply to
    #            frozen precipitation rather than rain --> to discuss
    #number_ratio = input_data['MPNR']
    #mixing_ratio = input_data['MPQR']
    #r_lsrain = radius_from_mp_my2(number_ratio, mixing_ratio, air_density, 'rain')

    Reff[:,0,:,:,:] = r_lsliq    
    Reff[:,1,:,:,:] = r_lsice
    Reff[:,2,:,:,:] = r_lsrain  
    Reff[:,3,:,:,:] = r_lssnow  
    Reff[:,4,:,:,:] = r_ccliq   
    Reff[:,5,:,:,:] = r_ccice
    Reff[:,6,:,:,:] = r_ccrain 
    Reff[:,7,:,:,:] = r_ccsnow 
    Reff[:,8,:,:,:] = r_lsgrpl 

    #for i in range(9):
        #print(i,  np.min(np.min(np.min(np.min(Reff[:,i,:,:,:])))) ,  np.max(np.max(np.max(np.max(Reff[:,i,:,:,:])))) )
    output_data['Reff'] = Reff; ### effective radii

    del r_lsliq, r_lsice, r_lsrain, r_lssnow, r_ccrain, r_ccsnow, r_lsgrpl, Reff #r_ccliq, r_ccice are used below


    #print('\t Reff')
    #############################################################################################################################
    #                                               Optical depth and emmisivity                                                #
    #############################################################################################################################
    # Cloud visible optical depth (0.67 micron) and infrared emmisivity (10.5 micron)
    #   Emmisivity and optical depth are computing using equations in clodoppro
    #   To be consitent, we are using the radius from clodoppro (instead to REC/REI1 for LS part)

    # Large scale cloud
    mrw = output_data['mr_lsliq']
    mri = output_data['mr_lsice']
    rew = radius_from_cldoppro(air_density, output_data['landmask'], mrw, 'liquid'      ) * 1e6 
    rei = radius_from_cldoppro(air_density, output_data['landmask'], mri, 'ice_constant') * 1e6 
    dtau_s, dem_s = cloud_optical_depth_and_emmissivity(rew, rei, mrw, mri, full_height, output_data['orography'], air_density)

    # Convective cloud
    mrw = output_data['mr_ccliq']
    mri = output_data['mr_ccice']
    rew = r_ccliq * 1e6 
    rei = r_ccice * 1e6 
    dtau_c, dem_c = cloud_optical_depth_and_emmissivity(rew, rei, mrw, mri, full_height, output_data['orography'], air_density)

    output_data['dtau_s'] = dtau_s; ###  Cloud Optical depth of at 0.67 micron (visible) (large_scale)
    output_data['dtau_c'] = dtau_c; ###  Cloud Optical depth of at 0.67 micron (visible) (convective)
    output_data['dem_s' ] = dem_s;  ###  Cloud emissivity at 10.5 micron (infrared) (large_scale)
    output_data['dem_c' ] = dem_c;  ###  Cloud emissivity at 10.5 micron (infrared) (convective)


    del mrw, mri, rew, rei, dtau_s, dem_s, dtau_c, dem_c, r_ccliq, r_ccice, air_density   
    #print('\t dtau_s, dtau_c, dem_s, dem_c')




#output_data['dem_c' ]    = output_data['dem_c' ] * 0
#output_data['dtau_c']    = output_data['dtau_c'] * 0
#output_data['cca'      ] = output_data['cca'      ] * 0
#output_data['mr_ccliq' ] = output_data['mr_ccliq' ] * 0
#output_data['mr_ccice' ] = output_data['mr_ccice' ] * 0 
#output_data['mr_ccsnow'] = output_data['mr_ccsnow'] * 0
#output_data['mr_ccrain'] = output_data['mr_ccrain'] * 0
#Reff[:,4,:,:,:] = r_ccliq  * 0
#Reff[:,5,:,:,:] = r_ccice  * 0
#Reff[:,6,:,:,:] = r_ccrain * 0
#Reff[:,7,:,:,:] = r_ccsnow * 0
#output_data['Reff'] = Reff




    #############################################################################################################################
    #                                                   Creating output files                                                   #
    #############################################################################################################################
    #for field in output_data: print(field)

    #print('Creating output file')

    for t in range(ntime):
    
        # Create filename (they will be labelled by the date + hour)
        time       = datetime.strptime(formatted_time[t],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M')
        ncfile_path = output_directory + '/' + time + '.nc'
        ncfile      = netCDF4.Dataset(ncfile_path, 'w', format='NETCDF4')

        # Create dimension
        ncfile.createDimension('lon'  ,nlon)
        ncfile.createDimension('lat'  ,nlat)
        ncfile.createDimension('level',nlev)
        ncfile.createDimension('hydro',   9)

        # Create variable: lat, lon, emsfc_lw
        ncfile.createVariable('emsfc_lw', 'f4',zlib=True)
        ncfile['emsfc_lw'][:] = 0.95
        ncfile.createVariable('lon', 'f4', ('lon'),zlib=True)
        ncfile['lon'][:] = output_data['lon']
        ncfile.createVariable('lat', 'f4', ('lat'),zlib=True)
        ncfile['lat'][:] = output_data['lat']
    
        # Cerate other variables
        for fieldname in output_data:

            fieldshape = output_data[fieldname].shape
            #if t == 0 :
                #output_data[fieldname] = np.nan_to_num(output_data[fieldname]) # Set NaN --> 0, doing one time (t=0) for all timestep

            if   len(fieldshape) == 2:      # orography, landmask, longitude, latitude
                ncfile.createVariable(fieldname, 'f4', ('lat','lon'), zlib=True)
                ncfile[fieldname][:] = np.nan_to_num( output_data[fieldname] )

            elif len(fieldshape) == 3:      # sunlit, skt
                ncfile.createVariable(fieldname, 'f4', ('lat','lon'), zlib=True)
                ncfile[fieldname][:] = np.nan_to_num( output_data[fieldname][t,:,:] )

            elif len(fieldshape) == 4:      # all other variables
                ncfile.createVariable(fieldname, 'f4', ('level','lat','lon'), zlib=True)
                ncfile[fieldname][:] = np.nan_to_num( np.flip(output_data[fieldname][t,:,:,:],0) )

            elif len(fieldshape) == 5:      # effective radii
                ncfile.createVariable(fieldname, 'f4', ('hydro','level','lat','lon'), zlib=True)
                ncfile[fieldname][:] = np.nan_to_num( np.flip(output_data[fieldname][t,:,:,:,:],1) )

    
        # Facultative fields attributes usefull for geolocations (ncview, panoply, etc.)
        ncgrid = ncfile_pm0
        grd    = netCDF4.Dataset(ncgrid , 'r');
        x      = ncfile.createVariable('rotated_pole', grd['rotated_pole'].datatype )
        ncfile['rotated_pole'].setncatts(grd['rotated_pole'].__dict__)
        ncfile['lat'         ].setncatts(grd['rlon'        ].__dict__)
        ncfile['lon'         ].setncatts(grd['rlat'        ].__dict__)

        
        output_data = {}
        input_data  = {}
        del pfull, full_height

        #for name in dir():
        #    myvalue = eval(name)
        #    print (name, "is", type(name))
        print(ncfile_path)
        print(' ')

