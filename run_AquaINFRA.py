'''
This scripts is for AquaINFRA project to integrate pyOWT into the Galaxy platform

Shun Bi, Shun.Bi@outlook.com
13.09.2024
'''

import numpy as np
import pandas as pd

#from OpticalVariables import OpticalVariables
#from OWT import OWT
from pygeoapi.process.pyOWT.OpticalVariables import OpticalVariables
from pygeoapi.process.pyOWT.OWT import OWT


import argparse

def run_owt_csv(input_path_to_csv, input_sensor, output_path, output_option=1):
    d = pd.read_csv(input_path_to_csv)
    Rrs = d.values.reshape(d.shape[0], 1, d.shape[1])
    band = [int(x) for x in d.columns.tolist()]
    
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

def run_owt_sat(input_path_to_sat, input_sensor, output_path):
    # TODO processing satellite data...
    return 0


def main():

    support_sensors = pd.read_csv("data/AVW_all_regression_800.txt").iloc[:, 0].astype(str)
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

    # in terminal, try
    # python run_AquaINFRA.py --input 'data/Rrs_demo_AquaINFRA_hyper.csv' --input_option 'csv' --sensor 'HYPER' --output 'data/results/owt_result_hyper.txt'
    # python run_AquaINFRA.py --input 'data/Rrs_demo_AquaINFRA_msi.csv' --input_option 'csv' --sensor 'MSI_S2A' --output 'data/results/owt_result_msi.txt'
    # python run_AquaINFRA.py --input 'data/Rrs_demo_AquaINFRA_olci.csv' --input_option 'csv' --sensor 'OLCI_S3A' --output 'data/results/owt_result_olci.txt'

    # extensive output
    # python run_AquaINFRA.py --input 'data/Rrs_demo_AquaINFRA_hyper.csv' --input_option 'csv' --sensor 'HYPER' --output 'data/results/owt_result_hyper.txt' --output_option 2






