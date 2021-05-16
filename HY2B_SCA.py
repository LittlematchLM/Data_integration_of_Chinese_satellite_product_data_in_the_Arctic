from RSData import *
from HaiYangData import *
import glob
import os
import datetime
import math

satellite = r'HY2B'
sensor = r'SCA'
value = r'wind'
resolution_n = r'25KM'
# save_path =
files = glob.glob(r"h:\\wind\\SCA\\*\\*\\*.h5")
files = files[6:7]


hy_sca = HaiYangData(satellite=satellite, sensor=sensor,resolution=35000)

# 将WGS 84坐标（4326）转化为极射投影
crs = CRS.from_epsg(4326)
crs = CRS.from_string("epsg:4326")
crs = CRS.from_proj4("+proj=latlon")
crs = CRS.from_user_input(4326)
crs2 = CRS(proj="aeqd")

transformer = HaiYangData.set_transformer(crs,crs2)
transformer_back = HaiYangData.set_transformer(crs2,crs)

file_list = []
list = []
for i in range(len(files)):

    if i == 0:
        list.append(files[i])
        continue

    if (files[i].split('\\')[-1].split('_')[5].split('T')[0]) == (files[i-1].split('\\')[-1].split('_')[5].split('T')[0]):
        list.append(files[i])
    else:
        file_list.append(list)
        list = []
        list.append(files[i])
file_list.append(list)

for files in file_list:
    grid_array = np.zeros((hy_sca.nlat, hy_sca.nlon))
    grid_num_array = np.zeros((hy_sca.nlat, hy_sca.nlon))

    for file in files:
        with Dataset(files[0], mode='r') as f:
            date = f.getncattr('Equator_Crossing_Time').split('T')[0]
            lats = f.variables['wvc_lat'][:,2:-2]
            lons = f.variables['wvc_lon'][:,2:-2]
            # time = f.variables['time'][:]
            wind_speed = f.variables['wind_speed_selection'][:,2:-2]
            wind_dir = f.variables['wind_dir_selection'][:,2:-2]

# lats[lats > 90] = 100

# projlats, projlons = transformer.transform(lats, lons)
    value_array = np.empty(shape=(lons.shape[0], lons.shape[1], 6))


    value_array[:, :, 0] = lats
    value_array[:, :, 1] = lons
    value_array[:, :, 2], value_array[:, :, 3] = transformer.transform(value_array[:, :, 0], value_array[:, :, 1])
    value_array[:, :, 4] = wind_speed
    value_array[:, :, 5] = wind_dir


# value_array[:, :, 2][value_array[:, :, 4] < 0 ] = 0
# value_array[:, :, 3][value_array[:, :, 4] < 0 ] = 0
#
# value_array[:, :, 2][value_array[:, :, 5] < 0 ] = 0
# value_array[:, :, 3][value_array[:, :, 5] < 0 ] = 0


x = (value_array[:, :, 2] / hy_sca.resolution).astype(np.int)
y = (value_array[:, :, 3] / hy_sca.resolution).astype(np.int)


grid_array[y, x] += value_array[:, :, 4]
grid_num_array[y, x] += 1



# 获得XYmgrid
grid_array[grid_array < 0 ]=np.nan


grid_array = grid_array / grid_num_array
# grid_array_dir = grid_array_dir / grid_num_array_dir


x_map, y_map = hy_sca.get_map_grid(transformer_back)

uwind = np.sin(np.radians(wind_dir)) * wind_speed
vwind = np.cos(np.radians(wind_dir)) * wind_speed



plt.figure(figsize=(9, 9))
hy_m = Basemap(projection='npaeqd', boundinglat=60, lon_0=0, resolution='c')
# 用原始的lons，lats画图
# hy_m.pcolormesh(lons, lats, data=wind_speed, cmap=plt.cm.jet,vmax = 24 ,vmin=0,latlon = True)
# hy_m.quiver(lons[::10,::10], lats[::10,::10], uwind[::10,::10],vwind[::10,::10], units='width',scale_units='width',color='black',latlon = True)
# 用投影出来的grid画图
hy_m.pcolormesh(x_map, y_map, data=grid_array, cmap=plt.cm.jet,vmax = 24 ,vmin=0,latlon = True)
hy_m.quiver(x_map, y_map, uwind[::10,::10],vwind[::10,::10], units='width',scale_units='width',color='black',latlon = True)
hy_m.colorbar(location='right')
hy_m.fillcontinents()

hy_m.drawmapboundary()
hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
plt.show()

