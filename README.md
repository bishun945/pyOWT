# **pyOWT**: python library for Optical Water Type classification

Note: this repo is translated from the R repo [`OWT`](https://github.com/bishun945/OWT) for the water type classification and has been maintained independently from its original version.

# Install

Clone the whole repo to the your path and install it:

```console
pip install /path/to/pyowt
```

# License

See the [LICENSE](/LICENSE) file.

# How to use it

Two classes, `OWT` and `OpticalVariables` are needed to perform the OWT classification.

```python
from pyowt.OWT import OWT
from pyowt.OpticalVariables import OpticalVariables
from pyowt.PlotOWT import PlotOV, PlotSpec

# first calculate three optical variables from Rrs
# `sensor` should be specified for satellite data
ov = OpticalVariables(Rrs=Rrs_data, band=Band_list, sensor=Sensor_str)

# feed data into classification
owt = OWT(AVW=ov.AVW, Area=ov.Area, NDI=ov.NDI)

# show classification results
print(owt.type_str) 

# show plots

## scatter plot
PlotOV(owt) 

## spectral distribution
PlotSpec(owt, ov, norm=False) 

## spectral distribution - normalized
PlotSpec(owt, ov, norm=True)
```

Check the [example](/run_examples.py) file for more detailed demo runs:

1) Some hyperspectral Remote-sensing reflectance data simulated by Bi et al. (2023)

2) Satellite data with atmosphericly corrected by A4O (Hieronymi et al. 2023)

# Short description of OWTs

|OWT | Desciption |
|----|------------|
| 1  | Extremely clear and oligotrophic indigo-blue waters with high reflectance in the short visible wavelengths. |
| 2  | Blue waters with similar biomass level as OWT 1 but with slightly higher detritus and CDOM content. |
| 3a | Turquoise waters with slightly higher phytoplankton, detritus, and CDOM compared to the first two types. |
| 3b | A special case of OWT 3a with similar detritus and CDOM distribution but with strong scattering and little absorbing particles like in the case of Coccolithophore blooms. This type usually appears brighter and exhibits a remarkable ~490 nm reflectance peak. |
| 4a | Greenish water found in coastal and inland environments, with higher biomass compared to the previous water types. Reflectance in short wavelengths is usually depressed by the absorption of particles and CDOM. |
| 4b | A special case of OWT 4a, sharing similar detritus and CDOM distribution, exhibiting phytoplankton blooms with higher scattering coefficients, e.g., Coccolithophore bloom. The color of this type shows a very bright green. |
| 5a | Green eutrophic water, with significantly higher phytoplankton biomass, exhibiting a bimodal reflectance shape with typical peaks at ~560 and ~709 nm.|
| 5b | Green hyper-eutrophic water, with even higher biomass than that of OWT 5a (over several orders of magnitude), displaying a reflectance plateau in the Near Infrared Region, NIR (vegetation-like spectrum). |
| 6  | Bright brown water with high detritus concentrations, which has a high reflectance determined by scattering. |
| 7  | Dark brown to black water with very high CDOM concentration, which has low reflectance in the entire visible range and is dominated by absorption.  |

<br>

<center>

<img src="figs/owt_spec.png" alt="owt_spec" width="500"/>

</center>

*Mean spectrum of simulated spectra for optical water types. Panel (A) displays the raw remote-sensing reflectance (unscaled), while Panel (B) shows the spectral normalized by trapezoidal-area. The positions of RGB bands are marked on the x-axis. Image Source: Bi and Hieronymi (2024)*

# Supported band configurations

The Spectral Response Functions (SRFs) for the satellite sensors used in `pyOWT` were obtained from the NASA [Ocean Color website](https://oceancolor.gsfc.nasa.gov/resources/docs/rsr_tables/). The naming convention for these SRFs follows the format `instrument-platform`, which is directly derived from corresponding NetCDF files associated with each sensor.

- "HSI-EnMAP": from 426.5 to 797.0 nm
- "OCI-PACE": from 400.2 to 799.4
- "OCTS-adeos": [412, 443, 490, 516, 565, 667, 862]
- "modis-aqua": [412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859]
- "GOCI-coms": [412, 443, 490, 555, 660, 680, 745, 865]
- "MERIS-envisat": [413, 443, 490, 510, 560, 620, 665, 681, 709, 754, 779, 865]
- "viirs-jpss-1": [411, 445, 489, 556, 667, 746, 868]
- "viirs-jpss-2": [411, 445, 488, 555, 671, 747, 868]
- "OLI-landsat-8": [443, 482, 561, 655, 865]
- "SeaWiFS-orbview-2": [412, 443, 490, 510, 555, 670, 865]
- "olci-s3a": [400, 412, 443, 490, 510, 560, 620, 665, 674, 682, 709, 754, 779, 866]
- "olci-s3b": [400, 412, 443, 490, 510, 560, 620, 665, 674, 681, 709, 754, 779, 866]
- "HAWKEYE-seahawk1": [412, 447, 488, 510, 556, 670, 752, 867]
- "msi-sentinel-2a": [443, 492, 560, 665, 704, 740, 783, 835, 865]
- "msi-sentinel-2b": [442, 492, 559, 665, 704, 739, 780, 835, 864]
- "viirs-suomi-npp": [410, 443, 486, 551, 671, 745, 862]
- "modis-terra": [412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859]

CMEMS setups
- "CMEMS_BAL_HROC": [443, 492, 560, 665, 704, 740, 783, 865] # likely msi-sentinel-2a
- "CMEMS_BAL_NRT": [400, 412, 443, 490, 510, 560, 620, 665, 674, 682, 709, 779, 866] # likely olci-s3a
- "CMEMS_MED_MYINT": [400, 412, 443, 490, 510, 560, 620, 665, 674, 682, 709, 779, 866] # likely olci-s3a

AERONET-OC setups
- "AERONET_OC_1": [400, 412, 443, 490, 510, 560, 620, 665, 779, 866] # likely olci-s3a
- "AERONET_OC_2": [412, 443, 490, 532, 551, 667, 870] # likely modis-aqua

# Bug rerport

When you find any issues or bugs while running the module, please [open an issue](https://github.com/bishun945/pyOWT/issues) or directly contact [Shun Bi](Shun.Bi@outlook.com) with a reproducible script with data.

# Projects

The `projects` directory contains tasks that rely on the `pyowt` package but are maintained independently of `pyowt`.

## AquaINFRA

This part is supported by [Merret Buurman](merret.buurman@igb-berlin.de)

AquaINFRA related scripts can be found in `projects/AquaINFRA`

When running this as OGC-compliant web service in an installation of pygeoapi, please create a json config file `config.json` with the below contents (or add it to the general AquaINFRA config file), and define an environment variable called `PYOWT_CONFIG_FILE` that contains the path to it.

```
{
    "download_dir": "/var/www/nginx/download/",
    "download_url": "https://someserver/download/",
    "pyowt": {
        "example_input_data_dir": ".../pygeoapi/process/pyOWT/data/", # this is where the process will try to find existing example inputs
        "input_data_dir": "/.../inputs/", # this is where the process will try to store downloaded inputs
        "path_sensor_band_library": ".../pygeoapi/process/pyOWT/data/sensor_band_library.yaml"
    }
}
```

## zenodo

This part is supported by Shun Bi and Martin Hieronymi.

The `projects/zenodo` directory contains R and python scripts used to generate NetCDF files for the training data set in Bi and Hieronymi (2024). These data sets, available in both hyperspectral and Sentinel-3 OLCI band configurations, are published on [zenodo](https://zenodo.org/records/12803329). Note that some files are too large to be uploaded to GitHub, but they are available upon request.

# Contributors

- Dr. Shun Bi - Project maintainer, developer
- Dr. Martin Hieronymi (Hereon) - Reviewer, Support
- Merret Buurman (IGB-Berlin) - Developer for AquaINFRA
- Dr. Markus Konkol (52north) - Developer for AquaINFRA

# References

- Bi and Hieronymi (2024). Holistic optical water type classification for ocean, coastal, and inland waters. Limnol Oceanogr. https://doi.org/10.1002/lno.12606

- Bi et al. (2023). Bio-geo-optical modelling of natural waters. Front. Mar. Sci. 10, 1196352. https://doi.org/10.3389/fmars.2023.1196352

- Hieronymi et al. (2023). Ocean color atmospheric correction methods in view of usability for different optical water types. Front. Mar. Sci. 10, 1129876. https://doi.org/10.3389/fmars.2023.1129876 

- Bi et al. (2024). Supplementary dataset to the publication "Bi, S., and Hieronymi, M. (2024). Holistic optical water type classification for ocean, coastal, and inland waters. Limnology & Oceanography" [Data set]. Zenodo. https://doi.org/10.5281/zenodo.12803329