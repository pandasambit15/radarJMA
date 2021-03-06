# Reading JMA radar data in netcdf format
# for preprocessing 
import netCDF4
import numpy as np
import h5py

import glob
import subprocess
import sys
import os.path

from scipy.interpolate import RectBivariateSpline
import matplotlib.pyplot as plt

# extract data from nc file
def ext_nc_JMA(fname,nx_out,ny_out):
    #nc = netCDF4.Dataset('../data/2015/01/01/2p-jmaradar5_2015-01-01_0000utc.nc', 'r')
    nc = netCDF4.Dataset(fname, 'r')
    #
    # dimensions
    nx = len(nc.dimensions['LON'])
    ny = len(nc.dimensions['LAT'])
    nt = len(nc.dimensions['TIME'])
    print("dims:",nx,ny,nt)
    #
    # ext variable
    lons = nc.variables['LON'][:]
    lats = nc.variables['LAT'][:]
    R = nc.variables['PRATE'][:]
    #
    # clip area around tokyo
    lat_tokyo = 35.681167
    lon_tokyo = 139.767052
    nx_clip = 200
    ny_clip = 200
    i0=np.argmin(np.abs(lons.data-lon_tokyo)) - int(nx_clip/2)
    j0=np.argmin(np.abs(lats.data-lat_tokyo)) - int(ny_clip/2)
    i1=i0+nx_clip
    j1=j0+ny_clip
    #
    # extract data
    Rclip = R.data[0,j0:j1,i0:i1]
    #Rclip = Rclip.T   # transpose so that i index comes first
    lon_clip=lons.data[i0:i1]
    lat_clip=lats.data[j0:j1]
    print("rainfall min:max",Rclip.min(),Rclip.max())
    interp_spline = RectBivariateSpline(np.arange(nx_clip), np.arange(ny_clip), Rclip,kx=1,ky=1,s=0)
    x2 = np.linspace(0,nx_clip,nx_out)
    y2 = np.linspace(0,nx_clip,ny_out)
    Rclip_resize = interp_spline(x2,y2)
    Rclip_resize = np.maximum(Rclip_resize,0) # replace negative value with 0
#    plt.imshow(Rclip)
#    plt.savefig("interp_before.png")
#    plt.imshow(Rclip_resize) 
#    plt.savefig("interp_after.png")
    print("interpolated rainfall min:max",Rclip_resize.min(),Rclip_resize.max())
    # save data
    return(Rclip_resize)

# read
infile_root = '../data/jma_radar/2015/'
infile_root = '../data/jma_radar/2016/'
infile_root = '../data/jma_radar/2017/'
print('input dir:',infile_root)

# outfile
outfile_root = '../data/data_kanto_resize/'
print('output dir:',infile_root)

nx = 128
ny = 128
nt = 12

#for infile in sorted(glob.iglob(infile_root + '*00utc.nc.gz')):
for infile in sorted(glob.iglob(infile_root + '/*/*/*00utc.nc.gz')):
#for infile in sorted(glob.iglob(infile_root + '/*/*/*/*00utc.nc.gz')):
    # read 1hour data at a time
    # initialize with -999.0
    R1h = np.full((nt,nx,ny),-999.0,dtype=np.float32)
    for i in range(12):
        shour = '{0:02d}utc'.format(i*5)
        in_zfile = infile.replace('00utc',shour)
        print('reading zipped file:',in_zfile)
        # '-k' option for avoiding removing gz file
        subprocess.run('gunzip -kf '+in_zfile,shell=True)
        in_nc=in_zfile.replace('.gz','')
        print('reading nc file:',in_nc)
        if os.path.exists(in_nc):
            Rclip = ext_nc_JMA(in_nc,nx,ny)
        else:
            print('nc file not found!!!',in_nc)
            next
        R1h[i,:,:]=Rclip
        subprocess.run('rm '+in_nc,shell=True)

    # write to h5 file
    h5fname = infile.split('/')[-1]
    h5fname = h5fname.replace('.nc.gz','.h5')
    print('writing h5 file:',h5fname)
    h5file = h5py.File(outfile_root+h5fname,'w')
    h5file.create_dataset('R',data= R1h)
    h5file.close()
    #sys.exit()
