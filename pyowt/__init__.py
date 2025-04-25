'''

Version history
===============

0.32:
    - Use absolute file path of OWT_centroids.nc
    - Clean the root folder

0.40:
    - Deprecated run and run_classification functions in OpticalVariables and OWT, respectively
    - Add manipulation of input Rrs for OpticalVariables which now supports any input shapes
    - Add new classes `PlotOV` and `PlotSpec` for plotting
    - Add new csv file (data/OWT_mean_spec.csv) for mean spectra of OWTs
    - run_examples.py revised accordingly

0.41:
    - Fig bugs in satellite sensor waveband settings and add new setups
    - Add new subcalss in `OpticalVariables`, `ArrayWithAttributes`, to allow attributes for np.array
    - A new demo of Rrs updated in the folder `data`
    - `run_examples.py` add Google Drive link for demo satellite data

0.50:
    - Reorganize the structure for tidiness
    - Add `projects` folder to contain scripts for different application.
    - `projects` now has two folders, AquaINFRA for scripts related to the project, and zenodo for its data preparation
    - Merge Merret's PR for AquaINFRA project which employs pygeoapi module for cloud processing
    - Collect pyowt-related scripts to `pyowt` for better management.
    - Have a `setup.py` for development install mode, `pip install -e .`

0.60:
    - Add a new version of classification centroids which has been shrinked with smaller covariance
    - Since different centroid versions were added, the data folder was revised correspondingly
    - Add satellite_handlers for processing cmems and eumetsat olci level-2 products

0.61:
    - add ENVI format reader in ./satellite_handlers which is supposed to read Liu's ENVI results but can be used (modified) for other ENVI results
    - Add warning for eumetsat_olci_level2 if uninstalled packages are imported
    - OpticalVariable now supports to find nearest waveband to calculate AVW (just like I did for RGB bands). However, it still needs more strict input checking...

0.62:
    - Fixed the bug when sensor is None for AVW calculation (issue from Merret)

0.63:
    - Rewrite OWT centroids generation codes (now for v01 and v02)
    - pyowt.OpticalVariables now checks the input hyperspectral Rrs is ranging from 400 to 800 nm
    - pyowt.OpticalVariables now interpolates hyperspectral Rrs into 1 nm interval if they are not
    - satellite_handlers: detect projection for Liu's image files
    - modified README.md in main

0.64:
    - Reprocessed the spectral convolution based on SRF files downloaded from the NASA Ocean Color website
    - The convoluted Rrs were then calculated multispectral AVW and used to perform regression analysis with hyperspectral AVW
    - Add new functions pyowt/satellite_handlers/srf_convolution.py for the above work
    - The pyowt/data/AVW_all_regression_800.txt file was updated
    - The sensor names in pyowt/data/AVW_all_regression_800.txt has been updated according to the NASA netcdf files
    - Demos in projects/AquaINFRA/run_AquaINFRA.py and projects/AquaINFRA/run_AquaINFRA2.py were revised due to sensor name changing

0.65:
    - Bugs fixed for Sentinel-2 band setups, regression coefficients of which are updated correspondingly
    - Tested a new version of centroid (shrunk) but probably will be deprecated in the future... 
    - Added a new satellite handler for Dr. Liu's ENVI format data (basically converting them to netcdf file)

0.66: 
    - Add new option for OpticalVariables if given Rrs is a 4-d array, say (wavelen, time, lat, lon)

'''

__package__ = "pyOWT"
__version__ = "0.65"

