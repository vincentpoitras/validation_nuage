import sys
import os
import netCDF4
import numpy             as np
import matplotlib.pyplot as plt

# Info: poitras.vincent@uqam.ca
# Date: 2022-05-09


ncfilei1 = sys.argv[1]
ncfilei2 = sys.argv[2]
ncfileo  = sys.argv[3]

nci1 = netCDF4.Dataset(ncfilei1, 'r');
nci2 = netCDF4.Dataset(ncfilei2, 'r');
nco  = netCDF4.Dataset(ncfileo , 'w');



varnames_to_do_not_average = [ 'lon', 'lat', 'rlon', 'rlat', 'rotated_pole' ]
varnames                   = [var for var in nci1.variables if var  not in varnames_to_do_not_average ]


# Copying global attributes
nco.setncatts(nci1.__dict__)

# Creating dimensions
dimnames = [ dim for dim in nci1.dimensions ]
for dimname in dimnames:
    dimension = nci1.dimensions[dimname]
    nco.createDimension(dimname, (len(dimension) if not dimension.isunlimited() else None))

# Creating variables
varnames = [ var for var in nci1.variables ]
for varname in varnames:
    variable = nci1[varname]
    x = nco.createVariable(varname, variable.datatype, variable.dimensions, zlib=True, complevel=4)
    nco[varname].setncatts(variable.__dict__)

# Copying values of the variables which don't need to be averaged
varnames_to_do_not_average = [ 'lon', 'lat', 'rlon', 'rlat', 'rotated_pole' ]
for varname in varnames_to_do_not_average:
    nco[varname][:] = nci1[varname][:]




# Copying values of the variables which need to be averaged
varnames = [var for var in nci1.variables if var  not in  varnames_to_do_not_average  ]
varnames.remove('Cloud_Phase_Infrared')
for varname in varnames:
    missing_value = getattr(nci1[varname], 'missing_value')
    ncx = np.stack((nci1[varname][:],nci2[varname][:])).astype(float)
    ncx [ ncx == missing_value ] = np.nan
    ncx = np.nanmean(ncx,axis=0)
    ncx [ np.isnan(ncx) ] = missing_value
    nco[varname][:] = ncx


# Copying categorical values (Cloud_Phase_Infrared) 
# Note: flag_day_night is equal for nci1 and nci2 (when value are present), so there is no need to process it here (but it could be)
cf1 = np.array(nci1['Cloud_Fraction'][:])
cf2 = np.array(nci2['Cloud_Fraction'][:])
missing_value = getattr(nci1['Cloud_Fraction'], 'missing_value')
cf1 [ cf1 == missing_value ] = -1
cf2 [ cf2 == missing_value ] = -1
varnames = [ 'Cloud_Phase_Infrared' ]
for varname in varnames:
    missing_value = getattr(nci1[varname], 'missing_value')
    ncx = np.where(cf1>cf2,nci1[varname][:],nci2[varname][:]) 
    nco[varname][:] = ncx

print(ncfileo)
