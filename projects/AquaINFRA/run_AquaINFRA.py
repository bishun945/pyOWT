'''
This script is for AquaINFRA project to integrate pyOWT into the Galaxy platform

Examples:

# run in terminal

# csv as input
python projects/AquaINFRA/run_AquaINFRA.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_hyper.csv' --input_option 'csv' --sensor 'HYPER' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 1
python projects/AquaINFRA/run_AquaINFRA.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_msi.csv' --input_option 'csv' --sensor 'MSI_S2A' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 1
python projects/AquaINFRA/run_AquaINFRA.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_ocli.csv' --input_option 'csv' --sensor 'OLCI_S3A' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 1

# extensive output
python projects/AquaINFRA/run_AquaINFRA.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_hyper.csv' --input_option 'csv' --sensor 'HYPER' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 2

# satellite as input
python projects/AquaINFRA/run_AquaINFRA.py --input '/path/S3B_OL_2_WFR____20220703T075301_20220703T075601_20220704T171729_0179_067_363_2160_MAR_O_NT_003.SEN3.zip' --input_option 'sat' --sensor 'OLCI_S3A' --output '/path/to/save' --output_option 1

Shun Bi, shun.bi@outlook.com
10.10.2024
'''

import argparse

# common pkg
import numpy as np
import pandas as pd

# import OWT pkg
# the exception is for pygeoapi importing in AquaINFRA 
try:
    from pyowt.OpticalVariables import OpticalVariables
    from pyowt.OWT import OWT
except ModuleNotFoundError as e:
    from pygeoapi.process.pyOWT.OpticalVariables import OpticalVariables
    from pygeoapi.process.pyOWT.OWT import OWT


# satellite data pkg
import xarray as xr
import zipfile
import tempfile
from lxml import etree
import os
from datetime import date


def read_csv_with_auto_sep(file_path): 
    separators = [',', '\t', r'\s+']
    for sep in separators:
        try:
            df = pd.read_csv(file_path, sep=sep)
            if len(df.columns) > 1:
                return df
        except Exception as e:
            continue
    raise ValueError('Unable to read file with common separators: ' + ' '.join(separators))

def run_owt_csv(input_path_to_csv, input_sensor, output_path, output_option=1):
    d = read_csv_with_auto_sep(input_path_to_csv)
    Rrs = d.values.reshape(d.shape[0], 1, d.shape[1])
    band = [float(x) for x in d.columns.tolist()]
    
    input_sensor = None if input_sensor == "HYPER" else input_sensor
    ov = OpticalVariables(Rrs=Rrs, band=band, sensor=input_sensor)
    owt = OWT(ov.AVW, ov.Area, ov.NDI)
    u_total = np.sum(owt.u, axis=-1)

    if output_option == 1:
        owt_result = pd.DataFrame({
            'OWT': owt.type_str.flatten(),
            'AVW': owt.AVW.flatten().round(3),
            'Area': owt.Area.flatten().round(3),
            'NDI': owt.NDI.flatten().round(3),
            'Utot': u_total.flatten().round(3),
        })

    elif output_option == 2:
        u = np.round(owt.u, 5)
        owt_result = pd.DataFrame({
            'OWT': owt.type_str.flatten(),
            'AVW': owt.AVW.flatten().round(3),
            'Area': owt.Area.flatten().round(3),
            'NDI': owt.NDI.flatten().round(3),
            'Utot': u_total.flatten().round(3),
            'U_OWT1': u[:,:,0].flatten(),
            'U_OWT2': u[:,:,1].flatten(),
            'U_OWT3a': u[:,:,2].flatten(),
            'U_OWT3b': u[:,:,3].flatten(),
            'U_OWT4a': u[:,:,4].flatten(),
            'U_OWT4b': u[:,:,5].flatten(),
            'U_OWT5a': u[:,:,6].flatten(),
            'U_OWT5b': u[:,:,7].flatten(),
            'U_OWT6': u[:,:,8].flatten(),
            'U_OWT7': u[:,:,9].flatten(),
        })
    else:
        raise ValueError('The output_option should be either 1 or 2')

    owt_result.to_csv(output_path, index=False)

    return owt_result

def find_file(directory, filename):
    for root, dirs, files in os.walk(directory):
        if filename in files:
            return os.path.join(root, filename)
    return None


def run_owt_sat(input_path_to_sat, input_sensor, output_path, output_option=1):
    today = date.today()

    # product path - unzip in a temporary directory
    zip_path = input_path_to_sat
    temp_dir = tempfile.TemporaryDirectory()
    temp_path = temp_dir.name
    zip_ref = zipfile.ZipFile(zip_path, 'r')

    try:
        # start image processing...
        zip_ref.extractall(temp_path)
        basename = os.path.basename(os.path.splitext(os.path.basename(zip_path))[0])
        # path = os.path.join(temp_path, basename)
        path_xfdu = find_file(temp_path, 'xfdumanifest.xml')
        path = os.path.dirname(path_xfdu)

        save_path = output_path

        # get xml - tree file
        fn = os.path.join(path, 'xfdumanifest.xml') 
        tree = etree.parse(fn)
        namespaces = tree.getroot().nsmap
        wavelengths = tree.xpath('//sentinel3:centralWavelength/text()', namespaces=namespaces)
        wavelengths = [float(wl) for wl in wavelengths]
        bandnames = tree.xpath('//sentinel3:band/@name', namespaces=namespaces)

        # get WQSF_REFLECTANCE_RECOM flags
        ds = xr.open_dataset(os.path.join(path, 'wqsf.nc'))
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

        # read geo_coordinates
        ds = xr.open_dataset(os.path.join(path, 'geo_coordinates.nc'))
        lon = ds['longitude']
        lat = ds['latitude']

        # read reflectance data from files and combine them in one xr.nc
        Ref_list = []

        for i, bandname in enumerate(bandnames):
            nc_file_path = os.path.join(path, f"{bandname}_reflectance.nc")

            if os.path.exists(nc_file_path):
                ds = xr.open_dataset(nc_file_path)
                Ref_data = ds[f"{bandname}_reflectance"]
                Ref_data.attrs['radiation_wavelength'] = wavelengths[i]
                Ref_data.attrs['radiation_wavelength_unit'] = 'nm'
                Ref_data = Ref_data.assign_coords(longitude = lon, latitude = lat)

                Ref_list.append(Ref_data)
            else:
                print(f"File {nc_file_path} does not exist.")

        ds_new = xr.merge(Ref_list)

        # end of image processing
        # TODO: the reading above should be wrapped into `read_*` functions in pyowt module as they should be quite common...
        # the common data interface should include (as a list):
        # - Coordinates variables for outputing
        # - Remote sensing reflectance (divided by pi if Rw is imported)
        # - Binary flag for selecting valid pixels
        # - Some extra elements if necessary

        # owt processing
        reflectance_vars = np.array([ds_new[f"{bandname}_reflectance"].data for bandname in bandnames]).transpose(1, 2, 0)
        # TODO: one may want Rrs as output directly instead of reflectance
        Rrs_vars = reflectance_vars / np.pi

        ov = OpticalVariables(Rrs=Rrs_vars, band=wavelengths, sensor=input_sensor)
        owt = OWT(ov.AVW, ov.Area, ov.NDI)

        ds_new = ds_new.drop_vars([f"{bandname}_reflectance" for bandname in bandnames])

        ds_new.attrs = {
            'Description': 'This dataset contains reflectance data and flags for ocean color remote sensing.',
            'Source': os.path.basename(path),
            "Author": "Shun Bi, shun.bi@outlook.com",
            "CreatedDate": today.strftime("%d/%m/%Y"),
        }

        # combine flag into it and save out
        # TODO: more flags should be added, e.g., sunglint, cloud risk, white scatt.

        ds_new['flag'] = (['rows', 'columns'], WQSF_REFLECTANCE_RECOM.data.astype(np.int32))

        ds_new['type_idx'] = (
            ['rows', 'columns'], 
            owt.type_idx.astype(np.int32),
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
        
        AVW_clipped = np.where((owt.AVW >= 400) & (owt.AVW <= 800), owt.AVW, np.nan)
        ds_new['AVW'] = (
            ['rows', 'columns'], 
            AVW_clipped.astype(np.float32),
            {'Description': 'Apparent Visible Wavelength 400-800 nm'}
        )

        ds_new['Area'] = (
            ['rows', 'columns'], 
            owt.Area.astype(np.float32),
            {'Description': 'Trapezoidal area of Rrs at RGB bands'}
        )

        NDI_clipped = np.where((owt.NDI >= -1) & (owt.NDI <= 1), owt.AVW, np.nan)
        ds_new['NDI'] = (
            ['rows', 'columns'], 
            NDI_clipped.astype(np.float32),
            {'Description': 'Normalized Difference Index of Rrs at G and B bands'}
        )

        # save membership matrix
        u = owt.u
        utot = owt.utot

        ds_new['utot'] = (
            ['rows', 'columns'], 
            utot.astype(np.float32),
            {'Description': 'Total membership values of ten water types'}
        )

        if output_option == 1:
            pass
        elif output_option == 2:
            for sel_type in owt.typeName:
                ds_new[f'U_OWT{sel_type}'] = (
                    ['rows', 'columns'], 
                    u[:,:,owt.typeName.index(sel_type)].astype(np.float32),
                    {'Description': f'Membership values of optical water type {sel_type}'}
                )        
        else:
            raise ValueError('The output_option should be either 1 or 2')

        # for sel_type in owt.typeName:
        #     ds_new[f'normU_{sel_type}'] = (
        #         ['rows', 'columns'], 
        #         norm_u[:,:,owt.typeName.index(sel_type)].astype(np.float32),
        #         {'Description': f'Normalized membership values of optical water type {sel_type}'}
        #         )

        encoding = {
            var: {
                'zlib': True,
                'complevel': 5,
                'shuffle': True
            }
            for var in list(ds_new.data_vars)
        }

        ds_new.to_netcdf(os.path.join(save_path, f"{basename}_owt.nc"), encoding=encoding)

    finally:
        temp_dir.cleanup()
        zip_ref.close()



def main():
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
    data_file_path = os.path.join(project_root, 'pyowt', 'data', 'AVW_all_regression_800.txt')

    support_sensors = pd.read_csv(data_file_path).iloc[:, 0].astype(str)
    support_sensors = ', '.join(support_sensors)

    parser = argparse.ArgumentParser(description='Perform Optical Water Type classification based on Bi and Hieronymi (2024)')
    parser.add_argument('--input', type=str, required=True, help='Path to your input file')
    parser.add_argument('--input_option', type=str, default='csv', required=True, help='Input option. "csv" for text data input; "sat" for satellite products input (e.g., Sentinel-3 OLCI Level-2)')
    parser.add_argument('--sensor', type=str, required=True, help=f'Name of you sensor. Select from {support_sensors}')
    parser.add_argument('--output', type=str, required=True, help='Path to your output file')
    parser.add_argument('--output_option', type=int, required=True, default='1', help='Output option. 1: for standard output; 2: for extensive output with memberships of all types')

    args = parser.parse_args()

    if args.input_option == "csv":
        run_owt_csv(input_path_to_csv=args.input, input_sensor=args.sensor, output_path=args.output, output_option=args.output_option)
    elif args.input_option == "sat":
        run_owt_sat(input_path_to_sat=args.input, input_sensor=args.sensor, output_path=args.output, output_option=args.output_option)
    else:
        raise ValueError('The input_option should be either "csv" or "sat"')



if __name__ == "__main__":

    main()

