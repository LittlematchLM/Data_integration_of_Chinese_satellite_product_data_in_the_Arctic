from RSData import *
from HaiYangData import *
import glob
import datetime

def polar_plot(x_map, y_map,grid,color_lable=None,title=None,cmap = plt.cm.jet):
    m = Basemap(projection='npaeqd', boundinglat=66, lon_0=0, resolution='c')
    m.pcolormesh(x_map, y_map, data=grid, cmap=cmap,latlon = True)
    # cb = m.colorbar(location='bottom')
    # if color_lable:
    #     cb.set_label(color_lable)
    m.fillcontinents()
    m.drawmapboundary()
    m.drawparallels(np.arange(-90., 120., 10.), labels=[1, 0, 0, 0])
    m.drawmeridians(np.arange(-180., 180., 60.), labels=[0, 0, 0, 1])
    plt.title(title)


satellite = r'HY2B'
sensor = r'ALT'
value_swh = r'SWH'
resolution_n = r'25KM'

years = ['2019','2020']
months = ['04','05','06','07','08','09']
resolution = 25000
output_dir = r'E:\\python_workfile\\remote_sensing\\dayil_cover\\'
hy_value = ['swh_ku','rain_flag','ice_flag','surface_type']

crs = CRS.from_epsg(4326)
crs = CRS.from_string("epsg:4326")
crs = CRS.from_proj4("+proj=latlon")
crs = CRS.from_user_input(4326)
crs2 = CRS(proj="aeqd")

transformer = HaiYangData.set_transformer(crs,crs2)
transformer_back = HaiYangData.set_transformer(crs2,crs)


hyfiles = []
hy_fill_value = 32767
for yea in years:
    for mon in months:
        hy_dir_path = r'I:\\remote_sensing_data\\swh\\hy2b\\ALT\\'+ yea + '\\' + mon
        hyfiles = hyfiles + (glob.glob(hy_dir_path + '\*.nc'))


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

hy_alt = HaiYangData(satellite=satellite, sensor=sensor,resolution=25000)
hy_x_map, hy_y_map = hy_alt.get_map_grid(transformer_back)

# files = file_list[1]
for files in file_list:
    year = files[0].split('_')[-1][:4]
    month = files[0].split('_')[-1][4:6]
    day = files[0].split('_')[-1][6:8]
    hy_ori_df = pd.DataFrame(np.column_stack((hy_alt.alt_from_nc_files(files, value=hy_value))), columns=['lon', 'lat', 'time']+hy_value)
    # hy_df = hy_ori_df.drop(hy_ori_df[hy_ori_df['swh_ku'] >500].index)
    hy_df = hy_alt.data_filter(hy_ori_df, 'lat', 66)

    # hy_df = hy_df.drop(hy_df[(hy_df.rain_flag != 0)].index)
    hy_df = hy_df.drop(hy_df[(hy_df.ice_flag == 0)].index)
    # hy_df = hy_df.drop(hy_df[(hy_df.surface_type == 2)].index)
    hy_alt.add_proj(hy_df, transformer)
    hy_swh_grid = hy_alt.coincident_point_mean(hy_df, 'swh_ku')
    plt.figure(figsize=(10, 10))
    polar_plot(hy_x_map, hy_y_map,hy_swh_grid,title='HaiYang2B '+str(year) + str(month) + str(day))
    plt.savefig(output_dir+ str(year) + str(month) + str(day)  +' HY' + 'ice_flag_cover.jpg')
    plt.close()
