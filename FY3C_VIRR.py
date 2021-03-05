from RSData import *
from HaiYangData import *
import glob
import os

satellite = r'FY3C'
sensor = r'VIRR'

files = glob.glob(r'/mnt/data12/users/hanlu/data/icecon/VIRR/FY-3C VIRR/*/*.HDF')
files.sort()
save_path = r'//mnt//data12//users//hanlu//data//icecon//VIRR_save//FY-3C//'

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



grid_array = np.zeros((fy_virr.nlat,fy_virr.nlon))
grid_num_array = np.zeros((fy_virr.nlat,fy_virr.nlon))

for i,file in enumerate(files[con_point:]):
    try:
        with Dataset(file, mode='r') as fh:
            sic = fh.variables['Daily Sea Ice Coverage Grid'][:]
            day = file.split('//')[-1].split(r'_')[7]


        file_name = satellite + '_' + sensor + '_' + day
        lats, lons = np.mgrid[ 90:-90:1800j,-180:180:3600j]

        projlats, projlons = transformer.transform(lats, lons)

        value_array = np.empty(shape=(lons.shape[0], lons.shape[1],5))

        value_array[:,:,0] = lats
        value_array[:,:,1] = lons
        value_array[:,:,2],value_array[:,:,3] = transformer.transform(value_array[:,:,0], value_array[:,:,1])
        value_array[:,:,4] = sic


        x = (value_array[:,:,2] / fy_virr.resolution).astype(np.int)
        y = (value_array[:,:,3] / fy_virr.resolution).astype(np.int)

        grid_array[y,x] += value_array[:,:,4]
        grid_num_array[y,x] += 1
# 获得XYmgrid
        grid_array = grid_array / grid_num_array
        x_map, y_map = fy_virr.get_map_grid(transformer_back)


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

    except OSError:
        print(file)