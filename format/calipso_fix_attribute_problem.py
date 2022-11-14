import netCDF4
import sys;                  


nc_file = sys.argv[1]
ncdata  = netCDF4.Dataset(nc_file,'a');

for var in ncdata.variables:
    if 'valid_range' in ncdata.variables[var].ncattrs():
        valid_range       = ncdata.variables[var].getncattr('valid_range')
        data_format       = ncdata.variables[var].getncattr('format')
        valid_range_array = valid_range.split('...')

        if   'Int'   in data_format: valid_range_formated = [ int  (valid_range_array[0]), int  (valid_range_array[1]) ]
        elif 'Float' in data_format: valid_range_formated = [ float(valid_range_array[0]), float(valid_range_array[1]) ]
        #print(valid_range,valid_range_formated, data_format)
        ncdata[var].setncatts({'valid_range' : valid_range_formated}  )
        ncdata[var].setncatts({'scale_factor':                    1}  )
 
         




