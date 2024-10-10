import pandas as pd
import numpy as np
import xarray as xr

# read single variables, ID
d_sing = pd.read_csv("test_running/reshape_netcdf_temp_data/single_variable.csv")

# read spectrum data, ID ~ wavelen
d_ad = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_ad.csv")
d_agp = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_agp.csv")
d_aph = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_aph.csv")
d_aw = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_aw.csv")
d_bbp = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_bbp.csv")
d_bp = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_bp.csv")
d_bw = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_bw.csv")
d_Rrs = pd.read_csv("test_running/reshape_netcdf_temp_data/spec_Rrs.csv")

# slice wavelen number
wavelen_sel = [str(i) for i in range(400, 901, 2)]


# get dimension numbers
wavelen = np.arange(400, 901, step=2)
ID = np.arange(1, d_sing.shape[0] + 1)


# convert to numpy array
ad = d_ad[wavelen_sel].to_numpy().round(8)
agp = d_agp[wavelen_sel].to_numpy().round(8)
aph = d_aph[wavelen_sel].to_numpy().round(8)
aw = d_aw[wavelen_sel].to_numpy().round(8)
bbp = d_bbp[wavelen_sel].to_numpy().round(8)
bp = d_bp[wavelen_sel].to_numpy().round(8)
bw = d_bw[wavelen_sel].to_numpy().round(8)
Rrs = d_Rrs[wavelen_sel].to_numpy().round(8)

# create netcdf file
from datetime import date

today = date.today()

data = xr.Dataset(
    {
        "ad": (["ID", "wavelen"], ad),
        "agp": (["ID", "wavelen"], agp),
        "aph": (["ID", "wavelen"], aph),
        "aw": (["ID", "wavelen"], aw),
        "bbp": (["ID", "wavelen"], bbp),
        "bp": (["ID", "wavelen"], bp),
        "bw": (["ID", "wavelen"], bw),
        "Rrs": (["ID", "wavelen"], Rrs),
        "ID_ref": (["ID"], d_sing["ID"].to_numpy()),
        "source": (["ID"], d_sing["source"].to_numpy()),
        "type": (["ID"], d_sing["type"].to_numpy()),
        "Chl": (["ID"], d_sing["Chl"].to_numpy().round(3)),
        "ISM": (["ID"], d_sing["ISM"].to_numpy().round(3)),
        "ag440": (["ID"], d_sing["ag440"].to_numpy().round(8)),
        "A_d": (["ID"], d_sing["A_d"].to_numpy().round(8)),
        "G_d": (["ID"], d_sing["G_d"].to_numpy().round(8)),
        "Sal": (["ID"], d_sing["Sal"].to_numpy().round(2)),
        "Temp": (["ID"], d_sing["Temp"].to_numpy().round(2)),
        "a_frac": (["ID"], d_sing["a_frac"].to_numpy().round(3)),
        "cocco_frac": (["ID"], d_sing["cocco_frac"].to_numpy().round(3)),
    },
    coords={"ID": ID, "wavelen": wavelen},
    attrs={
        "description": "Training data for the OWT classification framework by Bi and Hieronymi (2024) - Hyperspectral version 400 to 900 nm (step 2 nm)",
        "reference": (
            "OWT framework: Bi, S., and Hieronymi, M. (2024). Holistic optical water type classification"
            " for ocean, coastal, and inland waters. Limnology & Oceanography, lno.12606. doi: 10.1002/lno.12606"
            "\n"
            "Component IOP model: Bi, S., Hieronymi, M., and Röttgers, R. (2023). Bio-geo-optical modelling of natural waters."
            " Front. Mar. Sci. 10, 1196352. doi: 10.3389/fmars.2023.1196352"
            "\n"
            "Pure water IOP model: Röttgers, R., Doerffer, R., McKee, D., and Schönfeld, W. (2016)."
            " The Water Optical Properties Processor (WOPP): Pure Water Spectral Absorption, Scattering and"
            " Real Part of Refractive Index Model. Technical Report No WOPP-ATBD/WRD6."
            " Available at: https://calvalportal.ceos.org/tools"
            "\n"
            "Rrs model: Lee, Z., Du, K., Voss, K. J., Zibordi, G., Lubac, B., Arnone, R., et al. (2011)."
            " An inherent-optical-property-centered approach to correct the angular effects in water-leaving radiance."
            " Appl. Opt. 50, 3155. doi: 10.1364/AO.50.003155"
        ),
        "Author": "Shun Bi, Martin Hieronymi, Rüdiger Röttgers",
        "Creator": "Shun Bi, Shun.Bi@heren.de",
        "CreatedDate": today.strftime("%d/%m/%Y"),
    },
)

# add variable and dimension description (according to Bi et al. 2023 IOP Paper Table 1)
data.coords["ID"].attrs["description"] = "Sample ID number"
data.coords["wavelen"].attrs["description"] = "Wavelength of light"
data.coords["wavelen"].attrs["units"] = "nm"


data["ad"].attrs["description"] = "Absorption coefficient of detritus"
data["ad"].attrs["units"] = "1/m"

data["agp"].attrs["description"] = "Total absorption coefficient without pure water"
data["agp"].attrs["units"] = "1/m"

data["aph"].attrs["description"] = "Absorption coefficient of phytoplankton"
data["aph"].attrs["units"] = "1/m"

data["aw"].attrs["description"] = "Absorption coefficient of pure water"
data["aw"].attrs["units"] = "1/m"

data["bbp"].attrs["description"] = "Backscattering coefficient of total particulate matter"
data["bbp"].attrs["units"] = "1/m"

data["bp"].attrs["description"] = "Scattering coefficient of total particulate matter"
data["bp"].attrs["units"] = "1/m"

data["bw"].attrs["description"] = "Scattering coefficient of pure water"
data["bw"].attrs["units"] = "1/m"

data["Rrs"].attrs["description"] = (
    "Remote-sensing reflectance (above water surface). Calculated by Lee et al. (2011) model. "
    "Note that the inelastic scattering were not considered in the model."
)
data["Rrs"].attrs["units"] = "1/sr"

data["ID_ref"].attrs["description"] = "Reference identity from original data sources"
data["source"].attrs["description"] = "Data source from Global or Specific. See Bi and Hieronymi (2024) for details."

data["type"].attrs["description"] = "Optical water type for 1, 2, 3a, 3b, 4a, 4b, 5a, 5b, 6, and 7. See Bi and Hieronymi (2024) for detailed descriptions."

data["Chl"].attrs["description"] = "Concentration of chlorophyll a"
data["Chl"].attrs["units"] = "mg/m^3"

data["ISM"].attrs["description"] = "Concentration of inorganic suspended matter"
data["ISM"].attrs["units"] = "g/m^3"

data["ag440"].attrs["description"] = "Colored dissolved organic matter absorption coefficient at 440 nm"
data["ag440"].attrs["units"] = "1/m"

data["A_d"].attrs["description"] = "Single-scattering albedo of detritus at 550 nm. Albedo_d(550) = 1 - 10^A_d"
data["G_d"].attrs["description"] = "Power law exponent of attenuation of detritus. c_d(lam) = c_d(550) * (lam0/lam) ^ G_d"

data["Sal"].attrs["description"] = "Water salinity"
data["Sal"].attrs["units"] = "PSU"

data["Temp"].attrs["description"] = "Water temperature"
data["Temp"].attrs["units"] = "degC"

data["a_frac"].attrs["description"] = "Fraction for diminished Coccolithophore absorption - minic its lifecycle from bloom to cocclith-detached."
data["cocco_frac"].attrs["description"] = "Fraction of Coccolithophore group"

# Define the encoding dictionary for compression
complevel_sel = 5
encoding = {
    "ad": {"zlib": True, "complevel": complevel_sel},
    "agp": {"zlib": True, "complevel": complevel_sel},
    "aph": {"zlib": True, "complevel": complevel_sel},
    "aw": {"zlib": True, "complevel": complevel_sel},
    "bbp": {"zlib": True, "complevel": complevel_sel},
    "bp": {"zlib": True, "complevel": complevel_sel},
    "bw": {"zlib": True, "complevel": complevel_sel},
    "Rrs": {"zlib": True, "complevel": complevel_sel},
    "Chl": {"zlib": True, "complevel": complevel_sel},
    "ISM": {"zlib": True, "complevel": complevel_sel},
    "ag440": {"zlib": True, "complevel": complevel_sel},
    "A_d": {"zlib": True, "complevel": complevel_sel},
    "G_d": {"zlib": True, "complevel": complevel_sel},
    "Sal": {"zlib": True, "complevel": complevel_sel},
    "Temp": {"zlib": True, "complevel": complevel_sel},
    "a_frac": {"zlib": True, "complevel": complevel_sel},
    "cocco_frac": {"zlib": True, "complevel": complevel_sel},
    # No compression for object data types
    "ID_ref": {},
    "source": {},
    "type": {},
}

# save data
data.to_netcdf(
    "/Users/Bi/Documents/GitHub/pyOWT/test_running/owt_BH2024_training_data_hyper.nc",
    encoding=encoding,
)


# # plot test
# # test plotting for check
# import matplotlib.pyplot as plt
# import random
# import seaborn as sns
#
# ind = random.randint(0, len(ID)-1)
# plt.figure(figsize=(10, 6))
# plt.plot(wavelen, ad[ind,:], label='ad')
# plt.plot(wavelen, agp[ind,:], label='agp')
# plt.plot(wavelen, aph[ind,:], label='aph')
# # plt.plot(wavelen, aw[ind,:], label='aw')
# plt.legend()
# plt.show()
#
# plt.figure(figsize=(10, 6))
# sns.boxplot(x='type', y='ag440', data=d_sing)
# plt.yscale('log')
# plt.ylabel('Value (log scale)')
# plt.title('Boxplot with log10 scale on y-axis')
# plt.show()
