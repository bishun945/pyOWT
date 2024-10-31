import numpy as np
import xarray as xr
from scipy.interpolate import interp1d

def gaussian_srf(central_wavelength, fwhm, wavelengths):
    # Calculate standard deviation from FWHM
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
    
    # Calculate the spectral response function using a Gaussian model
    srf = np.exp(-((wavelengths - central_wavelength) ** 2) / (2 * sigma ** 2))
    
    # Normalize the SRF so that its peak value is 1
    srf /= np.max(srf)
    
    return srf


def interpolate_rrs(rrs, rrs_wavelength, target_wavelength):
    """
    Interpolate Rrs to match target wavelengths. 
    Values out of the rrs_wavelength range are extrapolated constantly from boundary values.
    Optimized to use vectorized operations for efficiency.
    """
    target_wavelength = np.atleast_1d(target_wavelength)
    interpolated_rrs = np.full(rrs.shape[:-1] + (len(target_wavelength),), np.nan)

    valid_indices = (target_wavelength >= rrs_wavelength[0]) & (target_wavelength <= rrs_wavelength[-1])
    interp_func = interp1d(rrs_wavelength, rrs, kind='linear', axis=-1, bounds_error=False, fill_value='extrapolate')
    interpolated_rrs[..., valid_indices] = interp_func(target_wavelength[valid_indices])

    # Extrapolate constant values for out-of-bounds
    extrap_below = target_wavelength < rrs_wavelength[0]
    extrap_above = target_wavelength > rrs_wavelength[-1]
    interpolated_rrs[..., extrap_below] = rrs[..., 0][..., np.newaxis]
    interpolated_rrs[..., extrap_above] = rrs[..., -1][..., np.newaxis]

    return interpolated_rrs


def convolute_rrs_to_multispectral(rrs_interp, srf_rsr, delta_lambda):
    """
    Convolute the Rrs with the SRF to obtain multispectral Rrs.
    Optimized using vectorized numpy operations for efficiency.
    """
    nrow, ncol, nband = rrs_interp.shape
    rrs_interp_reshape = rrs_interp.reshape(-1, nband)

    numerator = np.dot(rrs_interp_reshape, srf_rsr.T)
    denominator = np.sum(srf_rsr, axis=1)
    multispectral_rrs = numerator / denominator.reshape(1, denominator.shape[0])
    multispectral_rrs = multispectral_rrs.reshape(nrow, ncol, srf_rsr.shape[0])

    return multispectral_rrs


def srf_convolution(rrs_wavelength, rrs_data, srf_nc_path):
    """Perform SRF convolution on input Rrs data.

    Args:
        rrs_wavelength (array-like): The wavelengths corresponding to the Rrs data.
        rrs_data (array-like): The Rrs data, can be 1D, 2D, or 3D. If 1D or 2D, it will be reshaped to 3D.
        srf_nc_path (str): The file path to the SRF netCDF file.

    Return:
        - bands (array): The bands information extracted from the netCDF file.
        - multispectral_rrs (np.array): The Rrs after SRF convolution, maintaining the same shape as the input Rrs.
        - instrument (str): The instrument information from the netCDF file.
        - platform (str): The platform information from the netCDF file.
    """
    # Load SRF data from netCDF file
    ds = xr.open_dataset(srf_nc_path)
    srf_wavelength = ds['wavelength'].values
    srf_rsr = ds['RSR'].values
    srf_rsr = np.nan_to_num(srf_rsr, nan=0.0)
    bands = ds['bands'].values
    instrument = ds.attrs.get('instrument', 'Unknown')
    platform = ds.attrs.get('platform', 'Unknown')

    # Ensure Rrs data is at least 3D
    if rrs_data.ndim == 1:
        rrs_data = rrs_data[np.newaxis, np.newaxis, :]
    elif rrs_data.ndim == 2:
        rrs_data = rrs_data[:, np.newaxis, :]

    # Interpolate Rrs to match SRF wavelengths
    rrs_interpolated = interpolate_rrs(rrs_data, rrs_wavelength, srf_wavelength)

    # Check wavelength intervals
    wavelength_diff = np.diff(rrs_wavelength)
    if np.allclose(wavelength_diff, wavelength_diff[0]):
        delta_lambda = wavelength_diff[0]
    else:
        raise ValueError('Interval of RSR wavelength is different. Please check!')

    # Normalize SRF
    srf_rsr_normalized = srf_rsr / np.sum(srf_rsr, axis=1, keepdims=True)

    # Perform convolution
    multispectral_rrs = convolute_rrs_to_multispectral(rrs_interpolated, srf_rsr_normalized, delta_lambda)

    # Replace Rrs values with NaN where input wavelengths do not cover the band
    for i, band in enumerate(bands):
        if band < rrs_wavelength[0] or band > rrs_wavelength[-1]:
            multispectral_rrs[..., i] = np.nan

    return bands, multispectral_rrs, instrument, platform

if __name__ ==  '__main__':

    import matplotlib.pyplot as plt

    fn = "/Users/apple/GitHub/pyOWT/projects/zenodo/owt_BH2024_training_data_hyper.nc"
    ds = xr.open_dataset(fn)
    wavelen = ds['wavelen'].values
    # Rrs = ds['Rrs'].values[85_002, :]
    Rrs = ds['Rrs'].values[85_002:85_102, :]
    Rrs = np.atleast_2d(Rrs)

    srf_nc_path = '/Users/apple/Satellite_data/SRF/s3a_olci_RSR.nc'
    bands, Rrs_multi, instrument, platform = srf_convolution(wavelen, Rrs, srf_nc_path)

    plt.plot(wavelen, Rrs[0,:], label='hyper')
    plt.plot(bands, Rrs_multi[0,0,:], 'o', label=f"{instrument}-{platform}")

    srf_nc_path = '/Users/apple/Satellite_data/SRF/sentinel-2a_msi_RSR.nc'
    bands, Rrs_multi, instrument, platform = srf_convolution(wavelen, Rrs, srf_nc_path)
    
    plt.plot(bands, Rrs_multi[0,0,:], '+', label=f"{instrument}-{platform}")

    srf_nc_path = '/Users/apple/Satellite_data/SRF/aqua_modis_RSR.nc'
    bands, Rrs_multi, instrument, platform = srf_convolution(wavelen, Rrs, srf_nc_path)
    
    plt.plot(bands, Rrs_multi[0,0,:], 'x', label=f"{instrument}-{platform}")

    srf_nc_path = '/Users/apple/Satellite_data/SRF/landsat-8_oli_RSR.nc'
    bands, Rrs_multi, instrument, platform = srf_convolution(wavelen, Rrs, srf_nc_path)
    
    plt.plot(bands, Rrs_multi[0,0,:], 'D', label=f"{instrument}-{platform}")

    plt.legend()
    plt.show()

    print(Rrs_multi)
