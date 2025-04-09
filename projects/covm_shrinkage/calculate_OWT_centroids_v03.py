# 07.11.2024 Shun
# In some of applications, the input Rrs spectrum is significantly affected by
#   various noise such as skyligth residuals, sun glint, or atmospheric correction
# I have realized such disturbance will eventually change the water classification
#   results even though, for example, it is a just slight offset for blue ocean
#   spectrum (with red shifted AVW and lifting Area values).
# To enhance the resistance of the OWT framework on such dataset, one should add
#   artificial noise into the training data and re-calcualte the centroids.
#   However, this might contrary the original intention of the classification
#   that is able to detect the unclassifiable spectrum with low data quality...

# Some testings are played around here...

import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

fn = "projects/zenodo/owt_BH2024_training_data_hyper.nc"
ds = xr.open_dataset(fn)
wavelen_org = ds['wavelen'].values
Rrs_org = ds['Rrs'].values
ind = np.where((wavelen_org >= 400) & (wavelen_org <= 800))[0]
wavelen = wavelen_org[ind]
Rrs_mat = Rrs_org[:,ind]
Rrs = Rrs_mat[10,:]

plt.plot(wavelen, Rrs, label = 'original')
plt.plot(wavelen, Rrs + 0.001, label = '+0.001')
plt.legend()
plt.show()
