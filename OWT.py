import numpy as np
import netCDF4 as nc
from scipy.stats import chi2

class OWT():

    def __init__(self, AVW, Area, NDI):
        """Initialize three optical variables for spectral classification

        Args:
            AVW (np.array, ndim <= 2): Apparent Visible Wavelength 400-800 nm
            Area (np.array, ndim <= 2): Trapezoidal area of Rrs at RGB bands
            NDI (np.array, ndim <= 2): Normalized Difference Index of Rrs at G and B bands
        """

        self.AVW = AVW
        self.Area = Area
        self.NDI = NDI

        if any(np.ndim(arr) > 2 for arr in [self.AVW, self.Area, self.NDI]):

            raise ValueError("AVW, Area, and NDI with more than two dims are not supported!")

        self.AVW = np.atleast_2d(self.AVW)
        self.Area = np.atleast_2d(self.Area)
        self.NDI = np.atleast_2d(self.NDI)

        if not (self.AVW.shape == self.Area.shape == self.NDI.shape):

            raise ValueError("The shapes of AVW, Area, and NDI must be the same!")


        # load pre-trained centroids
        classInfo = self.load_centroids()
        self.mean_OWT = classInfo["mean_OWT"]
        self.covm_OWT = classInfo["covm_OWT"]
        self.lamBC = classInfo["lamBC"]
        self.typeName = classInfo["typeName"]
        self.typeNumb = classInfo["typeNumb"]
        self.typeColor = classInfo["typeColHex"]
        
        dict_idx_name = {i: self.typeName[i] for i in range(self.typeNumb)} # for mapping
        dict_idx_name[-1] = "NaN" # once not classifiable
        self.dict_idx_name = {key: dict_idx_name[key] for key in sorted(dict_idx_name)}
        
        dict_idx_color = {i: self.typeColor[i] for i in range(self.typeNumb)} # for mapping
        dict_idx_color[-1] = "#808080" # once not classifiable
        self.dict_idx_color = {key: dict_idx_color[key] for key in sorted(dict_idx_color)}

        
        # placeholder
        self.u = np.full(self.AVW.shape + (self.typeNumb,), None)
        self.type_idx = np.full(self.AVW.shape, None)
        self.type_str = np.full(self.AVW.shape, None)

        # TODO: use Martin's level to define classifiability
        self.classifiability = np.full(self.AVW.shape, None) 

    def update_type_idx(self):
        """Update the type (index of `typeName`) based on the current membership value. 
        The function will be updated once `run_classification` is performed.
        OWT will be asigned to -1 if all memberships are zero.
        """
        if self.u is not None:
            idx_max = np.argmax(self.u, axis=-1)
            self.type_idx = idx_max
            mask_all_zero = np.all(self.u <= 0, axis=-1)
            self.type_idx[mask_all_zero] = -1
            mask_all_nan = np.all(np.isnan(self.u), axis=-1)
            self.type_idx[mask_all_nan] = -1
        else:
            raise ValueError("Membership values have not been calculated! Run the classification first")


    def update_type_str(self):
        """Update the type (name in `typeName`) based on `self.type_idx`
        """
        if self.u is not None:
            vectorized_map = np.vectorize(lambda x: self.dict_idx_name.get(x, ''))
            self.type_str = vectorized_map(self.type_idx)
        else:
            raise ValueError("Membership values have not been calculated! Run the classification first")


    def run_classification(self):
        """Run the classification procedure

        Returns:
            np.array, ndim <= 2: membership values for pre-defined 10 types
        """

        self.ABC = self.trans_boxcox(self.Area, self.lamBC)

        x = np.array([self.AVW, self.ABC, self.NDI]).transpose(1, 2, 0)
        d = np.zeros((x.shape[0], x.shape[1], self.typeNumb))

        for i in range(self.typeNumb):

            y = self.mean_OWT[i, :][None, None, :]
            covm = self.covm_OWT[i, :, :]
            covm_inv = np.linalg.inv(covm)
            diff = x - y 
            d[:, :, i] = np.einsum("...i,ij,...j->...", diff, covm_inv, diff)
        
        u = np.round(1 - chi2.cdf(d, df=x.shape[2]), 6)

        self.u = u
        self.update_type_idx()
        self.update_type_str()

        return u
    
    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    owt = OWT(AVW = [560, 400], Area = [1, 0.9], NDI = [0.2, 0.0])
    print(owt.type_idx)
    print(owt.type_str)

    """ 
    (1) Test for simulated Rrs data (Bi et al. 2023 model)
    """

    import pandas as pd

    d0 = pd.read_csv("./data/Rrs_demo.csv")
    d = d0.pivot_table(index='SampleID', columns='wavelen', values='Rrs')
    owt_train = d0[d0['wavelen']==350].sort_values(by="SampleID").type.values

    Rrs = d.values.reshape(d.shape[0], 1, d.shape[1])
    band = d.columns.tolist()

    from OpticalVariables import OpticalVariables

    ov = OpticalVariables(Rrs=Rrs, band=band)
    ov.run()

    owt = OWT(ov.AVW, ov.Area, ov.NDI)
    owt.run_classification()

    owt_result = owt.type_str.flatten()

    print(owt_train)
    print(owt_result)


    """
    (2) Test for satellite data (A4O results)
    """

    # from netCDF4 import Dataset as ds
    # import re

    # def str_match(input, pattern, ind=False):
    #     # input:   list of strings
    #     # pattern: the string to be matched
    #     # ind:     (boolean) True will return the index in the input list; otherwise, the matched strings
    #     pattern = re.compile(pattern)
    #     if ind:
    #         indices = [i for i in range(len(input)) if pattern.match(input[i])]
    #     else:
    #         indices = [v for v in input if pattern.match(v)]
    #     return indices

    # # this nc file is ~327MB, hard to be shared via email...
    # fn = "/Users/Bi/Documents/GitHub/OWT/Paper/Apply_framework_to_image_subset/GermanBight_20160720T093421_subset.nc"
    # d = ds(fn, mode="r")
    # name_var = list(d.variables.keys())
    # var_A4O_Rrs = str_match(name_var, "A4O_Rrs_\d+$")
    # wavelen_A4O_Rrs = np.array([float(i.split("_")[-1]) for i in var_A4O_Rrs])
    # Rrs_A4O = np.array([d.variables[x][:] for x in var_A4O_Rrs]).transpose(1, 2, 0)

    # ## the required variables are:
    # # >>> Rrs_A4O.shape
    # # (1006, 1509, 16) # a 3d np.array where 1006 and 1509 for lon-lat coord and 16 is for sixteen bands
    # # >>> wavelen_A4O_Rrs
    # # array([ 400.,  412.,  442.,  490.,  510.,  560.,  620.,  665.,  674.,
    # #         681.,  709.,  754.,  779.,  865.,  885., 1020.])

    # from OpticalVariables import OpticalVariables

    # ov = OpticalVariables(Rrs=Rrs_A4O, band=wavelen_A4O_Rrs, sensor="OLCI_S3A")
    # ov.run()

    # owt = OWT(ov.AVW, ov.Area, ov.NDI)
    # owt.run_classification()

    # import matplotlib.pyplot as plt
    # import matplotlib.colors as mcolors

    # cmap = mcolors.ListedColormap(owt.dict_idx_color.values())
    # bounds = np.arange(-1.5, 10.5)
    # norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

    # plt.figure(figsize=(8, 6))

    # # plt.imshow(owt.type_idx)

    # plt.imshow(owt.type_idx, cmap=cmap, norm=norm)
    # cbar = plt.colorbar(ticks = np.arange(-1, 10), orientation="horizontal")
    # cbar.ax.set_xticklabels(owt.dict_idx_name.values())

    # plt.show()
    # plt.savefig("type_owt.png", dpi=300, bbox_inches="tight")

    # plt.close()
