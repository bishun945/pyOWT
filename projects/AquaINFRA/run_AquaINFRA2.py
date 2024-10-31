'''
This script is for AquaINFRA project to integrate pyOWT into the Galaxy platform

Examples:

# run in terminal

# csv as input
python projects/AquaINFRA/run_AquaINFRA2.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_hyper.csv' --input_option 'csv' --sensor 'HYPER' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 1
python projects/AquaINFRA/run_AquaINFRA2.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_msi.csv' --input_option 'csv' --sensor 'msi-sentine-2a' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 1
python projects/AquaINFRA/run_AquaINFRA2.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_ocli.csv' --input_option 'csv' --sensor 'olci-s3a' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 1

# extensive output
python projects/AquaINFRA/run_AquaINFRA2.py --input 'projects/AquaINFRA/data/Rrs_demo_AquaINFRA_hyper.csv' --input_option 'csv' --sensor 'HYPER' --output 'projects/AquaINFRA/results/owt_result_hyper.txt' --output_option 2

# satellite as input
python projects/AquaINFRA/run_AquaINFRA2.py --input '/path/S3B_OL_2_WFR____20220703T075301_20220703T075601_20220704T171729_0179_067_363_2160_MAR_O_NT_003.SEN3.zip' --input_option 'sat' --sensor 'olci-s3a' --output '/path/to/save' --output_option 1

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
    from pyowt.satellite_handlers.eumetsat_olci_level2 import eumetsat_olci_level2
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

    eumetsat = eumetsat_olci_level2(filename=input_path_to_sat, sensor=input_sensor, save_path=output_path, save=False)

    if output_option == 1:
        eumetsat.save_result()
    elif output_option == 2:
        for sel_type in eumetsat.owt.classInfo.typeName:
            eumetsat.ds_new[f'U_OWT{sel_type}'] = (
                ['rows', 'columns'], 
                eumetsat.u[:,:,eumetsat.owt.classInfo.typeName.index(sel_type)].astype(np.float32),
                {'Description': f'Membership values of optical water type {sel_type}'}
            )
        eumetsat.save_result()
    else:
        raise ValueError('The output_option should be either 1 or 2')


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

