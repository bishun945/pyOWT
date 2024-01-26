# **pyOWT**: python library for Optical Water Type classification

Version 0.31

by [Shun Bi](Shun.Bi@hereon.de) 

Last update 28.01.2024

Note: this repo is translated from the R repo [`OWT`](https://github.com/bishun945/OWT) for the water type classification and has been maintained independently from its original version.

# Install

Clone the whole repo and cd to the folder. 

Then, install the [requirements](/requirements.txt).

```console
pip install -r requirements.txt
```

# License

See the [LICENSE](/LICENSE) file.

# How to use it

Two classes, `OWT` and `OpticalVariables` are needed to perform the OWT classification.

```python
from OWT import OWT
from OpticalVariables import OpticalVariables

# first calculate three optical variables from Rrs
# `sensor` should be specified for satellite data
ov = OpticalVariables(Rrs=Rrs_data, band=Band_list, sensor=Sensor_str)
ov.run()

# feed data into classification
owt = OWT(AVW=ov.AVW, Area=ov.Area, NDI=ov.NDI)
owt.run_classification()

# show classification results
print(owt.type_str) 
```

Check the [example](/run_examples.py) file for more detailed demo runs:

1) Some hyperspectral Remote-sensing reflectance data simulated by Bi et al. (2023)

2) Satellite data with atmosphericly corrected by A4O (Hieronymi et al. 2023)

# Bug rerport

When you find any issues or bugs while running the module, please [open an issue](https://github.com/bishun945/pyOWT/issues) or directly contact [Shun Bi](Shun.Bi@hereon.de) with a reproducible script with data.

# References

- Bi et al. (2023). Bio-geo-optical modelling of natural waters. Front. Mar. Sci. 10, 1196352. https://doi.org/10.3389/fmars.2023.1196352

- Bi and Hieronymi (2023). Holistic optical water type classification for ocean, coastal, and inland waters (submitted).

- Hieronymi et al. (2023). Ocean color atmospheric correction methods in view of usability for different optical water types. Front. Mar. Sci. 10, 1129876. https://doi.org/10.3389/fmars.2023.1129876 
