import matplotlib.pyplot as plt
import cartopy.feature   as cfeature
import cartopy.crs       as ccrs
import numpy             as np
import xarray            as xr
from   pylab             import cm
from   scipy             import ndimage
import netCDF4
import yaml
import sys
import os
import warnings
warnings.filterwarnings("ignore")


#################################################################################################################
### FUNCTIONS ###################################################################################################
#################################################################################################################
def make_map(ncfile, pngfile, data, cmap, vext, title,showcolorbar=True):
    dpi = 150

    # Get lat, lon and cartopy_projection_object
    ds  = xr.open_dataset(ncfile)
    lat = ds.lat.values
    lon = ds.lon.values
    m   = ccrs.RotatedPole(ds.rotated_pole.grid_north_pole_longitude,
                           ds.rotated_pole.grid_north_pole_latitude)

    # Domain limites
    xll, yll = m.transform_point(lon[ 0,  0],lat[ 0,  0], ccrs.PlateCarree())
    xur, yur = m.transform_point(lon[-1, -1],lat[-1, -1], ccrs.PlateCarree())

    # Creating figure
    fig = plt.figure()
    fig.set_dpi(dpi)
    ax = plt.axes(projection=m)
    pc = ax.pcolormesh(lon, lat, data, cmap=cmap,vmin=vext[0], vmax=vext[1], transform=ccrs.PlateCarree())
    vext[0], vext[1] = pc.get_clim() # Useful when input was vext[0]=None and/or vext[1]=None  
 
    # Domain limites
    xll, yll = m.transform_point(lon[ 0,  0],lat[ 0,  0], ccrs.PlateCarree())
    xur, yur = m.transform_point(lon[-1, -1],lat[-1, -1], ccrs.PlateCarree())
    ax.set_extent([xll, xur, yll, yur], crs=m)

    # Coastlines + political borders
    ax.coastlines()
    L0_country_ALL = cfeature.NaturalEarthFeature(category='cultural', name='admin_1_states_provinces_lakes',scale='50m',facecolor='none')
    ax.add_feature(L0_country_ALL, edgecolor='black')

    # Title
    plt.title(title, fontsize=8)

    # Colorbar
    if showcolorbar == True:
        
        if   vext[0] ==  -vext[1]: extend = 'both'
        else                     : extend = 'neither'
        sm = plt.cm.ScalarMappable(cmap=cmap,norm=plt.Normalize(vext[0],vext[1]))
        sm._A = []
        plt.colorbar(sm,ax=ax, extend=extend)

    # Saving figure
    plt.savefig(pngfile,bbox_inches='tight', dpi=dpi)
    
    #plt.close()
    

#################################################################################################################
### MAIN ########################################################################################################
#################################################################################################################






#########################################################################
# Input arguments                                                       #
#########################################################################
working_directory =         sys.argv[1]
YYYYi             =     int(sys.argv[2])
YYYYf             =     int(sys.argv[3])
period            =         sys.argv[4]
dataset           =         sys.argv[5]
layerdef_MODIS    =         sys.argv[6]
layerdef_CALIPSO  =         sys.argv[7]
window            =     int(sys.argv[8])
overwrite         =         sys.argv[9].lower()


#########################################################################
# Hardcoded values                                                      #
#########################################################################
if   period == 'annual': MMs = [1,2,3,4,5,6,7,8,9,10,11,12]
elif period == 'DJF'   : MMs = [ 1, 2,12]
elif period == 'MAM'   : MMs = [ 3, 4, 5]
elif period == 'JJA'   : MMs = [ 6, 7, 8]
elif period == 'SON'   : MMs = [ 9,10,11]
else                   : MMs = [ int(period) ] # single month

cmapv = cm.get_cmap('jet'    , 10);
cmapd = cm.get_cmap('seismic', 11);



#########################################################################
# Configuration file (yml)                                              #
#########################################################################
yml_file = working_directory + '/../config.yml'
stream = open(yml_file,'r')
config = yaml.safe_load(stream)

domain     = config['domain'        ]
dir_NetCDF = config['CALIPSOvsMODIS']['NetCDF'] + '/CALIPSO_' + layerdef_CALIPSO + '_' + dataset + '_' + layerdef_MODIS  + '/' + domain
dir_png    = config['CALIPSOvsMODIS']['png'   ] + '/CALIPSO_' + layerdef_CALIPSO + '_' + dataset + '_' + layerdef_MODIS  + '/' + domain + '/%03d' % (window) 

if not os.path.exists(dir_png): os.makedirs(dir_png)




#########################################################################
# Main part                                                             #
#########################################################################

# Summing data (value and n for each level) from all the selected months
data_sum = {}
for YYYY in range(YYYYi,YYYYf+1):
    for MM in MMs:
        ncfile = '%s/%4d%02d.nc' % (dir_NetCDF,YYYY,MM)
        ds     = xr.open_dataset(ncfile)
        for varname in ds.keys():
            if 'cloud_cover' in varname:
                if varname not in data_sum: data_sum[varname]  = ds[varname].values
                else                      : data_sum[varname] += ds[varname].values
      


# Making plot of the averaged values (temporal + spatial)
for varname in ['Tot_cloud_cover', 'High_cloud_cover', 'Mid_cloud_cover', 'Low_cloud_cover' ]:
    
    varname_cloudcover_MODIS   = varname + '_sum_MODIS'
    varname_cloudcover_CALIPSO = varname + '_sum_CALIPSO'
    varname_n                  = varname + '_n'

    'Computing temoral mean: at this point we still to have only tracks'
    data_temporal_mean_MODIS   = data_sum[varname_cloudcover_MODIS  ] / data_sum[varname_n]
    data_temporal_mean_CALIPSO = data_sum[varname_cloudcover_CALIPSO] / data_sum[varname_n]
    
    'Computing spatial mean over a square of size window x window'
    data_spatial_mean_MODIS   = ndimage.generic_filter(data_temporal_mean_MODIS  , np.nanmean, size=window, mode='constant',cval=np.nan)
    data_spatial_mean_CALIPSO = ndimage.generic_filter(data_temporal_mean_CALIPSO, np.nanmean, size=window, mode='constant',cval=np.nan) 
    data_spatial_mean_DIFF    = data_temporal_mean_MODIS - data_temporal_mean_CALIPSO

    title_MODIS   = '%s %s\n%s %d-%d' % ('MODIS'        , varname, period, YYYYi, YYYYf)
    title_CALIPSO = '%s %s\n%s %d-%d' % ('CALIPSO'      , varname, period, YYYYi, YYYYf)
    title_DIFF    = '%s %s\n%s %d-%d' % ('MODIS-CALIPSO', varname, period, YYYYi, YYYYf)

    pngfile_MODIS   = '%s/%s_%s_%d-%d_%s.png' % (dir_png,'MODIS'        ,  varname, YYYYi, YYYYf, period)
    pngfile_CALIPSO = '%s/%s_%s_%d-%d_%s.png' % (dir_png,'CALIPSO'      ,  varname, YYYYi, YYYYf, period)
    pngfile_DIFF    = '%s/%s_%s_%d-%d_%s.png' % (dir_png,'MODIS-CALIPSO',  varname, YYYYi, YYYYf, period)

    make_map(ncfile, pngfile_MODIS  , data_spatial_mean_MODIS  , cmapv, [ 0.00,1.00], title_MODIS  )
    make_map(ncfile, pngfile_CALIPSO, data_spatial_mean_CALIPSO, cmapv, [ 0.00,1.00], title_CALIPSO)
    make_map(ncfile, pngfile_DIFF   , data_spatial_mean_DIFF   , cmapd, [-0.55,0.55], title_DIFF   )
    print(pngfile_MODIS)

    #plt.show()


















