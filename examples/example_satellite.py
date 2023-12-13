from netCDF4 import Dataset as ds
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import re

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import classification
import misc


def str_match(input, pattern, ind=False):
    # input:   list of strings
    # pattern: the string to be matched
    # ind:     (boolean) True will return the index in the input list; otherwise, the matched strings
    pattern = re.compile(pattern)
    if ind:
        indices = [i for i in range(len(input)) if pattern.match(input[i])]
    else:
        indices = [v for v in input if pattern.match(v)]
    return indices


"""
Subset NC file from ONNS outputs
"""
# fn = "/Users/Bi/Documents/GitHub/OWT/Paper/Apply_framework_to_image_subset/GermanBight_20160720T093421_subset.nc"
# d = ds(fn, mode="r")
# name_var = list(d.variables.keys())
# var_A4O_Rrs = str_match(name_var, "A4O_Rrs_\d+$")
# wavelen_A4O_Rrs = np.array([float(i.split("_")[-1]) for i in var_A4O_Rrs])
# Rrs_A4O = np.array([d.variables[x][:] for x in var_A4O_Rrs]).transpose(1, 2, 0)


"""
When comes to original ONNS outputs, read group first
"""
# fn = "/Users/Bi/Documents/ImageData/A4O_version5/S3A_OL_2_WFR____20160720T092821_20160720T093021_different_AC_20230125.nc"
# fn = "/Users/Bi/Documents/ImageData/A4O_version5/S3A_OL_2_WFR____20160720T093421_20160720T093621_different_AC_20230125.nc"
fn = "/Users/Bi/Documents/ImageData/A4O_version5/S3A_OL_2_WFR____20170114T130626_20170114T130826_different_AC_20230125.nc"
d = ds(fn, mode="r")
d = d.groups["A4O"]
name_var = list(d.variables.keys())
var_A4O_Rrs = str_match(name_var, "A4O_Rrs_\d+$")
wavelen_A4O_Rrs = np.array([float(i.split("_")[-1]) for i in var_A4O_Rrs])
Rrs_A4O = np.array([d.variables[x][0] for x in var_A4O_Rrs]).transpose(1, 2, 0)

"""
Apply classification framework
*_vec function are used for numpy array
"""
# three optical variables
index_for_AVW = (wavelen_A4O_Rrs >= 400) & (wavelen_A4O_Rrs <= 866)
bands_for_AVW = wavelen_A4O_Rrs[index_for_AVW]
Rrs_for_AVW = Rrs_A4O[:, :, index_for_AVW]

AVW = misc.cal_AVW_vec(bands_for_AVW, Rrs_for_AVW, "OLCI_S3A")

bands_for_Area = np.array([442, 560, 665])
Rrs_for_Area = Rrs_A4O[:, :, np.where(np.isin(wavelen_A4O_Rrs, bands_for_Area))[0]]
Area = misc.cal_Area_vec(bands_for_Area, Rrs_for_Area)

Rrs_for_NDI = Rrs_A4O[:, :, np.where(np.isin(wavelen_A4O_Rrs, [560, 665]))[0]]
NDI = misc.cal_NDI_vec(Rrs_for_NDI)

# do the classification
u = classification.calssification_vec(AVW, Area, NDI)
water_type = np.argmax(u, axis = -1)
water_type[np.all(np.isnan(u), axis = -1)] = -1

"""
Post-processing, plotting
"""

type_info = classification.load_centroids()
type_name = type_info["typeName"]
type_name.insert(0, "NaN")
type_color = type_info["typeColHex"]
type_color.insert(0, "#808080")

# fig, axes = plt.subplots(2, 5, figsize = (15, 6))

# for i in range(2):
#     for j in range(5):
#         index = i * 5 + j
#         axes[i, j].imshow(u[:, :, index], vmin = 0)
#         axes[i, j].set_title("OWT {}".format(type_name[index]))
#         axes[i, j].set_xticks([])
#         axes[i, j].set_yticks([])

# plt.colorbar(label = "Memb", extend = "both", orientation = "horizontal", pad = 0.05, fraction = 0.05)
# plt.tight_layout()
# # plt.show()
# plt.savefig("memb_owt.png", dpi=300, bbox_inches="tight")
# plt.close()


cmap = mcolors.ListedColormap(type_color)
bounds = np.arange(-1.5, 10.5)
norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

plt.figure(figsize=(8, 6))
plt.imshow(water_type, cmap=cmap, norm=norm)

cbar = plt.colorbar(ticks = np.arange(-1, 10), orientation="horizontal")
cbar.ax.set_xticklabels(type_name)

plt.savefig("type_owt.png", dpi=300, bbox_inches="tight")
plt.close()


