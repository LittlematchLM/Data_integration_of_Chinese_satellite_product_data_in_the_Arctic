from RSData import *
from HaiYangData import *
import glob
import os

satellite = r'FY3A'
sensor = r'VIRR'
fyfiles = glob.glob(r'H:\sst\FY-3A\*\*\*.HDF')
fyfiles.sort()
save_path = r'H:\\polor_project\\output_new\\sst\\FY3A_VIRR\\'

# 文件排序
def sort_key(s):
    if s:

        c = s.split('\\')[-1].split('_')[7]
        return c

fyfiles.sort(key=sort_key)

file_list = []
list = []
for i in range(len(fyfiles)):

    if i == 0:
        list.append(fyfiles[i])
        continue

    if (fyfiles[i].split('\\')[-1].split('_')[7]) == (fyfiles[i-1].split('\\')[-1].split('_')[7]):
        list.append(fyfiles[i])
    else:
        file_list.append(list)
        list = []
        list.append(fyfiles[i])
file_list.append(list)
# 如果运行中断，从哪个文件开始继续运行
con_point = 0

try:
    os.mkdir(save_path + 'pic')
except :
    pass

fy_virr = HaiYangData(satellite=satellite, sensor=sensor,resolution=25000)


# 将WGS 84坐标（4326）转化为极射投影
crs = CRS.from_epsg(4326)
crs = CRS.from_string("epsg:4326")
crs = CRS.from_proj4("+proj=latlon")
crs = CRS.from_user_input(4326)
crs2 = CRS(proj="aeqd")

transformer = HaiYangData.set_transformer(crs,crs2)
transformer_back = HaiYangData.set_transformer(crs2,crs)
test_list = [file_list[3][14:17]]
for i,files in enumerate(file_list[con_point:]):
    grid_array = np.zeros((fy_virr.nlat, fy_virr.nlon))
    grid_num_array = np.zeros((fy_virr.nlat, fy_virr.nlon))
    day = files[0].split('//')[-1].split(r'_')[7]
    file_name = satellite + '_' + sensor + '_' + day
    for file in files:
        with Dataset(file, mode='r') as fh:
            left_top_lat = fh.getncattr('Left-Top Latitude')
            right_top_lat = fh.getncattr('Right-Top Latitude')
            left_bottom_lat = fh.getncattr('Left-Bottom Latitude')
            right_bottom_lat = fh.getncattr('Right-Bottom Latitude')
            
            left_top_lon = fh.getncattr('Left-Top Longitude')
            right_top_lon = fh.getncattr('Right-Top Longitude')
            left_bottom_lon = fh.getncattr('Left-Bottom Longitude')
            right_bottom_lon = fh.getncattr('Right-Bottom Longitude')

            sst = fh.variables['VIRR_SST'][:]

            lats, lons = np.mgrid[ left_top_lat:left_bottom_lat:1000j,left_top_lon:right_top_lon:1000j]

            # projlats, projlons = transformer.transform(lats, lons)

            value_array = np.empty(shape=(lons.shape[0], lons.shape[1],5))

            value_array[:,:,0] = lats
            value_array[:,:,1] = lons
            value_array[:,:,2],value_array[:,:,3] = transformer.transform(value_array[:,:,0], value_array[:,:,1])
            value_array[:,:,4] = sst


            x = (value_array[:,:,2] / fy_virr.resolution).astype(np.int)
            y = (value_array[:,:,3] / fy_virr.resolution).astype(np.int)

            grid_array[y,x] += value_array[:,:,4]
            grid_num_array[y,x] += 1
    # 获得XYmgrid
            grid_array = grid_array / grid_num_array
            x_map, y_map = fy_virr.get_map_grid(transformer_back)

            # x_map += 150

# 将非法点置为np.nan
    grid_array[grid_array==0] = np.nan

    plt.figure(figsize=(16, 9))
    hy_m = Basemap(projection='npaeqd', boundinglat=60, lon_0=0, resolution='c')
    hy_m.pcolormesh(x_map, y_map, data=grid_array, cmap=plt.cm.jet,vmin=0,vmax=100,latlon = True)
    hy_m.colorbar(location='right')
    hy_m.fillcontinents()
    hy_m.drawmapboundary()
    hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(satellite +'_'+ sensor +'_'+ day)
    plt.show()


            plt.savefig(save_path +r'pic//'+ file_name + '.jpg')
            plt.close()


        with Dataset(save_path + file_name + '.nc', 'w', format='NETCDF4') as file:
            file.createDimension('x', grid_array.shape[0])
            file.createDimension('y', grid_array.shape[0])
            icecon_north = file.createVariable('icecon_north', 'i4', dimensions=('x', 'y'))
            lat = file.createVariable('lat', 'f4', dimensions=('x', 'y'))
            lon = file.createVariable('lon', 'f4', dimensions=('x', 'y'))
            icecon_north[:] = grid_array
            lon[:] = x_map
            lat[:] = y_map
        print(str(i+con_point) + '//' + str(len(files)))
        print(satellite +'_'+ sensor +'_'+ day)