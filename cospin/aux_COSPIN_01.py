# info: poitras.vincent@uqam.ca
# date: 2022/02/18
# aim : "modules" used cosp2_prepare_input_main.py
# Note: A part of this script is adapted from previous work made by Zhipeng Qu.
#       Discussions from our "COSP group" (Faisal Boudala, Mélissa Cholette.Jason Milbrant,Vincent Poitras, Zhipeng Qu)
#       also help to develop this script.

import matplotlib.pyplot as     plt
import numpy as np
from   datetime          import datetime
import netCDF4


NaN = np.nan
PI  = np.pi

##########################################################################################################
def add_time_dimension(varlist,data):
    #   If the NetCDF file contain only one time step (ntime == 1), there will be no time dimension in the input field
    #   We are adding it because the rest of the script is expecting to have one
    for field in varlist:
        ndim = len(data[field].shape)
        if ndim   == 0: data[field] = data[field] [np.newaxis      ]
        elif ndim == 1: data[field] = data[field] [np.newaxis,:    ]
        elif ndim == 2: data[field] = data[field] [np.newaxis,:,:  ]
        elif ndim == 3: data[field] = data[field] [np.newaxis,:,:,:]
    

##########################################################################################################
def radius_from_cldoppro(aird, sealand_mask, mixing_ratio, type):
    # Code is extracted from cldoppro_mp.F90
    # Effective radius are in micron
    # As far in undestand, i only the option type = ice_constant is used for ice [to double-check]

    if type.lower() not in ['liquid', 'ice_constant', 'ice' ]:
        print('radius_from_cldooppro: type must be liquid, ice_constant or ice, not: %s' % type)
        exit()

    if type.lower() == 'liquid':

        rec_cdd = sealand_mask.copy()
        rec_cdd [ sealand_mask <= 0.5] = 0.01  # particle number concentration over ocean [1 / 100 cm-3]    
        rec_cdd [ sealand_mask >  0.5] = 0.002 # particle number concentration over land  [1 / 500 cm-3] 
        vs1 = mixing_ratio * aird * rec_cdd;
        rew = 754.6 * np.power(vs1, 1/3);
        rew [ rew == 0      ] = NaN
        rew [ rew > 17      ] = 17
        rew [ rew <  4      ] =  4
        #rew [ np.isnan(rew) ] =  0
        rew = rew * 1e-6              # micron --> m
        return rew.astype(np.float32)

    elif type.lower() == 'ice':
        vs1 = mixing_ratio * aird * 1000
        rei = 83.8 * np.power(vs1, 0.216);
        rei [ rei == 0      ] = NaN
        rei [ rei > 50      ] = 50
        rei [ rei < 20      ] = 20
        #rei [ np.isnan(rei) ] =  0
        rei = rei * 1e-6              # micron --> m
        return rei.astype(np.float32)

    elif type.lower() == 'ice_constant':
        rei = np.ones(mixing_ratio.shape)*15
        #rei [mixing_ratio < 1e-10] = 0
        rei [mixing_ratio < 1e-10] = NaN
        rei = rei * 1e-6              # micron --> m
        return rei.astype(np.float32)

#######################################################################################################
def format_time_for_sunlit(reftime,time):
    import re
    from   datetime import datetime, timedelta
    
    format_out = '%Y-%m-%d %H:%M:%S'
    regex1     = re.compile('hours since ....-..-.. ..:..:..')


    if  re.fullmatch(regex1, reftime):
        N         = len(time)
        format_in = 'hours since %Y-%m-%d %H:%M:%S' 
        t0        = datetime.strptime(reftime,  format_in)
        t         = np.empty(N, dtype='object')
        for n in range(N):
            t[n] = (t0 + timedelta(hours=int(time[n]))).strftime(format_out)
    else:
        print('Error in format_time_for_sunlit')
        print('reftime must have this form: hours since YYYY-MM-DD hh:mm:ss')
        print('You have: ', reftime)
        print('You can edit the module format_time_for_sunlit to fix the problem')
        exit()

    return t;

#######################################################################################################
def sunlit(lon,lat,time):
    import astropy.coordinates as coord
    import astropy.units       as u
    from   astropy.time        import Time

    ni    = len(lon[0])
    nj    = len(lon[1])
    nt    = len(time)
    isun  = np.zeros((nt,ni,nj))
    N = len(time)
    for n in range(N):
        sun_time = Time(time[n]) #UTC time
        #loc = coord.EarthLocation.of_address('Montreal, Qc')  # To check everthing worked fine
        loc      = coord.EarthLocation(lon=lon * u.deg,lat=lat * u.deg)
        altaz    = coord.AltAz(obstime=sun_time, location=loc)
        zen_ang  = coord.get_sun(sun_time).transform_to(altaz).zen.degree
        isun[n,:,:] [ zen_ang < 90 ] = 1
    
    return isun.astype(np.float32)   # int8? check if in cosp it is ok to have a int


#######################################################################################################
def cloud_optical_depth_and_emmissivity(rew, rei, mrw, mri, full_height, orography, aird):

    # Computing layer thickness
    #   Layer order is going from TOA (n=0) to the closet height to the ground (nz-1)
    #   Input
    #       rew        : Effective radius (liquid water)
    #       rei        : Effective radius (ice)
    #       mrw        : Mixing ratio     (liquid water)                              [kg/kg]
    #       mri        : Mixing ratio     (ice)                                       [kg/kg]
    #       full_height: Full height level --> to compute DZ
    #       orography  : Orography         --> to compute DZ
    #       aird       : Air density       --> to convert mixing ratio: kg/kg -> g/m3

    DZ = np.zeros(full_height.shape,dtype=np.float32)
    nz = len(full_height[0,:,0,0])
    for n in range(nz-1):
        DZ[:,n,:,:] = full_height[:,n,:,:] - full_height[:,n+1,:,:]
    DZ[:,nz-1,:,:] = full_height[:,nz-1,:,:] - orography
    DZ = DZ.astype(np.float32)

    # Convert kg/kg -> g/m3
    CLW = 1000 * mrw * aird;
    CIC = 1000 * mri * aird;


    # Inverting radius
    invrew = 1/rew;
    invrei = 1/rei;

    # Visible optical depth (0.67 micron)
    tauwvis = DZ*CLW*( 4.483e-04 + invrew*(1.501 + invrew*(7.441e-01 - invrew*9.620e-01)));
    tauivis = DZ*CIC*(-0.303108e-04 + 0.251805e+01*invrei);

    # Infrared optical depth (10.5 micron)
    tauwir  = DZ*CLW*( 0.14532e-01  - 0.47449e-03*rew + invrew*(0.22898e+01 - invrew*(0.92402e+01 - invrew*0.100999e+02)));
    tauiir  = DZ*CIC*(-7.627102e-03 + 3.406420*invrei - 1.732583e+01*(invrei**2));

    tauwvis [np.isnan(tauwvis)] = 0;
    tauivis [np.isnan(tauivis)] = 0;
    tauwir  [np.isnan(tauwir )] = 0;
    tauiir  [np.isnan(tauiir )] = 0;

    # Optical depth: Adding liquid and ice contributions
    tauvis = tauwvis + tauivis;
    tauir  = tauwir  + tauiir;

    # Infrared emmisivity (10.5 micron)
    RU   = 1.6487213;
    emir = 1 - np.exp(-RU*tauir);
    
    return tauvis, emir


#######################################################################################################
def radius_from_mp_my2(number_ratio, mixing_ratio, aird, type):
    # iAdapted from a Zhipeng script which seem to be extracted from mp_my2_mod.F90
    # In mp_my2_mod.F90: Compute effective radii for cloud and ice (to be passed to radiation scheme)
    # This routine does not seem to be able to compute radii for rain (only cloud and frozen precipitation)
    # The rain constants are actually the frozen precipitation constant(ice, snow, graupel, hail)
    #  ---> To clarify with Zhipeng
    
    from math import gamma

    # Get fields dimensions
    ntime = aird.shape[0]
    nlev  = aird.shape[1]
    nlat  = aird.shape[2]
    nlon  = aird.shape[3] 

    if type.lower() == 'cloud':
        # Cloud constant
        # icex9 and rcoef are used later, other constant serve to compute icex9
        iMUc     = 1/3;     # Shape parameter for cloud (1/mu)
        alpha_c  = 1;       # Shape parameter for cloud (alpha)
        dew      = 1000;    # ?
        GC2      =   gamma(alpha_c + 1 + 3.0*iMUc);
        iGC1     = 1/gamma(alpha_c + 1           );
        icex9    = 1/(GC2*iGC1*PI/6*dew);
        rcoef    = 1.5

    elif type.lower() == 'rain':
        # Rain constant --> according to mp_my2_mod.F90, seems to be frozen precipitation constant
        # icex9, rcoef, iLAMmin2 are used later, other constant serve to compute icex9
        alpha_r  = 0;           # Shape parameter for rain (alpha)
        dmr      = 3;           # ?  
        cmr      = (PI/6)*1000; # ?
        iGI31_r  = 1/gamma(1 + alpha_r);                
        icex9    = 1/(cmr*gamma(1 + alpha_r + dmr)*iGI31_r);
        rcoef    = 0.664639
        iLAMmin2 = 1.e-10;

    # Cloud and rain constant
    mixing_ratio_min         = 0.e-14;  # kg kg-1, min. allowable mixing ratio (epsQ)
    number_concentration_min = 0.e-3 ;  # m-3,     min. allowable number concentration (epsN)

    # Conversion from #/kg to #/m3
    number_concentration = number_ratio * aird;
    reff = np.zeros(mixing_ratio.shape)
    
    for t in range(ntime):
        for k in range(nlev):
            for i in range(nlat):
                for j in range(nlon):
                    if mixing_ratio[t,k,i,j] > mixing_ratio_min and number_concentration[t,k,i,j] > number_concentration_min:
                        iN   = 1 / number_concentration[t,k,i,j]
                        MR   = mixing_ratio[t,k,i,j]
                        AD   = aird[t,k,i,j]
                        iLAM = iLAMDA_x(AD,MR,iN,icex9,1/3); #hardcoded for alpha = 1 and mu = 3 (cloud); alpha = 0 and mu = 1 (rain <-- seems actualy be frozen precip) 
                        if type.lower() == 'rain':
                            iLAM = np.max([iLAM, iLAMmin2])
                        reff[t,k,i,j] = rcoef*iLAM;
    return reff.astype(np.float32)
#######################################################################################################
def iLAMDA_x(DE_local,QX_local,iNX_local,icex_local,idmx_local):
# Computes 1/LAMDA ("slope" parameter) in radius_from_mp_my2
    data = np.exp(idmx_local*np.log(DE_local*QX_local*iNX_local*icex_local));
    return data


#######################################################################################################
def write_ncfile_output(output_data,formatted_time,dirout,delete_fields=True):
    ntime = len(formatted_time)
    for t in range(ntime):

        # Create filename (they will be labelled by the date + hour)
        time       = datetime.strptime(formatted_time[t],'%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M')
        ncfile_path = dirout + '/cosp_input_' + time + '.nc'
        ncfile      = netCDF4.Dataset(ncfile_path, 'a', format='NETCDF4')
        # Create dimension
        #ncfile.createDimension('lon'  ,nlon)
        #ncfile.createDimension('lat'  ,nlat)
        #ncfile.createDimension('level',nlev)
        #ncfile.createDimension('hydro',   9)

        # Create variable: lat, lon, emsfc_lw
        #ncfile.createVariable('emsfc_lw', 'f4')
        #ncfile['emsfc_lw'][:] = 0.95
        #ncfile.createVariable('lon', 'f4', ('lon'))
        #ncfile['lon'][:] = output_data['lon']
        #ncfile.createVariable('lat', 'f4', ('lat'))
        #ncfile['lat'][:] = output_data['lat']

        # Cerate other variables
        for fieldname in output_data:

            fieldshape = output_data[fieldname].shape
            #if t == 0 :
                #output_data[fieldname] = np.nan_to_num(output_data[fieldname]) # Set NaN --> 0, doing one time (t=0) for all timestep

            if   len(fieldshape) == 2:      # orography, landmask, longitude, latitude
                ncfile.createVariable(fieldname, 'f4', ('lat','lon'))
                ncfile[fieldname][:] = np.nan_to_num( output_data[fieldname] )

            elif len(fieldshape) == 3:      # sunlit, skt
                ncfile.createVariable(fieldname, 'f4', ('lat','lon'))
                ncfile[fieldname][:] = np.nan_to_num( output_data[fieldname][t,:,:] )

            elif len(fieldshape) == 4:      # all other variables
                ncfile.createVariable(fieldname, 'f4', ('level','lat','lon'))
                ncfile[fieldname][:] = np.nan_to_num( np.flip(output_data[fieldname][t,:,:,:],0) )

            elif len(fieldshape) == 5:      # effective radii
                ncfile.createVariable(fieldname, 'f4', ('hydro','level','lat','lon'))
                ncfile[fieldname][:] = np.nan_to_num( np.flip(output_data[fieldname][t,:,:,:,:],1) )
     

    fieldnames = dict.fromkeys(output_data.keys(),[])
    for fieldname in fieldnames:
        print(fieldname)
        if delete_fields:
            output_data.pop(fieldname)
