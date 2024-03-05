# OWT
from OpticalVariables import OpticalVariables
from OWT import OWT

# data processing
from netCDF4 import Dataset
import re
import numpy as np

def str_match(input, pattern, ind=False):
    """Find out the matched strings

    Args:
        input (list): list of strings
        pattern (character): the string to be matched
        ind (bool, optional): True will return the index in the input list; 
            otherwise, the matched strings. Defaults to False.

    Returns:
        list: characters or indices of matched variables
    """    
    pattern = re.compile(pattern)
    if ind:
        indices = [i for i in range(len(input)) if pattern.match(input[i])]
    else:
        indices = [v for v in input if pattern.match(v)]
    return indices

def copy_group(src_group, dst_group):
    # Copy dimensions
    for name, dimension in src_group.dimensions.items():
        dst_group.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

    # Copy variables
    for name, variable in src_group.variables.items():
        new_var = dst_group.createVariable(name, variable.datatype, variable.dimensions, zlib=True, complevel=4, shuffle=True)
        new_var.setncatts({k: variable.getncattr(k) for k in variable.ncattrs()})
        new_var[:] = variable[:]

    # Copy group attributes
    dst_group.setncatts({k: src_group.getncattr(k) for k in src_group.ncattrs()})

    # Recursively copy all subgroups (if any)
    for name, subgroup in src_group.groups.items():
        dst_subgroup = dst_group.createGroup(name)
        copy_group(subgroup, dst_subgroup)


import glob
import os

# replace the folder path for your data downloaded from https://zenodo.org/record/7567533
path = "/Users/Bi/Documents/ImageData/A4O_version5"

nc_files = glob.glob(os.path.join(path, "*.nc"))

for i in range(len(nc_files)):
# for i in range(1):
    fn = nc_files[i]
    print(f"{i+1}/{len(nc_files)}: {fn}")

    with Dataset(fn, mode='r') as d:
        fn_out = fn[0:-3] + "_owt.nc"
        with Dataset(fn_out, mode='w', format='NETCDF4') as new_ds:

            # Copy global attributes
            new_ds.setncatts(d.__dict__)
            
            # Copy the root group content (dimensions, variables, and attributes)
            copy_group(d, new_ds)

            # read Rrs from d
            name_var = list(d.groups["A4O"].variables.keys())
            var_A4O_Rrs = str_match(name_var, "A4O_Rrs_\d+$")
            wavelen_A4O_Rrs = np.array([float(i.split("_")[-1]) for i in var_A4O_Rrs])
            Rrs_A4O = np.array([d.groups["A4O"].variables[x][:] for x in var_A4O_Rrs])
            Rrs_A4O = np.squeeze(Rrs_A4O, axis=1).transpose(1, 2, 0)

            # apply owt classification
            ov = OpticalVariables(Rrs=Rrs_A4O, band=wavelen_A4O_Rrs, sensor="OLCI_S3A")
            ov.run()
            owt = OWT(ov.AVW, ov.Area, ov.NDI)
            owt.run_classification()

            # total membership and the weighted-membership
            owt.utot = np.sum(owt.u, axis=2)
            utot_array = np.repeat(owt.utot[:, :, np.newaxis], 10, axis=2)
            owt.u_weighted = owt.u / utot_array

            # Create a new "OWT" group
            owt_group = new_ds.createGroup("OWT")
            
            # fetch the dim from original d
            out_dim = d.groups["A4O"].variables[var_A4O_Rrs[0]].dimensions[1:]

            # Save membership to variables    
            for j in range(owt.u.shape[2]):
                var_name = "U_OWT_" + owt.typeName[j]
                var = owt_group.createVariable(var_name, "f4", out_dim, zlib=True, complevel=4, shuffle=True)
                var[:] = owt.u[:, :, j]
                var.units = "-"
                var.long_name = "Membership of Optical Water Type " + owt.typeName[j]

            # Save weighted-membership to variables    
            for j in range(owt.u_weighted.shape[2]):
                var_name = "U_weighted_OWT_" + owt.typeName[j]
                var = owt_group.createVariable(var_name, "f4", out_dim, zlib=True, complevel=4, shuffle=True)
                var[:] = owt.u_weighted[:, :, j]
                var.units = "-"
                var.long_name = "Weighted-membership of Optical Water Type " + owt.typeName[j]

            # Save Total membership to variable
            var = owt_group.createVariable("U_tot", "f4", out_dim, zlib=True, complevel=4, shuffle=True)
            var[:] = owt.utot[:]
            var.units = "-"
            var.long_name = "Total membership values"

            # Save OWT index to variable
            var = owt_group.createVariable("OWT_index", "i1", out_dim, zlib=True, complevel=4, shuffle=True)
            var[:] = owt.type_idx[:]
            var.units = "-"
            var.long_name = "Optical Water Type index"
