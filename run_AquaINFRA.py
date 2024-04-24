# OWT
from OpticalVariables import OpticalVariables
from OWT import OWT

# data processing
from netCDF4 import Dataset as ds
import numpy as np

import glob
import os

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# path_root = "/Users/Bi/koflux/feederdata2/EighteenTB05/AquaINFRA"
# month_dir = ["onns_06-2023", "onns_07-2023", "onns_08-2023", "onns_09-2023"]

# i_month = 0

# path = os.path.join(path_root, month_dir[i_month], "dailymeans_full")
# o_path = os.path.join(path_root, month_dir[i_month], "owt_results")

# onns_files = glob.glob(path + "/*.nc")


# file = onns_files[0]
# o_file = os.path.join(o_path, os.path.basename(file)[:-3] + "_owt.nc") 

file = "/Users/Bi/Documents/ImageData/AquaINFRA/S3__OL_3_WFRA4O_20230601T075534_20230601T112032_20240402T155246.nc"

o_file = file[:-3] + "_owt.nc"
o_png = file[:-3] + "_owt.png"
o_rgb = file[:-3] + "_rgb.png"

# for file in onns_files:

# open netcdf file
d = ds(file, mode="r")

var_Rrs = [
    "Rrs_n_400",
    "Rrs_n_412",
    "Rrs_n_442",
    "Rrs_n_490",
    "Rrs_n_510",
    "Rrs_n_560",
    "Rrs_n_620",
    "Rrs_n_665",
    "Rrs_n_674",
    "Rrs_n_681",
    "Rrs_n_709",
    "Rrs_n_754",
    "Rrs_n_779",
    "Rrs_n_865",
]

wavelen_Rrs = np.array([float(i.split("_")[-1]) for i in var_Rrs])

var_flags = [
    "AC_flag_bright",
    "AC_flag_suspect_pixel",
    "ONNS_valid",
    "ONNS_limited_valid",
    "AC_flag_cloud_risk",
    "AC_flag_adjacency",
    "AC_flag_sea_ice",
    "AC_flag_Rtoa_excess",
    "AC_flag_floating",
    "AC_flag_glint_risk",
    "cloud_risk",
    "limited_valid",
]

# read TOA rgb for RGB
toa_R = np.array(d.variables["R_toa_665"][:])
toa_G = np.array(d.variables["R_toa_560"][:])
toa_B = np.array(d.variables["R_toa_442"][:])

# read Rrs data
im = np.array([d.variables[x][:] for x in var_Rrs]).transpose(1, 2, 0)

# read flags
flags = [d.variables[x][:] for x in var_flags]

# run owt classification
ov = OpticalVariables(Rrs=im, band=wavelen_Rrs, sensor="OLCI_S3A")
ov.run()

owt = OWT(ov.AVW, ov.Area, ov.NDI)
owt.run_classification()

# set up outputs
owt.utot = np.sum(owt.u, axis=2)
w_utot_zero = np.where(owt.utot == 0)
utot_array = np.repeat(owt.utot[:, :, np.newaxis], 10, axis=2)
utot_array[w_utot_zero[0], w_utot_zero[1], :] = 1.0
utot_array_divided = 1 / utot_array
utot_array_divided[w_utot_zero[0], w_utot_zero[1], :] = 0
owt.u_weighted = owt.u * utot_array_divided


# save out the new netcdf
nc_out = ds(o_file, "w", format="NETCDF4")

# copy global attributes from input nc file
for x in d.ncattrs():
    nc_out.setncattr(x, d.__getattribute__(x))

# edit some global attributes to output
nc_out.setncattr('title', "Optical water type classification results for ONNS merged products")
nc_out.setncattr('product_name', os.path.basename(o_file))
nc_out.setncattr('contributor', 'Shun Bi et al.')

nc_out.createDimension("lat", d.variables['lat'].shape[0])
nc_out.createDimension("lon", d.variables['lon'].shape[0])
dims = ('lat', 'lon', )

# create coordinate variables in outfile with attributes from infile
var_lat = nc_out.createVariable('lat', 'f8', ('lat',))
var_lat[:] = d.variables['lat'][:]
for x in d.variables['lat'].ncattrs():
    var_lat.setncattr(x, d.variables['lat'].__getattribute__(x))

var_lon = nc_out.createVariable('lon', 'f8', ('lon',))
var_lon[:] = d.variables['lon'][:]
for x in d.variables['lon'].ncattrs():
    var_lon.setncattr(x, d.variables['lon'].__getattribute__(x))

# Save OWT index to variable
var = nc_out.createVariable("OWT_index", "i1", dims, zlib=True)
var[:] = owt.type_idx[:]
var.units = "-"
var.long_name = "Optical Water Type index"

# save total membership to variable
var = nc_out.createVariable("U_tot", "f4", dims, zlib=True)
var[:] = owt.utot[:]
var.units = "-"
var.long_name = "Total membership values"

# save membership to variables
for i, name in enumerate(owt.typeName):
    var_name = "U_OWT_" + name
    var = nc_out.createVariable(var_name, "f4", dims, zlib=True)
    var[:] = owt.u[:,:,i]
    var.units = "-"
    var.long_name = "Membership of Optical Water Type " + name

# save weighted-membership to variables
for i, name in enumerate(owt.typeName):
    var_name = "U_weighted_OWT_" + name
    var = nc_out.createVariable(var_name, "f4", dims, zlib=True)
    var[:] = owt.u_weighted[:,:,i]
    var.units = "-"
    var.long_name = "Weighted-membership of Optical Water Type " + name

# save flags to variables
for i, name in enumerate(var_flags):
    var = nc_out.createVariable(name, "b", dims, zlib=True)
    var[:] = flags[i]
    var.units = "-"

nc_out.close()
d.close()

# save out png files
cmap = mcolors.ListedColormap(owt.dict_idx_color.values())
bounds = np.arange(-1.5, 10.5)
norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

plt.figure(figsize=(8, 6))
ax = plt.gca()
im = ax.imshow(owt.type_idx, cmap=cmap, norm=norm, origin='lower')
cbar = plt.colorbar(im, ticks = np.arange(-1, 10), orientation="horizontal", pad=0.05)
cbar.ax.set_xticklabels(owt.dict_idx_name.values())
ax.axis('off')
plt.tight_layout()
plt.savefig(o_png, dpi=300, bbox_inches="tight")
plt.close()

# save out rgb files
def stretch_channel(channel):
    # Calculate the 2.5% and 60% quantiles
    low, high = np.percentile(channel, [0.5, 60])
    # Scale the channel to [0, 1] range based on the quantiles
    channel = (channel - low) / (high - low)
    # Clip to [0, 1] to eliminate outliers
    channel = np.clip(channel, 0, 1)
    return channel

R_stretched = stretch_channel(toa_R)
G_stretched = stretch_channel(toa_G)
B_stretched = stretch_channel(toa_B)
RGB = np.stack([R_stretched, G_stretched, B_stretched], axis=-1)
ax = plt.gca()
im = ax.imshow(RGB, origin='lower')
ax.axis('off')
plt.tight_layout()
plt.savefig(o_rgb, dpi=300, bbox_inches="tight")
plt.close()
