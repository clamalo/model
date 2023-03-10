# import necessary packages
import requests
import os
import threading
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from timezonefinder import TimezoneFinder
obj = TimezoneFinder()
from dateutil import tz as dateutil
from_zone = dateutil.tz.tzutc()
import time
import imageio
from metpy.plots import USCOUNTIES
from adjustText import adjust_text
from metpy.calc import wet_bulb_temperature
from metpy.units import units
import metpy
import math
import warnings
from matplotlib import cm as cm
warnings.filterwarnings("ignore")

# function to find the most recent model run (00 & 12 only for canadian)
def get_datestr_and_cycle(canadian):
    current_utc_time = datetime.utcnow()
    hour = current_utc_time.hour
    if canadian == True:
        if 4 <= hour < 16:
            cycle = "00"
            datestr = current_utc_time.strftime("%Y%m%d")
        elif 16 <= hour < 24:
            cycle = "12"
            datestr = current_utc_time.strftime("%Y%m%d")
        else:
            cycle = "12"
            previous_day = current_utc_time - timedelta(days=1)
            datestr = previous_day.strftime("%Y%m%d")
    else:
        if 4 <= hour < 10:
            cycle = "00"
            datestr = current_utc_time.strftime("%Y%m%d")
        elif 10 <= hour < 16:
            cycle = "06"
            datestr = current_utc_time.strftime("%Y%m%d")
        elif 16 <= hour < 22:
            cycle = "12"
            datestr = current_utc_time.strftime("%Y%m%d")
        elif 22 <= hour < 24:
            cycle = "18"
            datestr = current_utc_time.strftime("%Y%m%d")
        else:
            cycle = "18"
            previous_day = current_utc_time - timedelta(days=1)
            datestr = previous_day.strftime("%Y%m%d")
    return datestr, cycle


# function to make the frame a three digit string
def name_frame(f):
    if f < 10:
        return '00' + str(f)
    elif f < 100:
        return '0' + str(f)
    else:
        return str(f)

# create colormap for total snow plotting
def total_snow_colormap():
    cmap = colors.ListedColormap(['#ffffff','#7fb2ff','#4c72d8','#1933b2','#7fff7f','#46b246','#0c660c','#ffff66','#e1b244','#c36622','#a51900','#ff99ff','#cc68cc','#993899','#660766','#cccccc','#999999','#666666'])
    return cmap

# create nws snow colormap
def nws_snow_colormap():
    cmap = colors.ListedColormap(['#ffffff','#7db9dd','#5594ca','#346bac','#072692','#f9ff93','#fec400','#ff8700','#db1400','#9e0000','#680000','#562a29','#d4d3fd','#ad9fdd','#916eb2','#916eb2'])
    return cmap

# create colormap for total precip plotting
def weatherbell_precip_colormap():
    cmap = colors.ListedColormap(['#ffffff', '#bdbfbd','#aba5a5', '#838383', '#6e6e6e', '#b5fbab', '#95f58b','#78f572', '#50f150','#1eb51e', '#0ea10e', '#1464d3', '#2883f1', '#50a5f5','#97d3fb', '#b5f1fb','#fffbab', '#ffe978', '#ffc13c', '#ffa100', '#ff6000','#ff3200', '#e11400','#c10000', '#a50000', '#870000', '#643c31', '#8d6558','#b58d83', '#c7a095','#f1ddd3', '#cecbdc'])#, '#aca0c7', '#9b89bd', '#725ca3','#695294', '#770077','#8d008d', '#b200b2', '#c400c4', '#db00db'])
    return cmap

# create colormap for hourly snow plotting
def hourly_snow_colormap():
    cmap = colors.ListedColormap(['#FFFFFF', '#cccccc', '#7fb2ff', '#1933b2', '#7fff7f', '#0c660c', '#ffff66', '#a51900', '#ff99ff', '#660766', '#9455f4'])
    return cmap

# create colormap for hourly precip plotting
def hourly_precip_colormap():
    cmap = colors.ListedColormap(['#ffffff', '#bdbfbd','#aba5a5', '#838383', '#6e6e6e', '#b5fbab', '#95f58b','#78f572', '#50f150','#1eb51e', '#0ea10e', '#1464d3'])
    return cmap

# create colormap for temp plotting
def temp_colormap():
    cmap = colors.ListedColormap(['#7f1786','#8634e5','#8469c7','#ea33f7','#3c8925','#5dca3b','#a0fc4e','#75fb4c','#0000f5','#458ef7','#4fafe8','#6deaec','#75fbfd','#ffff54','#eeee4e','#f9d949','#f2a95f','#ef8955','#ef8632','#fbe5dd','#f3b1ba','#ed736f','#db4138','#dc4f25','#ea3323','#bc271a','#c3882e','#824b2d','#7f170e'])
    return cmap

# create colormap for slr plotting
def slr_colormap():
    cmap = colors.ListedColormap(['#ffffff','#afeeee','#81a7e8','#5b6ce1','#4141de','#4b0082','#611192','#7722a2','#8e33b3','#a444c3','#ba55d3','#da70d6','#d452bb','#cd33a0','#c71585','#d24081','#de6b7e','#e9967a','#f0b498','#f8d1b7'])
    return cmap

# create colormap for wind plotting
def wind_colormap():
    cmap = colors.ListedColormap(['#ffffff','#5fdee4','#108b9f','#ccf06f','#ff3713','#5a0304','#e38dff','#ffa6c1','#ff6164'])
    return cmap

# create colormap for ptype plotting
def ptype_colormap():
    white_cmap = colors.ListedColormap(['#ffffff','#ffffff','#ffffff','#ffffff','#ffffff'])
    rain_cmap = colors.ListedColormap(['#b5e5ad','#76c77c','#56c164','#3cb15c','#319f4f'])
    mixed_cmap = colors.ListedColormap(['#fab87d','#fec067','#ffa772','#f69b55','#ff892e'])
    snow_cmap = colors.ListedColormap(['#b3cbe5','#919bcd','#8f85bd','#8d6ab5','#8b54a5'])
    snow_cmap = cm.get_cmap('seismic_r',10)
    cmap = np.vstack((white_cmap(np.linspace(0,1,5)),rain_cmap(np.linspace(0,1,5)),mixed_cmap(np.linspace(0,1,5)),snow_cmap(np.linspace(0,1,10))[5:]))
    cmap = colors.ListedColormap(cmap, name='ptype')
    return cmap


# function to download a low-res upper air file given the frame, ingest source, and whether to download wind data
def download_25_file(frame,ingest_source,compute_wind):

    if ingest_source == 'nomads':
        if compute_wind == True:
            # url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{cycle}z.pgrb2.0p25.f{name_frame(frame)}&lev_0C_isotherm=on&lev_1000_mb=on&lev_500_mb=on&lev_700_mb=on&lev_850_mb=on&lev_925_mb=on&var_HGT=on&var_TMP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
            url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{cycle}z.pgrb2.0p25.f{name_frame(frame)}&lev_0C_isotherm=on&lev_1000_mb=on&lev_500_mb=on&lev_700_mb=on&lev_850_mb=on&lev_925_mb=on&var_HGT=on&var_TMP=on&var_UGRD=on&var_VGRD=on&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
        else:
            # url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{cycle}z.pgrb2.0p25.f{name_frame(frame)}&lev_0C_isotherm=on&lev_1000_mb=on&lev_500_mb=on&lev_700_mb=on&lev_850_mb=on&lev_925_mb=on&var_HGT=on&var_TMP=on&subregion=&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
            url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{cycle}z.pgrb2.0p25.f{name_frame(frame)}&lev_0C_isotherm=on&lev_1000_mb=on&lev_500_mb=on&lev_700_mb=on&lev_850_mb=on&lev_925_mb=on&var_HGT=on&var_TMP=on&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
    elif ingest_source == 'aws':
        url = f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{datestr}/{cycle}/atmos/gfs.t{cycle}z.pgrb2.0p25.f{name_frame(frame)}'

    if 'nomads' in url:
        file_name = directory+'files/gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2'
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
    if 'aws' in url:
        idx_url = url + '.idx'
        idx_response = requests.get(idx_url)
        idx = idx_response.text
        lines = idx.splitlines()
        line_indices = []
        if int(frame) == 0:
            variable_suffix = 'anl'
        else:
            variable_suffix = str(int(frame))+' hour fcst'
        if compute_wind == True:
            target_variables = ['TMP:500 mb:', 'TMP:700 mb:', 'TMP:850 mb:', 'TMP:925 mb:', 'TMP:1000 mb:', 'HGT:500 mb:', 'HGT:700 mb:', 'HGT:850 mb:', 'HGT:925 mb:', 'HGT:1000 mb:', 'UGRD:500 mb:', 'UGRD:700 mb:', 'UGRD:850 mb:', 'UGRD:925 mb:', 'UGRD:1000 mb:', 'VGRD:500 mb:', 'VGRD:700 mb:', 'VGRD:850 mb:', 'VGRD:925 mb:', 'VGRD:1000 mb:']
        else:
            target_variables = ['TMP:500 mb:', 'TMP:700 mb:', 'TMP:850 mb:', 'TMP:925 mb:', 'TMP:1000 mb:', 'HGT:500 mb:', 'HGT:700 mb:', 'HGT:850 mb:', 'HGT:925 mb:', 'HGT:1000 mb:']
        for i in range(len(target_variables)):
            target_variables[i] = target_variables[i] + variable_suffix
        data_list = []
        for l in range(len(lines)):
            line_variable = lines[l].split(':')[3]+':'+lines[l].split(':')[4]+':'+lines[l].split(':')[5]
            if line_variable in target_variables:
                line_indices.append(l)
        for line_index in line_indices:
            line = lines[line_index]
            start_bytes = int(line.split(':')[1])
            end_bytes = int(lines[line_index+1].split(':')[1])
            headers = {'Range': 'bytes=' + str(start_bytes) + '-' + str(end_bytes)}
            response = requests.get(url, headers=headers)
            data_list.append(response.content)
        data = b''.join(data_list)
        file_name = directory+'files/gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2'
        with open(file_name, 'wb') as f:
            f.write(data)


# function to download a flux file given the frame and ingest source
def download_flux_file(frame,ingest_source):
    if ingest_source == 'nomads':
        # url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_sflux.pl?file=gfs.t{cycle}z.sfluxgrbf{name_frame(frame)}.grib2&lev_surface=on&var_PRATE=on&subregion=&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
        url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_sflux.pl?file=gfs.t{cycle}z.sfluxgrbf{name_frame(frame)}.grib2&lev_surface=on&var_PRATE=on&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
    elif ingest_source == 'aws':
        url = f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{datestr}/{cycle}/atmos/gfs.t{cycle}z.sfluxgrbf{name_frame(frame)}.grib2'

    if 'nomads' in url:
        file_name = directory+'files/gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '_sp.grib2'
        response = requests.get(url)
        with open(file_name, 'wb') as f:
            f.write(response.content)
    if 'aws' in url:
        idx_url = url + '.idx'
        idx_response = requests.get(idx_url)
        idx = idx_response.text
        lines = idx.splitlines()
        if int(frame)%6 == 0:
            target_variables = ['PRATE:surface:'+str(frame-6)+'-'+str(frame)+' hour ave fcst']
        else:
            target_variables = ['PRATE:surface:'+str(frame-int(frame)%6)+'-'+str(frame)+' hour ave fcst']

        data_list = []
        line_indices = []
        for l in range(len(lines)):
            line_variable = lines[l].split(':')[3]+':'+lines[l].split(':')[4]+':'+lines[l].split(':')[5]
            if line_variable in target_variables:
                line_indices.append(l)
        for line_index in line_indices:
            line = lines[line_index]
            start_bytes = int(line.split(':')[1])
            end_bytes = int(lines[line_index+1].split(':')[1])
            headers = {'Range': 'bytes=' + str(start_bytes) + '-' + str(end_bytes)}
            response = requests.get(url, headers=headers)
            data_list.append(response.content)
        data = b''.join(data_list)
        file_name = directory+'files/gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '_sp.grib2'
        with open(file_name, 'wb') as f:
            f.write(data)


# function to download canadian data given the frame and whether to download wind data
def download_canadian_file(frame,compute_wind):
    if not os.path.exists(directory+'files/gribs/' + name_frame(frame)):
        os.makedirs(directory+'files/gribs/' + name_frame(frame))

    canadian_urls = []

    if frame > 0:
        canadian_urls.append(f'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{cycle}/{name_frame(frame)}/CMC_glb_APCP_SFC_0_latlon.15x.15_{datestr+cycle}_P{name_frame(frame)}.grib2')

    levels = ['1000','500','700','850','925']
    variables = ['HGT','TMP']
    if compute_wind == True:
        variables = variables+['UGRD','VGRD']
    for level in levels:
        for variable in variables:
            canadian_urls.append(f'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{cycle}/{name_frame(frame)}/CMC_glb_{variable}_ISBL_{level}_latlon.15x.15_{datestr+cycle}_P{name_frame(frame)}.grib2')

    if os.path.exists(directory+'files/gribs/' + name_frame(frame) + '/gdps_init.grib2'):
        os.remove(directory+'files/gribs/' + name_frame(frame) + '/gdps_init.grib2')

    for url in canadian_urls:
        if 'APCP' in url:
            r = requests.get(url, allow_redirects=True)
            open(directory+'files/gribs/' + name_frame(frame) + '/gdps_init.grib2', 'wb').write(r.content)
        else:
            r = requests.get(url, allow_redirects=True)
            open(directory+'files/gribs/' + name_frame(frame) + '/gdps_init.grib2', 'ab').write(r.content)


# function to thread the above functions for downloading data
def ingest_frame(frame,datestr,cycle,ingest_source,canadian,compute_wind):

    if frame == first_frame or (frame-first_frame)%(step*10) == 0:
        if frame+(step*10) > max_frame:
            max_ingest_frame = max_frame+1
        else:
            max_ingest_frame = frame+(step*10)+1
        frames = range(frame,max_ingest_frame,step)

        print('Ingesting initialization data for forecast hours ' + str(frame) + ' to ' + str(max_ingest_frame-1)+'...')

        if frame == max_frame:
            frames = [frame]

        for ingest_frame_number in frames:
            if not os.path.exists(directory+'files/gribs/' + name_frame(ingest_frame_number)):
                os.makedirs(directory+'files/gribs/' + name_frame(ingest_frame_number))

        if canadian == False and ingest_source == 'nomads':
            if frame != first_frame:
                last_download_time = os.path.getmtime(directory+'files/gribs/' + name_frame(int(frame)-step) + '/gfs_init' + name_frame(int(frame)-step) + '.grib2')
                if time.time()-last_download_time < 60:
                    time.sleep(60+(time.time()-last_download_time))

        #american data ingestion
        threads = [threading.Thread(target=download_25_file, args=(ingest_frame_number,ingest_source,compute_wind)) for ingest_frame_number in frames]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if frames[0] == 0:
            frames = frames[1:]
        threads = [threading.Thread(target=download_flux_file, args=(ingest_frame_number,ingest_source)) for ingest_frame_number in frames]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        #canadian data ingestion
        if canadian == True:
            if frame+(step*10) > max_frame:
                max_ingest_frame = max_frame+1
            else:
                max_ingest_frame = frame+(step*10)+1
            frames = range(frame,max_ingest_frame,step)
            threads = [threading.Thread(target=download_canadian_file, args=(ingest_frame_number,compute_wind)) for ingest_frame_number in frames]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

# function to find temperatures at elevations given two isobaric arrays
def find_temperature(gh1,gh2,parameter_pair,elevation):
    parameter = parameter_pair[0]
    gh = parameter_pair[1]
    temperature = gh1[parameter] + (gh2[parameter] - gh1[parameter]) * ((elevation - gh1[gh]) / (gh2[gh] - gh1[gh]))
    return temperature

# function to find elevations at temperatures given two isobaric arrays
def find_elevation(gh1, gh2, parameter_pair, temperature):
    parameter = parameter_pair[0]
    gh = parameter_pair[1]
    elevation = gh1[gh] + (gh2[gh] - gh1[gh]) * ((temperature - gh1[parameter]) / (gh2[parameter] - gh1[parameter]))
    return elevation


def day_night_scatters(points,day_and_night_scatter_separate,domain,plot_states,plot_counties):

    if type(domain) != list:
        domain_name = domain
        directory_name = domain_name.lower()
    else:
        domain_name = 'custom'
        directory_name = 'custom'

    if not os.path.exists(directory+'outputs/scatters/'+directory_name):
        os.makedirs(directory+'outputs/scatters/'+directory_name)
    for the_file in os.listdir(directory+'outputs/scatters/'+directory_name):
        os.remove(directory+'outputs/scatters/'+directory_name+'/'+the_file)

    if type(domain) != list:
        with open(directory+'domains.txt', 'r') as myfile:
            domain_text=myfile.read()
            domain_text = domain_text.replace(' ','')
            domain_text = domain_text.split('\n')
            for i in range(len(domain_text)):
                if domain_text[i].split('=')[0] == domain_name:
                    domain = domain_text[i].split('=')[1].split(',')
            if len(domain) != 4:
                print('\n\nERROR: Requested domain not found in domains.txt\n')
                quit()
    for i in range(len(domain)):
        domain[i] = float(domain[i])

    print('Plotting day/night scatters...')
    empty_df = pd.DataFrame(columns=['name','forecast_hour','valid_time','total_snow'])

    names = []

    for n in range(len(points)):
        name = points[n][0]
        lat,lon = float(points[n][1]),float(points[n][2])

        if lat < domain[2] or lat > domain[0] or lon < domain[1] or lon > domain[3]:
            continue
        else:
            if points_tag != None:
                if points[n][-1] == points_tag:
                    names.append(name)
            else:
                names.append(name)

    if len(names) == 0:
        print('No points in domain')
        return

    for name in names:
        df = pd.read_csv(directory+'files/csvs/'+name+'.csv')

        for row in range(len(df)):
            valid_time = df['valid_time'][row]
            date_format = "%Y-%m-%d %H:%M:%S%z"
            valid_time = datetime.strptime(valid_time, date_format)
            hour = valid_time.hour

            if day_and_night_scatter_separate == True:
                if hour == 8 or hour == 16:
                    empty_df = empty_df.append({'name':name,'latitude':df['latitude'][row],'longitude':df['longitude'][row],'forecast_hour':df['forecast_hour'][row],'valid_time':df['valid_time'][row],'total_snow':df['total_snow'][row]}, ignore_index=True)
            else:
                if hour == 16:
                    empty_df = empty_df.append({'name':name,'latitude':df['latitude'][row],'longitude':df['longitude'][row],'forecast_hour':df['forecast_hour'][row],'valid_time':df['valid_time'][row],'total_snow':df['total_snow'][row]}, ignore_index=True)

    first_forecast_hour = empty_df['forecast_hour'][0]
    date_format = "%Y-%m-%d %H:%M:%S%z"
    first_valid_year = datetime.strptime(empty_df['valid_time'][0], date_format).year
    first_valid_month = datetime.strptime(empty_df['valid_time'][0], date_format).month
    first_valid_day = datetime.strptime(empty_df['valid_time'][0], date_format).day
    first_valid_hour = datetime.strptime(empty_df['valid_time'][0], date_format).hour
    first_valid_date = datetime(first_valid_year,first_valid_month,first_valid_day,first_valid_hour)

    for row in range(len(empty_df)-1,0,-1):

        date_format = "%Y-%m-%d %H:%M:%S%z"
        valid_year = datetime.strptime(empty_df['valid_time'][row], date_format).year
        valid_month = datetime.strptime(empty_df['valid_time'][row], date_format).month
        valid_day = datetime.strptime(empty_df['valid_time'][row], date_format).day
        valid_hour = datetime.strptime(empty_df['valid_time'][row], date_format).hour
        valid_date = datetime(valid_year,valid_month,valid_day,valid_hour)

        if valid_date != first_valid_date:
            empty_df['total_snow'][row] = empty_df['total_snow'][row] - empty_df['total_snow'][row-1]

    empty_df = empty_df[empty_df.forecast_hour != first_forecast_hour]

    empty_df = empty_df.reset_index(drop=True)

    for row in range(len(empty_df)):
        valid_time = empty_df['valid_time'][row]
        date_format = "%Y-%m-%d %H:%M:%S%z"
        valid_time = datetime.strptime(valid_time, date_format)
        day_of_week = valid_time.strftime("%A")
        hour = valid_time.hour

        if hour == 8:
            valid_time = valid_time-timedelta(days=1)
            day_of_week = valid_time.strftime("%A")
            day_night = 'Night'
            hour_range = '4pm-8am'
        else:
            day_night = 'Day'
            hour_range = '8am-4pm'

        month_day = valid_time.strftime("%m/%d")

        if day_and_night_scatter_separate == True:
            label = day_of_week + ' ' + day_night + ' (' + hour_range + ') - ' + month_day
        else:
            label = day_of_week + ' - ' + month_day

        empty_df['valid_time'][row] = label

    empty_df.to_csv(directory+'files/csvs/empty.csv')

    valid_times = empty_df['valid_time'].unique()
    for valid_time in valid_times:
        df = empty_df[empty_df.valid_time == valid_time]
        df = df.reset_index(drop=True)

        fig = plt.figure(figsize=(10,7),facecolor='grey')
        ax = plt.axes(projection=ccrs.PlateCarree())

        ax.set_facecolor("grey")

        ax.set_extent([domain[1],domain[3],domain[2],domain[0]], crs=ccrs.PlateCarree())

        texts = []

        cmap = nws_snow_colormap()
        cmap.set_over(color='#6600cc')
        bounds = [0,1,2,3,4,6,8,12,18,24,30,36,48,60,72,96]

        for resort in range(len(df)):
            name = df['name'][resort]
            total_snow = abs(round(df['total_snow'][resort],1))

            latitude = df['latitude'][resort]
            longitude = df['longitude'][resort]

            point_text = name + '\n' + str(total_snow)+'"'

            texts.append(ax.annotate(point_text, (longitude, latitude), xytext=(longitude, latitude), transform=ccrs.PlateCarree(), fontsize=8, fontweight='bold', color=cmap(np.digitize(total_snow, bounds)-1)))
            plt.plot(longitude,latitude,'o',color=cmap(np.digitize(total_snow, bounds)-1),markersize=3,transform=ccrs.PlateCarree())

        norm = colors.BoundaryNorm(bounds, cmap.N)
        cbar = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, orientation='horizontal', pad=0.05, fraction=0.05, ticks=bounds, shrink=0.8)
        cbar.outline.set_edgecolor('white')
        cbar.set_label('Total Snowfall (in)', fontsize=10, color='white')
        cbar.ax.tick_params(color='white')
        cbar.ax.set_xticklabels(['0','1','2','3','4','6','8','12','18','24','30','36','48','60','72','96'], color='white')

        adjust_text(texts, arrowprops=dict(arrowstyle='-', color='white', lw=0.7, alpha=0.5))

        ax.coastlines()
        ax.add_feature(cfeature.BORDERS, edgecolor='black')
        if plot_states == True:
            ax.add_feature(cfeature.STATES, edgecolor='black', linewidth=0.5)
        if plot_counties == True:
            ax.add_feature(USCOUNTIES.with_scale('500k'),linewidth=0.2, edgecolor='black')

        plt.title('Total Snowfall - '+valid_time,fontsize=12,color='white',fontweight='bold')
        if day_and_night_scatter_separate == True:
            save_label = (valid_time.split(' ')[-1]).replace('/','-')+'-'+(valid_time.split(' ')[0])+(valid_time.split(' ')[1])
        else:
            save_label = (valid_time.split(' ')[2]).replace('/','-')+'-'+valid_time.split(' ')[0]
        plt.savefig(directory+'outputs/scatters/'+domain_name+'/'+save_label+'.png',bbox_inches='tight',dpi=300)

directory = os.path.dirname(os.path.realpath(__file__))+'/'
# open the model config file and read in the parameters
with open(directory+'model_config.txt', 'r') as myfile:
    text=myfile.read()
    text = text.split('\n')
    for arg in range(len(text)):
        if text[arg] == '':
            continue
        config = text[arg].split('=')[1]
        config = config.replace(' ','')
        text[arg] = config

    if os.name == 'nt':
        clear_prompt = 'cls'
    else:
        clear_prompt = 'clear'

    if text[0] == 'True':
        ingest = True
    else:
        ingest = False
    if text[1] == 'True':
        canadian = True
    else:
        canadian = False
    american_data_percentage = 0.5
    if text[2] == 'True':
        compute_wind = True
    else:
        compute_wind = False
    
    snow_temp,mix_temp = 34,38

    step = int(text[3])
    first_frame = int(text[4])
    max_frame = int(text[5])
    ingest_source = 'nomads'
    if text[6] == 'Detect':
        detect_recent_run = True
        datestr,cycle = get_datestr_and_cycle(canadian)
    else:
        detect_recent_run = False
        datestr,cycle = text[6][0:8],text[6][8:10]
    plot_types = text[7].split(',')
    if text[8] == 'True':
        plot_states = True
    else:
        plot_states = False
    if text[9] == 'True':
        plot_counties = True
    else:
        plot_counties = False
    if text[10] == 'True':
        plot_points = True
    else:
        plot_points = False
    domain = text[11].split(',')
    if len(domain) == 1:
        domain = domain[0]
    domain_name = domain
    if text[12] == 'True':
        scatters_only = True
    else:
        scatters_only = False
    if text[13] == 'True':
        day_and_night_scatter_separate = True
    else:
        day_and_night_scatter_separate = False
    if text[14] == 'None':
        points_tag = None
    else:
        points_tag = text[14]

if scatters_only == True:
    point_dataframes = []
    with open(directory+'points.txt', 'r') as myfile:
        text=myfile.read()
    text = text.replace(' ','')
    points = text.split('\n')
    for n in range(len(points)):
        points[n] = points[n].split(',')
        if len(points[n]) < 4:
            continue
        df = pd.DataFrame(columns=['tp','snow','t2m','slr','wind','total_tp','total_snow','valid_time'])
        point_dataframes.append(df)

    day_night_scatters(points,day_and_night_scatter_separate,domain,plot_states,plot_counties)
    quit()

if type(domain) != list:
    with open(directory+'domains.txt', 'r') as myfile:
        domain_text=myfile.read()
        domain_text = domain_text.replace(' ','')
        domain_text = domain_text.split('\n')
        for i in range(len(domain_text)):
            if domain_text[i].split('=')[0] == domain:
                domain = domain_text[i].split('=')[1].split(',')
        if len(domain) != 4:
            print('\n\nERROR: Requested domain not found in domains.txt\n')
            quit()
for i in range(len(domain)):
    domain[i] = float(domain[i])

# check the parameters for errors
if step == 0:
    print('\n\nERROR: Step cannot be less than 1\n')
    quit()
if step > 6:
    print('\n\nERROR: Step cannot be greater than 6\n')
    quit()
if canadian == True and (step != 3 and step != 6):
    print('\n\nERROR: Canadian initialization can only be run with 3 or 6 hour steps\n')
    quit()
if american_data_percentage < 0 or american_data_percentage > 1:
    print('\n\nERROR: Model ratio must be between 0 and 1\n')
    quit()
if step < 3 and max_frame > 120:
    print('\n\nERROR: Step cannot be less than 3 with a max frame greater than 120\n')
    quit()
if canadian == True and max_frame > 240:
    print('\n\nERROR: Canadian initialization can only be run with a max frame less than 240\n')
    quit()
if ingest == True and ingest_source != 'nomads' and ingest_source != 'aws':
    print('\n\nERROR: Ingest type must be nomads or aws\n')
    quit()
if canadian == True and cycle!='00' and cycle!='12':
    print('\n\nERROR: Canadian initialization can only be run at 00 or 12 UTC cycles\n')
    quit()
if os.path.exists(directory) == False:
    print('\n\nERROR: Directory does not exist\n')
    quit()
if compute_wind == False and 'wind' in plot_types:
    print('\n\nERROR: compute_wind must be set to True to plot wind\n')
    quit()
for plot_type in plot_types:
    if plot_type not in ['tp','total_snow','total_tp','snow','t2m','slr','wind','ptype','']:
        print('\n\nERROR: Plot type must be tp, total_snow, total_tp, snow, t2m, slr, wind, ptype, or none\n')
        quit()
if domain[0] < -60:
    print('\n\nERROR: Domain minimum latitude must be greater than -60\n')
    quit()
if domain[1] > 180 or domain[3] > 180:
    print('\n\nERROR: Domain longitudes must be on -180 to 180 scale\n')
    quit()
if domain [0] < domain[2]:
    print('\n\nERROR: Domain maximum latitude must be greater than domain minimum latitude\n')
    quit()
if domain[1] < 180 and domain[3] > 180:
    print('\n\nERROR: Domain cannot cross the 180th meridian\n')
    quit()

# turn the date and cycle into a datetime object
init_datetime = datetime.strptime(datestr+cycle,'%Y%m%d%H')

# create subdirectories if they don't exist
sub_directory = directory+'outputs/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
sub_directory = directory+'files/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
sub_directory = directory+'outputs/figures/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
sub_directory = directory+'files/gribs/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
sub_directory = directory+'files/csvs/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
sub_directory = directory+'outputs/points/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
for filename in os.listdir(sub_directory):
    os.remove(sub_directory+filename)
sub_directory = directory+'outputs/scatters/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)

# download and open the elevation dataset, crop to desired domain, and coarsen 2x
if os.path.exists(directory+'files/elevation.nc') == False:
    r = requests.get('https://www.dropbox.com/s/wholbzwikcyogte/new_elevation.nc?dl=1', allow_redirects=True)
    open(directory+'files/elevation.nc', 'wb').write(r.content)
elevation_ds = xr.open_dataset(directory+'files/elevation.nc', engine='netcdf4')
elevation_ds = elevation_ds.sel(longitude=slice(domain[1],domain[3]),latitude=slice(domain[2],domain[0]))
elevation_ds = elevation_ds.fillna(0)
# elevation_ds = elevation_ds.coarsen(latitude=5,longitude=5, boundary='trim').mean()

times = []

# for loop to iterate through frames using minimum frame, maximum frame, and step specified by user
for frame in range(first_frame,max_frame+1,step):

    start = time.time()

    os.system(clear_prompt)
    if frame >= first_frame+(2*step):
        average_time = sum(times)/len(times)
        time_remaining = str(int(average_time*((max_frame-frame)/step)/60))
        print('Processing frame '+str(frame)+' of '+str(max_frame)+' - estimated time remaining: '+time_remaining+' minutes')

    # if the frame is the first frame, create a dataframe to store data at each point, append to list
    if frame == first_frame:
        point_dataframes = []
        with open(directory+'points.txt', 'r') as myfile:
            text=myfile.read()
        text = text.replace(' ','')
        points = text.split('\n')
        for n in range(len(points)):
            points[n] = points[n].split(',')
            if len(points[n]) < 4:
                continue
            df = pd.DataFrame(columns=['tp','snow','t2m','slr','wind','total_tp','total_snow','valid_time'])
            point_dataframes.append(df)

    # create grib subdirectories for each frame if they don't already exist
    sub_directory = directory+'files/gribs/'+name_frame(frame)
    if not os.path.exists(sub_directory):
        os.makedirs(sub_directory)

    # download initialization grib files if the user requests to ingest data
    if ingest == True:
        ingest_frame(frame,datestr,cycle,ingest_source,canadian,compute_wind)

    print('Opening and pre-processing initialization data...')
    # open the upper air init file
    reg_ds = xr.load_dataset(directory+'files/gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2', engine='cfgrib',filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
    # convert to the correct longitudes
    reg_ds['longitude'] = np.where(reg_ds['longitude'] > 180, reg_ds['longitude'] - 360, reg_ds['longitude'])
    # # open the freezing level init file, convert to feet and add to reg_ds
    # # isotherm_ds = xr.load_dataset(directory+'files/gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2', engine='cfgrib',filter_by_keys={'typeOfLevel': 'isothermZero'})
    # # reg_ds['freezing_level'] = isotherm_ds['gh']*3.28084
    # interpolate reg_ds to the elevation dataset
    reg_ds = reg_ds.interp(latitude=elevation_ds.latitude,longitude=elevation_ds.longitude)
    # if the user requests to compute wind, compute it and drop the u and v components
    if compute_wind == True:
        reg_ds['wind'] = (np.sqrt(reg_ds['u']**2+reg_ds['v']**2))*2.23694
        reg_ds = reg_ds.drop(['u','v'])
    # if the frame is not the first frame, compute the average temperatures and heights between the current and prior frame (for use in slr calculations)
    if frame > first_frame:
        reg_ds['t_avg'] = (reg_ds['t'] + prior_reg_ds['t'])/2
        reg_ds['gh_avg'] = (reg_ds['gh'] + prior_reg_ds['gh'])/2
    # copy the dataset to use as the prior dataset for the next frame
    prior_reg_ds = reg_ds.copy()


    # if the frame is not the first frame, open the surface init file
    if frame > first_frame:
        sp_ds = xr.load_dataset(directory+'files/gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '_sp.grib2', engine='cfgrib')
        # convert to the correct longitudes
        sp_ds['longitude'] = np.where(sp_ds['longitude'] > 180, sp_ds['longitude'] - 360, sp_ds['longitude'])
        # interpolate sp_ds to the elevation dataset
        sp_ds = sp_ds.interp(latitude=elevation_ds.latitude,longitude=elevation_ds.longitude)
        # compute the frame precipitation
        if (frame-step)%6 != 0:
            if frame%6 == 0:
                remainder = 6
            else:
                remainder = frame%6
            sp_ds['tp'] = ((sp_ds['prate']*remainder)-(prior_sp_ds['prate']*(remainder-step)))*3600
        else:
            sp_ds['tp'] = sp_ds['prate']*3600*step
        # copy the dataset to use as the prior dataset for the next frame
        prior_sp_ds = sp_ds.copy()


    # if the user requests to compute with canadian data, open the init file
    if canadian == True:
        canadian_ds = xr.load_dataset(directory+'files/gribs/' + name_frame(frame) + '/gdps_init.grib2', engine='cfgrib')
        # interpolate canadian_ds to the elevation dataset
        canadian_ds = canadian_ds.interp(latitude=elevation_ds.latitude,longitude=elevation_ds.longitude)
        # if the user requests to compute wind, compute it and drop the u and v components
        if compute_wind == True:
            canadian_ds['wind'] = (np.sqrt(canadian_ds['u']**2+canadian_ds['v']**2))*2.23694
            canadian_ds = canadian_ds.drop(['u','v'])
        # if the frame is not the first frame, compute the average temperatures and heights between the current and prior frame (for use in slr calculations)
        if frame > first_frame:
            canadian_ds['t_avg'] = (canadian_ds['t'] + prior_canadian_ds['t'])/2
            canadian_ds['gh_avg'] = (canadian_ds['gh'] + prior_canadian_ds['gh'])/2
            # compute the frame precipitation
            if frame == first_frame+step:
                if first_frame != 0:
                    prior_canadian_ds = xr.load_dataset(directory+'files/gribs/' + name_frame(frame-step) + '/gdps_init.grib2', engine='cfgrib')
                    prior_canadian_ds = prior_canadian_ds.interp(latitude=elevation_ds.latitude,longitude=elevation_ds.longitude)
                    canadian_ds['tp'] = canadian_ds['unknown']-prior_canadian_ds['unknown']
                else:
                    canadian_ds['tp'] = canadian_ds['unknown']
            else:
                canadian_ds['tp'] = (canadian_ds['unknown'] - prior_canadian_ds['unknown'])
        # copy the dataset to use as the prior dataset for the next frame
        prior_canadian_ds = canadian_ds.copy()


    print('Processing data...')
    # if the frame is the first frame, skip the rest of the loop
    if frame == first_frame:
        continue

    # # compute the dewpoint and wet bulb temperature
    # reg_ds['r'] = reg_ds['r'].where(reg_ds['r'] != 0, 0.1)
    # reg_ds['td'] = metpy.calc.dewpoint_from_relative_humidity(reg_ds['t'], reg_ds['r']/100)
    # reg_ds['tw'] = metpy.calc.wet_bulb_temperature(500*metpy.units.units.hPa, reg_ds['t']*metpy.units.units.degK, reg_ds['td'])

    reg_ds['tp'] = sp_ds['tp'].copy()

    # if the user requests to compute with canadian data, combine the american and canadian data according to the percentage of american data specified
    if canadian == True:
        reg_ds['t'] = (reg_ds['t']*american_data_percentage) + (canadian_ds['t']*(1-american_data_percentage))
        reg_ds['gh'] = (reg_ds['gh']*american_data_percentage) + (canadian_ds['gh']*(1-american_data_percentage))
        reg_ds['t_avg'] = (reg_ds['t_avg']*american_data_percentage) + (canadian_ds['t_avg']*(1-american_data_percentage))
        reg_ds['gh_avg'] = (reg_ds['gh_avg']*american_data_percentage) + (canadian_ds['gh_avg']*(1-american_data_percentage))
        reg_ds['tp'] = (reg_ds['tp']*american_data_percentage) + (canadian_ds['tp']*(1-american_data_percentage))

        if compute_wind == True:
            reg_ds['wind'] = (reg_ds['wind']*american_data_percentage) + (canadian_ds['wind']*(1-american_data_percentage))

    reg_ds['elevation'] = elevation_ds['elevation']

    # create variables for each isobaric level
    gh1 = reg_ds.isel(isobaricInhPa=0)
    gh2 = reg_ds.isel(isobaricInhPa=1)
    gh3 = reg_ds.isel(isobaricInhPa=2)
    gh4 = reg_ds.isel(isobaricInhPa=3)
    gh5 = reg_ds.isel(isobaricInhPa=4)
    elevation = reg_ds['elevation']

    # # compute the freezing level and snow level
    # freezing_temp = 273.15
    # reg_ds['freezing_level'] = xr.where(freezing_temp > gh1['t'], gh1['gh'], xr.where(freezing_temp > gh2['t'], find_elevation(gh1,gh2,['t','gh'],freezing_temp), xr.where(freezing_temp > gh3['t'], find_elevation(gh2,gh3,['t','gh'],freezing_temp), xr.where(freezing_temp > gh4['t'], find_elevation(gh3,gh4,['t','gh'],freezing_temp),find_elevation(gh4,gh5,['t','gh'],freezing_temp)))))
    # reg_ds['freezing_level'] = reg_ds['freezing_level']*3.28084
    # reg_ds['snow_level'] = xr.where(freezing_temp > gh1['tw'], gh1['gh'], xr.where(freezing_temp > gh2['tw'], find_elevation(gh1,gh2,['tw','gh'],freezing_temp), xr.where(freezing_temp > gh3['tw'], find_elevation(gh2,gh3,['tw','gh'],freezing_temp), xr.where(freezing_temp > gh4['tw'], find_elevation(gh3,gh4,['tw','gh'],freezing_temp),find_elevation(gh4,gh5,['tw','gh'],freezing_temp)))))
    # reg_ds['snow_level'] = reg_ds['snow_level']*3.28084

    # compute the elevation-adjusted temperatures from the isobaric levels
    reg_ds['t2m'] = xr.where(elevation < gh2['gh'], find_temperature(gh1,gh2,['t','gh'],elevation), xr.where(elevation < gh3['gh'], find_temperature(gh2,gh3,['t','gh'],elevation), xr.where(elevation < gh4['gh'], find_temperature(gh3,gh4,['t','gh'],elevation),find_temperature(gh4,gh5,['t','gh'],elevation))))
    reg_ds['t2m_avg'] = xr.where(elevation < gh2['gh'], find_temperature(gh1,gh2,['t_avg','gh_avg'],elevation), xr.where(elevation < gh3['gh'], find_temperature(gh2,gh3,['t_avg','gh_avg'],elevation), xr.where(elevation < gh4['gh'], find_temperature(gh3,gh4,['t_avg','gh_avg'],elevation),find_temperature(gh4,gh5,['t_avg','gh_avg'],elevation))))
    # if the user wants to compute wind, compute the elevation-adjusted wind from the isobaric levels
    if compute_wind == True:
        reg_ds['wind'] = xr.where(elevation < gh2['gh'], find_temperature(gh1,gh2,['wind','gh'],elevation), xr.where(elevation < gh3['gh'], find_temperature(gh2,gh3,['wind','gh'],elevation), xr.where(elevation < gh4['gh'], find_temperature(gh3,gh4,['wind','gh'],elevation),find_temperature(gh4,gh5,['wind','gh'],elevation))))

    # convert the temperatures to fahrenheit and compute the elevation-adjusted SLRs
    reg_ds['t2m_avg'] = reg_ds['t2m_avg'] * 9/5 - 459.67
    reg_ds['t2m'] = reg_ds['t2m'] * 9/5 - 459.67
    reg_ds['slr'] = xr.where(reg_ds['t2m_avg'] > snow_temp, 0, xr.where(reg_ds['t2m_avg'] >= 30, 1+(39-reg_ds['t2m_avg']), xr.where(reg_ds['t2m_avg'] >= 10, 10+((30-reg_ds['t2m_avg'])*0.5), xr.where(reg_ds['t2m_avg'] >= 1, 20-((10-reg_ds['t2m_avg'])*0.5), xr.where(reg_ds['t2m_avg'] >= -4, 15-(0-reg_ds['t2m_avg']), xr.where(reg_ds['t2m_avg'] < -4, 10, np.nan))))))

    # compute the snowfall using the precipitation and SLR data
    reg_ds['tp']*=.0393701
    reg_ds['tp'] = reg_ds['tp'].where(reg_ds['tp'] > 0, 0)
    reg_ds['snow'] = reg_ds['tp']*reg_ds['slr']

    reg_ds['tp_maxed'] = reg_ds['tp'].copy()
    reg_ds['tp_maxed'] = xr.where((reg_ds['tp_maxed']) > 0.5, 0.5,
                                      reg_ds['tp_maxed'])

    reg_ds['ptype'] = xr.where((reg_ds['tp']) < 0.01, 0.25,
        xr.where(reg_ds['t2m_avg'] > float(mix_temp), 0.49999+(reg_ds['tp_maxed']),
            xr.where(reg_ds['t2m_avg'] > float(snow_temp), 0.99999+(reg_ds['tp_maxed']),
                1.49999+(reg_ds['tp_maxed']))))

    # if the frame is the first frame, create the total_ds dataset, otherwise add the snowfall and precip to the total_ds dataset
    if frame == first_frame+step:
        total_ds = reg_ds.copy()
        total_ds = total_ds[['snow','tp']]
    else:
        total_ds['snow'] += reg_ds['snow']
        total_ds['tp'] += reg_ds['tp']

    # add all the data to the point dataframes
    for n in range(len(points)):
        lat,lon = float(points[n][1]),float(points[n][2])
        elevation = float(reg_ds['elevation'].sel(latitude=lat,longitude=lon,method='nearest').values)*3.28084
        valid_time = init_datetime + timedelta(hours=frame)
        tp_value = float(reg_ds['tp'].sel(latitude=lat,longitude=lon,method='nearest').values)
        snow_value = float(reg_ds['snow'].sel(latitude=lat,longitude=lon,method='nearest').values)
        total_tp_value = float(total_ds['tp'].sel(latitude=lat,longitude=lon,method='nearest').values)
        total_snow_value = float(total_ds['snow'].sel(latitude=lat,longitude=lon,method='nearest').values)
        t2m_value = float(reg_ds['t2m'].sel(latitude=lat,longitude=lon,method='nearest').values)
        t2m_avg_value = float(reg_ds['t2m_avg'].sel(latitude=lat,longitude=lon,method='nearest').values)
        slr_value = float(reg_ds['slr'].sel(latitude=lat,longitude=lon,method='nearest').values)
        ptype_value = float(reg_ds['ptype'].sel(latitude=lat,longitude=lon,method='nearest').values)
        if compute_wind == True:
            wind_value = float(reg_ds['wind'].sel(latitude=lat,longitude=lon,method='nearest').values)
        # freezing_level_value = float(reg_ds['freezing_level'].sel(latitude=lat,longitude=lon,method='nearest').values)
        if compute_wind == True:
            new_row = {'tp':tp_value,'snow':snow_value,'t2m':t2m_value,'t2m_avg':t2m_avg_value,'slr':slr_value,'wind':wind_value,'total_tp':total_tp_value,'total_snow':total_snow_value,'forecast_hour':frame,'elevation':elevation,'latitude':lat,'longitude':lon,'ptype':ptype_value}
        else:
            new_row = {'tp':tp_value,'snow':snow_value,'t2m':t2m_value,'t2m_avg':t2m_avg_value,'slr':slr_value,'total_tp':total_tp_value,'total_snow':total_snow_value,'forecast_hour':frame,'elevation':elevation,'latitude':lat,'longitude':lon,'ptype':ptype_value}
        point_dataframes[n] = point_dataframes[n].append(new_row, ignore_index=True)


    print('Plotting...')
    # plot each of the requested plot types
    for plot_type in plot_types:

        if plot_type == '':
            continue

        # create the specific plot output directory if it doesn't already exist
        if not os.path.exists('outputs/figures/'+plot_type):
            os.makedirs('outputs/figures/'+plot_type)

        # create the figure and axes
        fig = plt.figure(figsize=(10,7))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # specify the colormap, bounds, and tick labels, and title depending on the plot type
        if plot_type == 'total_snow':
            # colormap = total_snow_colormap()
            colormap = nws_snow_colormap()
            colormap.set_over(color='#6600cc')
            # bounds = [0,1,2,4,6,8,10,12,15,18,21,24,27,30,33,36,42,48]
            bounds = [0,1,2,3,4,6,8,12,18,24,30,36,48,60,72,96]
            # tick_labels = ['0','1','2','4','6','8','10','12','15','18','21','24','27','30','33','36','42','48']
            tick_labels = [str(x) for x in bounds]
            plot_label,units = 'Total Snowfall (in)','"'
        elif plot_type == 'total_tp':
            colormap = weatherbell_precip_colormap()
            colormap.set_over(color='#aca0c7')
            bounds = [0,0.01,0.03,0.05,0.075,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.2,1.4,1.6,1.8,2,2.5,3,3.5,4,5,6,7,8,9,10]#,11,12,13,14,15,16,17,18,19,20])
            tick_locations = [0,0.1,0.5,1,2,5,10]
            tick_labels = [str(x) for x in tick_locations]
            plot_label,units = 'Total Precipitation (in)','"'
        elif plot_type == 'snow':
            colormap = hourly_snow_colormap()
            colormap.set_over(color='#6600cc')
            bounds = [0,0.1,0.5,0.75,1,1.5,2,2.5,3,3.5,4]
            tick_labels = [str(x) for x in bounds]
            plot_label,units = str(step)+' Hour Snowfall (in)','"'
        elif plot_type == 'tp':
            colormap = hourly_precip_colormap()
            colormap.set_over('#4fc3f7')
            bounds = [0,0.01,0.03,0.05,0.075,0.1,0.15,0.2,0.25,0.3,0.4,0.5]
            tick_labels = [str(x) for x in bounds]
            plot_label,units = str(step)+' Hour Precipitation (in)','"'
        elif plot_type == 't2m':
            colormap = temp_colormap()
            bounds = [-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110]
            tick_labels = ['-30','-20','-10','0','10','20','30','40','50','60','70','80','90','100','110']
            plot_label,units = 'Temperature (F)','F'
        elif plot_type == 'slr':
            colormap = slr_colormap()
            bounds = [0,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
            tick_labels = [str(x) for x in bounds]
            plot_label,units = 'SLR',''
        elif plot_type == 'wind':
            colormap = wind_colormap()
            bounds = [0,10,20,30,40,50,60,70,80]
            tick_labels = [str(x) for x in bounds]
            plot_label,units = 'Wind Speed (mph)','mph'
        elif plot_type == 'ptype':
            colormap = ptype_colormap()
            bounds = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2]
            tick_locations = [0.25,0.75,1.25,1.75]
            tick_labels = ['None','Rain','Mixed','Snow']
            plot_label,units = 'Precipitation Type (0.1" QPF Increments)',''

        norm = colors.BoundaryNorm(boundaries=bounds, ncolors=len(bounds))

        if 'total' in plot_type:
            plot_ds = total_ds
            parameter = plot_type.split('_')[1]
        else:
            plot_ds = reg_ds
            parameter = plot_type

        if plot_type != 'ptype':
            if plot_type == 'slr':
                cf = ax.contourf(plot_ds.longitude, plot_ds.latitude, plot_ds[parameter], transform=ccrs.PlateCarree(), cmap=colormap, norm=norm, levels=bounds)
            elif plot_type == 't2m':
                cf = ax.contourf(plot_ds.longitude, plot_ds.latitude, plot_ds[parameter], transform=ccrs.PlateCarree(), cmap=colormap, norm=norm, levels=bounds, extend='both', extendfrac=0.1)
            else:
                cf = ax.contourf(plot_ds.longitude, plot_ds.latitude, plot_ds[parameter], transform=ccrs.PlateCarree(), cmap=colormap, norm=norm, levels=bounds, extend='max', extendfrac=0.1)
        else:
            cf = ax.pcolormesh(plot_ds.longitude, plot_ds.latitude, plot_ds[parameter], transform=ccrs.PlateCarree(), cmap=colormap, norm=norm)

        # scatter the points on the map if specified by the user
        if plot_points == True:
            for n in range(len(points)):
                lat = float(points[n][1])
                lon = float(points[n][2])
                if lat < domain[2] or lat > domain[0] or lon < domain[1] or lon > domain[3]:
                    continue
                ax.plot(lon, lat, marker='o', color='black', markersize=2, transform=ccrs.PlateCarree())

        cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.02, shrink = 0.8, aspect=40)#, label=plot_label)

        if plot_type != 'ptype' and plot_type != 'total_tp':
            cbar.set_ticks([float(i) for i in tick_labels])
            cbar.set_ticklabels(tick_labels)
        else:
            cbar.set_ticks(tick_locations)
            cbar.set_ticklabels(tick_labels)
        max_value = round(float(plot_ds[parameter].max().values),1)
        min_value = round(float(plot_ds[parameter].min().values),1)
        init_label = init_datetime.strftime('%m/%d %Hz')
        valid_label = (init_datetime + timedelta(hours=frame)).strftime('%m/%d %Hz')
        day_of_week = (init_datetime + timedelta(hours=frame)).strftime('%A')[0:3]
        valid_label = day_of_week + ' ' + valid_label

        if first_frame != 0 and plot_type in ['total_tp','total_snow']:
            forecast_hour_label = 'Hour '+str(first_frame)+'-'+str(frame)
        else:
            forecast_hour_label = 'Hour '+str(frame)

        if plot_type == 't2m':
            plt.title(plot_label + " ??? Init: " + init_label, fontsize=10, loc='left')
            plt.title(forecast_hour_label + ' ??? Valid: ' + valid_label, fontsize=10, loc='right')
            fig.text(0.9, 0.14, 'Max: '+str(max_value)+units+', Min: '+str(min_value)+units, fontsize=8, ha='right', va='bottom')
        elif plot_type == 'ptype':
            plt.title(plot_label + " ??? Init: " + init_label, fontsize=10, loc='left')
            plt.title(forecast_hour_label + ' ??? Valid: ' + valid_label, fontsize=10, loc='right')
        else:
            plt.title(plot_label + " ??? Init: " + init_label, fontsize=10, loc='left')
            plt.title(forecast_hour_label + ' ??? Valid: ' + valid_label, fontsize=10, loc='right')
            fig.text(0.9, 0.14, 'Max: ' + str(max_value) + units, fontsize=8, ha='right', va='bottom')

        ax.coastlines()
        ax.add_feature(cfeature.BORDERS)
        if plot_states == True:
            ax.add_feature(cfeature.STATES, edgecolor='black', linewidth=0.5)
        if plot_counties == True:
            ax.add_feature(USCOUNTIES.with_scale('500k'),linewidth=0.2)

        plt.savefig(directory+'outputs/figures/'+plot_type+'/'+plot_type+'_'+str(frame)+'.png', dpi=300, bbox_inches='tight')
        ax.cla()
        plt.clf()

    times.append(time.time()-start)

    # if the frame is not the max frame and not a multiple of step*8, skip it
    if frame != max_frame and frame%(step*8) != 0:
        continue

    print('Plotting point forecasts...')
    # plot each point's data
    for n in range(len(points)):

        name = points[n][0]
        point_domain = points[n][3]
        lat,lon = float(points[n][1]),float(points[n][2])

        # if the point is outside of the simulated domain, skip it
        if lat < domain[2] or lat > domain[0] or lon < domain[1] or lon > domain[3]:
            continue

        # get the timezone of the point
        timezone_str = obj.timezone_at(lng=lon, lat=lat)
        to_zone = dateutil.tz.gettz(timezone_str)

        # get the point's data from the dataframe list
        df = point_dataframes[n]

        for i in range(df.shape[0] - 1):
            row1 = df.iloc[i]
            row2 = df.iloc[i+1]

            if step != 1:

                # interpolate the data to 1 hour intervals
                interpolated_rows = []
                for x in range(1,step):
                    interpolated_row = (row1 * (step-x)/step) + (row2 * x/step)
                    interpolated_rows.append(interpolated_row)

                for interpolated_row in interpolated_rows:
                    df = df.append(interpolated_row, ignore_index=True)

        # sort the dataframe by forecast hour and calculate the valid time
        df = df.sort_values(by=['forecast_hour'])
        df['valid_time'] = df['forecast_hour'].apply(lambda x: init_datetime + timedelta(hours=x))
        df['valid_time'] = df['valid_time'].apply(lambda x: x.replace(tzinfo=from_zone).astimezone(to_zone))

        df.loc[df['t2m_avg'] <= mix_temp, 'ptype'] = 2
        df.loc[df['t2m_avg'] <= snow_temp, 'ptype'] = 3
        df.loc[df['t2m_avg'] > mix_temp, 'ptype'] = 1
        
        ptypes = []

        initial_ptype_time = df.iloc[0]['valid_time']
        initial_ptype = df.iloc[0]['ptype']
        ptypes.append([initial_ptype_time,initial_ptype])

        for i in range(3,df.shape[0],3):
            if df.iloc[i]['ptype'] != ptypes[-1][1] or i == 3:
                ptypes.append([df.iloc[i-3]['valid_time'],df.iloc[i]['ptype']])
        final_ptype_time = df.iloc[-1]['valid_time']
        final_ptype = ptypes[-1][1]
        if final_ptype_time != ptypes[-1][0]:
            ptypes.append([final_ptype_time,final_ptype])

        # adjust each valid time to the correct timezone, find the snow and precip values at 8am and 4pm
        tick_times = []
        tick_labels = []
        total_snow_values = []
        total_tp_values = []
        for i in range(df.shape[0]):
            valid_time = df.iloc[i]['valid_time']
            hour = valid_time.hour
            if hour == 8 or hour == 16:
                valid_time = df.iloc[i]['valid_time']
                day_of_week = valid_time.strftime('%A')[0:3]
                if hour == 8:
                    valid_time = day_of_week + ' ' + valid_time.strftime('%m/%d %H')
                else:
                    valid_time = valid_time.strftime('%m/%d %H')

                tick_times.append(df.iloc[i]['valid_time'])
                tick_labels.append(valid_time)
                total_snow_values.append(round(df.iloc[i]['total_snow'],1))
                total_tp_values.append(round(df.iloc[i]['total_tp'],2))

        df.to_csv(directory+'files/csvs/'+name+'.csv')
        
        # find the night/day snowfall and precip totals by subtracting the 8am/4pm values from the previous 8am/4pm values
        halfway_tick_times = []
        for x in range(1,len(tick_times)):
            halfway_tick_times.append(tick_times[x-1]+(tick_times[x]-tick_times[x-1])/2)

        halfway_acc_snow_values = []
        for x in range(1,len(total_snow_values)):
            halfway_acc_snow_values.append(total_snow_values[x]-total_snow_values[x-1])

        halfway_precip_values = []
        for x in range(1,len(total_tp_values)):
            halfway_precip_values.append(total_tp_values[x]-total_tp_values[x-1])

        # plot the data on subplots
        fig,ax = plt.subplots(figsize=(20,15))
        plt.subplots_adjust(hspace=0.25,left=0.03, right=0.97, top=0.9, bottom=0.08)

        df_times = list(df['valid_time'])

        plt.subplot(3,2,1)
        plt.plot(df_times,df['snow'],color='blue',linewidth=2)
        plt.title('Snow',fontsize=15)
        if max(df['snow']) < 5:
            max_tick = float(round(max(df['snow']),1)+0.5)
        else:
            max_tick = float(round(max(df['snow']),1)+1)
        plt.ylim(0, max_tick)
        plt.xlim(df_times[0],df_times[-1])
        plt.grid()

        plt.subplot(3,2,2)
        plt.plot(df_times,df['total_snow'],color='blue',linewidth=2)
        plt.title('Total Snow',fontsize=15)
        if max(df['total_snow']) < 50:
            max_tick = float(round(max(df['total_snow']),1)+5)
        else:
            max_tick = float(round(max(df['total_snow']),1)+10)
        plt.ylim(0, max_tick)
        plt.xlim(df_times[0],df_times[-1])
        plt.grid()
        for halfway_acc_snow_value, halfway_tick_time in zip(halfway_acc_snow_values, halfway_tick_times):
            plt.text(halfway_tick_time,max_tick-1,str(round(halfway_acc_snow_value,1)),ha='center',va='top',fontsize=11,color='blue',fontweight='bold')

        plt.subplot(3,2,3)
        plt.plot(df_times,df['tp'],color='green',linewidth=2)
        plt.title('Precip',fontsize=15)
        if max(df['tp']) < 0.5:
            max_tick = float(round(max(df['tp']),1)+0.05)
        else:
            max_tick = float(round(max(df['tp']),1)+0.1)
        plt.ylim(0, max_tick)
        plt.xlim(df_times[0],df_times[-1])
        plt.grid()
        ptype_colors = {0: 'white', 1: 'green', 2: 'orange', 3: 'blue'}
        for p in range(1,len(ptypes)):
            plt.axvspan(ptypes[p-1][0], ptypes[p][0], facecolor=ptype_colors[ptypes[p-1][1]], alpha=0.1)
            ptype_label = datetime.strftime(ptypes[p][0], '%m/%d %H')

        plt.subplot(3,2,4)
        plt.plot(df_times,df['total_tp'],color='green',linewidth=2)
        plt.title('Total Precip',fontsize=15)
        if max(df['total_tp']) < 5:
            max_tick = float(round(max(df['total_tp']),1)+0.5)
        else:
            max_tick = float(round(max(df['total_tp']),1)+1)
        plt.ylim(0, max_tick)
        plt.xlim(df_times[0],df_times[-1])
        plt.grid()
        for p in range(1,len(ptypes)):
            plt.axvspan(ptypes[p-1][0], ptypes[p][0], facecolor=ptype_colors[ptypes[p-1][1]], alpha=0.1)
            ptype_label = datetime.strftime(ptypes[p][0], '%m/%d %H')

        ax1 = plt.subplot(3,2,5)
        plt.plot(df_times,df['t2m'],color='red',linewidth=2)
        if compute_wind == True:
            plt.title('Temperature (Red) / SLR (Black)',fontsize=15)
        else:
            plt.title('Temperature',fontsize=15)
        plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
        plt.xlim(df_times[0],df_times[-1])
        plt.grid()
        if compute_wind == True:
            ax2 = ax1.twinx()
            plt.plot(df_times,df['slr'],color='black',linewidth=2)
            plt.xlim(df_times[0],df_times[-1])
            plt.grid()

        if compute_wind == True:
            plt.subplot(3,2,6)
            plt.plot(df_times,df['wind'],color='black',linewidth=2)
            plt.title('Wind',fontsize=15)
            plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
            plt.xlim(df_times[0],df_times[-1])
            plt.grid()
        else:
            plt.subplot(3,2,6)
            plt.plot(df_times,df['slr'],color='black',linewidth=2)
            plt.title('SLR',fontsize=15)
            plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
            plt.xlim(df_times[0],df_times[-1])
            plt.grid()

        # plt.subplot(3,2,6)
        # plt.plot(df_times,df['freezing_level'],color='black',linewidth=2)
        # plt.title('Freezing Level')
        # plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
        # plt.xlim(df_times[0],df_times[-1])
        # plt.grid()

        plt.setp(plt.gcf().get_axes()[:-2], xticks=tick_times, xticklabels=[])
        plt.setp(plt.gcf().get_axes()[-2:], xticks=tick_times, xticklabels=tick_labels)
        plt.gcf().get_axes()[-2].tick_params(axis='x', which='major', labelsize=11, rotation=45)
        plt.gcf().get_axes()[-1].tick_params(axis='x', which='major', labelsize=11, rotation=45)

        plt.setp(plt.gcf().get_axes()[1], xticks=tick_times, xticklabels=total_snow_values)
        plt.setp(plt.gcf().get_axes()[3], xticks=tick_times, xticklabels=total_tp_values)
        plt.gcf().get_axes()[1].tick_params(axis='x', which='major', labelsize=11, rotation=45)
        plt.gcf().get_axes()[3].tick_params(axis='x', which='major', labelsize=11, rotation=45)

        init_label = init_datetime.strftime('%m/%d %Hz')

        plt.suptitle("Point Forecast: "+name+" (Grid Elevation: "+str(round(df['elevation'][0]))+"') - Init: "+init_label, fontsize=20)
        plt.savefig(directory+'outputs/points/'+point_domain+'-'+name+'.png')


# for domain in ['Utah','Colorado','California','PNW']:
for domain in [domain_name]:
    day_night_scatters(points,day_and_night_scatter_separate,domain,plot_states,plot_counties)

os.system(clear_prompt)
print('Done with model run: '+datestr+cycle+'z')
