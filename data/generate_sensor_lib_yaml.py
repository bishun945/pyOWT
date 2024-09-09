import yaml

sensor_AVW_bands_library = {
    "MODIS_Aqua": [412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859],
    "MODIS_Terra": [412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859],
    "OLCI_S3A": [400, 412, 443, 490, 510, 560, 620, 665, 674, 682, 709, 754, 779, 866],
    "OLCI_S3B": [400, 412, 443, 490, 510, 560, 620, 665, 674, 681, 709, 754, 779, 866],
    "MERIS": [413, 443, 490, 510, 560, 620, 665, 681, 709, 754, 779, 865],
    "SeaWiFS": [412, 443, 490, 510, 555, 670, 865],
    "HawkEye": [412, 447, 488, 510, 556, 670, 752, 867],
    "OCTS": [412, 443, 490, 516, 565, 667, 862],
    "GOCI": [412, 443, 490, 555, 660, 680, 745, 865],
    "VIIRS_SNPP": [410, 443, 486, 551, 671, 745, 862],
    "VIIRS_JPSS1": [411, 445, 489, 556, 667, 746, 868],
    "VIIRS_JPSS2": [411, 445, 488, 555, 671, 747, 868],
    "CZCS": [443, 520, 550, 670],
    "MSI_S2A": [443, 492, 560, 665, 704, 740, 783, 835],
    "MSI_S2B": [442, 492, 559, 665, 704, 739, 780, 835],
    "OLI": [443, 482, 561, 655, 865],
    "CMEMS_HROC_L3_optics": [443, 492, 560, 665, 704, 783, 865],
    "cmems_P1D400": [443, 490, 510, 560, 620, 665, 674, 682, 709, 779, 866],
    "AERONET_OC_1": [400, 412, 443, 490, 510, 560, 620, 665, 779, 866],
    "AERONET_OC_2": [412, 443, 490, 532, 551, 667, 870],
}

sensor_RGB_bands_library = {
    "MODIS_Aqua": [443, 555, 667],
    "MODIS_Terra": [443, 555, 667],
    "OLCI_S3A": [443, 560, 665],
    "OLCI_S3B": [443, 560, 665],
    "MERIS": [443, 560, 665],
    "SeaWiFS": [443, 555, 670],
    "HawkEye": [447, 556, 670],
    "OCTS": [443, 565, 667],
    "GOCI": [443, 555, 660],
    "VIIRS_SNPP": [443, 551, 671],
    "VIIRS_JPSS1": [445, 556, 667],
    "VIIRS_JPSS2": [445, 555, 671],
    "CZCS": [443, 550, 670],
    "MSI_S2A": [443, 560, 665],
    "MSI_S2B": [442, 559, 665],
    "OLI": [443, 561, 655],
    "CMEMS_HROC_L3_optics": [443, 560, 665],
    "cmems_P1D400": [443, 560, 665],
    "AERONET_OC_1": [443, 560, 665],
    "AERONET_OC_2": [443, 551, 667],
}

sensor_RGB_min_max = {
    "MODIS_Aqua": {"min": 412, "max": 667},
    "MODIS_Terra": {"min": 412, "max": 667},
    "OLCI_S3A": {"min": 400, "max": 866},
    "OLCI_S3B": {"min": 400, "max": 866},
    "MERIS": {"min": 413, "max": 865},
    "SeaWiFS": {"min": 412, "max": 865},
    "HawkEye": {"min": 412, "max": 867},
    "OCTS": {"min": 412, "max": 862},
    "GOCI": {"min": 412, "max": 865},
    "VIIRS_SNPP": {"min": 410, "max": 862},
    "VIIRS_JPSS1": {"min": 411, "max": 868},
    "VIIRS_JPSS2": {"min": 411, "max": 868},
    "CZCS": {"min": 443, "max": 670},
    "MSI_S2A": {"min": 443, "max": 835},
    "MSI_S2B": {"min": 442, "max": 835},
    "OLI": {"min": 443, "max": 865},
    "CMEMS_HROC_L3_optics": {"min": 443, "max": 865},
    "cmems_P1D400": {"min": 443, "max": 866},
    "AERONET_OC_1": {"min": 400, "max": 866},
    "AERONET_OC_2": {"min": 412, "max": 870},
}

AVW_regression_coef = "data/AVW_all_regression_800.txt"


lib_800 = {
    'sensor_AVW_bands_library': sensor_AVW_bands_library,
    'sensor_RGB_bands_library': sensor_RGB_bands_library,
    'sensor_RGB_min_max': sensor_RGB_min_max,
    'AVW_regression_coef': AVW_regression_coef
}


data = {
    'lib_800': lib_800
}

# Save to a YAML file
with open('data/sensor_band_library.yaml', 'w') as file:
    yaml.dump(data, file)


# with open('data/sensor_band_library.yaml', 'r') as file:
#     data = yaml.load(file, Loader=yaml.FullLoader)