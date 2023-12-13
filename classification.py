import misc
import numpy as np
import pandas as pd
import netCDF4 as nc
from scipy.stats import chi2


def classification(wavelen, Rrs):
    """
    Main function of classification based on AVW, Area, NDI

    Args:
        wavelen (float array): wavelength in [nm]
        Rrs (float array): Remote-sensing reflectance in [sr^-1]

    Returns:
        float array: Memebership values for each OWT
    """
    AVW = misc.cal_AVW(wavelen, Rrs)
    Area = misc.cal_Area(wavelen, Rrs)
    NDI = misc.cal_NDI(wavelen, Rrs)

    """load centroids"""
    classInfo = load_centroids()
    mean_OWT = classInfo["mean_OWT"]
    covm_OWT = classInfo["covm_OWT"]
    lamBC = classInfo["lamBC"]
    # typeName = classInfo["typeName"]
    typeNumb = classInfo["typeNumb"]

    """do the classiifcaiton"""

    # Input vector for three optical variables
    x = np.array([AVW, misc.trans_boxcox(Area, lamBC), NDI])
    # Initialize distance array on type numer
    d = np.zeros(typeNumb, float)

    for i in range(typeNumb):
        y = mean_OWT[i, :]
        covm = covm_OWT[i, :, :]
        # Calculate squared mahalanobis distance
        covm_inv = np.linalg.inv(covm)
        z = (x - y) @ covm_inv * (x - y)
        d[i] = sum(z)

    # Calcualte membership values using Chi2 CDF on df = 3
    u = np.round(1 - chi2.cdf(d, df=len(x)), 6)

    return u

def calssification_vec(AVW, Area, NDI):
    
    """load centroids"""
    classInfo = load_centroids()
    mean_OWT = classInfo["mean_OWT"]
    covm_OWT = classInfo["covm_OWT"]
    lamBC = classInfo["lamBC"]
    # typeName = classInfo["typeName"]
    typeNumb = classInfo["typeNumb"]

    ABC = misc.trans_boxcox(Area, lamBC)

    x = np.array([AVW, ABC, NDI]).transpose(1, 2, 0)
    d = np.zeros((x.shape[0], x.shape[1], typeNumb))

    for i in range(typeNumb):
        y = mean_OWT[i, :][None, None, :]
        covm = covm_OWT[i, :, :]
        covm_inv = np.linalg.inv(covm)
        diff = x - y
        d[:,:,i] = np.einsum("...i,ij,...j->...", diff, covm_inv, diff)
    
    u = np.round(1 - chi2.cdf(d, df = x.shape[2]), 6)

    return u


def read_Rrs_demo():
    """read some demo Rrs data from R library"""
    fn = "./data/Rrs_demo.csv"
    df = pd.read_csv(fn)
    return df


def load_centroids():
    """
    load the centroids for classification
    For the "./data/OWT_centroids.nc" file, three variables included:
    - [mean] mean of each optical water type (OWT) at three dims
    - [covm] covariance matrix (3x3) of each OWT
    - [lamBC] lambda coeffcient for the Box-Cox transformation
    Dimensions: [AVW, Area, NDI]
    Note: Area in the nc lib is after Box-Cox transformation
    """
    fn = "./data/OWT_centroids.nc"
    ds = nc.Dataset(fn)
    mean_OWT = ds.variables["mean"][:]
    covm_OWT = ds.variables["covm"][:]
    lamBC = ds.variables["lamBC"][:].__float__()
    typeName = ds.getncattr("TypeName").split(", ")
    typeNumb = len(typeName)
    typeColName = ds.getncattr("TypeColorName").split(", ")
    typeColHex = ds.getncattr("TypeColorHex").split(", ")

    # mean_OWT[0,:] returns 1x3 matrix for the first OWT
    # covm_OWT[0,:,:] returns 3x3 matrix for the first OWT
    result = {
        "mean_OWT": mean_OWT,
        "covm_OWT": covm_OWT,
        "lamBC": lamBC,
        "typeName": typeName,
        "typeNumb": typeNumb,
        "typeColName": typeColName,
        "typeColHex": typeColHex,
    }
    return result


if __name__ == "__main__":
    df = read_Rrs_demo()

    # from plotnine import ggplot2, aes, geom_path
    # use plotnine pakcage (ggplot2-style) to show the demo spectra
    # print(
    #     ggplot(df)
    #     + aes(x="wavelen", y="Rrs", group="ID", color="type")
    #     + geom_path()
    # )

    ID_uniques = df.ID.unique()
    df_sub = df[df["ID"] == ID_uniques[0]]
    wavelen = df_sub.wavelen.values
    Rrs = df_sub.Rrs.values

    print(classification(wavelen, Rrs))
