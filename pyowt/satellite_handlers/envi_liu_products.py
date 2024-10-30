import numpy as np
import xarray as xr
import re

try:
    from osgeo import gdal, osr
    osgeo_installed = True
except ImportError:
    osgeo_installed = False

class ENVIImageReader:
    def __init__(self, img_file):
        if not osgeo_installed:
            raise ImportError("The 'osgeo' package is required but not installed. Please install it using 'pip install gdal'.")

        self.img_file = img_file
        self.dataset = gdal.Open(img_file, gdal.GA_ReadOnly)
        if self.dataset is None:
            raise FileNotFoundError(f"Unable to open image file: {img_file}")

    def get_band_info(self):
        """ Get number of bands and band names """
        band_count = self.dataset.RasterCount
        band_names = [
            self.dataset.GetRasterBand(i).GetDescription() or f"Band_{i}"
            for i in range(1, band_count + 1)
        ]
        return band_count, band_names

    def get_geotransform_info(self):
        """ Get geotransformation and projection information """
        geotransform = self.dataset.GetGeoTransform()
        projection = self.dataset.GetProjection()
        spatial_ref = osr.SpatialReference()
        spatial_ref.ImportFromWkt(projection)
        return geotransform, spatial_ref

    def to_xarray(self, band_prefix=None):
        """
        Convert image data to xarray Dataset.
        Optionally filter bands by prefix (e.g., 'rhos', 'Rrs').
        """
        band_count, band_names = self.get_band_info()
        geotransform, spatial_ref = self.get_geotransform_info()

        # Image dimensions
        ncols = self.dataset.RasterXSize
        nrows = self.dataset.RasterYSize

        # Create lon/lat coordinate arrays
        target_spatial_ref = spatial_ref.CloneGeogCS()
        # transform = osr.CoordinateTransformation(spatial_ref, target_spatial_ref)
        lon_coords = np.zeros((nrows, ncols))
        lat_coords = np.zeros((nrows, ncols))

        if spatial_ref.IsGeographic():
            print("This image file doesn't have a projection and is Geographic.")
            for i in range(nrows):
                for j in range(ncols):
                    lon = geotransform[0] + j * geotransform[1] + i * geotransform[2]
                    lat = geotransform[3] + j * geotransform[4] + i * geotransform[5]
                    lat_coords[i, j] = lat
                    lon_coords[i, j] = lon
        else:
            transform = osr.CoordinateTransformation(spatial_ref, target_spatial_ref)
            for i in range(nrows):
                for j in range(ncols):
                    x = geotransform[0] + j * geotransform[1] + i * geotransform[2]
                    y = geotransform[3] + j * geotransform[4] + i * geotransform[5]
                    lat, lon, _ = transform.TransformPoint(x, y)
                    lat_coords[i, j] = lat
                    lon_coords[i, j] = lon

        # for i in range(nrows):
        #     for j in range(ncols):
        #         x = geotransform[0] + j * geotransform[1] + i * geotransform[2]
        #         y = geotransform[3] + j * geotransform[4] + i * geotransform[5]
        #         lat, lon, _ = transform.TransformPoint(x, y)
        #         lat_coords[i, j] = lat
        #         lon_coords[i, j] = lon

        # Read band data and create xarray variables
        data_vars = {}
        mask = None
        for band_number in range(1, band_count + 1):
            band = self.dataset.GetRasterBand(band_number)
            band_array = band.ReadAsArray()
            band_name = band_names[band_number - 1]

            if band_prefix and not band_name.startswith(band_prefix):
                continue

            match = re.search(r'_(\d+)', band_name)
            wavelength = match.group(1) if match else 'unknown'

            if mask is None:
                mask = np.zeros_like(band_array, dtype=bool)
            mask |= (band_array != 0)

            data_var = xr.DataArray(
                band_array,
                dims=('y', 'x'),
                attrs={
                    'radiation_wavelength': wavelength,
                    'radiation_wavelength_unit': 'nm'
                }
            )
            data_vars[band_name] = data_var

        # Set pixels with all-zero values to NaN
        for band_name in data_vars:
            data_vars[band_name] = data_vars[band_name].where(mask, np.nan)

        # Create xarray Dataset with latitude/longitude coordinates
        xr_dataset = xr.Dataset(
            data_vars,
            coords={
                'x': ('x', np.arange(ncols)),
                'y': ('y', np.arange(nrows)),
                'lon': (('y', 'x'), lon_coords),
                'lat': (('y', 'x'), lat_coords),
            },
            attrs={
                'crs': spatial_ref.ExportToWkt(),
                'transform': geotransform
            }
        )
        xr_dataset['lat'].attrs = {
            'units': 'degrees_north',
            'standard_name': 'latitude',
            'long_name': 'Latitude'
        }
        xr_dataset['lon'].attrs = {
            'units': 'degrees_east',
            'standard_name': 'longitude',
            'long_name': 'Longitude'
        }

        return xr_dataset

    def save_as_netcdf(self, output_file, band_prefix=None):
        """ Save image data as a NetCDF file """
        xr_dataset = self.to_xarray(band_prefix=band_prefix)
        xr_dataset.to_netcdf(output_file, format='NETCDF4')
        print(f"Saved as NetCDF file: {output_file}")

# Example usage
if __name__ == "__main__":
    img_file = '/Users/apple/Satellite_data/Liu/504.shp/S3A_OL_1_EFR____20160429T013941_20160429T014241_20180205T153045_0180_003_288_2340_LR2_R_NT_002_x.Rrs.img'
    output_file = '/Users/apple/Satellite_data/Liu/gdal_test.nc'

    reader = ENVIImageReader(img_file)
    reader.save_as_netcdf(output_file, band_prefix='Rrs')
