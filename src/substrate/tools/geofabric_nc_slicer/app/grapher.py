
from datetime import date

import netCDF4

import numpy as np
import matplotlib
from matplotlib import pyplot as plt
matplotlib.use('Agg')

def graph(i_ncpath, i_variable, i_date, i_hour, i_rname):
    filepath = i_ncpath
    month, day, year = i_date.split('/')
    month = int(month)
    day = int(day)
    year = int(year)
    hour = int(i_hour)
    
    day_of_year = date(year, month, day).timetuple().tm_yday

    offset = 0;
    if year == 2016:
        offset = day_of_year - 214
    
    year_offset = year - 2017
    day_2016_offset = 366-214
    offset = 365 * year_offset + day_2016_offset + day_of_year

    time_index = offset * 24 + (hour-1)
    
    f = netCDF4.Dataset(filepath)
    variables = f.variables.keys()

    lats = f.variables['latitude']
    lons = f.variables['longitude']
    lats = lats[:]
    lons = lons[:]


    # (time, long, lat)
    vars = f.variables[i_variable]
    var = vars[time_index, :, :]

    #to mask outside regions
    mask = f.variables['bdy']
    mask = mask[:]
    mask = mask.transpose()
    mask = np.array(mask)

    indexed_lats = []
    for i in range(len(lats)):
        indexed_lats.append(i)
    indexed_lons = []
    for i in range(len(lons)):
        indexed_lons.append(i)

    
    data = var.transpose()
    data = np.array(data)

    np.copyto(mask, np.nan, where = mask == -9999)
    np.copyto(mask, np.nan, where = mask == 9999)
    np.copyto(mask, data, where = mask == 0)
    data = mask

    plt.imshow(data)

    cbar = plt.colorbar()
    try:
        tmp = vars.getncattr('units')
        fa = tmp.replace('_', ' ')
        cbar.set_label(fa, ha='center',  wrap=True)
    except:
        pass
    var_name = i_variable.replace('_', ' ')
    plt.title(var_name,ha='center', y = 1.02,  wrap=True)
    plt.ylabel("Latitude")
    plt.xlabel("Longitude")
    plt.xticks(indexed_lons, lons)
    plt.xticks(rotation = 90, fontsize = 8)
    plt.yticks(indexed_lats, lats,  fontsize = 8)

    plt.tight_layout()
    return plt

def get_numpy(i_ncpath, i_variable, i_date, i_hour):
    filepath = i_ncpath
    month, day, year = i_date.split('/')
    month = int(month)
    day = int(day)
    year = int(year)
    hour =int(i_hour)
   
    day_of_year = date(year, month, day).timetuple().tm_yday

    offset = 0;
    if year == 2016:
        offset = day_of_year - 214
   
    year_offset = year - 2017
    day_2016_offset = 366-214
    offset = 365 * year_offset + day_2016_offset + day_of_year

    time_index = offset * 24 + (hour-1)
    
    f = netCDF4.Dataset(filepath)
    variables = f.variables.keys()

    lats = f.variables['latitude']
    lons = f.variables['longitude']
    lats = lats[:]
    lons = lons[:]


    # (time, long, lat)
    var = f.variables[i_variable]
    var = var[time_index, :, :]

    indexed_lats = []
    for i in range(len(lats)):
        indexed_lats.append(i)
    indexed_lons = []
    for i in range(len(lons)):
        indexed_lons.append(i)


    data = var.transpose()

    numpy_array = np.array(data)
    return numpy_array