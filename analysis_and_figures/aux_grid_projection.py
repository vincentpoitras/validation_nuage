import numpy as np
PI  = np.pi
NaN = np.nan

###############################################################################################################
def rotate_rotlatlon(lon,lat,south_pole_coordinates,rotation_type):


  #CONVERT INPUT DATA FROM DEGREES TO RADIANS
  lon = np.array(lon)
  lat = np.array(lat)
  lon = (lon*PI)/180;                            # Convert degrees to radians
  lat = (lat*PI)/180;                            # Convert degrees to radians

  SP_lon = np.array(south_pole_coordinates[0]);
  SP_lat = np.array(south_pole_coordinates[1]);
  theta  = SP_lat + 90;                          # Rotation angle around y-axis;
  phi    = SP_lon;                               # Rotation angle around z-axis;
  theta  = (theta*PI)/180;                       # Convert degrees to radians
  phi    = (phi  *PI)/180;                       # Convert degrees to radians


  #CONVERTION FROM SPHERICAL TO CARTESIAN COORDINATES
  x = np.cos(lon)*np.cos(lat); 
  y = np.sin(lon)*np.cos(lat);
  z = np.sin(lat);


  #CONVERT FROM THE SOURCE GRID TO THE TARGET GRID
  if   rotation_type == "unrot2rot":     #(Regular grid --> Rotated grid)
    x_new =  np.cos(theta)*np.cos(phi)*x  +  np.cos(theta)*np.sin(phi)*y  +  np.sin(theta)*z;
    y_new =               -np.sin(phi)*x  +                np.cos(phi)*y                    ;
    z_new = -np.sin(theta)*np.cos(phi)*x  -  np.sin(theta)*np.sin(phi)*y  +  np.cos(theta)*z;

  elif rotation_type == "rot2unrot":     #(Rotated grid --> Regular grid)
    phi   = -phi;
    theta = -theta;
    x_new =  np.cos(theta)*np.cos(phi)*x  +  np.sin(phi)*y  +  np.sin(theta)*np.cos(phi)*z;
    y_new = -np.cos(theta)*np.sin(phi)*x  +  np.cos(phi)*y  -  np.sin(theta)*np.sin(phi)*z;
    z_new = -np.sin(theta)            *x  +                    np.cos(theta)            *z;

  else:
    print('ERROR: Accepted value for rotation_type: unrot2rot, rot2unrot')
    lon_new  = NaN
    lat_new  = NaN
    return(lon_new, lat_new)
 

  #CONVERTING CARTESIAN COORDINATES BACK TO SPHERICAL COORDINATES
  lon_new = np.arctan2(y_new,x_new)
  lat_new = np.arcsin(z_new)


  #CONVERTING RADIANS BACK TO DEGREES
  lon_new = (lon_new*180)/PI; 
  lat_new = (lat_new*180)/PI;


  #RETURNING THE NEW VALUES
  return(lon_new, lat_new)




#############################################################################################################
def convert_rotlatlon_to_cartesian(v1,v2,grd,domain_type,convertion_type):

    domain_type     = domain_type.lower()
    convertion_type = convertion_type.lower()
    xlat1   = grd["xlat1"  ];   xlon1 = grd["xlon1"]   #1st point on the rotated equator
    xlat2   = grd["xlat2"  ];   xlon2 = grd["xlon2"]   #2nd point on the rotated equator
    dx      = grd["dx"     ];   dy    = grd["dy"   ]   #Grid-cell size in the rotated grid
    iref    = grd["iref"   ];   jref  = grd["jref" ]   #Reference point coordinates in index space
    lonr    = grd["lonr"   ];   latr  = grd["latr" ]   #Reference point coordinates in the rotated grid
    ni      = grd["ni"     ];   nj    = grd["nj"   ]   #Number of grid-cells
    maxcfl  = grd["maxcfl" ];                          #Maximum number of points used four the cfl
    blend_H = grd["blend_H"];                          #Number of grid-cells used for the blending zone

    if   domain_type == "model": d = maxcfl + 7;
    elif domain_type == "free" : d = -blend_H  ;  
    elif domain_type == "core" : d = 0         ;
    elif domain_type == "other": d = 0         ;
    else                       : print('ERROR: Accepted value for convertion_type: model, free, core'); return(NaN, NaN);
    iref = iref + d
    jref = jref + d
    

    if xlon2 - xlon1 != 90:
        print('convert_rotlatlon_to_cartesian works correctly only if xlon2-xlon1=90' )
        return(NaN,NaN)
    else:
        south_pole_coordinates = [-(90+xlon2), (90-xlat1)]


    if  convertion_type == "index2lonlat":        #Convert: Indices coordinates (on the rotated grid)  -->  latlon coordinates (on the UNrotated grid)
        i          = np.array(v1)                 #i-indices on the   rotated grid
        j          = np.array(v2)                 #j-indices on the   rotated grid
        rlon       = (i-iref)*dx + lonr           #Longitude on the   rotated grid
        rlat       = (j-jref)*dy + latr           #Latitude  on the   rotated grid
        lon, lat   = rotate_rotlatlon(rlon, rlat, south_pole_coordinates, "rot2unrot")
        lon        =-(180+lon)                    #Longitude on the unrotated grid
        lon        = lon + 360*(lon<=-360)
        lat        =-lat                          #Latitude  on the unrotated grid¸
        return(lon, lat)

    elif convertion_type == "lonlat2index":       #Convert: latlon coordinates (on the UNrotated grid) -->  Indices coordinates (on the rotated grid)
        lon        =-np.array(v1) + 180           #Longitude on the unrotated grid [Modified]
        lat        =-np.array(v2)                 #Latitude  on the unrotated grid [Modified]
        rlon, rlat = rotate_rotlatlon(lon,  lat,  south_pole_coordinates, "unrot2rot")
        rlon       = rlon + 360*(rlon<0);         #Longitude on the   rotated grid [Modified]
        i          = (rlon-lonr)/dx + iref        #i-indices on the   rotated grid
        j          = (rlat-latr)/dy + jref        #j-indices on the   rotated grid
        return(i, j)

    else:
       print('ERROR: Accepted value for convertion_type: index2lonlat, lonlat2index')
       return(NaN, NaN)




#############################################################################################################
def domainbox(grid_source,domain_type_source,grid_target,domain_type_target):
   

    domain_type_source = domain_type_source.lower()
    domain_type_target = domain_type_target.lower()
    
    src_ni      = grid_source['ni'     ];  
    src_nj      = grid_source['nj'     ];
    src_maxcfl  = grid_source['maxcfl' ];
    src_blend_H = grid_source['blend_H'];

    
    
    


    if   domain_type_source == 'free' : d = src_blend_H
    elif domain_type_source == 'core' : d = 0
    elif domain_type_source == 'model': d = -(src_maxcfl + 7)
    

    n=1000;
    Ii=1-0.5+d;   If=Ii+src_ni-2*d;   di=(If-Ii)/n;
    Ji=1-0.5+d;   Jf=Ji+src_nj-2*d;   dj=(Jf-Ji)/n;
    


    segiB = np.arange(Ii, If, di);   segjB = segiB*0+Ji;
    segiT = np.arange(If, Ii,-di);   segjT = segiT*0+Jf;
    segjR = np.arange(Ji, Jf, dj);   segiR = segjR*0+If;
    segjL = np.arange(Jf, Ji,-dj);   segiL = segjL*0+Ii;

    i = np.concatenate((segiB, segiR, segiT, segiL));
    j = np.concatenate((segjB, segjR, segjT, segjL));
    
    lon, lat = convert_rotlatlon_to_cartesian(i  ,j  ,grid_source,'core'            , "index2lonlat");
    i  , j   = convert_rotlatlon_to_cartesian(lon,lat,grid_target,domain_type_target, "lonlat2index");

    return(i,j)



#############################################################################################################
def read_gem_settings(file):
    import os

    filepath="/chinook/poitras/gem_settings/"+file
    if os.path.isfile(filepath): file = filepath

    keys  = ["dx", "dy", "ni", "nj", "iref","jref","lonr","latr","xlon1","xlon2","xlat1","xlat2","maxcfl"]
    grd  = {"blend_H": 10}; #Default value for Lam_Blend_H if not assigned


    

    with open (file, "r") as hfile:
        gem_settings = hfile.read()
        #print (sp)

    lines = gem_settings.split("\n")
    for line in lines:
        sublines = line.split(",")
        for subline in sublines:
            for key in keys:
                if  "Grd_"+key in subline:
                    #print("Grd_"+key, subline)
                    parts   = subline.split("=")
                    parts[0] = parts[0].replace(" ", "").replace("\t", "")
                    parts[1] = parts[1].replace(" ", "").replace("\t", "")
                    #print("key:[{0}], value:[{1}]".format(parts[0], parts[1]))
                    grd[key] = float(parts[1])
            if  "Lam_blend_H" in subline:
                parts   = subline.split("=")
                parts[0] = parts[0].replace(" ", "").replace("\t", "")
                parts[1] = parts[1].replace(" ", "").replace("\t", "")
                grd["blend_H"] = float(parts[1])
                #print("key:[{0}], value:[{1}],{2}".format(parts[0], parts[1],subline))

    return grd



def convert_latlon_to_domain_indices(track, domain):
    grid             = read_gem_settings('NAM-11m.nml')
    track_i, track_j = convert_rotlatlon_to_cartesian(track['longitude'], track['latitude'], grid, 'free', 'lonlat2index')
    track_roundi     = np.round(track_i).astype(int)
    track_roundj     = np.round(track_j).astype(int)

    Nray = len(track_i)
    indx = {}
    indx['i'] = np.empty(Nray, dtype=int)
    indx['j'] = np.empty(Nray, dtype=int)
    for n in range(Nray):
        indx['j'][n] = track_roundi[n] - 1
        indx['i'][n] = track_roundj[n] - 1

    return indx


