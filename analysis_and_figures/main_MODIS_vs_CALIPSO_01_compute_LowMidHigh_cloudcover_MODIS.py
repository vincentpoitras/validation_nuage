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


def compute_cloud_cover(ncfilei):
    ''' Compute total, low, mid and high cloud cover'''
    ''' NOTE on utilise Cloud_Top_Pressure, mais il y a aussi (à implémenter et tester?)
            Cloud_Top_Pressure_infrared
            Cloud_Top_Pressure_From_Ratio
            Cloud_Top_Height
    '''

    ''' Reading the NetCDF file'''
    nc = netCDF4.Dataset(ncfilei,'r')
    Cloud_Fraction     = np.array(nc['Cloud_Fraction'    ][:])
    Cloud_Top_Pressure = np.array(nc['Cloud_Top_Pressure'][:])
    
    ''' Cloud top pressure mask (raw) '''
    mask_t    = np.where(Cloud_Top_Pressure >                    0, 1 , 0)
    mask_h    = np.where(Cloud_Top_Pressure >                    0, 1 , 0) * np.where(Cloud_Top_Pressure <= pressure_lim_midhigh, 1 , 0)
    mask_m    = np.where(Cloud_Top_Pressure > pressure_lim_midhigh, 1 , 0) * np.where(Cloud_Top_Pressure <= pressure_lim_midlow , 1 , 0)
    mask_l    = np.where(Cloud_Top_Pressure > pressure_lim_midlow , 1 , 0)
    
    ''' Cloud top pressure mask (corrected)
         1: Upper layers: cloudless, Current layer: cloudy 
         0: Upper layers: cloudless, Current layer: cloudless
        -1: Upper layers: cloudy OR cell not covered by the swath   
    '''
    mask_tot  = np.where(Cloud_Fraction == 127, -1 , 1) # 127 = grid cell without data
    mask_high = mask_tot - (1*mask_m + 1*mask_l) 
    mask_mid  = mask_tot - (2*mask_h + 1*mask_l) 
    mask_low  = mask_tot - (2*mask_h + 2*mask_m) 
    
    ''' Cloud cover '''
    Cloud_Cover      = Cloud_Fraction * mask_tot
    Cloud_Cover_high = Cloud_Fraction * mask_high
    Cloud_Cover_mid  = Cloud_Fraction * mask_mid
    Cloud_Cover_low  = Cloud_Fraction * mask_low

    Cloud_Cover      = np.where(Cloud_Cover      < 0, 127 , Cloud_Cover     )
    Cloud_Cover_high = np.where(Cloud_Cover_high < 0, 127 , Cloud_Cover_high)
    Cloud_Cover_mid  = np.where(Cloud_Cover_mid  < 0, 127 , Cloud_Cover_mid )
    Cloud_Cover_low  = np.where(Cloud_Cover_low  < 0, 127 , Cloud_Cover_low )

    return Cloud_Cover, Cloud_Cover_high, Cloud_Cover_mid, Cloud_Cover_low



def create_ouput_file(ncfilei,ncfileo,Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover):
    
    ''' I/O file '''
    if     os.path.exists(ncfileo)                 : os.remove(ncfileo)
    if not os.path.exists(os.path.dirname(ncfileo)): os.makedirs(os.path.dirname(ncfileo))
    nci = netCDF4.Dataset(ncfilei, 'r');
    nco = netCDF4.Dataset(ncfileo, 'w');


    ''' New data to output / Old data to copy  '''
    newvarnames = [ 'Tot_cloud_cover', 'High_cloud_cover', 'Mid_cloud_cover', 'Low_cloud_cover']
    varnames    = [ 'lat', 'lon', 'rlon', 'rlat', 'rotated_pole', 'Cloud_Top_Pressure', 'flag_day_night' ]
    
    ''' Extracting the diemnsion '''
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
    long_name_Tot  = 'Total cloud cover'                      
    long_name_High = 'High cloud cover : cloud top pressure < %dha'           % (pressure_lim_midhigh)
    long_name_Mid  = 'Mid cloud cover  : %dhPa > cloud top pressure >= %dhPa' % (pressure_lim_midlow, pressure_lim_midhigh)
    long_name_Low  = 'Low cloud cover  : cloud top pressure >= %dhPa'         % (pressure_lim_midlow)


    ''' Writting new variables '''
    Cloud_Fraction = nci['Cloud_Fraction']
    for varname in newvarnames:

        if   varname ==  'Tot_cloud_cover' : data =  Tot_cloud_cover; long_name = long_name_Tot
        elif varname == 'High_cloud_cover' : data = High_cloud_cover; long_name = long_name_High
        elif varname ==  'Mid_cloud_cover' : data =  Mid_cloud_cover; long_name = long_name_Mid
        elif varname ==  'Low_cloud_cover' : data =  Low_cloud_cover; long_name = long_name_Low
       
        x = nco.createVariable(varname, Cloud_Fraction.datatype, Cloud_Fraction.dimensions, zlib=True, complevel=4)
        nco[varname].setncatts(Cloud_Fraction.__dict__)
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
dataset           =     sys.argv[3]
overwrite         =     sys.argv[4].lower()

YYYY = int(str(YYYYMM[0:4]))
MM   = int(str(YYYYMM[4:6]))


#########################################################################
# Configuration file (yml)                                              #
#########################################################################
yml_file = working_directory + '/../config.yml'
stream = open(yml_file,'r')
config = yaml.safe_load(stream)

domain  = config['domain']
dirout  = config['MODIS']['NetCDF'].replace('MXD06_L2',dataset) + '_LowMidHigh' + '/' + domain 
dirlist = config['MODIS']['list'  ].replace('MXD06_L2',dataset) + '/' + domain





#########################################################################
# Hardcoded parameter                                                   #
#########################################################################

''' Altitude and pressure limit for High, Mid, Low layer. See eg: https://atmosphere-imager.gsfc.nasa.gov/sites/default/files/ModAtmo/documents/L3_MCD06COSP_UserGuide_v13.pdf '''

pressure_lim_midlow  =  680 # hPa
pressure_lim_midhigh =  440 # hPa
    

altitude_lim_midlow  = 3200 # m 
altitude_lim_midhigh = 6500 # m 

#########################################################################
# Computing Low, Mid, High, Tot cloud cover                             #
#########################################################################

''' Create a dataframe containing YYYYMM files '''
df_MODIS = create_dataframe(dirlist, YYYYMM)

''' Loop over each file of the dataframe '''
for iMOD in range(len(df_MODIS['file'])):

    ''' Compute Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover'''
    date    = df_MODIS['date'][iMOD]
    ncfilei = df_MODIS['file'][iMOD]
    Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover = compute_cloud_cover(ncfilei)
    
    ''' Output data '''
    YYYY    = os.path.basename(os.path.dirname(ncfilei))
    ncfileo = dirout + '/Cloud_Top_Pressure/' + YYYY + '/' + os.path.basename(ncfilei)     
    create_ouput_file(ncfilei, ncfileo, Tot_cloud_cover, High_cloud_cover, Mid_cloud_cover, Low_cloud_cover)
    print(date, ncfileo)


