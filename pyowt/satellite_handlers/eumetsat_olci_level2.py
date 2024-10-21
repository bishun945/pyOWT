import xarray as xr
import zipfile
import tempfile
from lxml import etree
import os
from datetime import date
import numpy as np
from pyowt.OpticalVariables import OpticalVariables
from pyowt.OWT import OWT

class eumetsat_olci_level2:

    def __init__(self, filename, sensor='OLCI_S3A', save_path=None, save=True):

        self.filename = filename
        self.sensor = sensor

        if save_path is None:
            self.save_path = os.path.dirname(self.filename)
        else:
            self.save_path = save_path

        self.create_temporary_dir()

        try:
            self.parse_xml()
            self.apply_flag()
            self.read_geo_coordinates()
            self.read_reflectance()
            self.classification()
            self.prepare_nc()
            if save:
                self.save_result()
        finally:
            self.temp_dir.cleanup()
            self.zip_ref.close()

    def create_temporary_dir(self):
        # product path - unzip in a temporary directory
        zip_path = self.filename
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name
        self.zip_ref = zipfile.ZipFile(zip_path, 'r')
        # the temporary directory can deleted as:
        #   self.temp_dir.cleanup()
        #   self.zip_ref.close()
        self.zip_ref.extractall(self.temp_path)
        self.basename = os.path.basename(os.path.splitext(os.path.basename(zip_path))[0])

    @staticmethod
    def find_file(directory, filename):
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
        return None

    def parse_xml(self):
        self.path_xfdu = self.find_file(self.temp_path, 'xfdumanifest.xml')
        self.path = os.path.dirname(self.path_xfdu)
        tree = etree.parse(self.path_xfdu)
        namespaces = tree.getroot().nsmap
        wavelengths = tree.xpath('//sentinel3:centralWavelength/text()', namespaces=namespaces)
        wavelengths = [float(wl) for wl in wavelengths]
        bandnames = tree.xpath('//sentinel3:band/@name', namespaces=namespaces)

        self.wavelengths = wavelengths
        self.bandnames = bandnames

    def apply_flag(self):
        ds = xr.open_dataset(os.path.join(self.path, 'wqsf.nc'))
        wqsf = ds['WQSF']
        attrs = wqsf.attrs

        flag_masks = attrs.get('flag_masks', [])
        flag_meanings = attrs.get('flag_meanings', '').split()

        # WATER or INLAND_WATER
        WATER_mask = flag_masks[flag_meanings.index('WATER')]
        INLAND_WATER_mask = flag_masks[flag_meanings.index('INLAND_WATER')]
        water_mask = (wqsf & WATER_mask) | (wqsf & INLAND_WATER_mask)

        # Initialize mask as True for everywhere
        final_mask = water_mask.astype(bool)

        # Exclude the listed flags
        exclude_flags = [
            'CLOUD', 'CLOUD_AMBIGUOUS', 'CLOUD_MARGIN', 'INVALID', 'COSMETIC',
            'SATURATED', 'SUSPECT', 'HISOLZEN', 'HIGHGLINT', 'SNOW_ICE',
            'AC_FAIL', 'WHITECAPS', 'ADJAC', 'RWNEG_O2', 'RWNEG_O3', 
            'RWNEG_O4', 'RWNEG_O5', 'RWNEG_O6', 'RWNEG_O7', 'RWNEG_O8'
        ]

        for flag in exclude_flags:
            mask = flag_masks[flag_meanings.index(flag)]
            final_mask &= ~(wqsf & mask).astype(bool)

        WQSF_REFLECTANCE_RECOM = final_mask.astype(int)

        self.WQSF_REFLECTANCE_RECOM = WQSF_REFLECTANCE_RECOM

    def read_geo_coordinates(self):
        ds = xr.open_dataset(os.path.join(self.path, 'geo_coordinates.nc'))
        self.lon = ds['longitude']
        self.lat = ds['latitude']

    def read_reflectance(self):
        Ref_list = []
        for i, bandname in enumerate(self.bandnames):
            nc_file_path = os.path.join(self.path, f"{bandname}_reflectance.nc")

            if os.path.exists(nc_file_path):
                ds = xr.open_dataset(nc_file_path)
                Ref_data = ds[f"{bandname}_reflectance"]
                Ref_data.attrs['radiation_wavelength'] = self.wavelengths[i]
                Ref_data.attrs['radiation_wavelength_unit'] = 'nm'
                Ref_data = Ref_data.assign_coords(longitude = self.lon, latitude = self.lat)

                Ref_list.append(Ref_data)
            else:
                print(f"File {nc_file_path} does not exist.")

        ds_new = xr.merge(Ref_list)

        reflectance_vars = np.array([ds_new[f"{bandname}_reflectance"].data for bandname in self.bandnames]).transpose(1, 2, 0)
        Rrs_vars = reflectance_vars / np.pi
        
        self.Rrs_vars = Rrs_vars
        self.ds_new = ds_new
    
    def classification(self):
        ov = OpticalVariables(Rrs=self.Rrs_vars, band=self.wavelengths, sensor=self.sensor)
        owt = OWT(ov.AVW, ov.Area, ov.NDI)
        self.ov = ov
        self.owt = owt
    
    def prepare_nc(self):
        self.ds_new = self.ds_new.drop_vars([f"{bandname}_reflectance" for bandname in self.bandnames])

        today = date.today()

        self.ds_new.attrs = {
            'Description': 'This dataset contains reflectance data and flags for ocean color remote sensing.',
            'Source': os.path.basename(self.path),
            "Author": "Shun Bi, shun.bi@outlook.com",
            "CreatedDate": today.strftime("%d/%m/%Y"),
        }

        self.ds_new['flag'] = (['rows', 'columns'], self.WQSF_REFLECTANCE_RECOM.data.astype(np.int32))

        self.ds_new['type_idx'] = (
            ['rows', 'columns'], 
            self.owt.type_idx.astype(np.int32),
            {'Description': (
                'Index value for optical water types. '
                '-1: No data; '
                '0: OWT 1; '
                '1: OWT 2; '
                '2: OWT 3a; '
                '3: OWT 3b; '
                '4: OWT 4a; '
                '5: OWT 4b; '
                '6: OWT 5a; '
                '7: OWT 5b; '
                '8: OWT 6; '
                '9: OWT 7; '
            )}
        )

        AVW_clipped = np.where((self.owt.AVW >= 400) & (self.owt.AVW <= 800), self.owt.AVW, np.nan)

        self.ds_new['AVW'] = (
            ['rows', 'columns'], 
            AVW_clipped.astype(np.float32),
            {'Description': 'Apparent Visible Wavelength 400-800 nm'}
        )

        self.ds_new['Area'] = (
            ['rows', 'columns'], 
            self.owt.Area.astype(np.float32),
            {'Description': 'Trapezoidal area of Rrs at RGB bands'}
        )

        NDI_clipped = np.where((self.owt.NDI >= -1) & (self.owt.NDI <= 1), self.owt.NDI, np.nan)
        self.ds_new['NDI'] = (
            ['rows', 'columns'], 
            NDI_clipped.astype(np.float32),
            {'Description': 'Normalized Difference Index of Rrs at G and B bands'}
        )

        # save membership matrix
        self.u = self.owt.u
        self.utot = self.owt.utot

        self.ds_new['utot'] = (
            ['rows', 'columns'], 
            self.utot.astype(np.float32),
            {'Description': 'Total membership values of ten water types'}
        )

    def save_result(self):
        encoding = {
            var: {
                'zlib': True,
                'complevel': 5,
                'shuffle': True
            }
            for var in list(self.ds_new.data_vars)
        }

        self.ds_new.to_netcdf(os.path.join(self.save_path, f"{self.basename}_owt.nc"), encoding=encoding)


if __name__ == "__main__":

    fn = '/Users/apple/Satellite_data/S3B_OL_2_WFR____20220703T075301_20220703T075601_20220704T171729_0179_067_363_2160_MAR_O_NT_003.SEN3.zip'
    eumetsat = eumetsat_olci_level2(filename=fn, sensor='OLCI_S3B')