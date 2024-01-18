import numpy as np
import pandas as pd

"""
Cal functions for each spectrum
"""


def cal_AVW(wavelen, Rrs):
    """cal AVW for hyperspectra data from 400 to 800 nm"""
    try:
        if min(wavelen) > 400 or max(wavelen) < 800:
            raise ValueError("wavelen should between 400 and 800")
        wavelen_use = np.arange(400, 801, step=1)
        Rrs_use = np.interp(wavelen_use, wavelen, Rrs)
        AVW = np.sum(Rrs_use) / np.sum(Rrs_use / wavelen_use)
        return AVW
    except Exception as e:
        print("Error: ", e)


def cal_Area(wavelen, Rrs):
    """cal Area for the data have 443, 560, and 665 nm"""
    try:
        if min(wavelen) > 443 or max(wavelen) < 665:
            raise ValueError("wavelen should between 443 and 665")
        if wavelen.size < 3:
            raise ValueError("input length should be at least 3 bands")
        wavelen_rgb = np.array([443, 560, 665])
        Rrs_rgb = np.interp(wavelen_rgb, wavelen, Rrs)
        Area = np.trapz(x=wavelen_rgb, y=Rrs_rgb)
        return Area
    except Exception as e:
        print("Error: ", e)


def cal_NDI(wavelen, Rrs):
    """cal NDI at 560 and 665 nm"""
    try:
        if min(wavelen) > 560 or max(wavelen) < 665:
            raise ValueError("wavelen should between 560 and 665")
        if wavelen.size < 3:
            raise ValueError("input length should be at least 3 bands")
        wavelen_gb = np.array([560, 665])
        Rrs_gb = np.interp(wavelen_gb, wavelen, Rrs)
        NDI = (-np.diff(Rrs_gb)[0]) / (np.sum(Rrs_gb))
        return NDI
    except Exception as e:
        print("Error: ", e)


"""
Cal functions vectorized!
"""

# Shun (2023.12.10)
# Band inputs of sensors for AVW:
# MODIS_Aqua	412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859
# MODIS_Terra	412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859
# OLCI_S3A	    400, 412, 443, 490, 510, 560, 620, 665, 674, 682, 709, 754, 779, 866
# OLCI_S3B	    400, 412, 443, 490, 510, 560, 620, 665, 674, 681, 709, 754, 779, 866
# MERIS	        413, 443, 490, 510, 560, 620, 665, 681, 709, 754, 779, 865
# SeaWiFS	    412, 443, 490, 510, 555, 670, 865
# HawkEye	    412, 447, 488, 510, 556, 670, 752, 865
# OCTS	        412, 443, 490, 516, 565, 667, 862
# GOCI	        412, 443, 490, 555, 660, 680, 745, 865
# VIIRS_SNPP	410, 443, 486, 551, 671, 745, 862
# VIIRS_JPSS1	411, 445, 489, 556, 667, 746, 868
# VIIRS_JPSS2	411, 445, 488, 555, 671, 747, 868
# CZCS*	        443, 520, 550, 670
# MSI_S2A	    443, 492, 560, 665, 704, 740, 783, 835
# MSI_S2B	    442, 492, 559, 665, 704, 739, 780, 835
# OLI	        443, 482, 561, 655, 865
# Note that sensors with (*) don't have ~800 nm band will bias the AVW results

AVW_bands = {
    "MODIS_Aqua": [412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859],
    "MODIS_Terra": [412, 443, 469, 488, 531, 547, 555, 645, 667, 678, 748, 859],
    "OLCI_S3A": [400, 412, 443, 490, 510, 560, 620, 665, 674, 682, 709, 754, 779, 866],
    "OLCI_S3B": [400, 412, 443, 490, 510, 560, 620, 665, 674, 681, 709, 754, 779, 866],
    "MERIS": [413, 443, 490, 510, 560, 620, 665, 681, 709, 754, 779, 865],
    "SeaWiFS": [412, 443, 490, 510, 555, 670, 865],
    "HawkEye": [412, 447, 488, 510, 556, 670, 752, 865],
    "OCTS": [412, 443, 490, 516, 565, 667, 862],
    "GOCI": [412, 443, 490, 555, 660, 680, 745, 865],
    "VIIRS_SNPP": [410, 443, 486, 551, 671, 745, 862],
    "VIIRS_JPSS1": [411, 445, 489, 556, 667, 746, 868],
    "VIIRS_JPSS2": [411, 445, 488, 555, 671, 747, 868],
    "CZCS": [443, 520, 550, 670],
    "MSI_S2A": [443, 492, 560, 665, 704, 740, 783, 835],
    "MSI_S2B": [442, 492, 559, 665, 704, 739, 780, 835],
    "OLI": [443, 482, 655, 865],
}


def read_AVW_regression_coef():
    fn = "data/AVW_all_regression.txt"
    df = pd.read_csv(fn)
    return df


def convert_AVW_multi_to_hyper(AVW_multi, sensor="OLCI_S3A"):
    d = read_AVW_regression_coef()
    coef = d[d["variable"] == sensor][["0", "1", "2", "3", "4", "5"]].values.tolist()[0]
    AVW_hyper = np.zeros(AVW_multi.shape)
    for i in range(len(coef)):
        AVW_hyper += coef[i] * (AVW_multi**i)
    return AVW_hyper


def cal_AVW_vec(band, Rrs, sensor="OLCI_S3A"):
    """cal_AVW_vec
    Args:
        band (float, nm): the wavelength of input bands for `sensor`
        Rrs (float np array, sr^-1): a 3d np array (row, column, band) which should have the same len of `wavelen`
        sensor (string): string should match in `AVW_bands`
    """
    AVW_multi = np.sum(Rrs, axis=-1) / np.sum(Rrs / band[None, None, :], axis=-1)
    AVW = convert_AVW_multi_to_hyper(AVW_multi, sensor)
    return AVW


def cal_Area_vec(band, Rrs):
    """cal_Area_vec
    Args:
        bands (float, nm): the wavelength of input bands, should at least include R, G, and B bands
        Rrs (float np array, sr^-1), a 3d np array (row, column, band) which should have R G B bands
    """
    Area = np.trapz(x=band, y=Rrs, axis=-1)
    return Area


def cal_NDI_vec(Rrs):
    NDI = -np.diff(Rrs, axis=-1)[:, :, 0] / np.sum(Rrs, axis=-1)
    return NDI


"""
Other misc functions
"""


def trans_boxcox(x, lamb):
    """Box-Cox transformation

    Args:
        x (float): Input value
        lamb (float): One value for the lambda coefficient

    Returns:
        float: Transformed value
    """
    y = (x**lamb - 1) / lamb
    return y


def trans_boxcox_rev(y, lamb):
    """Reversed Box-Cox transformation

    Args:
        y (float): Input value
        lamb (float): One value for the lambda coefficient

    Returns:
        float: Transformed value
    """
    x = (y * lamb + 1) ** (1 / lamb)
    return x


if __name__ == "__main__":
    wavelen = np.arange(400, 801, 1)
    Rrs = np.random.rand(wavelen.size)

    print("AVW: ", cal_AVW(wavelen, Rrs))

    print("Area: ", cal_Area(wavelen, Rrs))

    print("NDI: ", cal_NDI(wavelen, Rrs))

    # import matplotlib.pyplot as plt

    # plt.plot(wavelen, Rrs)
    # plt.show()
