from RSData import *
import pyproj
from  pyproj  import  CRS
from pyproj import Proj
import h5py
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm, colors
import glob
from netCDF4 import Dataset
import pandas as pd
import gzip
from collections import defaultdict

class HaiYangData(RSData):
    def __init__(self,satellite,sensor,resolution,description='temp no'):
        super().__init__(satellite,sensor,description)
        self.resolution = resolution
        self.nlat,self.nlon  = self.get_nlat_nlon_npaeqd(self.resolution)

    def hy_file_day_split(self, files):
        '''
        :files 文件列表
        :returns 逐日分的hy文件列表
        '''
        files.sort()
        file_list = []
        list = []
        for i in range(len(files)):

            if i == 0:
                list.append(files[i])
                continue

            if (files[i].split('\\')[-1].split('_')[-2].split('T')[0]) == (
            files[i - 1].split('\\')[-1].split('_')[-2].split('T')[0]):
                list.append(files[i])
            else:
                file_list.append(list)
                list = []
                list.append(files[i])
        file_list.append(list)
        return file_list


    def alt_from_nc_files(self, files, value):
        '''
        从hy2B的netcdf中读取高度计数据
        :arg 要读取的Variable名称
        hy_value:传进来的value列表
        '''
        lon_array = np.array([])
        lat_array = np.array([])
        time_array = np.array([])
        value_array = np.full((1,len(value)),fill_value=65530)
        for file in files:
            try:
                with Dataset(file, mode='r') as fh:
                    lons = fh.variables['lon'][:]
                    lats = fh.variables['lat'][:]
                    times = fh.variables['time'][:]
                    value_a_t = np.zeros((lons.shape[0], len(value)))
                    for i,key in enumerate(value):
                        values = fh.variables[key][:]
                        value_a_t[:, i] = values

                        # np.vstack(value_array[0], values)
                    lon_array = np.append(lon_array, lons)
                    lat_array = np.append(lat_array, lats)
                    value_array = np.vstack((value_array, value_a_t))
                    time_array = np.append(time_array, times)

            except OSError:
                print('nc文件损坏{f}'.format(f=file))
        value_array = np.delete(value_array, 0, axis=0)
        return lon_array, lat_array, time_array,value_array

    def cy_siral_from_nc(self,files_path, value):
        # 加载cryosat数据
        lon_array = np.array([])
        lat_array = np.array([])
        time_array = np.array([])
        value_array = np.full((1, len(value)), fill_value=65530)
        for cyfile in files_path:
            with Dataset(cyfile, mode='r') as fh:
                lons = fh.variables['lon_01'][:]
                lats = fh.variables['lat_01'][:]
                time = fh.variables['time_cor_01'][:]
                value_a_t = np.zeros((lons.shape[0], len(value)))

                for i, key in enumerate(value):
                    if key == 'height_1_20_ku' or key == 'height_2_20_ku' or key == 'height_3_20_ku':
                        values = fh.variables[key][:]
                        value_a_t[:, i] = values[::20]
                    else:
                        values = fh.variables[key][:]
                        value_a_t[:, i] = values
                lon_array = np.append(lon_array, lons)
                lat_array = np.append(lat_array, lats)
                value_array = np.vstack((value_array, value_a_t))
                time_array = np.append(time_array, time)
        value_array = np.delete(value_array, 0, axis=0)
        return lon_array, lat_array, time_array, value_array

    def is_atlas_from_nc(self,files_path, value):
        # icesat2 的时间是从2018-01-01 00：00：00开始记的，Hy2b和cryosat2的是从2000-01-01 00：00：00开始计的
        # 2018-01-01 00：00：00 与2000-01-01 00：00：00 相差了568080000秒
        correction_second = 568080000

        lon_array = np.array([])
        lat_array = np.array([])
        light_array = np.array([])
        value_array = np.full((1, len(value)), fill_value=65530)
        time_array = np.array([])
        tracks = ['gt1l', 'gt1r', 'gt2l', 'gt2r', 'gt3l', 'gt3r']
        surf_array = np.full((1,5),fill_value=65530)
        
        for ncfile in files_path:
            with h5py.File(ncfile, 'r') as f:
                for track in tracks:
                    try:
                        lats = f[track]['ssh_segments']['latitude'][:]
                        lons = f[track]['ssh_segments']['longitude'][:]
                        # values = f[track]['ssh_segments']['heights'][value][:]
                        time = f[track]['ssh_segments']['delta_time'][:]
                        
                        
                        value_a_t = np.zeros((lons.shape[0], len(value)))
#                         surf_t = np.zeros((lons.shape[0], 5))
                        surf_t = f[track]['ssh_segments']['stats']['surf_type_prcnt'][:]
                        light = np.full(shape=(lons.shape[0],1),fill_value=track)

                        for i, key in enumerate(value):
                            values = f[track]['ssh_segments']['heights'][key][:]
                            value_a_t[:, i] = values
                        surf_array = np.vstack((surf_array, surf_t))
                        light_array = np.append(light_array, light)
                        lon_array = np.append(lon_array, lons)
                        lat_array = np.append(lat_array, lats)
                        value_array = np.vstack((value_array, value_a_t))
                        time_array = np.append(time_array, time + correction_second)
                    except KeyError:
                        print(ncfile, track)
                        pass
        value_array = np.delete(value_array, 0, axis=0)
        surf_array = np.delete(surf_array, 0, axis=0)
        return lon_array, lat_array, time_array,surf_array,light_array,value_array

    def data_filter(self,data_frame,lat_type,min):
        ''':arg
        按照min的标准，删除纬度在min以下的数据
        '''
        data_frame = data_frame.drop(data_frame[(data_frame[lat_type] < min)].index)
        return data_frame

    def get_nan_grid(self,nlat, nlon):
        nan_grid = np.full(shape=(nlon, nlat), fill_value=np.nan)
        return nan_grid

    def get_zeros_grid(self,nlat, nlon):
        zeros_grid = np.zeros((nlon, nlat))
        return zeros_grid

    # 交叉点平均化
    def coincident_point_mean(self,dataframe,value, get_count=False):
        num_grid = self.get_zeros_grid(self.nlat, self.nlon)
        grid_array = self.get_nan_grid(self.nlat, self.nlon)
        for index in dataframe.index:
            x = int(dataframe.projlons[index] / self.resolution)
            y = int(dataframe.projlats[index] / self.resolution)
            if num_grid[x][y] == 0:
                grid_array[x][y] = dataframe[value][index]
                num_grid[x][y] += 1
            else:
                grid_array[x][y] += dataframe[value][index]
                num_grid[x][y] += 1
        grid_array = grid_array / num_grid
        if get_count:
            return grid_array, num_grid
        return grid_array

    # 获取最大值
    def coincident_point_max(self,dataframe,value):
        num_grid = self.get_zeros_grid(self.nlat, self.nlon)
        grid_array = self.get_nan_grid(self.nlat, self.nlon)
        for index in dataframe.index:
            x = int(dataframe.projlons[index] / self.resolution)
            y = int(dataframe.projlats[index] / self.resolution)
            if num_grid[x][y] == 0:
                grid_array[x][y] = dataframe[value][index]
                num_grid[x][y] += 1
            else:
                if dataframe[value][index] <= grid_array[x][y]:
                    continue
                else:grid_array[x][y] = dataframe[value][index]
        return grid_array

    # 获取最小值
    def coincident_point_min(self,dataframe,value):
        num_grid = self.get_zeros_grid(self.nlat, self.nlon)
        grid_array = self.get_nan_grid(self.nlat, self.nlon)
        for index in dataframe.index:
            x = int(dataframe.projlons[index] / self.resolution)
            y = int(dataframe.projlats[index] / self.resolution)
            if num_grid[x][y] == 0:
                grid_array[x][y] = dataframe[value][index]
                num_grid[x][y] += 1
            else:
                if dataframe[value][index] >= grid_array[x][y]:
                    continue
                else:grid_array[x][y] = dataframe[value][index]
        return grid_array

    # 获取数组的长和宽
    def get_nlat_nlon_npaeqd(self,resolution):
        nlat, nlon = 40000000 / resolution, 40000000 / resolution
        nlat = np.int(nlat)
        nlon = np.int(nlon)
        return nlat, nlon

    def get_nlat_nlon_cyl(self,resolution):
        nlat, nlon = 40000000 / resolution, 20000000 / resolution
        nlat = np.int(nlat)
        nlon = np.int(nlon)
        return nlat, nlon

    def set_transformer(crs, crs_to):

        transformer = pyproj.Transformer.from_crs(crs, crs_to)
        return transformer

    def split_W_E_earth(self,data_frame,transformer):

        # 东西半球分别处理
        df_e = data_frame[data_frame.lon < 180].copy()
        df_w = data_frame[data_frame.lon > 180].copy()

        df_w['lon'] = df_w['lon'] - 180  # 不要试图删除这句话
        projlats_e, projlons_e = transformer.transform(df_e.lat.values, df_e.lon.values)
        projlats_w, projlons_w = transformer.transform(df_w.lat.values, df_w.lon.values)

        df_e['projlats'] = projlats_e
        df_e['projlons'] = projlons_e

        df_w['projlats'] = projlats_w
        df_w['projlons'] = projlons_w

        return df_e,df_w

    def add_proj(self,data_frame, transformer):
        ''':key
        '''
        projlats, projlons = transformer.transform(data_frame.lat.values, data_frame.lon.values)
        data_frame['projlats'] = projlats
        data_frame['projlons'] = projlons

    def get_map_grid(self,transformer_back):
        # 设置mgrid
        _x = np.arange(self.nlat)
        _y = np.arange(self.nlon)
        _xx, _yy = np.meshgrid(_x * self.resolution, _y * self.resolution)

        # 将xx,yy转换回坐标形式
        _y_map_e, _x_map_e = transformer_back.transform(_xx, _yy)
        _y_map_w, _x_map_w = transformer_back.transform(_xx - 40000000, _yy)

        # For superstitious reasons, two hemispheres had to be dealt with separately

        x_map = np.hstack((_x_map_e[:, :int(self.nlon / 2)], _x_map_w[:, int(self.nlon / 2):]))
        y_map = np.hstack((_y_map_e[:, :int(self.nlat / 2)], _y_map_w[:, int(self.nlat / 2):]))

        return x_map, y_map


    def coincident_point_mean_array(self,transformer,value_array,n):
        '''
        对数据进行交叉点平均化
        输入的数据纬度为（原始数据.shape[0],原始数据.shape[1],n））
        n为数据种类+4
        前四层分别是lat, lon, projlat,projlon
        '''
        num_grid = self.get_zeros_grid(self.nlat, self.nlon)
        grid_array = self.get_nan_grid(self.nlat, self.nlon)
        value_array[:,:,2],value_array[:,:,3] = transformer.transform(value_array[:,:,0], value_array[:,:,1])
        x = int(value_array[:,:,2] / self.resolution)
        y = int(value_array[:,:,3] / self.resolution)

        for index in dataframe.index:

            if num_grid[x][y] == 0:
                grid_array[x][y] = dataframe[value][index]
                num_grid[x][y] += 1
            else:
                grid_array[x][y] += dataframe[value][index]
                num_grid[x][y] += 1
        grid_array = grid_array / num_grid
        return grid_array


    def coincident_time_log(self,dataframe,value):
        time_dict = {}
        # value_grid存储原始值
        # time_grid存储原始时间
        # 当有两个点在一个格子的时候，用else里面的语句

        time_grid = self.get_nan_grid(self.nlat, self.nlon)
        num_grid = self.get_zeros_grid(self.nlat, self.nlon)
        value_grid = self.get_nan_grid(self.nlat, self.nlon)
        for index in dataframe.index:
            x = int((dataframe.projlons[index]) / self.resolution)
            y = int(dataframe.projlats[index] / self.resolution)

            if num_grid[x][y] == 0:
                value_grid[x][y] = dataframe[value][index]
                time_grid[x][y] = dataframe.time[index]
                dict_name = str(x) + '+' + str(y)
                time_dict[dict_name] = {time_grid[x][y]: value_grid[x][y]}
                num_grid[x][y] = 1

            else:
                dict_name = str(x) + '+' + str(y)
                time_dict[dict_name][dataframe.time[index]] = dataframe[value][index]
                num_grid[x][y] += 1
        return time_dict
    
    def coincident_time_log_test(self,dataframe,value):
        time_dict = {}
        # value_grid存储原始值
        # time_grid存储原始时间
        # 当有两个点在一个格子的时候，用else里面的语句

        time_grid = self.get_nan_grid(self.nlat, self.nlon)
        num_grid = self.get_zeros_grid(self.nlat, self.nlon)
        value_grid = self.get_nan_grid(self.nlat, self.nlon)
        x = ((dataframe.projlons) / self.resolution).astype(np.int)
        y = ((dataframe.projlats) / self.resolution).astype(np.int)
        for index in dataframe.index:
            if num_grid[x][y] == 0:
                value_grid[x][y] = dataframe[value][index]
                time_grid[x][y] = dataframe['time'][index]
                dict_name = str(x) + '+' + str(y)
                time_dict[dict_name] = {time_grid[x][y]: value_grid[x][y]}
                num_grid[x][y] = 1

            else:
                dict_name = str(x) + '+' + str(y)
                time_dict[dict_name][dataframe.time[index]] = dataframe[value][index]
                num_grid[x][y] += 1
        return time_dict
