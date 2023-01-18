# info: poitras.vincent@uqam.ca
# date: 2022-04-27
# aim : [1] Compress the ncfile
#       [2] Removed the duplicate field/field_reduced 
#           --> field is unintentional intepolation on a finer grid of field_reduced created by h4tonccf_nc4
#           --> We will keep only field_reduced and rename it field 
import netCDF4
import sys
import numpy as np
import matplotlib.pyplot as plt

ncfilei = sys.argv[1]
ncfileo = sys.argv[2]

#ncfilei = '/pampa/poitras/DATA/MYD06_L2/NetCDF/2014/MYD06_L2_20140105_1905.nc'
#ncfileo = '/pampa/poitras/DATA/MYD06_L2/NetCDF/2014/MYD06_L2_20140105_1905.nc'

nci = netCDF4.Dataset(ncfilei, 'r');
nco = netCDF4.Dataset(ncfileo, 'w', format='NETCDF4')

#for dimension  in nci.dimensions:
#    print(dimension,nci.dimensions[dimension])




##########################################################################################
# Selecting the variables to copy [PART 1]:  excluding the "reduced" ones

varoutput =             [ 'Cloud_Fraction'                                                                                                   ]
varoutput = varoutput + [ 'Cloud_Top_Height'    , 'cloud_top_height_1km'    , 'Cloud_Top_Pressure_From_Ratios', 'Cloud_Top_Pressure_Infrared']
varoutput = varoutput + [ 'Cloud_Top_Pressure'  , 'cloud_top_pressure_1km'                                                                   ]
varoutput = varoutput + [ 'Cloud_Phase_Infrared', 'Cloud_Phase_Infrared_1km', 'Cloud_Phase_Optical_Properties'                               ]
varoutput = varoutput + [ 'latitude'            , 'longitude'                                                                                ]
varoutput = varoutput + [ 'Sensor_Zenith'       , 'Sensor_Azimuth'                                                                           ]



#varouput = ['Cloud_Water_Path', 'Cloud_Effective_Radius', 'Cloud_Optical_Thickness']

varnames          = [var for var in nci.variables] 
#filtered_varnames = [var for var in varnames          if '_reduced' not in var ]
#filtered_varnames = [var for var in filtered_varnames if '_Night'   not in var ]
#filtered_varnames = [var for var in filtered_varnames if '_Day'     not in var ]
filtered_varnames = varoutput

#filtered_varnames = [var for var in filtered_varnames if 'Cloud_Fraction'     in var ]




# Selecting the dimensions related to the selected variables
#dimnames = [dim for dim in nci.dimensions] 
filtered_dimnames = []
for varname in filtered_varnames:
    reduced_name       = varname + '_reduced'
    if   set(varnames).intersection(set([reduced_name])): vname = reduced_name
    else:                                                 vname = varname
    for dimname in nci.variables[vname].dimensions:
        filtered_dimnames.append(dimname)
filtered_dimnames = set(filtered_dimnames)


###########################################################################################






###########################################################################################
# Copying global attributes
nco.setncatts(nci.__dict__)


# Copying selected dimensions
for dimname in filtered_dimnames:
    dimension = nci.dimensions[dimname]    
    nco.createDimension(dimname, (len(dimension) if not dimension.isunlimited() else None))
    

# Copying selected variables (+ removing the reduced suffix + cpmpressing files)
for varname in filtered_varnames:
   
    reduced_name       = varname + '_reduced'
    if   set(varnames).intersection(set([reduced_name])): vname = reduced_name
    else:                                                 vname = varname   
    variable      = nci[vname]
    if   varname == 'cloud_top_height_1km'   : varname = 'Cloud_Top_Height_1km'
    elif varname == 'cloud_top_pressure_1km' : varname = 'Cloud_Top_Pressure_1km'
    

    #print(vname,varname)
    #print(variable.dimensions)
    #print(getattr(variable, 'coordinates') )
    #coordinates = getattr(variable, 'coordinates')
    #if '_reduced' in getattr(variable, 'coordinates') :
    #    print(varname,getattr(variable, 'coordinates') )
    #    coordinates = coordinates.replace('_reduced','')
    #dst[name].setncatts({'grid_mapping': 'rotated_pole'})
    #var_att_names = variable.ncattrs()
    #if   set(var_att_names).intersection(set(['description'])): 
    #    print('====================================',varname,'====================================')
    #    print(getattr(variable, 'description') )
    #print(varname)




    x = nco.createVariable(varname, variable.datatype, variable.dimensions, zlib=True, complevel=4)
    nco[varname].setncatts(variable.__dict__)
    nco[varname][:] = nci[vname][:]
    
    coordinates = getattr(variable, 'coordinates')
    if '_reduced' in coordinates:
        fixed_coordinates = coordinates.replace('_reduced','')
        nco[varname].setncatts({'coordinates': fixed_coordinates})
###########################################################################################
# Creating a daynight flag
varname_o = 'flag_day_night'
varname_i = 'Solar_Zenith_Day_reduced'

variable = nci[varname_i]

fillvalue = getattr(variable, '_FillValue')
flag_day_night = np.copy(nci[varname_i][:])
flag_day_night = np.where(flag_day_night == fillvalue, 0, 1)

x = nco.createVariable(varname_o, 'int8', nci[varname_i].dimensions, zlib=True, complevel=4)
nco[varname_o][:] =  flag_day_night

fixed_coordinates = getattr(variable, 'coordinates').replace('_reduced','')
nco[varname_o].setncatts({'coordinates': fixed_coordinates})


###########################################################################################
# Creating high mid low cloud_fraction variable


#ctp            = nco['Cloud_Top_Pressure'  ][:]
#cpi            = nco['Cloud_Phase_Infrared'][:]
#cf             = nco['Cloud_Fraction'      ][:]

#masks                         = {} 
#Cloud_Fraction                = {}
#masks['High'               ]  = np.where(ctp >   0, 1 , 0) * np.where(ctp <= 440, 1 , 0)
#masks['Mid'                ]  = np.where(ctp > 440, 1 , 0) * np.where(ctp <= 680, 1 , 0)
#masks['Low'                ]  = np.where(ctp > 680, 1 , 0) 
#masks['No_Cloud_IR'        ]  = np.where(cpi == 0, 1 , 0) 
#masks['Water'              ]  = np.where(cpi == 1, 1 , 0) 
#masks['Ice'                ]  = np.where(cpi == 2, 1 , 0)
#masks['Mixed'              ]  = np.where(cpi == 3, 1 , 0)
#masks['Undetermined_Phase' ]  = np.where(cpi == 6, 1 , 0)

#lname                         = {}
#lname['High'               ]  = ' [480 mb >= ctp]'
#lname['Mid'                ]  = ' [680 mb >= ctp > 480 mb]'
#lname['Low'                ]  = ' [ctp > 680 mb]'
#lname['No_Cloud_IR'        ]  = ' [Infrared sensor]'
#lname['Water'              ]  = ' [Infrared sensor]'
#lname['Ice'                ]  = ' [Infrared sensor]'
#lname['Mixed'              ]  = ' [Infrared sensor]'
#lname['Undetermined_Phase' ]  = ' [Infrared sensor]'



#variable = nco['Cloud_Fraction']

#for mask in masks:
#    if mask != 'No_Cloud_IR':
#        Cloud_Fraction[mask] = masks[mask] * cf
#        varname = 'Cloud_Fraction_' + mask 
#    else:
#        Cloud_Fraction[mask] = masks[mask] 
#        varname =  mask
#
#    x = nco.createVariable(varname, variable.datatype, variable.dimensions, zlib=True, complevel=4)
#    nco[varname].setncatts(variable.__dict__)
#    nco[varname ][:] = Cloud_Fraction[mask]
#    if mask != 'No_Cloud_IR':
#        long_name = mask + ' ' + getattr(variable, 'long_name') + lname[mask]
#    else:
#        long_name = 'Mo cloud [Infrared sensor]'
#    nco[varname].setncatts({'long_name': long_name })

#print(ncfileo)
