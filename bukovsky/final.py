import xarray as xr
import netCDF4
import yaml
import sys
import os
import shutil
from scipy import ndimage

import numpy             as np
import xarray            as xr
import cartopy.crs       as ccrs
import cartopy.feature   as cfeature
import matplotlib.cm     as cm
import matplotlib.pyplot as plt
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
    #plt.savefig(pngfile,bbox_inches='tight', dpi=dpi)
    plt.show()
    #plt.close()






#########################################################################
# Input arguments                                                       #
#########################################################################

yml_file = os.getcwd() + '/../config.yml'

stream = open(yml_file,'r')
config = yaml.safe_load(stream)
rootdir     = config['bukovsky'];

if not os.path.exists(rootdir + '/final'): os.makedirs(rootdir + '/final')


cmap = cm.get_cmap('jet',1)


nc = rootdir + '/remap/sealandmask.nc' 
ds  = xr.open_dataset(nc)
landmask = np.where( np.squeeze(ds['mask'].values ) == 1, 1     , np.nan)
seamask  = np.where( np.squeeze(ds['mask'].values ) == 1, np.nan,      1)



#########################################################################
# Régions copiées sans modification                                     #
#########################################################################
regions = ['Appalachia.nc',  'NPlains.nc']

if 1==1:
    for region in regions:
        nci = rootdir + '/remap/' +  region
        nco = rootdir + '/final/' +  region
        shutil.copy(nci, nco)




#########################################################################
# Régions aquatique recrées : rectangle + mask                          #
#########################################################################


if 1 == 0:
    region='ColdNEPacific.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )
   
    m = m * np.nan
    m[345:500,50:150] = 1
    m = m * seamask


    # Pixel manquant Grand-Lacs
    region2='PacificNW.nc'
    nci2 = rootdir + '/remap/' +  region2
    ds2  = xr.open_dataset(nci2)
    m2   = np.squeeze(ds2['mask'].values )
    M    = np.where(~np.isnan(m2), m2, m)
    M = ndimage.binary_fill_holes(~np.isnan(M)).astype(float)
    M[M == 0] = np.nan
    m = np.where(m2==1, np.nan, M)



    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,1], region, showcolorbar=False)


if 1 == 0:
    region='GreatLakes.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )

    m = m * np.nan
    m[250:330,325:425] = 1
    m = m * seamask

    m = ndimage.binary_closing(~np.isnan(m)).astype(float)
    m[m == 0] = np.nan

    m = ndimage.binary_fill_holes(~np.isnan(m)).astype(float)
    m[m == 0] = np.nan


    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,1], region, showcolorbar=False)




if 1 == 0:
    region='WarmNEPacific.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )

    m = m * np.nan
    m[120:200,50:140] = 1
    m[120:170,50:150] = 1
    m[120:140,50:160] = 1
    m = m * seamask

    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,1], region, showcolorbar=False)


if 1 == 0:
    region='Hudson.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )

    m = m * np.nan
    m[350:460,300:400] = 1
    m = m * seamask


    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,1], region, showcolorbar=False)


if 1 == 0:
    region='WarmNWAtlantic.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )

    m = m * np.nan
    m[130:230,425:550] = 1
    m[150:230,415:550] = 1
    m = m * seamask
    m[130:200,440:550] = 1
    ds['mask'].values[0,:,:] = m

    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,1], region, showcolorbar=False)





#########################################################################
# Régions modifiées            :                                        #
#########################################################################


if 1 == 1:
    region='Appalachia.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )

    #m = m * np.nan
    m[269:274,395:405] = 1
    m[270:275,396:406] = 1
    m[271:276,397:407] = 1
    #m = m * np.nan
    m[281:290,393:405] = np.nan

    region2='GreatLakes.nc'
    nci2 = rootdir + '/final/' +  region2
    ds2  = xr.open_dataset(nci2)
    m2   = np.squeeze(ds2['mask'].values )
    m = np.where(m2==1, np.nan, m)

    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,1], region, showcolorbar=False)



if 1 == 0:
    region='PacificNW.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )
    
    m[0:346,:] = np.nan

    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,1], region, showcolorbar=False)



if 1 == 0:
    region='Southwest.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values )

    m[140:185,135:160] =  np.nan
    m[100:141,135:175] =  np.nan

    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,2], region, showcolorbar=False)


if 1 == 0:
    region='EastBoreal.nc'
    nci = rootdir + '/remap/' +  region
    nco = rootdir + '/final/' +  region
    ds  = xr.open_dataset(nci)
    m   = np.squeeze(ds['mask'].values ) 

    # Pixels manquant baie d'hudson
    xi = 300; yi = 375;  
    xf = 373; yf = 420;
    m[yi:yf,xi:xf] =  landmask[yi:yf,xi:xf]

    # Pixels manqaunt au nord de l'estiare du St-laurent
    xi = 450; yi = 350;
    xf = 455; yf = 365;
    m[yi:yf,xi:xf] =  landmask[yi:yf,xi:xf]

    xi = 454; yi = 358;
    xf = 460; yf = 365;
    m[yi:yf,xi:xf] =  landmask[yi:yf,xi:xf]

    xi = 459; yi = 360;
    xf = 462; yf = 366;
    m[yi:yf,xi:xf] =  landmask[yi:yf,xi:xf]


    # Pixel manqants au nors du fleuve st-laurent
    xi = 440; yi = 345;
    xf = 452; yf = 350;
    m[yi:yf,xi:xf] =  1

    xi = 440; yi = 340;
    xf = 451; yf = 345;
    m[yi:yf,xi:xf] =  1

    xi = 440; yi = 337;
    xf = 450; yf = 340;
    m[yi:yf,xi:xf] =  1

    xi = 440; yi = 333;
    xf = 448; yf = 337;
    m[yi:yf,xi:xf] =  1

    # Pixels excédentaire au sud du fleuve st-laurent
    xi = 446; yi = 332;
    xf = 449; yf = 334;
    m[yi:yf,xi:xf] =  np.nan

    xi = 445; yi = 331;
    xf = 447; yf = 333;
    m[yi:yf,xi:xf] =  np.nan

    # Lacs à l,intérieur du domaine (Winnipeg, Nippigon, St-Jean, etc)
    m = ndimage.binary_fill_holes(~np.isnan(m)).astype(float)
    m[m == 0] = np.nan

    # Pixel manquant Grand-Lacs
    region2='GreatLakes.nc'
    nci2 = rootdir + '/final/' +  region2
    ds2  = xr.open_dataset(nci2)
    m2   = np.squeeze(ds2['mask'].values )

    #m = m * np.nan
    xi = 370; yi = 310;
    xf = 400; yf = 320;
    m[yi:yf,xi:xf] =  1
    m = np.where(m2==1, np.nan, m)

    #m = m * np.nan
    xi = 320; yi = 325;
    xf = 350; yf = 333;
    m[yi:yf,xi:xf] =  1
    m = np.where(m2==1, np.nan, m)

    #m = m * np.nan
    xi = 320; yi = 317;
    xf = 337; yf = 325;
    m[yi:yf,xi:xf] =  1
    m = np.where(m2==1, np.nan, m)
    
    M    = np.where(~np.isnan(m2), m2, m)
    M = ndimage.binary_fill_holes(~np.isnan(M)).astype(float)
    M[M == 0] = np.nan
    m = np.where(m2==1, np.nan, M)



    ds['mask'].values[0,:,:] = m
    ds.to_netcdf(nco)
    make_map(nci, 'x', m, cmap, [0,2], region, showcolorbar=False)





