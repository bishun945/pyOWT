from pandas import read_csv
import numpy as np
import os

class OpticalVariables():

    def __init__(self, Rrs, band, sensor=None, AVW_regression_coef="data/AVW_all_regression.txt"):

        if not isinstance(Rrs, np.ndarray):

            raise TypeError("Input 'Rrs' should be np.ndarray type.")        

        # manipulate dimension of input Rrs as we always assume it is 3d nparray (raster-like)
        #   the wavelength should be on the shape[2] dim

        if np.ndim(Rrs) == 1:
            # here assume a signle spectrum
            self.Rrs = Rrs.reshape(1, 1, Rrs.shape[0])
        elif np.ndim(Rrs) == 2:
            # here assume shape[0] is sample and shape[1] is wavelength
            self.Rrs = Rrs.reshape(Rrs.shape[0], 1, Rrs.shape[1])
        elif np.ndim(Rrs) == 3:
            # here assume shape[2] is wavelength
            self.Rrs = Rrs
        else:
            raise ValueError("Input 'Rrs' should only have 1, 2, or 3 dims!")

        self.band = np.array(band)

        self.sensor = sensor

        self.AVW = None
        self.Area = None
        self.NDI = None

        # TODO: check the input band fits the selected sensor range
        # TODO: if AVW ends by 700 nm, this list has to be modified
        self.sensor_AVW_bands_library = {
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
        }

        self.sensor_RGB_bands_library = {
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
            "cmems_P1D400": [443, 560, 665]
        }

        # TODO: if AVW ends by 700 nm, this list has to be modified
        self.sensor_RGB_min_max = {
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
            "cmems_P1D400": {"min": 443, "max": 866}
        }
        
        self.available_sensors = ', '.join(self.sensor_AVW_bands_library.keys())

        if self.sensor is None:
            
            # the input Rrs are assumed to be hyperspectral
            self.spectral_attr = "hyper"
            ref_sensor_RGB_bands = [443, 560, 665]
            self.sensor_RGB_bands = [self.band[np.argmin(abs(self.band - v))] for v in ref_sensor_RGB_bands]
            self.sensor_band_min = 400
            self.sensor_band_max = 800
            self.AVW_conver_coef = [0, 1, 0, 0, 0, 0]

        else:
            
            if self.sensor not in self.sensor_AVW_bands_library.keys():
                
                raise ValueError(f"The input `sensor` couldn't be found in the library: {self.available_sensors}")

            # if `sensor` specifized, trigger `conver_AVW_multi_to_hyper` 
            self.spectral_attr = "multi"

            # define RGB bands, by B, R, G order
            ref_sensor_RGB_bands = self.sensor_RGB_bands_library[self.sensor]
            self.sensor_RGB_bands = [self.band[np.argmin(abs(self.band - v))] for v in ref_sensor_RGB_bands]

            # define min max ranges 
            self.sensor_band_min = self.sensor_RGB_min_max[self.sensor]["min"]
            self.sensor_band_max = self.sensor_RGB_min_max[self.sensor]["max"]

            # read coefficients to convert AVW_multi to AVW_hyper
            proj_root = os.path.dirname(os.path.abspath(__file__))
            fn = os.path.join(proj_root, AVW_regression_coef)
            d = read_csv(fn)
            self.AVW_convert_coef = d[d["variable"] == sensor][["0", "1", "2", "3", "4", "5"]].values.tolist()[0]


        # run calculation
        self.calculate_AVW()
        self.calculate_Area()
        self.calculate_NDI()

    class ArrayWithAttributes:
        '''This subclass add attributes to np.array

        Outputs of `OpticalVariables` (AVW, Area, NDI) can have attributes indicating
        some key features during the calculation. For example, we can know AVW starts 
        from 400 to 800 nm while sometimes we need to know it is to 700 nm.

        Examples:

            A = ArrayWithAttributes(np.array([1, 2, 3]), author='Shun')
            print(A)        # Output: [1 2 3]
            print(A.author) # Output: Shun
        '''
        def __init__(self, array, **attributes):
            self.array = np.asarray(array)
            self.__dict__.update(attributes)

        def __getitem__(self, item):
            return self.array[item]

        def __setitem__(self, key, value):
            self.array[key] = value

        def __repr__(self):
            return repr(self.array)

        def __str__(self):
            return str(self.array)

        def __getattr__(self, name):
            return getattr(self.array, name)

        def __array__(self):
            return self.array


    def convert_AVW_multi_to_hyper(self):
        self.AVW_hyper = np.zeros(self.AVW_multi.shape)
        for i in range(len(self.AVW_convert_coef)):
            self.AVW_hyper += self.AVW_convert_coef[i] * (self.AVW_multi**i)


    def calculate_AVW(self):
        idx_for_AVW = (self.band >= self.sensor_band_min) & (self.band <= self.sensor_band_max)
        bands_for_AVW = self.band[idx_for_AVW]
        Rrs_for_AVW = self.Rrs[:, :, idx_for_AVW]
        self.AVW_init = np.sum(Rrs_for_AVW, axis=-1) / np.sum(Rrs_for_AVW / bands_for_AVW[None, None, :], axis=-1)

        if self.spectral_attr == "hyper":
            self.AVW_hyper = self.AVW_init
        else:
            self.AVW_multi = self.AVW_init
            self.convert_AVW_multi_to_hyper()
        
        self.AVW = self.AVW_hyper


    def calculate_Area(self):
        bands_for_Area = np.array(self.sensor_RGB_bands)
        Rrs_for_Area = self.Rrs[:, :, np.where(np.isin(self.band, bands_for_Area))[0]]
        self.Area = np.trapz(x=bands_for_Area, y=Rrs_for_Area, axis=-1)


    def calculate_NDI(self):
        Rrs_for_NDI = self.Rrs[:, :, np.where(np.isin(self.band, self.sensor_RGB_bands[1:]))[0]] # [1:] for G and R
        self.NDI = -np.diff(Rrs_for_NDI, axis=-1)[:, :, 0] / np.sum(Rrs_for_NDI, axis=-1)


    def run(self):
        import warnings
        warnings.warn(
            "No need to calculate via 'ov.run()'. "
            "The optical variables will be calculated directly once you create this instance. "
            "This function is deprecated and will be removed in the future versions.",
            DeprecationWarning,
            stacklevel=2
        )

        self.calculate_AVW()
        self.calculate_Area()
        self.calculate_NDI()
    


if __name__ == "__main__":

    # ov = OpticalVariables(Rrs=1, band=1, sensor="OLCI_S3B")
    # print(ov.sensor_RGB_bands)
    band = np.arange(400, 801, step = 2)
    # Rrs = np.random.normal(loc = 0, scale = 1, size = len(band))
    Rrs = np.full(len(band), 1)
    ov = OpticalVariables(Rrs=Rrs, band=band)
    print(ov.AVW)

