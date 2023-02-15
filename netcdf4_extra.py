import netCDF4
import numpy   as np
NaN = np.nan;





##########################################################################################
def netcdf4_merge_files_and_extract_field(ncfile_list,varname,missing_value=NaN):
    for ncfile in ncfile_list:
        #print(ncfile, var)
        ncdata = netCDF4.Dataset(ncfile,'r');
        #print(ncdata.variables[varname])
        ###ncvar         = np.squeeze(ncdata.variables[varname]).astype(np.float32)
        ###missing_value = np.float32(missing_value)
        ncvar         = np.squeeze(ncdata.variables[varname])
        if 'NCVAR' in locals(): NCVAR = np.concatenate((NCVAR,ncvar),axis=0)
        else                  : NCVAR = ncvar
    #if not np.isnan(missing_value): NCVAR [ NCVAR == missing_value ] = NaN
    return NCVAR

###########################################################################################
def netcdf4_extract_fields_attributes(ncfile):
    dataset_attribute_all_fields = {}
    ncdata = netCDF4.Dataset(ncfile,'r');
    for varname, variable in ncdata.variables.items():
        dataset_attribute_single_field = {}
        for attrname in variable.ncattrs():
            #print("{}: {} -- {}".format(varname, attrname, getattr(variable, attrname)))
            dataset_attribute_single_field[attrname] = getattr(variable, attrname)
        dataset_attribute_all_fields[varname] = dataset_attribute_single_field
    return(dataset_attribute_all_fields)









###########################################################################################
def netcdf4_extract_attributes(ncfile,attributes):
    
    ncdata = netCDF4.Dataset(ncfile,'r');
    for varname, variable in ncdata.variables.items():
        varname_flag = 0
        attribute_single_field = {}

        #Extracting attribute from the netCDF file
        for attrname in variable.ncattrs():
            #print("{}: {} -- {}".format(varname, attrname, getattr(variable, attrname)))
            attribute_single_field[attrname] = getattr(variable, attrname)
            varname_flag = 1
        #Copying prexisting attribute (if any)
        if varname in attributes and varname_flag == 0:
            for attrname in attributes[varname]:
                attribute_single_field[attrname] = attributes[varname][attrname]
      
        #Setting default value for user_scale_factor and missing_value (if not already existing)
        if 'user_scale_factor' not in attribute_single_field: attribute_single_field['user_scale_factor'] = 1
        if 'missing_value'     not in attribute_single_field: attribute_single_field['missing_value'    ] = NaN   #Nothing will be done to the field in netcdf4_extract_fields if missing_value is set to NaN


        attributes[varname] = attribute_single_field
    return attributes




##########################################################################################
def netcdf4_extract_field(varname,ncfiles,scale_factor,missing_value):
    for ncfile in ncfiles:
        ncdata = netCDF4.Dataset(ncfile,'r');
        #ncvar         = np.squeeze(ncdata.variables[varname]).astype(np.float32)
        #missing_value = np.float32(missing_value)
        ncvar         = np.squeeze(ncdata.variables[varname])
        if 'NCVAR' in locals(): NCVAR = np.concatenate((NCVAR,ncvar),axis=0)
        else                  : NCVAR = ncvar
    #if not np.isnan(missing_value): NCVAR [ NCVAR == missing_value ] = NaN
    NCVAR = NCVAR * scale_factor
    return NCVAR








##########################################################################################
def netcdf4_extract_fields_and_attributes(varnames,ncfiles,fields,attributes):
    if isinstance(ncfiles, str): ncfiles = [ ncfiles ]
    for ncfile in ncfiles:
       netcdf4_extract_attributes(ncfile,attributes)

    if varnames == 'all_variables':
        varnames = []
        for attribute in attributes: varnames.append(attribute)  
    for varname in varnames:
        fields[varname] = netcdf4_extract_field(varname, ncfiles, attributes[varname]['user_scale_factor'], attributes[varname]['missing_value'])

















#############################################################################################
def ncdump(nc_fid, verb=True):
    '''

    ncdump outputs dimensions, variables and their attribute information.
    The information is similar to that of NCAR's ncdump utility.
    ncdump requires a valid instance of Dataset.

    Parameters
    ----------
    nc_fid : netCDF4.Dataset
        A netCDF4 dateset object
    verb : Boolean
        whether or not nc_attrs, nc_dims, and nc_vars are printed

    Returns
    -------
    nc_attrs : list
        A Python list of the NetCDF file global attributes
    nc_dims : list
        A Python list of the NetCDF file dimensions
    nc_vars : list
        A Python list of the NetCDF file variables
    '''
    def print_ncattr(key):
        """
        Prints the NetCDF file attributes for a given key

        Parameters
        ----------
        key : unicode
            a valid netCDF4.Dataset.variables key
        """
        try:
            print ("\t\ttype:", repr(nc_fid.variables[key].dtype))
            for ncattr in nc_fid.variables[key].ncattrs():
                print ('\t\t%s:' % ncattr, repr(nc_fid.variables[key].getncattr(ncattr)))
        except KeyError:
            print ("\t\tWARNING: %s does not contain variable attributes" % key)

    # NetCDF global attributes
    nc_attrs = nc_fid.ncattrs()
    if verb:
        print ("NetCDF Global Attributes:")
        for nc_attr in nc_attrs:
            print ('\t%s:' % nc_attr, repr(nc_fid.getncattr(nc_attr)))
    nc_dims = [dim for dim in nc_fid.dimensions]  # list of nc dimensions
    # Dimension shape information.
    if verb:
        print ("NetCDF dimension information:")
        for dim in nc_dims:
            print ("\tName:", dim)
            print ("\t\tsize:", len(nc_fid.dimensions[dim]))
            print_ncattr(dim)
    # Variable information.
    nc_vars = [var for var in nc_fid.variables]  # list of nc variables
    if verb:
        print ("NetCDF variable information:")
        for var in nc_vars:
            if var not in nc_dims:
                print ('\tName:', var)
                print ("\t\tdimensions:", nc_fid.variables[var].dimensions)
                print ("\t\tsize:", nc_fid.variables[var].size)
                print_ncattr(var)
    return nc_attrs, nc_dims, nc_vars
