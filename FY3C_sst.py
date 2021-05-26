from RSData import *
from HaiYangData import *
import glob
import os
import re
import datetime

satellite = r'FY3A'
sensor = r'VIRR'
parameter = r'SST'
resolution = r'25KM'
files = glob.glob(r'G:\sst\FY-3C\D\*\*.HDF')
files.sort()
save_path = r'G:\\polor_project\\output_all\\sst\\FY3C_VIRR\\DAY\\'

# 如果运行中断，从哪个文件开始继续运行
con_point = 0

try:
    os.mkdir(save_path + 'pic')
except:
    pass

fy_virr = HaiYangData(satellite=satellite, sensor=sensor, resolution=25000)

# 将WGS 84坐标（4326）转化为极射投影
crs = CRS.from_epsg(4326)
crs = CRS.from_string("epsg:4326")
crs = CRS.from_proj4("+proj=latlon")
crs = CRS.from_user_input(4326)
crs2 = CRS(proj="aeqd")

transformer = HaiYangData.set_transformer(crs, crs2)
transformer_back = HaiYangData.set_transformer(crs2, crs)


grid_array = np.full((fy_virr.nlat, fy_virr.nlon), fill_value=np.nan)
grid_num_array = np.zeros((fy_virr.nlat, fy_virr.nlon))
day = files[0].split('//')[-1].split(r'_')[7]
file_name = satellite + '_' + sensor + parameter + resolution + '_' + day



for file in files:
    with Dataset(files[6], mode='r') as fh:
        left_top_lat = fh.getncattr('Left-Top X')
        right_top_lat = fh.getncattr('Right-Top X')
        left_bottom_lat = fh.getncattr('Left-Bottom X')
        right_bottom_lat = fh.getncattr('Right-Bottom X')

        left_top_lon = fh.getncattr('Left-Top Y')
        right_top_lon = fh.getncattr('Right-Top Y')
        left_bottom_lon = fh.getncattr('Left-Bottom Y')
        right_bottom_lon = fh.getncattr('Right-Bottom Y')
        sst = fh.variables['sea_surface_temperature'][:]

    lats, lons = np.mgrid[left_top_lat:left_bottom_lat:3600j, left_top_lon:right_top_lon:7200j]

    value_array = np.empty(shape=(lons.shape[0], lons.shape[1], 5))

    value_array[:, :, 0] = lats
    value_array[:, :, 1] = lons
    value_array[:, :, 2], value_array[:, :, 3] = transformer.transform(value_array[:, :, 0], value_array[:, :, 1])
    value_array[:, :, 4] = sst

    x = (value_array[:, :, 2] / fy_virr.resolution).astype(np.int)
    y = (value_array[:, :, 3] / fy_virr.resolution).astype(np.int)
    grid_array[y, x] = value_array[:, :, 4]

    print(file)

# 将非法点置为np.nan
grid_array[grid_array < -20] = np.nan
grid_array[grid_array > 100 ] = np.nan

x_map, y_map = fy_virr.get_map_grid(transformer_back)
plt.figure(figsize=(16, 9))
hy_m = Basemap(projection='npaeqd', boundinglat=60, lon_0=0, resolution='c')
hy_m.pcolormesh(x_map, y_map, data=grid_array, cmap=plt.cm.jet, vmin=0, vmax=30, latlon=True)
hy_m.colorbar(location='right')
hy_m.fillcontinents()
hy_m.drawmapboundary()
hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
plt.title(satellite + '_' + sensor + '_' + day)
plt.show()

plt.savefig(save_path + r'pic\\' + file_name + '.jpg')
plt.close()

grid_array[np.where(np.isnan(grid_array))] = -888
# 只截取高纬度地区
grid_array_sub = np.hstack((grid_array[:700, :600], grid_array[:700, 1200:]))
x_map_sub = np.hstack((x_map[:700, : 600], x_map[:700, 1200:]))
y_map_sub = np.hstack((y_map[:700, : 600], y_map[:700, 1200:]))
count_grid = np.hstack((grid_num_array[:700, : 600], grid_num_array[:700, 1200:]))
with Dataset(save_path + file_name + '.h5', 'w') as f:
    f.createDimension('x', grid_array_sub.shape[0])
    f.createDimension('y', grid_array_sub.shape[1])
    # 添加数据属性
    f.setncattr_string('satellite', satellite)
    f.setncattr_string('sensor', sensor)
    f.setncattr_string('data time', day)
    f.setncattr_string('data create time', datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
    f.setncattr_string('projection mode', 'polar stereographic projection')
    f.setncattr_string('resolution', '25KM')
    f.setncattr_string('data processing organization', 'Ocean University Of China')

    sst_north = f.createVariable('SST', 'i4', dimensions=('x', 'y'))
    sst_north[:] = grid_array_sub
    sst_north.setncattr_string('Dataset Name', 'Daily Sea surface temperature')
    sst_north.setncattr_string('Datatype', 'int')
    sst_north.setncattr_string('valid_range', '-20,350')
    sst_north.setncattr_string('units', 'K')
    sst_north.setncattr_string('observation area', 'North of 60 N')
    sst_north.setncattr_string('origin data product', 'VIRR_L2_SST')

    lat = f.createVariable('latitude', 'f4', dimensions=('x', 'y'))
    lon = f.createVariable('longitude', 'f4', dimensions=('x', 'y'))
    lon[:] = x_map_sub
    lat[:] = y_map_sub

    count_g = f.createVariable('count_grid', 'i4', dimensions=('x', 'y'))
    count_g[:] = count_grid
print(str(i + con_point) + '/' + str(len(files)))
print(satellite + '_' + sensor + '_' + day)