from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
import imageio

ncfiles = glob.glob(r"H:\\wind\\SCA\\*\\*\\*.h5")
ncfiles = ncfiles[0:1]

# for ncfile in ncfiles:
with Dataset(ncfiles[0], mode='r') as f:
    date = f.getncattr('Equator_Crossing_Time').split('T')[0]
    lat = f.variables['wvc_lat'][:]
    lon = f.variables['wvc_lon'][:]
    # time = f.variables['time'][:]
    wind_speed = f.variables['wind_speed_selection'][:]
    wind_dir = f.variables['wind_dir_selection'][:]

# lat1 = lat[::10]
# lon1 = lon[::10]

# grid_array = np.sqrt((u_wind ** 2) + (v_wind ** 2))
# a, b = np.meshgrid(lon, lat)

# xx, yy = np.meshgrid(lon1, lat1)


# lon[lon > 360]= 0
# lon[lon < 0] = 0
# lat[lon > 360]= 0
# lat[lon < 0] = 0
#
# lat[lat > 90]= 0
# lat[lat < -90] = 0
# lon[lat > 90]= 0
# lon[lat < -90] = 0


plt.figure(figsize=(16, 16))
m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=0, urcrnrlon=360, lat_ts=20,
            resolution='i')

# m.pcolormesh(lon, lat, wind_speed, cmap=plt.cm.jet, vmax=24)

# cb = m.colorbar(location='right')
# cb.set_label('$wind speed(m/s)$')
m.drawcoastlines()
m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
m.drawmeridians(np.arange(-180., 180., 10.), labels=[0, 0, 0, 1])
m.quiver(lon, lat, wind_dir, color='red', width=0.0005, scale_units='x',headwidth=7)
plt.show()
#plt.savefig('.\\pic\\' +date+' '+ time +r'.jpg',bbox_inches='tight', dpi=300)