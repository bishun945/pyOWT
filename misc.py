import numpy as np


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
