from RSData import *
from HaiYangData import *
import glob
import os
import re
import datetime
from netCDF4 import Dataset
import math

RE = 6378.273
E2 = 0.006693883
PI = 3.141592654
E = np.sqrt(E2)
latlon_file = r'E:\python_workfile\polar_project\FY3C_MWRI\lat_lon.h5'
def mapll(latitude, longitude):
    # 输入为弧度制lat，lon

    xy = np.empty(shape=(latitude.shape[0],latitude.shape[1],2))
    # if (abs(latitude) < PI / 2) :
    SL = 70 * PI / 180
    T = np.tan(PI / 4 - latitude / 2) / ((1 - E * np.sin(latitude)) / (1 + E * np.sin(latitude))) ** (E / 2)
    TC = np.tan(PI / 4 - SL / 2) / ((1 - E * np.sin(SL)) / (1 + E * np.sin(SL))) ** (E / 2)
    MC = np.cos(SL) / np.sqrt(1.0 - E2 * (np.sin(SL) ** 2))
    RHO = RE * MC * T / TC

    xy[:, :, 0] = RHO * np.sin(longitude)
    xy[:, :, 1] = -RHO * np.cos(longitude)



    return xy

files = glob.glob(r'h:\sst\FY-3C\N\*\*.HDF')


with Dataset(files[1000], mode='r') as fh:
    left_top_lat = fh.getncattr('Left-Top X')
    right_top_lat = fh.getncattr('Right-Top X')
    left_bottom_lat = fh.getncattr('Left-Bottom X')
    right_bottom_lat = fh.getncattr('Right-Bottom X')

    left_top_lon = fh.getncattr('Left-Top Y')
    right_top_lon = fh.getncattr('Right-Top Y')
    left_bottom_lon = fh.getncattr('Left-Bottom Y')
    right_bottom_lon = fh.getncattr('Right-Bottom Y')
    sst = fh.variables['sea_surface_temperature'][:]
    slope = 0.01
sst = sst * slope


lats, lons = np.mgrid[90:-90:3600j, -180:180:7200j]

lons[lons < 0.0] += 360

lons = (lons + 45) * PI / 180
lats = abs(lats) * PI / 180

xy = mapll(lats, lons)

x = xy[:,:,0]
y = xy[:,:,1]

i = ((x + 3850 - 12.5 / 2.0) / 12.5).astype(np.int)
k = ((y + 5350 - 12.5 / 2.0) / 12.5).astype(np.int)
j = 896 - k

i[i >= 896 ] =0
j[i >= 896] =0
i[i < 0  ] =0
j[i < 0 ] =0

i[j >= 608 ] =0
j[j >= 608] =0
i[j < 0  ] =0
j[j < 0 ] =0


grid_array = np.full(shape=(896,608), fill_value=np.nan)
grid_array[i,j] = sst

grid_array[grid_array < -2] = np.nan


plt.imshow(grid_array, origin = 'lower')
plt.colorbar()
plt.show()

with Dataset(latlon_file, mode='r') as fh:
    lat = fh.variables['Latitude'][:]
    lon = fh.variables['Longitude'][:]

lats_map = np.array(lat)
lons_map = np.array(lon)


plt.figure(figsize=(9, 9))

hy_m = Basemap(projection='npaeqd', boundinglat=40, lon_0=0, resolution='c')
map = Basemap(llcrnrlon = 0, llcrnrlat = 31, urcrnrlon = 30, urcrnrlat = 90, resolution = 'h', epsg = 3411)# 3413
# hy_m.pcolormesh(lats_map, lons_map, data=grid_array, cmap=plt.cm.jet, vmin=-2, vmax=35)
hy_m.imshow(grid_array, cmap=plt.cm.jet, vmin=-2, vmax=35)
hy_m.colorbar(location='right')

# hy_m.fillcontinents()
# hy_m.drawmapboundary()

# hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
plt.show()