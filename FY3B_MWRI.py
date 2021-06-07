from RSData import *
from HaiYangData import *
import glob
import os
import datetime

satellite = r'FY3B'
sensor = r'MWRI'
parameter = 'SIC'
resolution = '25KM'
files = glob.glob(r'G:\icecon\micosoft\FY-3B\*\*.HDF')
files.sort()
latlon_file = r'E:\python_workfile\polar_project\FY3C_MWRI\lat_lon.h5'
save_path = r'G:\\polor_project\\output_all\\micosoft_save\\FY-3B\\'
# 如果运行中断，从哪个文件开始继续运行
con_point = 0
try:
    os.mkdir(save_path + 'pic')
except :
    pass

fy_mwri = HaiYangData(satellite=satellite, sensor=sensor,resolution=25000)

# 将WGS 84坐标（4326）转化为极射投影
crs = CRS.from_epsg(4326)
crs = CRS.from_string("epsg:4326")
crs = CRS.from_proj4("+proj=latlon")
crs = CRS.from_user_input(4326)
crs2 = CRS(proj="aeqd")

transformer = HaiYangData.set_transformer(crs,crs2)
transformer_back = HaiYangData.set_transformer(crs2,crs)


with Dataset(latlon_file, mode='r') as fh:
    lats = fh.variables['Latitude'][:]
    lons = fh.variables['Longitude'][:]

value_array = np.empty(shape=(lons.shape[0], lons.shape[1], 5))

value_array[:, :, 0] = lats
value_array[:, :, 1] = lons
value_array[:, :, 2] ,value_array[:, :, 3] = transformer.transform(value_array[:, :, 0], value_array[:, :, 1])
x = (value_array[:, :, 2] / fy_mwri.resolution).astype(np.int)
y = (value_array[:, :, 3] / fy_mwri.resolution).astype(np.int)




for i,file in enumerate(files[con_point:]):
    grid_array = np.zeros((fy_mwri.nlat, fy_mwri.nlon))
    grid_num_array = np.zeros((fy_mwri.nlat, fy_mwri.nlon))

    try:
        with Dataset(file, mode='r') as fh:
            sic = fh.variables['icecon_north_avg'][:]
            day = file.split('\\')[-1].split(r'_')[7]
    except OSError:
        print(file)
    file_name = satellite + '_' + sensor + '_' +parameter + '_' +resolution + '_' + day

    # projlats, projlons = transformer.transform(lats, lons)
    # value_array = np.empty(shape=(lons.shape[0], lons.shape[1],5))
    #
    # value_array[:,:,0] = lats
    # value_array[:,:,1] = lons
    # value_array[:,:,2],value_array[:,:,3] = transformer.transform(value_array[:,:,0], value_array[:,:,1])
    # value_array[:,:,4] = sic
    #
    # x = (value_array[:,:,2] / fy_mwri.resolution).astype(np.int)
    # y = (value_array[:,:,3] / fy_mwri.resolution).astype(np.int)

    grid_array[y,x] += sic
    grid_num_array[y,x] += 1
    # 获得XYmgrid
    grid_array = grid_array / grid_num_array
    x_map, y_map = fy_mwri.get_map_grid(transformer_back)

    grid_array[grid_array>101] = np.nan
    grid_array[grid_array== 0] = np.nan

    plt.figure(figsize=(16, 9))
    hy_m = Basemap(projection='npaeqd', boundinglat=40, lon_0=0, resolution='c')
    hy_m.pcolormesh(x_map, y_map, data=grid_array, cmap=plt.cm.jet,vmax = 100,vmin=0,latlon = True)
    hy_m.colorbar(location='right')
    hy_m.fillcontinents()
    hy_m.drawmapboundary()
    hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(satellite +'_'+ sensor +'_'+ day)
    plt.savefig(save_path +r'\\pic\\'+ file_name + '.jpg')
    plt.close()

    # 只截取高纬度地区
    grid_array_sub = np.hstack((grid_array[:700,:600],grid_array[:700,1200:]))
    x_map_sub = np.hstack((x_map[:700,: 600],x_map[:700, 1200:]))
    y_map_sub = np.hstack((y_map[:700,: 600], y_map[:700, 1200:]))
    with Dataset(save_path + file_name + '.nc', 'w', format='NETCDF4') as f:
        f.createDimension('x', grid_array_sub.shape[0])
        f.createDimension('y', grid_array_sub.shape[1])
        f.setncattr_string('satellite',satellite)
        f.setncattr_string('sensor', sensor)
        f.setncattr_string('data time', day)
        f.setncattr_string('data create time', datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
        f.setncattr_string('projection mode', 'polar stereographic projection')
        f.setncattr_string('resolution', '25KM')
        f.setncattr_string('data processing organization', 'Ocean University Of China')

        icecon_north = f.createVariable('SIC', 'i4', dimensions=('x', 'y'))
        icecon_north[:] = grid_array_sub
        icecon_north.setncattr_string('Dataset Name', 'Daily Sea ice concentration')
        icecon_north.setncattr_string('Datatype', 'int')
        icecon_north.setncattr_string('valid_range','0 to 100')
        icecon_north.setncattr_string('units', '%')
        icecon_north.setncattr_string('observation area', 'North of 60 N')
        icecon_north.setncattr_string('origin data product', 'MWRI_L2_SIC')




        lat = f.createVariable('lat', 'f4', dimensions=('x', 'y'))
        lon = f.createVariable('lon', 'f4', dimensions=('x', 'y'))
        lon[:] = x_map_sub
        lat[:] = y_map_sub
    print(str(con_point + i+1) + '\\' + str(len(files)))
    print(satellite +'_'+ sensor +'_'+ day)

