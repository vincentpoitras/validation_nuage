import sys
import os
import netCDF4
import shutil
import numpy             as np
import matplotlib.pyplot as plt
######################################################################################################################

ncfiles  = sys.argv[1].split()
nncfiles = len(ncfiles)



######################################################################################################################
if nncfiles < 2:

    print('ERROR: An output filename and a least 1 input filename must be provided')
    print('     ' + files)
    exit()
######################################################################################################################
elif nncfiles == 2:
    shutil.copyfile(ncfiles[1], ncfiles[0])

######################################################################################################################
else:
    # Creating a list of variable to merge and to do not merge
    nc1                      = netCDF4.Dataset(ncfiles[1], 'r');
    varnames_to_do_not_merge = [ 'lon', 'lat', 'rlon', 'rlat', 'rotated_pole' ]
    varnames_to_merge        = [var for var in nc1.variables if var  not in varnames_to_do_not_merge ]

    # Creating empty fields where data will be merged
    mask      = {}
    field     = {}
    fillvalue = {}
    for varname in varnames_to_merge:
        field    [varname] = np.zeros(nc1[varname].shape, nc1[varname].datatype)
        mask     [varname] = np.zeros(nc1[varname].shape, nc1[varname].datatype)
        fillvalue[varname] = getattr(nc1[varname], 'missing_value')


    
    # Merging field and mask
    ncfileis = ncfiles[1:nncfiles]
    for ncfilei in ncfileis:
        nci = netCDF4.Dataset(ncfilei, 'r');
        for varname in varnames_to_merge:
            field[varname] = field[varname] + np.where(np.array(nci[varname][:])==fillvalue[varname],0,nci[varname][:])
            mask [varname] = mask[varname]  + np.where(np.array(nci[varname][:])==fillvalue[varname],0,              1)
            #plt.imshow(field[varname])
            #plt.show()

    # Masking field
    for varname in varnames_to_merge:
        mask [varname] = np.where(mask[varname] == 0, fillvalue[varname],0)
        field[varname] = field[varname] + mask[varname]        

    ########################################################
    # Creating the ouput file
    nco = netCDF4.Dataset(ncfiles[0], 'w', format='NETCDF4')


    # Copying global attributes
    nco.setncatts(nc1.__dict__)

    # Creating dimensions
    dimnames = [ dim for dim in nc1.dimensions ]  
    for dimname in dimnames:
        dimension = nci.dimensions[dimname]
        nco.createDimension(dimname, (len(dimension) if not dimension.isunlimited() else None))

    # Creating variables
    varnames = [ var for var in nc1.variables ]
    for varname in varnames:
        variable = nci[varname]
        x = nco.createVariable(varname, variable.datatype, variable.dimensions, zlib=True, complevel=4)
        nco[varname].setncatts(variable.__dict__)
        if varname in varnames_to_merge:
            nco[varname][:] = field[varname]
        else:
            nco[varname][:] = nci[varname][:]

######################################################################################################################
# Delete file if not data are available (--> located outside of the domain)
# Should be displaced above to avoid useless computation: TODO
nco = netCDF4.Dataset(ncfiles[0], 'r', format='NETCDF4')
if not np.sum(nco['Cloud_Fraction'][:]) < np.inf :
    print('Created + deleted (no data inside the domain)')
    os.remove(ncfiles[0]) 
else:
    print('Created')

