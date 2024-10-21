import numpy as np
import xarray as xr
from types import SimpleNamespace
from scipy.stats import chi2

import os

class OWT():

    def __init__(self, AVW=None, Area=None, NDI=None, version='v02', thres_u=0.0001):
        """Initialize three optical variables for spectral classification

        Args:
            AVW (np.array, ndim <= 2): Apparent Visible Wavelength 400-800 nm
            Area (np.array, ndim <= 2): Trapezoidal area of Rrs at RGB bands
            NDI (np.array, ndim <= 2): Normalized Difference Index of Rrs at G and B bands
            version (str): Version of the classification centroids. Default as 'v01'.
                Two version are now included:
                    - v01: original from Bi and Hieronymi (2024) paper
                    - v02: revised version of v01 which covariance matrix were shrinked
            thre_u (numeric): the threshold of membership (u) to mask out non-classifiable inputs.
                Default as 0.0001 from Hieronymi et al. (2023) Table 3.

        Return:
            u (np.array, ndim = 3): the first and second dims are from AVW or np.atleast_2d(AVW).
              Its last dim is water type (N = 10)
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

        # set the threshold of membership values for classifiable results
        self.thres_u = thres_u

        # load pre-trained centroids
        self.version = version
        self.classInfo = self.load_centroids_version(version=self.version)
        # classInfo = self.load_centroids()
        # self.mean_OWT = classInfo["mean_OWT"]
        # self.covm_OWT = classInfo["covm_OWT"]
        # self.lamBC = classInfo["lamBC"]
        # self.typeName = classInfo["typeName"]
        # self.typeNumb = classInfo["typeNumb"]
        # self.typeColor = classInfo["typeColHex"]
        
        dict_idx_name = {i: self.classInfo.typeName[i] for i in range(self.classInfo.typeNumb)} # for mapping
        dict_idx_name[-1] = "NaN" # once not classifiable
        self.dict_idx_name = {key: dict_idx_name[key] for key in sorted(dict_idx_name)}
        
        dict_idx_color = {i: self.classInfo.typeColHex[i] for i in range(self.classInfo.typeNumb)} # for mapping
        dict_idx_color[-1] = "#808080" # once not classifiable
        self.dict_idx_color = {key: dict_idx_color[key] for key in sorted(dict_idx_color)}

        
        # placeholder
        self.u = np.full(self.AVW.shape + (self.classInfo.typeNumb,), None)
        self.type_idx = np.full(self.AVW.shape, None)
        self.type_str = np.full(self.AVW.shape, None)

        # run classification
        self.run_classification()

        # Use Hieronymi et al. (2023) Table 3 to mask out non-classifiable inputs
        # if utot < thres_u, classifiability = 0; else = 1
        self.classifiability = np.full(self.AVW.shape, 1) 
        self.classifiability[self.type_idx == -1] = 0


    def update_type_idx(self):
        """Update the type (index of `typeName`) based on the current membership value. 
        The function will be updated once `run_classification` is performed.
        OWT will be asigned to -1 if all memberships are zero or below the threshold `thres_u`.
        """
        if self.u is not None:
            idx_max = np.argmax(self.u, axis=-1)
            self.type_idx = idx_max
            mask_all_zero = np.all(self.u <= 0, axis=-1)
            self.type_idx[mask_all_zero] = -1
            mask_all_nan = np.all(np.isnan(self.u), axis=-1)
            self.type_idx[mask_all_nan] = -1
            mask_blt_thres = np.all(self.utot <= self.thres_u, axis=-1)
            self.type_idx[mask_blt_thres] = -1
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
            np.array, ndim <= 3: membership values for pre-defined 10 types
        """

        import warnings
        warnings.warn(
            "No need to calculate via 'owt.run_classification()'. "
            "The classification will be performed directly once you create this instance. "
            "This function is deprecated and will be removed in the future versions.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.ABC = self.trans_boxcox(self.Area, self.classInfo.lamBC)

        x = np.array([self.AVW, self.ABC, self.NDI]).transpose(1, 2, 0)
        d = np.zeros((x.shape[0], x.shape[1], self.classInfo.typeNumb))

        for i in range(self.classInfo.typeNumb):

            y = self.classInfo.mean_OWT[i, :][None, None, :]
            covm = self.classInfo.covm_OWT[:, :, i]
            covm_inv = np.linalg.inv(covm)
            diff = x - y 
            d[:, :, i] = np.einsum("...i,ij,...j->...", diff, covm_inv, diff)
        
        u = np.round(1 - chi2.cdf(d, df=x.shape[2]), 6)

        self.u = u
        self.utot = np.sum(u, axis=-1)

        self.update_type_idx()
        self.update_type_str()

    def load_centroids_version(self, version):
        """
        load the centroids for classification
        For the "data/OWT_centroids.nc" file, three variables included:
        - [mean] mean of each optical water type (OWT) at three dims
        - [covm] covariance matrix (3x3) of each OWT
        - [lamBC] lambda coeffcient for the Box-Cox transformation
        Dimensions: [AVW, Area, NDI]
        Note: Area in the nc lib is after Box-Cox transformation
        """
        proj_root = os.path.dirname(os.path.abspath(__file__))
        fn = os.path.join(proj_root, f"data/{version}/OWT_centroids.nc")
        ds = xr.open_dataset(fn)
        mean_OWT = ds['mean'].values
        covm_OWT = ds['covm'].values
        lamBC = ds.attrs['lamBC']
        typeName = ds.attrs['TypeName'].split(", ")
        typeNumb = len(typeName)
        typeColName = ds.attrs['TypeColorName'].split(", ")
        typeColHex = ds.attrs['TypeColorHex'].split(", ")

        # mean_OWT[0,:] returns 1x3 matrix for the first OWT
        # covm_OWT[:,:,0] returns 3x3 matrix for the first OWT
        result = {
            "mean_OWT": mean_OWT,
            "covm_OWT": covm_OWT,
            "lamBC": lamBC,
            "typeName": typeName,
            "typeNumb": typeNumb,
            "typeColName": typeColName,
            "typeColHex": typeColHex,
        }
        result = SimpleNamespace(**result)

        return result
    
    @staticmethod
    def load_centroids_dep():
        """
        WARNING: This function has been deprecated, please use `load_centroids_version()'
        load the centroids for classification
        For the "data/OWT_centroids.nc" file, three variables included:
        - [mean] mean of each optical water type (OWT) at three dims
        - [covm] covariance matrix (3x3) of each OWT
        - [lamBC] lambda coeffcient for the Box-Cox transformation
        Dimensions: [AVW, Area, NDI]
        Note: Area in the nc lib is after Box-Cox transformation
        """
        import netCDF4 as nc
        import warnings
        warnings.warn(
            "This function has been deprecated and will be deleted in the future, "
            "please use `load_centroids_version()'",
            DeprecationWarning,
            stacklevel=2
        )
        proj_root = os.path.dirname(os.path.abspath(__file__))
        fn = os.path.join(proj_root, "data/v01/OWT_centroids.nc")
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
        mask = (x > 0) & np.isfinite(x)
        y = np.full_like(x, np.nan)
        y[mask] = (x[mask]**lamb - 1) / lamb
        # y = (x**lamb - 1) / lamb
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
    print(owt.u.shape[0:2])

