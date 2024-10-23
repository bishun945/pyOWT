import xarray as xr
import numpy as np
import re
from pyowt.OpticalVariables import OpticalVariables
from pyowt.OWT import OWT

class cmems_products():

    def __init__(self, filename, sensor):
        """Reader of CMEMS products

        Args:
            filename (str): Filename of the CMEMS products.
            sensor (str): The sensor name of the product waveband configurations. 
                Only accepts CMEMS_BAL_HROC, CMEMS_BAL_NRT, and CMEMS_MED_MYINT

        Returns:
            A class of `reader_cmems_products` that includes
                - filename
                - filename_output: for generating output netcdf file
                - sensor
                - Rrs: np.array used to feed into `OpticalVariables` and `OWT`
                - ds_Rrs: xr.dataset that used to append OWT results and with wavelength attrs for SNAP usage
        """
        
        self.filename = filename
        self.filename_output = filename[:-3] + '_result.nc'
        self.sensor = sensor

        ds = xr.open_dataset(filename)

        if sensor == 'CMEMS_BAL_HROC':
            wavelen_sel =['RRS443', 'RRS492', 'RRS560', 'RRS665', 'RRS704', 'RRS740', 'RRS783', 'RRS865']
            wavelengths = [int(re.search(r'\d+', wl).group()) for wl in wavelen_sel]
        elif sensor == 'CMEMS_BAL_NRT' or sensor == 'CMEMS_MED_MYINT':
            wavelen_sel = ['RRS400', 'RRS412_5', 'RRS442_5', 'RRS490', 'RRS510', 'RRS560', 'RRS620', 'RRS665', 'RRS673_75', 'RRS681_25', 'RRS708_75', 'RRS778_75', 'RRS865']
            wavelengths = [int(re.search(r'\d+', wl).group()) for wl in wavelen_sel]
        else:
            raise ValueError('Please select CMEMS_BAL_HROC, CMEMS_BAL_NRT, or CMEMS_MED_MYINT for `sensor`.')

        if 'time' in ds.dims:
            ds_Rrs = ds[wavelen_sel].isel(time=0)
        else: 
            ds_Rrs = ds[wavelen_sel]

        # do the correction on negative values
        Rrs = ds_Rrs.to_array().transpose('lat', 'lon', 'variable').values
        Rrs[Rrs < 0] = np.nan

        self.Rrs = Rrs
        self.wavelen = wavelengths

        for i, wavelength in enumerate(wavelengths):
            variable_name = list(ds_Rrs.data_vars)[i] 
            ds_Rrs[variable_name].attrs['radiation_wavelength'] = wavelength
            ds_Rrs[variable_name].attrs['radiation_wavelength_unit'] = 'nm'

        self.ds_Rrs = ds_Rrs

        self.classification()

    def classification(self):       
        ov = OpticalVariables(Rrs=self.Rrs, band=self.wavelen, sensor=self.sensor)
        owt = OWT(ov.AVW, ov.Area, ov.NDI)
        self.ds_Rrs['type_idx'] = (('lat', 'lon'), owt.type_idx.astype(np.int32))
        self.ds_Rrs['type_idx'].attrs['description'] = 'Type index classification'
        self.ds_Rrs.to_netcdf(self.filename_output)

if __name__ == "__main__":

    fn = '/Users/apple/Satellite_data/CMEMS/20241011_cmems_obs-oc_blk_bgc-reflectance_nrt_l3-olci-300m_P1D.nc'
    cmems = cmems_products(fn, sensor='CMEMS_BAL_NRT')







