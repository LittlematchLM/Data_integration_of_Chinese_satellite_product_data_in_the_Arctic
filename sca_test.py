
from mpl_toolkits.basemap import Basemap
from netCDF4 import Dataset
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
import imageio



satellite = r'HY2B'
sensor = r'SCA'
value = r'wind'
resolution_n = r'25KM'
# save_path =
files = glob.glob(r"G:\\wind\\SCA\\*\\*\\*.h5")
files = files[6:7]


with Dataset(files[0], mode='r') as f:
    date = f.getncattr('Equator_Crossing_Time').split('T')[0]
    lats = f.variables['wvc_lat'][:,2:-2]
    lons = f.variables['wvc_lon'][:,2:-2]
    # time = f.variables['time'][:]
    wind_speed = f.variables['wind_speed_selection'][:,2:-2]
    wind_dir = f.variables['wind_dir_selection'][:,2:-2]


uwind = np.sin(wind_dir) * wind_speed
vwind = np.cos(wind_dir) * wind_speed

lat1 = lats[::10]
lon1 = lons[::10]

# grid_array = np.sqrt((uwind ** 2) + (vwind ** 2))[::10]
# a, b = np.meshgrid(lon1, lat1)

# xx, yy = np.meshgrid(lon, lat)
plt.figure(figsize=(16, 16))
m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=90, llcrnrlon=0, urcrnrlon=360, lat_ts=20, resolution='i')

m.pcolormesh(lats, lons, wind_speed, cmap=plt.cm.jet, vmax=30,latlon=True)
cb = m.colorbar(location='right')
cb.set_label('$wind speed(m/s)$')
m.drawcoastlines()
m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
m.drawmeridians(np.arange(-180., 180., 10.), labels=[0, 0, 0, 1])
m.quiver(xx, yy, uwind[i, ::10, ::10], vwind[i, ::10, ::10], color='red', width=0.0005, scale_units='x', headwidth=7)

# plt.title(date + ' ' + str(time) + ':00 10-m Wind')
plt.show()
