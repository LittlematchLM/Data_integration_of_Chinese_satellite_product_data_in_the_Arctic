from RSData import *
from HaiYangData import *
import glob
import datetime

satellite = r'HY2B'
sensor = r'ALT'
hyfiles = glob.glob(r'H:\HY-2B\ALT\*\*\*.nc')
hyfiles.sort()
save_path_swh = r'H:\\polor_project\\output_new\\swh\\HY-2B\\'
save_path_ssh = r'H:\\polor_project\\output_new\\ssh\\HY-2B\\'
hy_value = ['swh_ku','swh_c','mean_sea_surface','rain_flag','ice_flag','surface_type']
hy_alt = HaiYangData(satellite=satellite, sensor=sensor,resolution=25000)

file_list = []
list = []
for i in range(len(hyfiles)):

    if i == 0:
        list.append(hyfiles[i])
        continue

    if (hyfiles[i].split('\\')[-1].split('_')[-2].split('T')[0]) == (hyfiles[i-1].split('\\')[-1].split('_')[-2].split('T')[0]):
        list.append(hyfiles[i])
    else:
        file_list.append(list)
        list = []
        list.append(hyfiles[i])
file_list.append(list)

# file_list = file_list[1:2]
file_list = file_list[::30]

# 将WGS 84坐标（4326）转化为极射投影
crs = CRS.from_epsg(4326)
crs = CRS.from_string("epsg:4326")
crs = CRS.from_proj4("+proj=latlon")
crs = CRS.from_user_input(4326)
crs2 = CRS(proj="aeqd")

transformer = HaiYangData.set_transformer(crs,crs2)
transformer_back = HaiYangData.set_transformer(crs2,crs)


file_list = file_list[-3:-1]
for i,files in enumerate(file_list):
    day =files[0].split('\\')[-1].split('_')[-2].split('T')[0]
    file_name = satellite + '_' + sensor + '_' + day
    hy_ori_df = pd.DataFrame(np.column_stack((hy_alt.alt_from_nc_files(files = files, value=hy_value))), columns=['lon', 'lat', 'time']+hy_value)

    # 删除无效点,只处理北纬66°以上的数据
    hy_fill_value = 32767
    hy_ori_df = hy_ori_df.drop(hy_ori_df[hy_ori_df.swh_ku > 500].index)
    hy_ori_df = hy_alt.data_filter(hy_ori_df,'lat',66)
    hy_ori_df = hy_ori_df.drop(hy_ori_df[(hy_ori_df.rain_flag != 0)].index)
    hy_ori_df = hy_ori_df.drop(hy_ori_df[(hy_ori_df.ice_flag != 0)].index)
    hy_ori_df = hy_ori_df.drop(hy_ori_df[(hy_ori_df.surface_type == 2)].index)
    hy_ori_df = hy_ori_df.drop(hy_ori_df[(hy_ori_df.swh_ku > 25)].index)
    # 将投影数据添加到原始dataframe中
    hy_alt.add_proj(hy_ori_df, transformer)

    # 交叉点平均化
    mean_grid,count_grid = hy_alt.coincident_point_mean(hy_ori_df,'swh_ku',get_count=True)
    max_grid = hy_alt.coincident_point_max(hy_ori_df,'swh_ku')
    min_grid = hy_alt.coincident_point_min(hy_ori_df, 'swh_ku')

    # # 计算平均每个格中落多少个点
    # mean_counter_num = count_grid.sum() / (count_grid != 0).sum()
    # 获得XYmgrid
    hy_x_map, hy_y_map = hy_alt.get_map_grid(transformer_back)

    plt.figure(figsize=(16, 9))
    hy_m = Basemap(projection='npaeqd', boundinglat=66, lon_0=0, resolution='c')
    hy_m.pcolormesh(hy_x_map, hy_y_map, data=mean_grid, cmap=plt.cm.jet,vmin=0, vmax=5,latlon = True)
    hy_m.colorbar(location='right')
    hy_m.fillcontinents()
    hy_m.drawmapboundary()
    hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(satellite +'_'+ sensor +'_'+ day)
    plt.savefig(save_path_swh + r'pic\\' + file_name + '.jpg')
    plt.close()

    plt.figure(figsize=(16, 9))
    hy_m = Basemap(projection='npaeqd', boundinglat=66, lon_0=0, resolution='c')
    hy_m.pcolormesh(hy_x_map, hy_y_map, data=max_grid, cmap=plt.cm.jet,vmin=0, vmax=5,latlon = True)
    hy_m.colorbar(location='right')
    hy_m.fillcontinents()
    hy_m.drawmapboundary()
    hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(satellite +'_'+ sensor +'_'+ day + 'max')
    plt.savefig(save_path_swh + r'pic\\' + file_name+ 'max' + '.jpg')
    plt.close()

    plt.figure(figsize=(16, 9))
    hy_m = Basemap(projection='npaeqd', boundinglat=66, lon_0=0, resolution='c')
    hy_m.pcolormesh(hy_x_map, hy_y_map, data=min_grid, cmap=plt.cm.jet,vmin=0, vmax=5,latlon = True)
    hy_m.colorbar(location='right')
    hy_m.fillcontinents()
    hy_m.drawmapboundary()
    hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(satellite +'_'+ sensor +'_'+ day + 'min')
    plt.savefig(save_path_swh + r'pic\\' + file_name+ 'min' + '.jpg')
    plt.close()

    mean_grid_sub = np.hstack((mean_grid[:700,:600],mean_grid[:700,1200:]))
    hy_x_map_sub = np.hstack((hy_x_map[:700,: 600],hy_x_map[:700, 1200:]))
    hy_y_map_sub = np.hstack((hy_y_map[:700,: 600], hy_y_map[:700, 1200:]))
    count_grid = np.hstack((count_grid[:700, : 600], count_grid[:700, 1200:]))

    with Dataset(save_path_swh  + file_name + '.h5', 'w') as file:
        file.createDimension('x', mean_grid_sub.shape[0])
        file.createDimension('y', mean_grid_sub.shape[1])
        # 添加数据属性
        file.setncattr_string('satellite',satellite)
        file.setncattr_string('sensor', sensor)
        file.setncattr_string('data time', day)
        file.setncattr_string('data create time', datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
        file.setncattr_string('projection mode', 'polar projection')
        file.setncattr_string('resolution', '25KM')
        file.setncattr_string('data processing organization', 'Ocean University Of China')

        swh_north = file.createVariable('swh_north', 'f4', dimensions=('x', 'y'))
        lat = file.createVariable('lat', 'f4', dimensions=('x', 'y'))
        lon = file.createVariable('lon', 'f4', dimensions=('x', 'y'))
        swh_north[:] = mean_grid_sub

        swh_north.setncattr_string('Dataset Name', 'Sea Wave Height')
        swh_north.setncattr_string('Datatype', 'float')
        swh_north.setncattr_string('valid_range','0.5-20')
        swh_north.setncattr_string('units', 'm')
        swh_north.setncattr_string('observation area', 'North of 60 N')
        swh_north.setncattr_string('origin data product', 'H2B_OPER_GDR_2PC')
        count_g = f.createVariable('count_grid', 'i4', dimensions=('x', 'y'))
        count_g[:] = count_grid

        lon[:] = hy_x_map_sub
        lat[:] = hy_y_map_sub
    print(str(i+1) + '//' + str(len(file_list)))
    print(satellite +'_'+ sensor +'_'+ day)

    hy_ori_df = hy_ori_df.drop(hy_ori_df[hy_ori_df.mean_sea_surface > 500].index)
    # 交叉点平均化
    mean_grid,count_grid = hy_alt.coincident_point_mean(hy_ori_df,'mean_sea_surface',get_count=True)

    plt.figure(figsize=(16, 9))
    hy_m = Basemap(projection='npaeqd', boundinglat=66, lon_0=0, resolution='c')
    hy_m.pcolormesh(hy_x_map, hy_y_map, data=mean_grid, cmap=plt.cm.jet,vmin=-15, vmax=60,latlon = True)
    hy_m.colorbar(location='right')
    hy_m.fillcontinents()
    hy_m.drawmapboundary()
    hy_m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    hy_m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(satellite +'_'+ sensor +'_'+ day)
    plt.savefig(save_path_ssh + r'pic\\' + file_name + '.jpg')
    plt.close()


    mean_grid_sub = np.hstack((mean_grid[:700,:600],mean_grid[:700,1200:]))
    hy_x_map_sub = np.hstack((hy_x_map[:700,: 600],hy_x_map[:700, 1200:]))
    hy_y_map_sub = np.hstack((hy_y_map[:700,: 600], hy_y_map[:700, 1200:]))
    count_grid = np.hstack((count_grid[:700, : 600], count_grid[:700, 1200:]))
    with Dataset(save_path_ssh  + file_name + '.h5', 'w') as f:
        f.createDimension('x', mean_grid_sub.shape[0])
        f.createDimension('y', mean_grid_sub.shape[1])
        # 添加数据属性
        f.setncattr_string('satellite',satellite)
        f.setncattr_string('sensor', sensor)
        f.setncattr_string('data time', day)
        f.setncattr_string('data create time', datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
        f.setncattr_string('projection mode', 'polar stereographic projection')
        f.setncattr_string('resolution', '25KM')
        f.setncattr_string('data processing organization', 'Ocean University Of China')

        swh_north = f.createVariable('ssh_north', 'f4', dimensions=('x', 'y'))

        swh_north[:] = mean_grid_sub
        swh_north.setncattr_string('Dataset Name', 'Mean Sea Surface Height')
        swh_north.setncattr_string('Datatype', 'float')
        swh_north.setncattr_string('valid_range','0.5-20')
        swh_north.setncattr_string('units', 'm')
        swh_north.setncattr_string('observation area', 'North of 60 N')
        swh_north.setncattr_string('origin data product', 'H2B_OPER_GDR_2PC')

        lat = f.createVariable('latitude', 'f4', dimensions=('x', 'y'))
        lon = f.createVariable('longitude', 'f4', dimensions=('x', 'y'))
        lon[:] = hy_x_map_sub
        lat[:] = hy_y_map_sub
        count_g = f.createVariable('count_grid', 'i4', dimensions=('x', 'y'))
        count_g[:] = count_grid

    print(str(i+1) + '/' + str(len(file_list)))
    print(satellite +'_'+ sensor +'_'+ day)
