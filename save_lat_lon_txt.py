''':key
存取经纬度数据至txt，用于读取shp文件

'''

from  netCDF4 import Dataset

file = r'E:\python_workfile\polar_project\FY3C_MWRI\lat_lon.h5'

with Dataset(file, 'r') as fh:
    lats = fh.variables['Latitude'][:]
    lons = fh.variables['Longitude'][:]

lat_data = lats.flatten()
lon_data = lons.flatten()

with open('lat_lon.txt', 'w') as f:
    for lat,lon in zip(lat_data, lon_data):
        if lat < 60:
            continue
        f.write(str(lat))
        f.write(',')
        f.write(str(lon))
        f.write('\n')