import xarray as xr
import numpy as np
import os
import re
import dask

from pyowt.OpticalVariables import OpticalVariables
from pyowt.OWT import OWT

def owt_classification_on_chunk(rrs_chunk, band_wavelengths, sensor_name):
    """
    A wrapper function to run the complete OWT classification process on a data chunk.
    This function is called by xarray.apply_ufunc for each chunk.
    """
    if np.all(np.isnan(rrs_chunk)):
        nan_shape = rrs_chunk.shape[:-1]  # Get lat, lon shape
        return (np.full(nan_shape, np.nan, dtype=np.float32),
                np.full(nan_shape, np.nan, dtype=np.float32),
                np.full(nan_shape, np.nan, dtype=np.float32),
                np.full(nan_shape, -1, dtype=np.int32))

    # Calculate optical variables from the Rrs chunk.
    ov = OpticalVariables(Rrs=rrs_chunk, band=band_wavelengths, sensor=sensor_name)
    
    # Perform the OWT classification.
    owt = OWT(ov.AVW, ov.Area, ov.NDI)
    
    # Clip the optical variable values to their valid ranges.
    avw_clipped = np.where((owt.AVW >= 400) & (owt.AVW <= 800), owt.AVW, np.nan)
    ndi_clipped = np.where((owt.NDI >= -1) & (owt.NDI <= 1), owt.NDI, np.nan)

    return (avw_clipped.astype(np.float32), 
            owt.Area.astype(np.float32), 
            ndi_clipped.astype(np.float32), 
            owt.type_idx.astype(np.int32))

class LakeCCIProcessor:
    """
    A class to process a single ESA Lake CCI NetCDF file.
    It applies the OWT classification using Dask for out-of-core processing
    and outputs a single, complete NetCDF file with the results.
    """
    def __init__(
        self,
        filename,
        output_dir=None,
        chunk_sizes={"lat": 1000, "lon": 1000},
        keep_rrs_bands=True,
        verbose=True,
    ):
        """
        Initializes and runs the processing workflow.

        Args:
            filename (str): Path to the input Lake CCI NetCDF file.
            chunk_sizes (dict): A dictionary specifying the chunk sizes for Dask.
            keep_rrs_bands (bool): If True, the output file will include the Rrs bands. 
                                   If False (default), only classification results are saved.
        """
        if not os.path.exists(filename):
            print(f"Error: Input file not found at '{filename}'.")
            return

        self.filename = filename
        if output_dir is None:
            self.output_filename = self.filename.replace('.nc', '_owt_result.nc')
        else:
            basename = os.path.basename(self.filename)
            self.output_filename = os.path.join(output_dir, basename.replace('.nc', '_owt_result.nc'))

        self.chunk_sizes = chunk_sizes
        self.keep_rrs_bands = keep_rrs_bands
        self.verbose = verbose

        self.sensor = 'LakeCCI-MERIS'
        self.predefined_bands = {'LakeCCI-MERIS': [413, 443, 490, 510, 560, 620, 665, 681, 709, 754, 779, 885]}

        self.process()

    def process(self):
        """
        Executes the main data processing workflow.
        """
        required_wavelengths = self.predefined_bands[self.sensor]

        with xr.open_dataset(self.filename, chunks=self.chunk_sizes) as ds:
            available_rw_vars = [var for var in ds.data_vars if var.startswith('Rw') and var[2:].isdigit()]
            available_wavelength_map = {int(re.search(r'\d+', var).group()): var for var in available_rw_vars}
            available_wavelengths = np.array(list(available_wavelength_map.keys()))

            wavelen_sel, final_wavelengths = [], []
            for req_wl in required_wavelengths:
                closest_idx = np.argmin(np.abs(available_wavelengths - req_wl))
                closest_wl = available_wavelengths[closest_idx]
                wavelen_sel.append(available_wavelength_map[closest_wl])
                final_wavelengths.append(closest_wl)

            # the input is called water reflectance not rrs?
            ds_rw = ds[wavelen_sel]
            ds_rrs = ds_rw / np.pi

            # set all required attributes for Rrs bands
            for var_name in ds_rrs.data_vars:
                # Use the actual wavelength found for the attributes
                wavelength = available_wavelength_map[final_wavelengths[wavelen_sel.index(var_name)]]
                attrs = ds_rrs[var_name].attrs
                attrs['long_name'] = f"Remote sensing reflectance at {wavelength} nm"
                attrs['units'] = 'sr-1'
                attrs['radiation_wavelength'] = float(wavelength[2:])
                attrs['radiation_wavelength_unit'] = 'nm'

            rrs_dask_array_unchunked_vars = ds_rrs.to_array(dim='variable')
            rrs_dask_array = rrs_dask_array_unchunked_vars.chunk({**self.chunk_sizes, 'variable': -1})
            rrs_dask_array = rrs_dask_array.transpose('time', 'lat', 'lon', 'variable').isel(time=0, drop=True)

            if self.verbose:
                print("Setting up Dask computation graph...")

            avw, area, ndi, type_idx = xr.apply_ufunc(
                owt_classification_on_chunk,
                rrs_dask_array,
                input_core_dims=[["variable"]],
                output_core_dims=[[], [], [], []],
                exclude_dims=set(("variable",)),
                dask="parallelized",
                output_dtypes=[np.float32, np.float32, np.float32, np.int32],
                kwargs={
                    "band_wavelengths": final_wavelengths,
                    "sensor_name": self.sensor,
                },
            )

            if self.verbose:
                print("Building the final output dataset...")
            # Conditionally build the output dataset
            if self.keep_rrs_bands:
                # Start with the newly created Rrs variables
                ds_out = ds_rrs.isel(time=0, drop=True)
            else:
                # Start with an empty dataset containing only coordinates
                ds_out = xr.Dataset(coords=ds_rrs.coords)

            # Add the new classification variables.
            ds_out['type_idx'] = type_idx
            ds_out['AVW'] = avw
            ds_out['Area'] = area
            ds_out['NDI'] = ndi

            # Set attributes for the new variables.
            ds_out['type_idx'].attrs = {'long_name': 'Optical Water Type Index', '_FillValue': -1}
            ds_out['AVW'].attrs = {'long_name': 'Apparent Visible Wavelength', 'units': 'nm'}
            ds_out['Area'].attrs = {'long_name': 'Trapezoidal area of Rrs at RGB bands', 'units': 'sr-1 nm'}
            ds_out['NDI'].attrs = {'long_name': 'Normalized Difference Index', 'units': '1'}

            if 'unlimited_dims' in ds_out.encoding:
                del ds_out.encoding['unlimited_dims']

        encoding = {var: {'zlib': True, 'complevel': 5} for var in ds_out.data_vars}

        if self.verbose:
            print(f"Starting computation and writing to a single file: {self.output_filename}")

        with dask.config.set(scheduler='synchronous'):
            ds_out.to_netcdf(self.output_filename, compute=True, encoding=encoding)

        if self.verbose:
            print(f"\n--- Global data processing complete! ---")

        return None


if __name__ == "__main__":
    # Example of how to use the class.
    input_file = '/media/elbe/Data/LakeCCI/dap.ceda.ac.uk/neodc/esacci/lakes/data/lake_products/L3S/v2.1/merged_product/2009/01/ESACCI-LAKES-L3S-LK_PRODUCTS-MERGED-20090101-fv2.1.0.nc'
    
    # Define the chunk size for processing.
    # Adjust based on your available RAM. Smaller chunks use less memory.
    processing_chunks = {'lat': 10_000, 'lon': 10_000}

    # Create an instance of the processor, which will automatically run the workflow.
    LakeCCIProcessor(filename=input_file, chunk_sizes=processing_chunks)
