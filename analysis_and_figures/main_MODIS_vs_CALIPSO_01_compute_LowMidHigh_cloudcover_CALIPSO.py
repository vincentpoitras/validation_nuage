import os
import sys
import yaml
import netCDF4
import warnings
import yaml
import numpy  as np
import pandas as pd

NaN = np.nan

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


def compute_cloud_cover(ncfilei, layerdef):
    ''' To compute total, low, mid and high cloud cover
        Low, Mid and High cloud cover may be defined 
            - From altitude (layerdef = amax, amin, amean)
            - From pressure (layerdef = pmax, pmin, pmean)
        All levels of the profiles beloging to a layer (total, low, mid and high) may be combined using (we used a "toy" example with 3 levels to illustrate the definitions)
            - Max overlap: (eg. 0.0 0.2 0.4 --> 0.4) 
            - Min overlap: (eg. 0.0 0.2 0.4 --> 0.6)
            - Mean value : (eg. 0.0 0.2 0.4 --> 0.2)
    '''

    ''' Reading the NetCDF file'''
    nc = netCDF4.Dataset(ncfilei,'r')


    ''' Altitude and pressure limit. See eg: https://climserv.ipsl.polytechnique.fr/cfmip-obs/Calipso_goccp.html#MapLowMidHigh '''
    if layerdef[0] == 'p':
        pressure_lim_midlow  =  680 # hPa
        pressure_lim_midhigh =  440 # hPa
    elif layerdef[0] == 'a':
        altitude_lim_midlow  = 3200 # m
        altitude_lim_midhigh = 6500 # m


    '''Création de masques pour garder les points du profile pour une couche donnée (Low,Mid,High)'''
    if layerdef[0] == 'p':
        Pressure  = nc['Pressure'][:]
        mask_high = np.where(Pressure <  pressure_lim_midhigh,  1, NaN)
        mask_low  = np.where(Pressure >= pressure_lim_midlow ,  1, NaN)
        mask_mid  = np.where(Pressure >= pressure_lim_midhigh,  1, NaN) * np.where(Pressure < pressure_lim_midlow , 1, NaN)
    elif layerdef[0] == 'a':
        Altitude = np.flip(np.arange(-480,-480+(398+1)*60,60))          # Il y a 398 niveaux de 60m commençant à -480 m
        mask_high = np.where(Altitude >  altitude_lim_midhigh, 1, NaN)
        mask_low  = np.where(Altitude <= altitude_lim_midlow , 1, NaN)
        mask_mid  = np.where(Altitude <= altitude_lim_midhigh, 1, NaN) * np.where(Altitude > altitude_lim_midlow , 1, NaN)


    '''Using masks to keep only the sublayers (delatz=60m) associated to the given layer (Low,Mid,High)'''
    Cloud_Layer_Fraction      = nc['Cloud_Layer_Fraction'][:] / 30          # On divise par 30 car il ya 30 mesures par points de grille
    Cloud_Layer_Fraction_high = Cloud_Layer_Fraction * mask_high
    Cloud_Layer_Fraction_mid  = Cloud_Layer_Fraction * mask_mid
    Cloud_Layer_Fraction_low  = Cloud_Layer_Fraction * mask_low


    '"Merging" the cloud_cover from each level'
    if 'max' in layerdef:
        Cloud_Cover      = np.nanmax(Cloud_Layer_Fraction     ,axis=1)
        Cloud_Cover_high = np.nanmax(Cloud_Layer_Fraction_high,axis=1)
        Cloud_Cover_mid  = np.nanmax(Cloud_Layer_Fraction_mid ,axis=1)
        Cloud_Cover_low  = np.nanmax(Cloud_Layer_Fraction_low ,axis=1)
    elif 'min' in layerdef:
        Cloud_Cover      = np.nansum(Cloud_Layer_Fraction     ,axis=1); Cloud_Cover      = np.where(Cloud_Cover      <= 1, Cloud_Cover     , 1)
        Cloud_Cover_high = np.nansum(Cloud_Layer_Fraction_high,axis=1); Cloud_Cover_high = np.where(Cloud_Cover_high <= 1, Cloud_Cover_high, 1)
        Cloud_Cover_mid  = np.nansum(Cloud_Layer_Fraction_mid ,axis=1); Cloud_Cover_mid  = np.where(Cloud_Cover_mid  <= 1, Cloud_Cover_mid , 1)
        Cloud_Cover_low  = np.nansum(Cloud_Layer_Fraction_low ,axis=1); Cloud_Cover_low  = np.where(Cloud_Cover_low  <= 1, Cloud_Cover_low , 1)
    elif 'mean' in layerdef:
        Cloud_Cover      = np.nanmean(Cloud_Layer_Fraction     ,axis=1)
        Cloud_Cover_high = np.nanmean(Cloud_Layer_Fraction_high,axis=1)
        Cloud_Cover_mid  = np.nanmean(Cloud_Layer_Fraction_mid ,axis=1)
        Cloud_Cover_low  = np.nanmean(Cloud_Layer_Fraction_low ,axis=1)

    return Cloud_Cover, Cloud_Cover_high, Cloud_Cover_mid, Cloud_Cover_low



def create_ouput_file(ncfilei,ncfileo,Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover, layerdef):
    
    ''' I/O file '''
    if     os.path.exists(ncfileo)                 : os.remove(ncfileo)
    if not os.path.exists(os.path.dirname(ncfileo)): os.makedirs(os.path.dirname(ncfileo))
    nci = netCDF4.Dataset(ncfilei, 'r');
    nco = netCDF4.Dataset(ncfileo, 'w');


    ''' New data to output / Old data to copy  '''
    newvarnames = [ 'Tot_cloud_cover', 'High_cloud_cover', 'Mid_cloud_cover', 'Low_cloud_cover']
    varnames    = [ 'Profile_Time', 'Profile_UTC_Time', 'Latitude', 'Longitude', 'Pressure', 'Day_Night_Flag' ]
    
    ''' Extracting the diemsnion '''
    dimnames = []
    for varname in varnames:
        for dimname in nci.variables[varname].dimensions:
            dimnames.append(dimname)
    dimnames = set(dimnames)

    ''' Copying global attributes '''
    nco.setncatts(nci.__dict__)

    ''' Copying dimensions '''
    #dimnames = [dim for dim in nci.dimensions]
    for dimname in dimnames:
        dimension = nci.dimensions[dimname]
        nco.createDimension(dimname, (len(dimension) if not dimension.isunlimited() else None))

    ''' Copying (old) variables '''
    for varname in varnames:
        variable = nci[varname]
        x = nco.createVariable(varname, variable.datatype, variable.dimensions, zlib=True, complevel=4)
        nco[varname].setncatts(variable.__dict__)
        nco[varname][:] = nci[varname][:]

    ''' Long_name for the new variable'''
    if    'max'  in layerdef: str_layerdef = 'maximum overlap'
    elif  'min'  in layerdef: str_layerdef = 'minimum overlap'
    elif  'mean' in layerdef: str_layerdef = 'mean value'
    if layerdef[0] == 'p':
        long_name_Tot  = 'Total cloud cover: %s (all layers)'                     % (str_layerdef)
        long_name_High = 'High cloud cover : %s (layers with p < %dha)'           % (str_layerdef, pressure_lim_midhigh)
        long_name_Mid  = 'Mid cloud cover  : %s (layers with %dhPa > p >= %dhPa)' % (str_layerdef, pressure_lim_midlow, pressure_lim_midhigh)
        long_name_Low  = 'Low cloud cover  : %s (layers with p >= %dhPa)'         % (str_layerdef, pressure_lim_midlow)
    elif layerdef[0] == 'a':
        long_name_Tot  = 'Total cloud cover: %s (all layers)'                     % (str_layerdef)
        long_name_High = 'High cloud cover : %s (layers with h > %dm)'            % (str_layerdef, altitude_lim_midhigh)
        long_name_Mid  = 'Mid cloud cover  : %s (layers with %dm < h <= %dm )'    % (str_layerdef, altitude_lim_midlow, altitude_lim_midhigh)
        long_name_Low  = 'Low cloud cover  : %s (layers with h <= %dm)'           % (str_layerdef, altitude_lim_midlow)


    ''' Writting new variables '''
    for varname in newvarnames:

        if   varname ==  'Tot_cloud_cover' : data =  Tot_cloud_cover; long_name = long_name_Tot
        elif varname == 'High_cloud_cover' : data = High_cloud_cover; long_name = long_name_High
        elif varname ==  'Mid_cloud_cover' : data =  Mid_cloud_cover; long_name = long_name_Mid
        elif varname ==  'Low_cloud_cover' : data =  Low_cloud_cover; long_name = long_name_Low
        
        x = nco.createVariable(varname, 'float32', 'fakeDim0', zlib=True, complevel=4)
        nco[varname].setncatts({'long_name': long_name})
        nco[varname][:] = data[:]



#################################################################################################################
### MAIN ########################################################################################################
#################################################################################################################


#########################################################################
# Input arguments                                                       #
#########################################################################
working_directory =     sys.argv[1]
YYYYMM            =     sys.argv[2]
layerdef          =     sys.argv[3]
overwrite         =     sys.argv[4].lower()

YYYY = int(str(YYYYMM[0:4]))
MM   = int(str(YYYYMM[4:6]))


#########################################################################
# Configuration file (yml)                                              #
#########################################################################
yml_file = working_directory + '/../config.yml'
stream = open(yml_file,'r')
config = yaml.safe_load(stream)

domain  = config['domain' ]
dirout  = config['CALIPSO']['NetCDF'] + '_LowMidHigh/' + layerdef
dirlist = config['CALIPSO']['list']   + '/' + domain

if not os.path.exists(dirout): os.makedirs(dirout)



#########################################################################
# Hardcoded parameter                                                   #
#########################################################################

''' Altitude and pressure limit for High, Mid, Low layer. See eg: https://climserv.ipsl.polytechnique.fr/cfmip-obs/Calipso_goccp.html '''
pressure_lim_midlow  =  680 # hPa
pressure_lim_midhigh =  440 # hPa
    
altitude_lim_midlow  = 3200 # m 
altitude_lim_midhigh = 6500 # m 



#########################################################################
# Computing Low, Mid, High, Tot cloud cover                             #
#########################################################################

''' Create a dataframe containing YYYYMM files '''
df_CALIPSO = create_dataframe(dirlist, YYYYMM)

''' Loop over each file of the dataframe '''
for iCAL in range(len(df_CALIPSO['file'])):

    ''' Compute Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover using layer definition given by layerdef'''
    date    = df_CALIPSO['date'][iCAL]
    ncfilei = df_CALIPSO['file'][iCAL]
    Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover = compute_cloud_cover(ncfilei, layerdef)
    
    ''' Output data '''
    YYYY    = os.path.basename(os.path.dirname(ncfilei))
    ncfileo = dirout + '/' + YYYY + '/' + os.path.basename(ncfilei)     
    create_ouput_file(ncfilei, ncfileo, Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover, layerdef)
    print(date, ncfileo)


exit()


exit()






NaN = np.nan

ncfilei = sys.argv[1]
ncfileo = sys.argv[2]
nci     = netCDF4.Dataset(ncfilei, 'r');
nco     = netCDF4.Dataset(ncfileo, 'w');



warnings.filterwarnings("ignore")



# COMPUTING DATA ##################################################################################################################################################################################


# Altitude and pressure limit
# See eg: https://climserv.ipsl.polytechnique.fr/cfmip-obs/Calipso_goccp.html#MapLowMidHigh
#altitude_lim_midlow  = 3200 # m
#altitude_lim_midhigh = 6500 # m
pressure_lim_midlow  =  680 # hPa
pressure_lim_midhigh =  440 # hPa





# High, mid, low layer masks (altitude)
#altitude           = np.flip(np.arange(-480,-480+(398+1)*60,60))
#altidude_mask_high = np.where(altitude >  altitude_lim_midhigh, 1, NaN)
#altidude_mask_low  = np.where(altitude <= altitude_lim_midlow , 1, NaN)
#altidude_mask_mid  = np.where(altitude <= altitude_lim_midhigh, 1, NaN) * np.where(altitude > altitude_lim_midlow , 1, NaN)


# High, mid, low layer masks (Pressure)
Pressure           = nci['Pressure'][:]
pressure_mask      = np.where(np.isnan(Pressure)             ,NaN,   1)
pressure_mask_high = np.where(Pressure <  pressure_lim_midhigh,  1, NaN)
pressure_mask_low  = np.where(Pressure >= pressure_lim_midlow ,  1, NaN)
pressure_mask_mid  = np.where(Pressure >= pressure_lim_midhigh,  1, NaN) * np.where(Pressure < pressure_lim_midlow , 1, NaN)



# Compute low mid and high cloud cover (altitude)
#Cloud_Layer_Fraction               = nci['Cloud_Layer_Fraction'][:] / 30.
#Cloud_Layer_Fraction_altitude_high = Cloud_Layer_Fraction * altidude_mask_high
#Cloud_Layer_Fraction_altitude_mid  = Cloud_Layer_Fraction * altidude_mask_mid
#Cloud_Layer_Fraction_altitude_low  = Cloud_Layer_Fraction * altidude_mask_low

#Cloud_Cover_altitude_min_high = np.nanmax(Cloud_Layer_Fraction_altitude_high,axis=1)
#Cloud_Cover_altitude_min_mid  = np.nanmax(Cloud_Layer_Fraction_altitude_mid ,axis=1)
#Cloud_Cover_altitude_min_low  = np.nanmax(Cloud_Layer_Fraction_altitude_low ,axis=1)

#Cloud_Cover_altitude_max_high = np.nansum(Cloud_Layer_Fraction_altitude_high,axis=1); Cloud_Cover_altitude_max_high = np.where(Cloud_Cover_altitude_max_high <= 1, Cloud_Cover_altitude_max_high, 1)
#Cloud_Cover_altitude_max_mid  = np.nansum(Cloud_Layer_Fraction_altitude_mid ,axis=1); Cloud_Cover_altitude_max_mid  = np.where(Cloud_Cover_altitude_max_mid  <= 1, Cloud_Cover_altitude_max_mid , 1)
#Cloud_Cover_altitude_max_low  = np.nansum(Cloud_Layer_Fraction_altitude_low ,axis=1); Cloud_Cover_altitude_max_low  = np.where(Cloud_Cover_altitude_max_low  <= 1, Cloud_Cover_altitude_max_low , 1)

#Cloud_Cover_altitude_avg_high = np.nanmean(Cloud_Layer_Fraction_altitude_high,axis=1)
#Cloud_Cover_altitude_avg_mid  = np.nanmean(Cloud_Layer_Fraction_altitude_mid ,axis=1)
#Cloud_Cover_altitude_avg_low  = np.nanmean(Cloud_Layer_Fraction_altitude_low ,axis=1)


# Compute low mid and high cloud cover (pressure)
Cloud_Layer_Fraction               = nci['Cloud_Layer_Fraction'][:] / 30
Cloud_Layer_Fraction_pressure_high = Cloud_Layer_Fraction * pressure_mask_high
Cloud_Layer_Fraction_pressure_mid  = Cloud_Layer_Fraction * pressure_mask_mid
Cloud_Layer_Fraction_pressure_low  = Cloud_Layer_Fraction * pressure_mask_low

Cloud_Cover_pressure_tot  = np.nanmax(Cloud_Layer_Fraction              ,axis=1)
Cloud_Cover_pressure_high = np.nanmax(Cloud_Layer_Fraction_pressure_high,axis=1)
Cloud_Cover_pressure_mid  = np.nanmax(Cloud_Layer_Fraction_pressure_mid ,axis=1)
Cloud_Cover_pressure_low  = np.nanmax(Cloud_Layer_Fraction_pressure_low ,axis=1)


#Cloud_Cover_pressure_min_high = np.nanmax(Cloud_Layer_Fraction_pressure_high,axis=1)  # min in the sens of minimum value 
#Cloud_Cover_pressure_min_mid  = np.nanmax(Cloud_Layer_Fraction_pressure_mid ,axis=1)
#Cloud_Cover_pressure_min_low  = np.nanmax(Cloud_Layer_Fraction_pressure_low ,axis=1)

#Cloud_Cover_pressure_max_high = np.nansum(Cloud_Layer_Fraction_pressure_high,axis=1); Cloud_Cover_pressure_max_high = np.where(Cloud_Cover_pressure_max_high <= 1, Cloud_Cover_pressure_max_high, 1)
#Cloud_Cover_pressure_max_mid  = np.nansum(Cloud_Layer_Fraction_pressure_mid ,axis=1); Cloud_Cover_pressure_max_mid  = np.where(Cloud_Cover_pressure_max_mid  <= 1, Cloud_Cover_pressure_max_mid , 1)
#Cloud_Cover_pressure_max_low  = np.nansum(Cloud_Layer_Fraction_pressure_low ,axis=1); Cloud_Cover_pressure_max_low  = np.where(Cloud_Cover_pressure_max_low  <= 1, Cloud_Cover_pressure_max_low , 1)

#Cloud_Cover_pressure_avg_high = np.nanmean(Cloud_Layer_Fraction_pressure_high,axis=1)
#Cloud_Cover_pressure_avg_mid  = np.nanmean(Cloud_Layer_Fraction_pressure_mid ,axis=1)
#Cloud_Cover_pressure_avg_low  = np.nanmean(Cloud_Layer_Fraction_pressure_low ,axis=1)



#Ni = Cloud_Layer_Fraction.shape[0]
#Nj = Cloud_Layer_Fraction.shape[1]
#print(Ni,Nj)
#for i in range(Ni):
    #for j in range(Nj):
        #print('%4d' % i, '%4d' % j, '%6.0f' % altitude[j], '%6.1f' % Pressure[i][j], altidude_mask_high[j], pressure_mask_high[i][j], Cloud_Layer_Fraction[i][j])
        #print(i,j, altitude[j], Pressure[j], altidude_mask_high[i][j], pressure_mask_high[i][j])




# CREATING OUTPUTFILES  #############################################################################################################################################################################

# List of variables and dimensions to copy
newvarnames = [ 'High_cloud_cover_amin' , 'Mid_cloud_cover_amin' , 'Low_cloud_cover_amin' , 'High_cloud_cover_pmin' , 'Mid_cloud_cover_pmin' , 'Low_cloud_cover_pmin' , \
                'High_cloud_cover_amax' , 'Mid_cloud_cover_amax' , 'Low_cloud_cover_amax' , 'High_cloud_cover_pmax' , 'Mid_cloud_cover_pmax' , 'Low_cloud_cover_pmax' , \
                'High_cloud_cover_amean', 'Mid_cloud_cover_amean', 'Low_cloud_cover_amean', 'High_cloud_cover_pmean', 'Mid_cloud_cover_pmean', 'Low_cloud_cover_pmean'  ] 


newvarnames = [ 'Tot_cloud_cover', 'High_cloud_cover' , 'Mid_cloud_cover' , 'Low_cloud_cover'   ]


varnames = ['Profile_Time', 'Profile_UTC_Time', 'Latitude', 'Longitude', 'Pressure', 'Cloud_Layer_Fraction', 'Day_Night_Flag' ]
dimnames = []
for varname in varnames:
    for dimname in nci.variables[varname].dimensions:
        dimnames.append(dimname)
dimnames = set(dimnames)



# Copying global attributes
nco.setncatts(nci.__dict__)

# Copying dimensions
#dimnames = [dim for dim in nci.dimensions]
for dimname in dimnames:
    dimension = nci.dimensions[dimname]
    nco.createDimension(dimname, (len(dimension) if not dimension.isunlimited() else None))

# Copying variables
for varname in varnames:
    variable = nci[varname]
    x = nco.createVariable(varname, variable.datatype, variable.dimensions, zlib=True, complevel=4)
    nco[varname].setncatts(variable.__dict__)
    nco[varname][:] = nci[varname][:]

# Writtting new variables
for varname in newvarnames:
    if   varname ==  'Tot_cloud_cover' : data = Cloud_Cover_pressure_tot ; long_name = 'Total cloud cover: max (all layers)'              
    elif varname == 'High_cloud_cover' : data = Cloud_Cover_pressure_high; long_name = 'High cloud cover: max (layers with p < %dha)'            % (pressure_lim_midhigh)
    elif varname ==  'Mid_cloud_cover' : data = Cloud_Cover_pressure_mid ; long_name = 'Mid  cloud cover: max (layers with %dhPa > p >= %dhPa )' % (pressure_lim_midlow, pressure_lim_midhigh)
    elif varname ==  'Low_cloud_cover' : data = Cloud_Cover_pressure_low ; long_name = 'Low  cloud cover: max (layers with p >= %dhPa)'          % (pressure_lim_midlow)


   # if   varname == 'High_cloud_cover_amin' : data = Cloud_Cover_altitude_min_high; long_name = 'High cloud cover (h > %dm) [min overlap]'             % altitude_lim_midhigh
   # elif varname ==  'Mid_cloud_cover_amin' : data = Cloud_Cover_altitude_min_mid ; long_name = 'Mid  cloud cover (%dm < h <= %dm ) [min overlap]'     % (altitude_lim_midlow, altitude_lim_midhigh)
   # elif varname ==  'Low_cloud_cover_amin' : data = Cloud_Cover_altitude_min_low ; long_name = 'Low  cloud cover (h <= %dm) [min overlap]'            % (altitude_lim_midlow)
   # elif varname == 'High_cloud_cover_amax' : data = Cloud_Cover_altitude_max_high; long_name = 'High cloud cover (h > %dm) [max overlap]'             % altitude_lim_midhigh
   # elif varname ==  'Mid_cloud_cover_amax' : data = Cloud_Cover_altitude_max_mid ; long_name = 'Mid  cloud cover (%dm < h <= %dm ) [max overlap]'     % (altitude_lim_midlow, altitude_lim_midhigh)
   # elif varname ==  'Low_cloud_cover_amax' : data = Cloud_Cover_altitude_max_low ; long_name = 'Low  cloud cover (h <= %dm) [max overlap]'            % (altitude_lim_midlow)
   # elif varname == 'High_cloud_cover_amean': data = Cloud_Cover_altitude_avg_high; long_name = 'High cloud cover (h > %dm) [mean value]'              % altitude_lim_midhigh
   # elif varname ==  'Mid_cloud_cover_amean': data = Cloud_Cover_altitude_avg_mid ; long_name = 'Mid  cloud cover (%dm < h <= %dm ) [mean value]'      % (altitude_lim_midlow, altitude_lim_midhigh)
   # elif varname ==  'Low_cloud_cover_amean': data = Cloud_Cover_altitude_avg_low ; long_name = 'Low  cloud cover (h <= %dm) [mean value]'             % (altitude_lim_midlow)


   # elif varname == 'High_cloud_cover_pmin' : data = Cloud_Cover_pressure_min_high; long_name = 'High cloud cover (p < %dha) [min overlap]'            % pressure_lim_midhigh
   # elif varname ==  'Mid_cloud_cover_pmin' : data = Cloud_Cover_pressure_min_mid ; long_name = 'Mid  cloud cover (%dhPa > p >= %dhPa ) [min overlap]' % (pressure_lim_midlow, pressure_lim_midhigh)
   # elif varname ==  'Low_cloud_cover_pmin' : data = Cloud_Cover_pressure_min_low ; long_name = 'Low  cloud cover (p >= %dhPa) [min overlap]'          % (pressure_lim_midlow)
   # elif varname == 'High_cloud_cover_pmax' : data = Cloud_Cover_pressure_max_high; long_name = 'High cloud cover (p < %dha) [max overlap]'            % pressure_lim_midhigh
   # elif varname ==  'Mid_cloud_cover_pmax' : data = Cloud_Cover_pressure_max_mid ; long_name = 'Mid  cloud cover (%dhPa > p >= %dhPa ) [max overlap]' % (pressure_lim_midlow, pressure_lim_midhigh)
   # elif varname ==  'Low_cloud_cover_pmax' : data = Cloud_Cover_pressure_max_low ; long_name = 'Low  cloud cover (p >= %dhPa) [max overlap]'          % (pressure_lim_midlow)
   # elif varname == 'High_cloud_cover_pmean': data = Cloud_Cover_pressure_avg_high; long_name = 'High cloud cover (p < %dha) [mean value]'             % pressure_lim_midhigh
   # elif varname ==  'Mid_cloud_cover_pmean': data = Cloud_Cover_pressure_avg_mid ; long_name = 'Mid  cloud cover (%dhPa > p >= %dhPa ) [mean value]'  % (pressure_lim_midlow, pressure_lim_midhigh)
   # elif varname ==  'Low_cloud_cover_pmean': data = Cloud_Cover_pressure_avg_low ; long_name = 'Low  cloud cover (p >= %dhPa) [mean value]'           % (pressure_lim_midlow)



    x = nco.createVariable(varname, 'float32', 'fakeDim0', zlib=True, complevel=4)
    nco[varname].setncatts({'long_name': long_name})
    nco[varname][:] = data[:]

#print(ncfileo)

