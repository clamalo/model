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
from datetime import datetime, timedelta
from tzwhere import tzwhere
from dateutil import tz as dateutil
tz = tzwhere.tzwhere()
from_zone = dateutil.gettz('UTC')
import time
import imageio
from metpy.plots import USCOUNTIES
from adjustText import adjust_text
from metpy.calc import wet_bulb_temperature
from metpy.units import units
import metpy
import math

def get_datestr_and_cycle():
    current_utc_time = datetime.utcnow()
    if 4 <= current_utc_time.hour < 16:
        cycle = "00"
        datestr = current_utc_time.strftime("%Y%m%d")
    elif 16 <= current_utc_time.hour < 24:
        cycle = "12"
        datestr = current_utc_time.strftime("%Y%m%d")
    else:
        cycle = "12"
        previous_day = current_utc_time - timedelta(days=1)
        datestr = previous_day.strftime("%Y%m%d")
    return datestr, cycle

def name_frame(f):
    if f < 10:
        return '00' + str(f)
    elif f < 100:
        return '0' + str(f)
    else:
        return str(f)
    
def name_member(m):
    if m < 10:
        return '0' + str(m)
    else:
        return str(m)

def total_snow_colormap():
    cmap = colors.ListedColormap(['#FFFFFF','#7fb2ff','#4c72d8','#1933b2','#7fff7f','#46b246','#0c660c','#ffff66','#e1b244','#c36622','#a51900','#ff99ff','#cc68cc','#993899','#660766','#cccccc','#999999','#666666'])
    return cmap

def weatherbell_precip_colormap():
    cmap = colors.ListedColormap(['#ffffff', '#bdbfbd','#aba5a5', '#838383', '#6e6e6e', '#b5fbab', '#95f58b','#78f572', '#50f150','#1eb51e', '#0ea10e', '#1464d3', '#2883f1', '#50a5f5','#97d3fb', '#b5f1fb','#fffbab', '#ffe978', '#ffc13c', '#ffa100', '#ff6000','#ff3200', '#e11400','#c10000', '#a50000', '#870000', '#643c31', '#8d6558','#b58d83', '#c7a095','#f1ddd3', '#cecbdc'])#, '#aca0c7', '#9b89bd', '#725ca3','#695294', '#770077','#8d008d', '#b200b2', '#c400c4', '#db00db'])
    return cmap

def hourly_snow_colormap():
    cmap = colors.ListedColormap(['#FFFFFF', '#cccccc', '#7fb2ff', '#1933b2', '#7fff7f', '#0c660c', '#ffff66', '#a51900', '#ff99ff', '#660766', '#666666'])
    return cmap

def hourly_precip_colormap():
    cmap = colors.ListedColormap(['#ffffff', '#bdbfbd','#aba5a5', '#838383', '#6e6e6e', '#b5fbab', '#95f58b','#78f572', '#50f150','#1eb51e', '#0ea10e', '#1464d3'])
    return cmap

def temp_colormap():
    cmap = colors.ListedColormap(['#ffffff','#7f1786','#8634e5','#8469c7','#ea33f7','#3c8925','#5dca3b','#a0fc4e','#75fb4c','#0000f5','#458ef7','#4fafe8','#6deaec','#75fbfd','#ffff54','#eeee4e','#f9d949','#f2a95f','#ef8955','#ef8632','#fbe5dd','#f3b1ba','#ed736f','#db4138','#dc4f25','#ea3323','#bc271a','#c3882e','#824b2d','#7f170e'])
    return cmap

def slr_colormap():
    cmap = colors.ListedColormap(['#ffffff','#afeeee','#81a7e8','#5b6ce1','#4141de','#4b0082','#611192','#7722a2','#8e33b3','#a444c3','#ba55d3','#da70d6','#d452bb','#cd33a0','#c71585','#d24081','#de6b7e','#e9967a','#f0b498','#f8d1b7'])
    return cmap

def wind_colormap():
    cmap = colors.ListedColormap(['#ffffff','#5fdee4','#108b9f','#ccf06f','#ff3713','#5a0304','#e38dff','#ffa6c1','#ff6164'])
    return cmap

def download_flux_file(frame,ingest_type):

    if ingest_type == 'nomads':
        url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_sflux.pl?file=gfs.t{cycle}z.sfluxgrbf{name_frame(frame)}.grib2&lev_surface=on&var_PRATE=on&subregion=&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
    elif ingest_type == 'aws':
        url = f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{datestr}/{cycle}/atmos/gfs.t{cycle}z.sfluxgrbf{name_frame(frame)}.grib2'

    if 'nomads' in url:
        file_name = directory+'gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '_sp.grib2'
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
        file_name = directory+'gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '_sp.grib2'
        with open(file_name, 'wb') as f:
            f.write(data)

def download_25_file(frame,ingest_type):

    if ingest_type == 'nomads':
        url = f'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t{cycle}z.pgrb2.0p25.f{name_frame(frame)}&lev_0C_isotherm=on&lev_1000_mb=on&lev_500_mb=on&lev_700_mb=on&lev_850_mb=on&lev_925_mb=on&var_HGT=on&var_TMP=on&var_UGRD=on&var_VGRD=on&subregion=&leftlon=230&rightlon=300&toplat=60&bottomlat=25&dir=%2Fgfs.{datestr}%2F{cycle}%2Fatmos'
    elif ingest_type == 'aws':
        url = f'https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{datestr}/{cycle}/atmos/gfs.t{cycle}z.pgrb2.0p25.f{name_frame(frame)}'

    if 'nomads' in url:
        file_name = directory+'gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2'
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
        target_variables = ['TMP:500 mb:', 'TMP:700 mb:', 'TMP:850 mb:', 'TMP:925 mb:', 'TMP:1000 mb:', 'HGT:500 mb:', 'HGT:700 mb:', 'HGT:850 mb:', 'HGT:925 mb:', 'HGT:1000 mb:', 'UGRD:500 mb:', 'UGRD:700 mb:', 'UGRD:850 mb:', 'UGRD:925 mb:', 'UGRD:1000 mb:', 'VGRD:500 mb:', 'VGRD:700 mb:', 'VGRD:850 mb:', 'VGRD:925 mb:', 'VGRD:1000 mb:']
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
        file_name = directory+'gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2'
        with open(file_name, 'wb') as f:
            f.write(data)

def download_canadian_file(frame,wind):
    if not os.path.exists(directory+'gribs/' + name_frame(frame)):
        os.makedirs(directory+'gribs/' + name_frame(frame))

    canadian_urls = []

    if frame > 0:
        canadian_urls.append(f'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{cycle}/{name_frame(frame)}/CMC_glb_APCP_SFC_0_latlon.15x.15_{datestr+cycle}_P{name_frame(frame)}.grib2')

    levels = ['1000','500','700','850','925']
    variables = ['HGT','TMP']
    if wind == True:
        variables = variables+['UGRD','VGRD']
    for level in levels:
        for variable in variables:
            canadian_urls.append(f'https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{cycle}/{name_frame(frame)}/CMC_glb_{variable}_ISBL_{level}_latlon.15x.15_{datestr+cycle}_P{name_frame(frame)}.grib2')

    if os.path.exists(directory+'gribs' + '/' + name_frame(frame) + '/gdps_init.grib2'):
        os.remove(directory+'gribs' + '/' + name_frame(frame) + '/gdps_init.grib2')

    for url in canadian_urls:
        if 'APCP' in url:
            r = requests.get(url, allow_redirects=True)
            open(directory+'gribs/' + name_frame(frame) + '/gdps_init.grib2', 'wb').write(r.content)
        else:
            r = requests.get(url, allow_redirects=True)
            open(directory+'gribs/' + name_frame(frame) + '/gdps_init.grib2', 'ab').write(r.content)




def ingest_frame(frame,datestr,cycle,ingest_type,canadian,wind):

    if frame%30 == 0:
        if frame+(step*10) > max_frame:
            max_ingest_frame = max_frame
        else:
            max_ingest_frame = frame+(step*10)+1
        frames = range(frame,max_ingest_frame,step)

        for frame in frames:
            if not os.path.exists(directory+'gribs/' + name_frame(frame)):
                os.makedirs(directory+'gribs/' + name_frame(frame))

        threads = [threading.Thread(target=download_25_file, args=(frame,ingest_type)) for frame in frames]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if frames[0] == 0:
            frames = frames[1:]
        threads = [threading.Thread(target=download_flux_file, args=(frame,ingest_type)) for frame in frames]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    if canadian == True and frame%30 == 0:
        if frame+(step*10) > max_frame:
            max_ingest_frame = max_frame
        else:
            max_ingest_frame = frame+(step*10)+1
        frames = range(frame,max_ingest_frame,step)
        threads = [threading.Thread(target=download_canadian_file, args=(frame,wind)) for frame in frames]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()



def find_temperature(gh1,gh2,parameter_pair,elevation):
    parameter = parameter_pair[0]
    gh = parameter_pair[1]
    temperature = gh1[parameter] + (gh2[parameter] - gh1[parameter]) * ((elevation - gh1[gh]) / (gh2[gh] - gh1[gh]))
    return temperature

def find_elevation(gh1, gh2, parameter_pair, temperature):
    parameter = parameter_pair[0]
    gh = parameter_pair[1]
    elevation = gh1[gh] + (gh2[gh] - gh1[gh]) * ((temperature - gh1[parameter]) / (gh2[parameter] - gh1[parameter]))
    return elevation
    

with open('model_config.txt', 'r') as myfile:
    text=myfile.read()
    text = text.split('\n')
    for arg in range(len(text)):
        config = text[arg].split('=')[1]
        config = config.replace(' ','')
        text[arg] = config
    directory = text[0]
    if text[1] == 'True':
        ingest = True
    else:
        ingest = False
    if text[2] == 'True':
        canadian = True
    else:
        canadian = False
    model_ratio = float(text[3])
    if text[4] == 'True':
        wind = True
    else:
        wind = False
    step = int(text[5])
    first_frame = int(text[6])
    max_frame = int(text[7])
    ingest_type = text[8]
    if text[9] == 'True':
        detect_recent_run = True
    else:
        detect_recent_run = False
    datestr = text[10]
    cycle = text[11]
    plot_types = text[12].split(',')
    if text[13] == 'True':
        plot_counties = True
    else:
        plot_counties = False
    if text[14] == 'True':
        plot_points = True
    else:
        plot_points = False
    domain = text[15].split(',')
    for i in range(len(domain)):
        domain[i] = float(domain[i])

    if step == 0:
        print('\n\nERROR: Step cannot be less than 1\n')
        quit()
    if step > 6:
        print('\n\nERROR: Step cannot be greater than 6\n')
        quit()

    if canadian == True and (step != 3 and step != 6):
        print('\n\nERROR: Canadian initialization can only be run with 3 or 6 hour steps\n')
        quit()

    if model_ratio < 0 or model_ratio > 1:
        print('\n\nERROR: Model ratio must be between 0 and 1\n')
        quit()

    if step < 3 and max_frame > 120:
        print('\n\nERROR: Step cannot be less than 3 with a max frame greater than 120\n')
        quit()

    if canadian == True and max_frame > 240:
        print('\n\nERROR: Canadian initialization can only be run with a max frame less than 240\n')
        quit()

    if ingest == True and ingest_type != 'nomads' and ingest_type != 'aws':
        print('\n\nERROR: Ingest type must be nomads or aws\n')
        quit()

    if canadian == True and cycle!='00' and cycle!='12':
        print('\n\nERROR: Canadian initialization can only be run at 00 or 12 UTC cycles\n')
        quit()

    if os.path.exists(directory) == False:
        print('\n\nERROR: Directory does not exist\n')
        quit()

    if wind == False and 'wind' in plot_types:
        print('\n\nERROR: wind must be set to True to plot wind\n')
        quit()

    for plot_type in plot_types:
        if plot_type not in ['tp','total_snow','total_tp','snow','t2m','slr','wind']:
            print('\n\nERROR: Plot type must be tp, total_snow, total_tp, snow, t2m, slr, or wind\n')
            quit()

    if domain[0] > 60:
        print('\n\nERROR: Domain maximum latitude must be less than 60\n')
        quit()
    if domain[1] < 235:
        print('\n\nERROR: Domain west latitude must be greater than 235\n')
        quit()
    if domain[2] < 25:
        print('\n\nERROR: Domain minimum longitude must be greater than 25\n')
        quit()
    if domain[3] > 310:
        print('\n\nERROR: Domain maximum longitude must be less than 300\n')
        quit()
    if domain [0] < domain[2]:
        print('\n\nERROR: Domain maximum latitude must be greater than domain minimum latitude\n')
        quit()
    if domain[1] > domain[3]:
        print('\n\nERROR: Domain west longitude must be less than domain east longitude\n')
        quit()

if detect_recent_run == True:
    datestr,cycle = get_datestr_and_cycle()

init_datetime = datetime.strptime(datestr+cycle,'%Y%m%d%H')

r = requests.get('https://www.dropbox.com/s/q5n29vow7dz93y0/elevation.nl?dl=1', allow_redirects=True)
open(directory+'elevation.nc', 'wb').write(r.content)
elevation_ds = xr.open_dataset(directory+'elevation.nc', engine='netcdf4')
elevation_ds = elevation_ds.sel(longitude=slice(domain[1],domain[3]),latitude=slice(domain[2],domain[0]))
elevation_ds = elevation_ds.fillna(0)
elevation_ds = elevation_ds.coarsen(latitude=2,longitude=2, boundary='trim').mean()


#create directories
sub_directory = directory+'figures/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
sub_directory = directory+'gribs/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)
sub_directory = directory+'points/'
if not os.path.exists(sub_directory):
    os.makedirs(sub_directory)


for frame in range(first_frame,max_frame+1,step):

    if frame == first_frame:
        point_dataframes = []
        with open(directory+'points.txt', 'r') as myfile:
            text=myfile.read()
        text = text.replace(' ','')
        points = text.split('\n')
        # points.pop()
        for n in range(len(points)):
            points[n] = points[n].split(',')
            df = pd.DataFrame(columns=['tp','snow','t2m','slr','wind','total_tp','total_snow','valid_time'])
            point_dataframes.append(df)


    #create necessary directories
    sub_directory = directory+'gribs/'+name_frame(frame)
    if not os.path.exists(sub_directory):
        os.makedirs(sub_directory)
        os.makedirs(sub_directory+'/sp')
        os.makedirs(sub_directory+'/reg/')

    if ingest == True:
        ingest_frame(frame,datestr,cycle,ingest_type,canadian,wind)


    reg_ds = xr.load_dataset(directory+'gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2', engine='cfgrib',filter_by_keys={'typeOfLevel': 'isobaricInhPa'})
    isotherm_ds = xr.load_dataset(directory+'gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '.grib2', engine='cfgrib',filter_by_keys={'typeOfLevel': 'isothermZero'})
    reg_ds['freezing_level'] = isotherm_ds['gh']*3.28084
    if ingest_type == 'aws':
        reg_ds = reg_ds.sel(latitude=slice(domain[0],domain[2]),longitude=slice(domain[1],domain[3]))
    elif ingest_type == 'nomads':
        reg_ds = reg_ds.sel(latitude=slice(domain[2],domain[0]),longitude=slice(domain[1],domain[3]))
    if wind == True:
        reg_ds['wind'] = (np.sqrt(reg_ds['u']**2+reg_ds['v']**2))*2.23694
        reg_ds = reg_ds.drop(['u','v'])
    if frame > first_frame:
        reg_ds['t_avg'] = (reg_ds['t'] + prior_reg_ds['t'])/2
        reg_ds['gh_avg'] = (reg_ds['gh'] + prior_reg_ds['gh'])/2
    prior_reg_ds = reg_ds.copy()

    if frame > first_frame:
        sp_ds = xr.load_dataset(directory+'gribs/' + name_frame(frame) + '/gfs_init' + name_frame(frame) + '_sp.grib2', engine='cfgrib')
        if ingest_type == 'aws':
            sp_ds = sp_ds.sel(latitude=slice(domain[0],domain[2]),longitude=slice(domain[1],domain[3]))
        elif ingest_type == 'nomads':
            sp_ds = sp_ds.sel(latitude=slice(domain[2],domain[0]),longitude=slice(domain[1],domain[3]))

        if (frame-step)%6 != 0:
            if frame%6 == 0:
                remainder = 6
            else:
                remainder = frame%6
            sp_ds['tp'] = ((sp_ds['prate']*remainder)-(prior_sp_ds['prate']*(remainder-step)))*3600
    
        else:
            sp_ds['tp'] = sp_ds['prate']*3600*step

        prior_sp_ds = sp_ds.copy()

    if canadian == True:
        canadian_ds = xr.load_dataset(directory+'gribs/' + name_frame(frame) + '/gdps_init.grib2', engine='cfgrib')
        canadian_ds['longitude'] = (canadian_ds['longitude'] - 180) % 360 + 180
        canadian_ds = canadian_ds.sel(latitude=slice(domain[2],domain[0]),longitude=slice(domain[1],domain[3]))
        if wind == True:
            canadian_ds['wind'] = (np.sqrt(canadian_ds['u']**2+canadian_ds['v']**2))*2.23694
            canadian_ds = canadian_ds.drop(['u','v'])
        if frame > first_frame:
            canadian_ds['t_avg'] = (canadian_ds['t'] + prior_canadian_ds['t'])/2
            canadian_ds['gh_avg'] = (canadian_ds['gh'] + prior_canadian_ds['gh'])/2
            if frame == first_frame+step:
                canadian_ds['tp'] = canadian_ds['unknown']
            else:
                canadian_ds['tp'] = (canadian_ds['unknown'] - prior_canadian_ds['unknown'])
        prior_canadian_ds = canadian_ds.copy()

    if frame == first_frame:
        continue

    # reg_ds['r'] = reg_ds['r'].where(reg_ds['r'] != 0, 0.1)
    # reg_ds['td'] = metpy.calc.dewpoint_from_relative_humidity(reg_ds['t'], reg_ds['r']/100)
    # reg_ds['tw'] = metpy.calc.wet_bulb_temperature(500*metpy.units.units.hPa, reg_ds['t']*metpy.units.units.degK, reg_ds['td'])

    if canadian == True:
        canadian_ds = canadian_ds.interp(latitude=sp_ds.latitude, longitude=sp_ds.longitude)

    reg_ds = reg_ds.interp(latitude=sp_ds.latitude, longitude=sp_ds.longitude)
    reg_ds['tp'] = sp_ds['tp'].copy()

    if canadian == True:
        reg_ds['t'] = (reg_ds['t']*model_ratio) + (canadian_ds['t']*(1-model_ratio))
        reg_ds['gh'] = (reg_ds['gh']*model_ratio) + (canadian_ds['gh']*(1-model_ratio))
        reg_ds['t_avg'] = (reg_ds['t_avg']*model_ratio) + (canadian_ds['t_avg']*(1-model_ratio))
        reg_ds['gh_avg'] = (reg_ds['gh_avg']*model_ratio) + (canadian_ds['gh_avg']*(1-model_ratio))
        reg_ds['tp'] = (reg_ds['tp']*model_ratio) + (canadian_ds['tp']*(1-model_ratio))
        if wind == True:
            reg_ds['wind'] = (reg_ds['wind']*model_ratio) + (canadian_ds['wind']*(1-model_ratio))

    #interp to elevation_ds
    reg_ds = reg_ds.interp(latitude=elevation_ds.latitude, longitude=elevation_ds.longitude)
    reg_ds['elevation'] = elevation_ds['elevation']

    gh1 = reg_ds.isel(isobaricInhPa=0)
    gh2 = reg_ds.isel(isobaricInhPa=1)
    gh3 = reg_ds.isel(isobaricInhPa=2)
    gh4 = reg_ds.isel(isobaricInhPa=3)
    gh5 = reg_ds.isel(isobaricInhPa=4)
    elevation = reg_ds['elevation']

    # freezing_temp = 273.15
    # reg_ds['freezing_level'] = xr.where(freezing_temp > gh1['t'], gh1['gh'], xr.where(freezing_temp > gh2['t'], find_elevation(gh1,gh2,['t','gh'],freezing_temp), xr.where(freezing_temp > gh3['t'], find_elevation(gh2,gh3,['t','gh'],freezing_temp), xr.where(freezing_temp > gh4['t'], find_elevation(gh3,gh4,['t','gh'],freezing_temp),find_elevation(gh4,gh5,['t','gh'],freezing_temp)))))
    # reg_ds['freezing_level'] = reg_ds['freezing_level']*3.28084

    # reg_ds['snow_level'] = xr.where(freezing_temp > gh1['tw'], gh1['gh'], xr.where(freezing_temp > gh2['tw'], find_elevation(gh1,gh2,['tw','gh'],freezing_temp), xr.where(freezing_temp > gh3['tw'], find_elevation(gh2,gh3,['tw','gh'],freezing_temp), xr.where(freezing_temp > gh4['tw'], find_elevation(gh3,gh4,['tw','gh'],freezing_temp),find_elevation(gh4,gh5,['tw','gh'],freezing_temp)))))
    # reg_ds['snow_level'] = reg_ds['snow_level']*3.28084

    reg_ds['t2m'] = xr.where(elevation < gh2['gh'], find_temperature(gh1,gh2,['t','gh'],elevation), xr.where(elevation < gh3['gh'], find_temperature(gh2,gh3,['t','gh'],elevation), xr.where(elevation < gh4['gh'], find_temperature(gh3,gh4,['t','gh'],elevation),find_temperature(gh4,gh5,['t','gh'],elevation))))
    reg_ds['t2m_avg'] = xr.where(elevation < gh2['gh'], find_temperature(gh1,gh2,['t_avg','gh_avg'],elevation), xr.where(elevation < gh3['gh'], find_temperature(gh2,gh3,['t_avg','gh_avg'],elevation), xr.where(elevation < gh4['gh'], find_temperature(gh3,gh4,['t_avg','gh_avg'],elevation),find_temperature(gh4,gh5,['t_avg','gh_avg'],elevation))))
    if wind == True:
        reg_ds['wind'] = xr.where(elevation < gh2['gh'], find_temperature(gh1,gh2,['wind','gh'],elevation), xr.where(elevation < gh3['gh'], find_temperature(gh2,gh3,['wind','gh'],elevation), xr.where(elevation < gh4['gh'], find_temperature(gh3,gh4,['wind','gh'],elevation),find_temperature(gh4,gh5,['wind','gh'],elevation))))

    reg_ds['t2m_avg'] = reg_ds['t2m_avg'] * 9/5 - 459.67
    reg_ds['t2m'] = reg_ds['t2m'] * 9/5 - 459.67
    reg_ds['slr'] = xr.where(reg_ds['t2m_avg'] > 40, 0, xr.where(reg_ds['t2m_avg'] >= 35, 3, xr.where(reg_ds['t2m_avg'] >= 30, 1+(39-reg_ds['t2m_avg']), xr.where(reg_ds['t2m_avg'] >= 10, 10+((30-reg_ds['t2m_avg'])*0.5), xr.where(reg_ds['t2m_avg'] >= 1, 20-((10-reg_ds['t2m_avg'])*0.5), xr.where(reg_ds['t2m_avg'] >= -4, 15-(0-reg_ds['t2m_avg']), 10))))))

    reg_ds['tp']*=.0393701
    reg_ds['tp'] = reg_ds['tp'].where(reg_ds['tp'] > 0, 0)
    reg_ds['slr'] = reg_ds['slr'].where(reg_ds['slr'] > 3, 0)
    reg_ds['snow'] = reg_ds['tp']*reg_ds['slr']

    if frame == first_frame+step:
        total_ds = reg_ds.copy()
        total_ds = total_ds[['snow','tp']]
    else:
        total_ds['snow'] += reg_ds['snow']
        total_ds['tp'] += reg_ds['tp']


    for n in range(len(points)):
        lat,lon = float(points[n][1]),float(points[n][2])+360

        elevation = float(reg_ds['elevation'].sel(latitude=lat,longitude=lon,method='nearest').values)*3.28084

        valid_time = init_datetime + timedelta(hours=frame)

        tp_value = float(reg_ds['tp'].sel(latitude=lat,longitude=lon,method='nearest').values)
        snow_value = float(reg_ds['snow'].sel(latitude=lat,longitude=lon,method='nearest').values)
        total_tp_value = float(total_ds['tp'].sel(latitude=lat,longitude=lon,method='nearest').values)
        total_snow_value = float(total_ds['snow'].sel(latitude=lat,longitude=lon,method='nearest').values)
        t2m_value = float(reg_ds['t2m'].sel(latitude=lat,longitude=lon,method='nearest').values)
        slr_value = float(reg_ds['slr'].sel(latitude=lat,longitude=lon,method='nearest').values)
        if wind == True:
            wind_value = float(reg_ds['wind'].sel(latitude=lat,longitude=lon,method='nearest').values)
        freezing_level_value = float(reg_ds['freezing_level'].sel(latitude=lat,longitude=lon,method='nearest').values)
        if wind == True:
            new_row = {'tp':tp_value,'snow':snow_value,'t2m':t2m_value,'slr':slr_value,'wind':wind_value,'total_tp':total_tp_value,'total_snow':total_snow_value,'freezing_level':freezing_level_value,'forecast_hour':frame,'elevation':elevation}
        else:
            new_row = {'tp':tp_value,'snow':snow_value,'t2m':t2m_value,'slr':slr_value,'total_tp':total_tp_value,'total_snow':total_snow_value,'freezing_level':freezing_level_value,'forecast_hour':frame,'elevation':elevation}
        point_dataframes[n] = point_dataframes[n].append(new_row, ignore_index=True)

    #basic plots
    for plot_type in plot_types:

        if not os.path.exists('figures/'+plot_type):
            os.makedirs('figures/'+plot_type)

        fig = plt.figure(figsize=(10,7))
        ax = plt.axes(projection=ccrs.PlateCarree())

        if plot_type == 'total_snow':
            colormap = total_snow_colormap()
            bounds = [0,1,2,4,6,8,10,12,15,18,21,24,27,30,33,36,42,48]
            tick_labels = ['0','1','2','4','6','8','10','12','15','18','21','24','27','30','33','36','42','48']
            plot_label,units = 'Total Snowfall (in)','"'
        elif plot_type == 'total_tp':
            colormap = weatherbell_precip_colormap()
            bounds = [0,0.01,0.03,0.05,0.075,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,1.2,1.4,1.6,1.8,2,2.5,3,3.5,4,5,6,7,8,9,10]#,11,12,13,14,15,16,17,18,19,20])
            tick_labels = ['0.01', '0.05', '0.1', '0.2', '0.3', '0.5', '0.7', '0.9', '1.2', '1.6', '2', '3', '4', '6', '8', '10']
            plot_label,units = 'Total Precipitation (in)','"'
        elif plot_type == 'snow':
            colormap = hourly_snow_colormap()
            bounds = [0,0.1,0.5,0.75,1,1.5,2,2.5,3,3.5,4]
            tick_labels = ['0','0.1','0.5','0.75','1','1.5','2','2.5','3','3.5','4']
            plot_label,units = str(step)+' Hour Snowfall (in)','"'
        elif plot_type == 'tp':
            colormap = hourly_precip_colormap()
            bounds = [0,0.01,0.03,0.05,0.075,0.1,0.15,0.2,0.25,0.3,0.4,0.5]
            tick_labels = ['0','0.01','0.03','0.05','0.075','0.1','0.15','0.2','0.25','0.3','0.4','0.5']
            plot_label,units = str(step)+' Hour Precipitation (in)','"'
        elif plot_type == 't2m':
            colormap = temp_colormap()
            bounds = [-100,-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110]
            tick_labels = ['-30','-20','-10','0','10','20','30','40','50','60','70','80','90','100']
            plot_label,units = 'Temperature (F)','F'
        elif plot_type == 'slr':
            colormap = slr_colormap()
            bounds = [0,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
            tick_labels = ['0','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20']
            plot_label,units = 'SLR',''
        elif plot_type == 'wind':
            colormap = wind_colormap()
            bounds = [0,10,20,30,40,50,60,70,80]
            tick_labels = ['0','10','20','30','40','50','60','70','80']
            plot_label,units = 'Wind Speed (mph)','mph'

        norm = colors.BoundaryNorm(boundaries=bounds, ncolors=len(bounds))

        if 'total' in plot_type:
            plot_ds = total_ds
            parameter = plot_type.split('_')[1]
        else:
            plot_ds = reg_ds
            parameter = plot_type

        cf = ax.contourf(plot_ds.longitude, plot_ds.latitude, plot_ds[parameter], transform=ccrs.PlateCarree(), cmap=colormap, norm=norm, levels=bounds)

        if plot_points == True:
            for n in range(len(points)):
                lat = float(points[n][1])
                lon = float(points[n][2])+360
                if lat < domain[2] or lat > domain[0] or lon < domain[1] or lon > domain[3]:
                    continue
                ax.plot(lon, lat, marker='o', color='black', markersize=3, transform=ccrs.PlateCarree())

        cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.04, label=plot_label)
        cbar.set_ticks([float(i) for i in tick_labels])
        cbar.set_ticklabels(tick_labels)
        max_value = round(float(plot_ds[parameter].max().values),1)
        init_label = init_datetime.strftime('%m/%d %Hz')
        valid_label = (init_datetime + timedelta(hours=frame)).strftime('%m/%d %Hz')
        plt.title(plot_label+' || FH'+str(frame)+' || Init: '+init_label+' || Valid: '+valid_label+' || Max: '+str(max_value)+units,fontsize=12)

        ax.coastlines()
        ax.add_feature(cfeature.STATES, edgecolor='black', linewidth=0.5)
        if plot_counties == True:
            ax.add_feature(USCOUNTIES.with_scale('500k'),linewidth=0.1)

        plt.savefig(directory+'figures/'+plot_type+'/'+plot_type+'_'+str(frame)+'.png', dpi=300, bbox_inches='tight')
        ax.cla()
        plt.clf()


    if frame%24 != 0 or frame == max_frame:
        continue

    for n in range(len(points)):

        name = points[n][0]
        lat,lon = float(points[n][1]),float(points[n][2])+360

        if lat < domain[2] or lat > domain[0] or lon < domain[1] or lon > domain[3]:
            continue

        timezone_str = tz.tzNameAt(lat, lon-360)
        to_zone = dateutil.gettz(timezone_str)

        df = point_dataframes[n]

        # Iterate over the rows in your DataFrame
        for i in range(df.shape[0] - 1):
            # Get the values for the two rows in the outer pair
            row1 = df.iloc[i]
            row2 = df.iloc[i+1]

            if step != 1:

                interpolated_rows = []
                for x in range(1,step):
                    interpolated_row = (row1 * (step-x)/step) + (row2 * x/step)
                    interpolated_rows.append(interpolated_row)

                for interpolated_row in interpolated_rows:
                    df = df.append(interpolated_row, ignore_index=True)

                # # Interpolate the first row, using 66% data from row1 and 33% data from row2
                # interpolated_row1 = (row1 * (2/3)) + (row2 * (1/3))
                # # Interpolate the second row, using 33% data from row1 and 66% data from row2
                # interpolated_row2 = (row1 * (1/3)) + (row2 * (2/3))
                # # add the interpolated rows to the df
                # df = df.append(interpolated_row1, ignore_index=True)
                # df = df.append(interpolated_row2, ignore_index=True)

        df = df.sort_values(by=['forecast_hour'])
        df['valid_time'] = df['forecast_hour'].apply(lambda x: init_datetime + timedelta(hours=x))

        # df.to_csv('/Users/clamalo/documents/'+name+'.csv', index=False)


        tick_times = []
        tick_labels = []
        total_snow_values = []
        total_tp_values = []
        for i in range(df.shape[0]):
            valid_time = df.iloc[i]['valid_time']
            valid_time = valid_time.replace(tzinfo=from_zone).astimezone(to_zone)
            hour = valid_time.hour
            if hour == 8 or hour == 16:
                valid_time = df.iloc[i]['valid_time']
                valid_time = valid_time.replace(tzinfo=from_zone).astimezone(to_zone)
                valid_time = valid_time.strftime('%m/%d %H')

                tick_times.append(df.iloc[i]['valid_time'])
                tick_labels.append(valid_time)
                total_snow_values.append(round(df.iloc[i]['total_snow'],1))
                total_tp_values.append(round(df.iloc[i]['total_tp'],2))
        
        halfway_tick_times = []
        for x in range(1,len(tick_times)):
            halfway_tick_times.append(tick_times[x-1]+(tick_times[x]-tick_times[x-1])/2)

        halfway_acc_snow_values = []
        for x in range(1,len(total_snow_values)):
            halfway_acc_snow_values.append(total_snow_values[x]-total_snow_values[x-1])

        halfway_precip_values = []
        for x in range(1,len(total_tp_values)):
            halfway_precip_values.append(total_tp_values[x]-total_tp_values[x-1])

        fig,ax = plt.subplots(figsize=(20,15))
        plt.subplots_adjust(hspace=0.25,left=0.05, right=0.925, top=0.9, bottom=0.04)

        times = list(df['valid_time'])

        plt.subplot(3,2,1)
        plt.plot(times,df['snow'],color='blue',linewidth=2)
        plt.title('Snow',fontsize=15)
        plt.xlim(times[0],times[-1])
        plt.grid()

        plt.subplot(3,2,2)
        plt.plot(times,df['total_snow'],color='blue',linewidth=2)
        plt.title('Total Snow',fontsize=15)
        if max(df['total_snow']) < 50:
            max_tick = float(round(max(df['total_snow']),1)+5)
        else:
            max_tick = float(round(max(df['total_snow']),1)+10)
        plt.ylim(0, max_tick)
        plt.xlim(times[0],times[-1])
        plt.grid()
        for halfway_acc_snow_value, halfway_tick_time in zip(halfway_acc_snow_values, halfway_tick_times):
            plt.text(halfway_tick_time,max_tick-1,str(round(halfway_acc_snow_value,1)),ha='center',va='top',fontsize=11,color='blue',fontweight='bold')

        plt.subplot(3,2,3)
        plt.plot(times,df['tp'],color='green',linewidth=2)
        plt.title('Precip',fontsize=15)
        plt.xlim(times[0],times[-1])
        plt.grid()

        plt.subplot(3,2,4)
        plt.plot(times,df['total_tp'],color='green',linewidth=2)
        plt.title('Total Precip',fontsize=15)
        if max(df['total_tp']) < 5:
            max_tick = float(round(max(df['total_tp']),1)+0.5)
        else:
            max_tick = float(round(max(df['total_tp']),1)+1)
        plt.ylim(0, max_tick)
        plt.xlim(times[0],times[-1])
        plt.grid()

        ax1 = plt.subplot(3,2,5)
        plt.plot(times,df['t2m'],color='red',linewidth=2)
        if wind == True:
            plt.title('Temperature (Red) / SLR (Black)',fontsize=15)
        else:
            plt.title('Temperature',fontsize=15)
        plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
        plt.xlim(times[0],times[-1])
        plt.grid()
        if wind == True:
            ax2 = ax1.twinx()
            plt.plot(times,df['slr'],color='black',linewidth=2)
            plt.xlim(times[0],times[-1])
            plt.grid()

        if wind == True:
            plt.subplot(3,2,6)
            plt.plot(times,df['wind'],color='black',linewidth=2)
            plt.title('Wind',fontsize=15)
            plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
            plt.xlim(times[0],times[-1])
            plt.grid()
        else:
            plt.subplot(3,2,6)
            plt.plot(times,df['slr'],color='black',linewidth=2)
            plt.title('SLR',fontsize=15)
            plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
            plt.xlim(times[0],times[-1])
            plt.grid()

        # plt.subplot(3,2,6)
        # plt.plot(times,df['freezing_level'],color='black',linewidth=2)
        # plt.title('Freezing Level')
        # plt.xticks(tick_times,tick_labels,rotation = 45,fontsize=9)
        # plt.xlim(times[0],times[-1])
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
        plt.savefig(directory+'points/'+name+'.png')
    
    if frame == max_frame:
        for plot_type in plot_types:
            images = []
            for frame_number in range(3,max_frame+1,3):
                images.append(imageio.imread('figures/'+plot_type+'/'+plot_type+'_'+str(frame_number)+'.png'))
            imageio.mimsave(directory+'figures/'+plot_type+'.gif', images, duration=0.25)
