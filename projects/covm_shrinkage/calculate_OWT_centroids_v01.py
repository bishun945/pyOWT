import xarray as xr
import numpy as np
import pandas as pd
import os
from datetime import datetime

from pyowt.OpticalVariables import OpticalVariables
from pyowt.OWT import OWT

# some setups
version_tag = 'v01'
date_tag = datetime.today().strftime("%Y-%m-%d")
# date_tag = '2024-10-21'
VersionLog = (
    "This is the original version of the OWT classification from the paper by Bi and Hieronymi (2024)." 
    " The centroid data were calculated from the training dataset (https://zenodo.org/records/12803329)"
    " based on the labeled water types. Note that this version may differ slightly from the version dated"
    " 2023-09-26, which was based on R packages. However, any classification differences resulting from"
    " switching to the Python environment are negligible."
)


# load training data set
fn = "projects/zenodo/owt_BH2024_training_data_hyper.nc"
ds = xr.open_dataset(fn)

wavelen = ds['wavelen'].values # from 400 to 900 nm
Rrs = ds['Rrs'].values
type_define = ds['type'].values # original OWT definition (BH2024)

lamBC = 0.226754 # Box-Cox transform coefficient, from BH2024
N = 10 # number of OWT, from BH2024

# calculate optcal variables: avw, area, and ndi
ov = OpticalVariables(Rrs=Rrs, band=wavelen)
AVW, Area, NDI = ov.AVW, ov.Area, ov.NDI
ABC = OWT.trans_boxcox(Area, lamBC)
ov_mat = np.hstack((AVW, ABC, NDI))

# select the used index
index_used = range(Rrs.shape[0])

# filter selected data
type_used = type_define[index_used]
ov_mat = ov_mat[index_used, :]
unique_types = np.sort(np.unique(type_used))


# keep the same data structure
# - mean: (N, 3)
# - covm: (3, 3, N)
mean_new = np.zeros((N, 3))
covm_new = np.zeros((3, 3, N))

for i, t in enumerate(unique_types):
    indices = np.where(type_used == t)[0]
    samples = ov_mat[indices, :]

    mean_type = np.mean(samples, axis=0)
    covm_type = np.cov(samples, rowvar=False)

    mean_new[i, :] = mean_type
    covm_new[:, :, i] = covm_type



# save to centroid netcdf files

dc_new = xr.Dataset(
    {
        "mean": (("type", "var1"), mean_new),
        "covm": (("var1", "var2", "type"), covm_new),
    },
    coords={
        "type": ["1", "2", "3a", "3b", "4a", "4b", "5a", "5b", "6", "7"],
        "var1": ["AVW", "ABC", "NDI"],
        "var2": ["AVW", "ABC", "NDI"]
    },
)

dc_new["mean"].attrs["long_name"] = "Mean matrix of three optical variables for ten types. Shape (10, 3)"
dc_new["mean"].attrs["units"] = "unitless"

dc_new["covm"].attrs["long_name"] = "Covariance matrix of three optical variables for ten types. Shape (3, 3, 10)"
dc_new["covm"].attrs["units"] = "unitless"

dc_new.attrs['Description'] = 'Centroids and covariance matrix data for the optical water type classification by Bi and Hieronymi (2024)'
dc_new.attrs['Version'] = version_tag
dc_new.attrs['VersionLog'] = VersionLog
dc_new.attrs['Author'] = 'Shun Bi'
dc_new.attrs['Email'] = 'Shun.Bi@outlook.com'
dc_new.attrs['CreateDate'] = date_tag
dc_new.attrs['lamBC'] = lamBC
dc_new.attrs['lamBC_description'] = 'Lambda coefficient for Box-Cox transformation for Area'
dc_new.attrs['TypeName'] = '1, 2, 3a, 3b, 4a, 4b, 5a, 5b, 6, 7'
dc_new.attrs['TypeColorName'] = 'blue, yellow, orange, cyan, green, purple, darkblue, red, chocolate, darkcyan'
dc_new.attrs['TypeColorHex'] = '#0000FF, #FFFF00, #FFA500, #00FFFF, #00FF00, #A020F0, #00008B, #FF0000, #D2691E, #008B8B'
dc_new.attrs['Reference'] = 'Bi, S., and Hieronymi, M. (2024). Holistic optical water type classification for ocean, coastal, and inland waters. Limnology & Oceanography, lno.12606. doi: 10.1002/lno.12606'

output_file = f"pyowt/data/{version_tag}/OWT_centroids.nc"
output_folder = os.path.dirname(output_file)
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

dc_new.to_netcdf(output_file)



# Update OWT_mean_spec.csv for plotting

results = []

for t in unique_types:

    indices = np.where(type_used == t)[0]
    Rrs_samples = Rrs[indices, :]
    Area_samples = Area[indices, 0]

    m_Rrs_t = np.mean(Rrs_samples, axis=0)
    sd_Rrs_t = np.std(Rrs_samples, axis=0)
    lo_Rrs_t = np.quantile(Rrs_samples, 0.05, axis=0)
    up_Rrs_t = np.quantile(Rrs_samples, 0.95, axis=0)

    nRrs_samples = Rrs_samples / Area_samples[:, np.newaxis]

    m_nRrs_t = np.mean(nRrs_samples, axis=0)
    sd_nRrs_t = np.std(nRrs_samples, axis=0)
    lo_nRrs_t = np.quantile(nRrs_samples, 0.05, axis=0)
    up_nRrs_t = np.quantile(nRrs_samples, 0.95, axis=0)

    for i in range(len(wavelen)):
        results.append([
            t,
            wavelen[i],

            m_Rrs_t[i],
            sd_Rrs_t[i],
            lo_Rrs_t[i],
            up_Rrs_t[i],

            m_nRrs_t[i],
            sd_nRrs_t[i],
            lo_nRrs_t[i],
            up_nRrs_t[i]
        ])

columns = ["type", "wavelen", "m_Rrs", "sd_Rrs", "lo_Rrs", "up_Rrs", "m_nRrs", "sd_nRrs", "lo_nRrs", "up_nRrs"]
df = pd.DataFrame(results, columns=columns)

output_file = f"pyowt/data/{version_tag}/OWT_mean_spec.csv"
df.to_csv(output_file, index=False)