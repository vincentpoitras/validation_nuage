from   datetime                 import datetime
from   datetime                 import timedelta
import matplotlib.pyplot as plt
import sys
import yaml
import math
import os.path
import netCDF4
import numpy as np
from   shapely.geometry         import Point
from   shapely.geometry.polygon import Polygon



############################################################################
###                      shapely related functions                       ###
############################################################################
def construct_coord(x,y):
    '''
    Convert a set of 2 array in an array of "pairs" (requiered by shapely)
    Example
    x     = [1,2,3]
    y     = [0,4,8]
    coord = [(1,0), (2,4), 3,8)]
    '''
    coord = []
    N     = len(x)
    for n in range(N):
        coord.append((x[n],y[n]))
    return coord


def point_inside_polygon(points, polygon):
    '''
    Inputs
        points: 
            List of points that will be loop on
            The points correspond to the lon-lat coord of the satellite
            format: [ (lon1, lat1), (lon2,lat2) ... (lonn, latn)]
        polygon
            List of points forming a closed polygon
            The polygon corresponds to the domain hedge (each cell center on the hedge)
            format: [ (LON1, LAT1), (LON2,LAT2) ... (LONn=LON1, LATn=LAT1)]
    Outputs
        Flags
            1-D array with 
                0:  (lon1, lat1) is outside the domain
                1:  (lon1, lat1) is  inside the domain
        
    '''
    polygon = Polygon(polygon)
    N       = len(points)
    flag    = np.zeros(N)
    for n in range(N):
        point = Point(points[n])
        if polygon.contains(point):
            flag[n] = 1
    return flag







def find_ncfile(directory):
    '''
    For a directory, the directory will be scanned recursively in order to find a NetCDF file
    We are searching among the file taht we convert from fst, tehay are supposed to have a lat and lon fields
    in which we are interested
    '''
    ncfile=''
    for root, dirs, files in os.walk(os.path.abspath(directory)):
        for file in files:
            ncfile = os.path.join(root, file)
            if ncfile.endswith('.nc'):
                break
        if ncfile.endswith('.nc'):
            break
    
    if not ncfile.endswith('.nc'):
        print('ERROR: Unable to find a ncfile in %s (and in any subdirectory)' % (directory))
        print('ERROR: Exit')
        exit()
    else:
        return ncfile

def extract_domain_coord(ncfile):
    '''
    Extract the lat lon value of the grid-cells on the 4 hedges of the domain.
    segment 1 (0,0) --> (1,0)
    segment 2 (1,0) --> (1,1)  
    segment 3 (1,1) --> (0,1)  (reverse [::-1])
    segemnt 4 (0,1) --> (0,0)  (reverse [::-1])
    The 4 segments are then concatenate
    The 2 array are finally converted into an array of "pairs of array"
    Examples:
        lat   = [1,2,3]
        lon   = [6,7,8]
        coord = [(1,6), (2,7), (3,8) ]

    '''
    nc  = netCDF4.Dataset(ncfile, 'r');
    lat = nc['lat'][:]
    lon = nc['lon'][:]

    lon1 = lon[0,:]; lon2 = lon[:,-1]; lon3 = lon[-1,:][::-1]; lon4 = lon[:,0][::-1]
    lat1 = lat[0,:]; lat2 = lat[:,-1]; lat3 = lat[-1,:][::-1]; lat4 = lat[:,0][::-1]
    
    longitude = np.concatenate((lon1, lon2, lon3, lon4)) - 360 
    latitude  = np.concatenate((lat1, lat2, lat3, lat4))

    plt.figure(1);
    plt.plot(longitude,latitude)



    coord = construct_coord(longitude,latitude)
    #plt.plot(longitude, latitude,'r-')
    #plt.show()
    
    coord = construct_coord(longitude,latitude)
    return coord



############################################################################
###                       Satellite-related functions                    ###
############################################################################
def set_satellite_time(ncfile):
    '''
    INPUT [Profile_UTC_Time]:  formatted as yymmdd.ffffffff
        yy        last two digits of year
        mm        month
        dd        day 
        ffffffff  fractional part of the day
    OUTPUT [UTC_time_str]: formatted as %Y%m%d%H%M%S.%f (see below for more details)
    '''
    nc            = netCDF4.Dataset(ncfile,'r');
    #Profile_time = nc['Profile_Time'][:]
    UTC_time      = nc['Profile_UTC_Time'][:]+20000000

    I   = len(UTC_time[:,0])
    J   = len(UTC_time[0,:])
    UTC_time_str = np.empty((I,J),dtype=object)
    for i in range(I):
        for j in range(J):
            dec, utc_YMD = math.modf(UTC_time[i,j]) # %Y%m%d YYYMMDD         (decimal part is reused below)
            dec, utc_H   = math.modf(24*dec)        # %H     2-digit hour    (decimal part is reused below)
            dec, utc_M   = math.modf(60*dec)        # %M     2-digit minute  (decimal part is reused below)
            dec, utc_S   = math.modf(60*dec)        # %S     2-digit secoond (here decimal part will be used directly in the output as the .%f)

            UTC_time_str[i,j]=str(int(utc_YMD)) + "{:02d}".format(int(utc_H)) + "{:02d}".format(int(utc_M)) + "{:02d}".format(int(utc_S)) + '.' + "{:.6f}".format(dec).split('.')[1]

    return UTC_time_str



def extract_satellite_track(ncfile, domain_coord):

    # Extract data from ncfile
    nc   = netCDF4.Dataset(ncfile,'r');
    lon  = nc['Longitude'][:,1]             # 3 values: initial[0], central[1], final[2], keeping the central
    lat  = nc['Latitude' ][:,1]             # 3 values: initial[0], central[1], final[2], keeping the central
    time = set_satellite_time(ncfile)[:,1]  # 3 values: initial[0], central[1], final[2], keeping the central
    

    # Shift satellite longitude in case domain longitude <-180 OR domain longitude > 180 
    # The shift concern only the part of the track that will be re-located in part of the domain with longitude <-180 OR with longitude > 180
    # Not able to treat the case where domain longitude <-180 AND domain longitude > 180 (which should never occur anyway)
    # When comping min and max, we are also considering the lat in domain_coord, but is not important since -90 <= lat <= 90
    lonmax = np.max(domain_coord)
    lonmin = np.min(domain_coord)
    if lonmax > 180:
        dlon = lonmax - 180
        lon = np.where(lon<-180+dlon, lon+360, lon)
    elif lonmin < -180:
        dlon = -lonmin - 180
        lon = np.where(lon>180-dlon, lon-360, lon)


    # Constructing cloudsat coord:  [x1,x2...] [y1,y2,...] --> [ (x1,y1), (x2,y2), ...]
    track_coord = construct_coord(lon, lat)

    # Setting a flag (1 = inside the polygon, 0 = outside the polygon)
    spatial_flag = point_inside_polygon(track_coord, domain_coord)
    
    # Number of data (Nray is the name used in calipso -- related to laserray???)
    Nray = int(np.sum(spatial_flag))

    # Initializing output data
    data_out = {}
    data_out['longitude'] = np.empty(Nray, dtype=float)
    data_out['latitude' ] = np.empty(Nray, dtype=float)
    data_out['time'     ] = np.empty(Nray, dtype=object)
    data_out['index'    ] = np.empty(Nray, dtype=int)

    # Output loop
    j = 0
    for i in range(len(spatial_flag)):
        if (spatial_flag[i] > 0):
            data_out['longitude'][j] = lon [i]
            data_out['latitude' ][j] = lat [i]
            data_out['time'     ][j] = time[i]
            data_out['index'    ][j] = i
        
            j = j + 1
        #print(i,spatial_flag[i], lon[i], lat[i], time[i]) 
    if Nray > 0:
        #plt.plot(lon                  , lat                 ,'k')
        plt.plot(data_out['longitude'], data_out['latitude'],'r')
        plt.draw()
        plt.pause(0.001)
        #input("Press [enter] to continue.")
        
    return data_out




def print_output_data(track, fout):
    format_in   = '%Y%m%d%H%M%S.%f'
    format_out  = '%Y%m%d%H%M'
    format_MM   = '%m'

    n   = len(track['latitude'])
    fti = datetime.strptime(str(track['time'][ 0]), format_in)
    ftf = datetime.strptime(str(track['time'][-1]), format_in)
    ti  = fti.strftime('%Y%m%d%H%M%S')
    tf  = ftf.strftime('%Y%m%d%H%M%S')
    dt  = ftf - fti
    ftm = (fti + dt/2)
    tm  = (ftm.replace(second=0, microsecond=0, minute=0, hour=ftm.hour) + timedelta(hours=ftm.minute//30)).strftime(format_out)
    MM  = (ftm.replace(second=0, microsecond=0, minute=0, hour=ftm.hour) + timedelta(hours=ftm.minute//30)).strftime(format_MM)

    YYYYMMDD_gem  = datetime.strptime(tm,format_out).strftime('%Y%m%d')
    t_gem   = int(datetime.strptime(tm,format_out).strftime('%H'))-1
    if t_gem == -1:
        t_gem = 23
        YYYYMMDD_gem = (datetime.strptime(YYYYMMDD_gem,'%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
    
    strout = ncfile+' '+  "{:4d}".format(n)+'   '+ ti+' '+  tf+'   '+  tm+'  '+ MM+' ' +  YYYYMMDD_gem+' '+  "{:2d}".format(t_gem) + '\n' 
    print(strout)
    fout.write(strout)
    




############################################################################
###                              MAIN PART                               ###
############################################################################
if __name__ == '__main__':
    
    # Input arguments
    yml_file =  sys.argv[1]
    YYYY     =  sys.argv[2]

    # Read the confguration file
    stream = open(yml_file,'r')
    config = yaml.safe_load(stream)
    GEM5_NetCDF       = config['GEM5'   ]['NetCDF']
    CALIPSO_NetCDF    = config['CALIPSO']['NetCDF'] + '/' + YYYY
    CALIPSO_list_dir  = config['CALIPSO']['list'  ] + '/' + config['domain'] 
    

    # Creating output directory (if needed) + assigning the path to the outputfile
    print(CALIPSO_list_dir)
    if os.path.exists(CALIPSO_list_dir) == False:
        os.mkdir(CALIPSO_list_dir)
    CALIPSO_list = CALIPSO_list_dir + '/' + YYYY + '.txt'

    # Extract domain border coordinates (1st search for a NetCDF file in the GEM5_Samples_NetCDF directory)
    ncfile_domain = find_ncfile(GEM5_NetCDF)
    domain_coord  = extract_domain_coord(ncfile_domain)

    # Open the output file
    fout = open(CALIPSO_list, 'w')

    # Loop over each file in CALISPO_NetCDF (in alpha-numerical order --> from the ealierstdate to the latest)
    list_of_files = sorted( filter( lambda x: os.path.isfile(os.path.join(CALIPSO_NetCDF, x)),os.listdir(CALIPSO_NetCDF) ) )
    for file_name in list_of_files:
        ncfile = CALIPSO_NetCDF + '/' + file_name
        # Make sure it is a NetCDF file
        if ncfile.endswith('.nc'):
            #print(ncfile)
            # Extract track satellite located inside the polygon defined by domain_cord
            track = extract_satellite_track(ncfile, domain_coord)
            
            # Check if the track is non empty (here we check latitude, both any field would have been ok to check)
            if 'latitude' in track:
                if len(track['latitude']) > 0:
                    print_output_data(track,fout)
        
        
    exit()
    # Loop over each file in CALISPO_NetCDF
    for root, dirs, files in os.walk(os.path.abspath(CALIPSO_NetCDF)):
        for file in files:
            ncfile = os.path.join(root, file)
            # Make sure it is a NetCDF file
            if ncfile.endswith('.nc'):
                print(ncfile)
                # Extract track satellite located inside the polygon defined by domain_cord
                #track = extract_satellite_track(ncfile, domain_coord)

exit()
ncfile =  sys.argv[1]  
fileo  =  sys.argv[2]




if os.path.isfile(fileo):
    mode='a'
else:
    mode='w'

f = open(fileo, mode)


format_in   = '%Y%m%d%H%M%S.%f'
format_out  = '%Y%m%d%H%M'
format_MM   = '%m'

domain_coord = generate_domain_coord(domain)
track        = extract_satellite_track(ncfile, domain_coord)



n = 0
if 'latitude' in track:
    n = len(track['latitude']) 
    if n > 0:
        fti = datetime.strptime(str(track['time'][ 0]), format_in)
        ftf = datetime.strptime(str(track['time'][-1]), format_in)
        ti  = fti.strftime('%Y%m%d%H%M%S')
        tf  = ftf.strftime('%Y%m%d%H%M%S')
        dt  = ftf - fti
        ftm = (fti + dt/2)
        tm  = (ftm.replace(second=0, microsecond=0, minute=0, hour=ftm.hour) + timedelta(hours=ftm.minute//30)).strftime(format_out)
        MM  = (ftm.replace(second=0, microsecond=0, minute=0, hour=ftm.hour) + timedelta(hours=ftm.minute//30)).strftime(format_MM)

        YYYYMMDD_gem  = datetime.strptime(tm,format_out).strftime('%Y%m%d')
        t_gem   = int(datetime.strptime(tm,format_out).strftime('%H'))-1
        if t_gem == -1: 
            t_gem = 23
            YYYYMMDD_gem = (datetime.strptime(YYYYMMDD_gem,'%Y%m%d') - timedelta(days=1)).strftime('%Y%m%d')
        strout = ncfile+' '+  "{:4d}".format(n)+'   '+ ti+' '+  tf+'   '+  tm+'  '+ MM+' ' +  YYYYMMDD_gem+' '+  "{:2d}".format(t_gem) + '\n'
        #print(strout)
        f.write(strout)

print(n) # value return to the main script



