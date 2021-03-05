
from RSData import *
from HaiYangData import *
import glob


satellite = r'HY1C'
sensor = r'COCTS'

files = glob.glob(r'H:\\HY-1C\\*\\*.h5')
files.sort()

save_path = r'G:\\polor_project\\output_new\\sst\\'
hy_cocts = HaiYangData(satellite=satellite, sensor=sensor,resolution=25000)

con_point = 0

file_list = []
list = []
for i in range(len(files)):

    if i == 0:
        list.append(files[i])
        continue

    if (files[i].split('\\')[-1].split('_')[4].split('T')[0]) == (files[i-1].split('\\')[-1].split('_')[4].split('T')[0]):
        list.append(files[i])
    else:
        file_list.append(list)
        list = []
        list.append(files[i])
file_list.append(list)
# 将WGS 84坐标（4326）转化为极射投影
crs = CRS.from_epsg(4326)
crs = CRS.from_string("epsg:4326")
crs = CRS.from_proj4("+proj=latlon")
crs = CRS.from_user_input(4326)
crs2 = CRS(proj="aeqd")

transformer = HaiYangData.set_transformer(crs,crs2)
transformer_back = HaiYangData.set_transformer(crs2,crs)


def draw_and_save(files):
    grid_array = np.zeros((hy_cocts.nlat, hy_cocts.nlon))
    grid_num_array = np.zeros((hy_cocts.nlat, hy_cocts.nlon))
    for i,file in enumerate(files[con_point:]):
        with Dataset(file, mode='r') as fh:
            D_N_flag = fh.getncattr('Day or Night Flag')

            lats = fh.groups['Navigation Data'].variables['Latitude'][:]
            lons = fh.groups['Navigation Data'].variables['Longitude'][:]
            if D_N_flag == 'D':
                print(file,D_N_flag)
                value = 'SST'
            else:
                value = 'NSST'
                print(file,D_N_flag)
            day = file.split('\\')[-1].split('_')[4].split('T')[0]
            sst = fh.groups['Geophysical Data'].variables[value][:]
            print(sst.max())

        file_name = satellite + '_' + sensor + '_' + day
        # projlats, projlons = transformer.transform(lats, lons)

        value_array = np.full(shape=(lons.shape[0], lons.shape[1],5), fill_value=np.nan)

        value_array[:,:,0] = lats
        value_array[:,:,1] = lons
        value_array[:,:,2],value_array[:,:,3] = transformer.transform(value_array[:,:,0], value_array[:,:,1])
        value_array[:,:,4] = sst

        x = (value_array[:,:,2] / hy_cocts.resolution).astype(np.int)
        y = (value_array[:,:,3] / hy_cocts.resolution).astype(np.int)

        grid_array[y,x] += value_array[:,:,4]
        grid_num_array[y,x] += 1
        # 获得XYmgrid
    grid_array = grid_array / grid_num_array
    x_map, y_map = hy_cocts.get_map_grid(transformer_back)

    grid_array[grid_array==0] = np.nan
    grid_array[grid_array<=-99] = np.nan

    plt.figure(figsize=(16, 9))
    hy_m = Basemap(projection='npaeqd', boundinglat=40, lon_0=180, resolution='c')
    hy_m.pcolormesh(x_map, y_map, data=grid_array, cmap=plt.cm.jet,vmin=0,latlon = True)
    hy_m.colorbar(location='right')
    # cb.set_label('sst')
    hy_m.fillcontinents()
    hy_m.drawmapboundary()
    hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(satellite +'_'+ sensor +'_'+ day)
    plt.savefig(save_path +r'pic\\'+ file_name + '.jpg')
    plt.close()

    # 只截取高纬度地区
    grid_array_sub = np.hstack((grid_array[:700,:600],grid_array[:700,1200:]))
    x_map_sub = np.hstack((x_map[:700,: 600],x_map[:700, 1200:]))
    y_map_sub = np.hstack((y_map[:700,: 600], y_map[:700, 1200:]))
    with Dataset(save_path + file_name + '.nc', 'w', format='NETCDF4') as f:
        f.createDimension('x', grid_array_sub.shape[0])
        f.createDimension('y', grid_array_sub.shape[1])
        sst_north = f.createVariable('sst_north', 'f4', dimensions=('x', 'y'))
        sst_north[:] = grid_array_sub
        lat = f.createVariable('lat', 'f4', dimensions=('x', 'y'))
        lon = f.createVariable('lon', 'f4', dimensions=('x', 'y'))
        lon[:] = x_map_sub
        lat[:] = y_map_sub
    print(str(con_point + i+1) + '\\' + str(len(files)))
    print(satellite +'_'+ sensor +'_'+ day)

if __name__ == '__main__':
    for log in file_list[::30]:
        draw_and_save(log)
