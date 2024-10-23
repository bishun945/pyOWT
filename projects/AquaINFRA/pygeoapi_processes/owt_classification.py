import logging

from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError
from pygeoapi.process.pyOWT.run_AquaINFRA import run_owt_csv
from pygeoapi.process.pyOWT.run_AquaINFRA import run_owt_sat
import os
import json
import requests


LOGGER = logging.getLogger(__name__)


'''

### Reading input csv from any URL:
# Example 1: HYPER, Rrs_demo_AquaINFRA_hyper.csv
curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"https://raw.githubusercontent.com/bishun945/pyOWT/refs/heads/AquaINFRA/data/Rrs_demo_AquaINFRA_hyper.csv\", \"input_option\":\"csv\", \"sensor\":\"HYPER\", \"output_option\": 1}}"

# Example 2: MSI_S2A, Rrs_demo_AquaINFRA_msi.csv
curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"https://raw.githubusercontent.com/bishun945/pyOWT/refs/heads/AquaINFRA/data/Rrs_demo_AquaINFRA_msi.csv\", \"input_option\":\"csv\", \"sensor\":\"MSI_S2A\", \"output_option\": 1}}"

# Example 3: OLCI_S3A, Rrs_demo_AquaINFRA_olci.csv
curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"https://raw.githubusercontent.com/bishun945/pyOWT/refs/heads/AquaINFRA/data/Rrs_demo_AquaINFRA_olci.csv\", \"input_option\":\"csv\", \"sensor\":\"OLCI_S3A\", \"output_option\": 1}}"

### Reading the example files from server:
# Example 1: HYPER, Rrs_demo_AquaINFRA_hyper.csv
curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"Rrs_demo_AquaINFRA_hyper.csv\", \"input_option\":\"csv\", \"sensor\":\"HYPER\", \"output_option\": 1}}"

# Example 2: MSI_S2A, Rrs_demo_AquaINFRA_msi.csv
curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"Rrs_demo_AquaINFRA_msi.csv\", \"input_option\":\"csv\", \"sensor\":\"MSI_S2A\", \"output_option\": 1}}"

# Example 3: OLCI_S3A, Rrs_demo_AquaINFRA_olci.csv
curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"Rrs_demo_AquaINFRA_olci.csv\", \"input_option\":\"csv\", \"sensor\":\"OLCI_S3A\", \"output_option\": 1}}"

### Extensive output:
curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"Rrs_demo_AquaINFRA_hyper.csv\", \"input_option\":\"csv\", \"sensor\":\"HYPER\", \"output_option\": 2}}"

'''

# Process metadata and description
# Has to be in a JSON file of the same name, in the same dir!
script_title_and_path = __file__
metadata_title_and_path = script_title_and_path.replace('.py', '.json')
PROCESS_METADATA = json.load(open(metadata_title_and_path))



class OwtClassificationProcessor(BaseProcessor):

    def __init__(self, processor_def):
        super().__init__(processor_def, PROCESS_METADATA)
        self.supports_outputs = True
        self.job_id = None
        self.config = None

        # Set config:
        config_file_path = os.environ.get('PYOWT_CONFIG_FILE', "./config.json")
        with open(config_file_path, 'r') as config_file:
            self.config = json.load(config_file)

    def __repr__(self):
        return f'<OwtClassificationProcessor> {self.name}'

    def set_job_id(self, job_id: str):
        self.job_id = job_id

    def execute(self, data, outputs=None):
        input_data_url = data.get('input_data_url', 'Rrs_demo_AquaINFRA_hyper.csv')
        input_option = data.get('input_option')
        sensor = data.get('sensor')
        output_option = int(data.get('output_option'))

        # Check sensor:
        support_sensors = set(['HYPER', 'AVW700', 'MODIS_Aqua', 'MODIS_Terra', 'OLCI_S3A', 'OLCI_S3B', 'MERIS', 'SeaWiFS', 'HawkEye', 'OCTS', 'GOCI', 'VIIRS_NPP', 'VIIRS_JPSS1', 'VIIRS_JPSS2', 'CZCS', 'MSI_S2A', 'MSI_S2B', 'OLI', 'ENMAP_HSI', 'CMEMS_HROC_L3_optics', 'cmems_P1D400', 'AERONET_OC_1', 'AERONET_OC_2'])
        #support_sensors = pd.read_csv("data/AVW_all_regression_800.txt").iloc[:, 0].astype(str)
        # TODO: Read this from AVW_all_regression_800.txt everytime. Add HYPER manually.
        # TODO: Ask Shun Bi: Why is HYPER included?
        if not sensor in support_sensors:
            raise ProcessorExecuteError('Sensor not supported: "%s". Please pick one of: %s' % (sensor, ', '.join(support_sensors)))

        # Use example input file:
        input_path = None
        if input_data_url in ['Rrs_demo_AquaINFRA_hyper.csv', 'Rrs_demo_AquaINFRA_msi.csv', 'Rrs_demo_AquaINFRA_olci.csv']:
            LOGGER.info('Using example input data file: %s' % input_data_url)
            input_dir = self.config['pyowt']['example_input_data_dir']
            input_path = input_dir.rstrip('/')+os.sep+input_data_url

        # ... Or download input file:
        # TODO: Also allow user to paste CSV as POST request body/payload! - Check size though!
        else:
            LOGGER.info('Downloading input data file: %s' % input_data_url)
            resp = requests.get(input_data_url)
            if resp.status_code == 200:
                input_dir = self.config['pyowt']['input_data_dir']
                input_path = input_dir.rstrip('/')+os.sep+'inputs_%s' % self.job_id
                LOGGER.debug('Writing input data file to: %s' % input_path)
                with open(input_path, 'w') as myfile:
                    myfile.write(resp.text)
            else:
                raise ProcessorExecuteError('Could not download input file (HTTP status %s): %s' % (resp.status_code, input_data_url))

        # Where to store output
        downloadfilename = 'pyowt_output_%s-%s.txt' % (sensor.lower(), self.job_id)
        downloadfilepath = self.config['download_dir']+downloadfilename

        # https://github.com/bishun945/pyOWT/blob/AquaINFRA/run_AquaINFRA.py
        if input_option.lower() == 'csv':
            run_owt_csv(input_path_to_csv=input_path, input_sensor=sensor, output_path=downloadfilepath, output_option=output_option)
        elif input_option.lower() == 'sat':
            run_owt_sat(input_path_to_sat=input_path, input_sensor=sensor, output_path=downloadfilepath, output_option=output_option)
        else:
            err_msg = 'The input_option should be either "csv" or "sat"'
            raise ProcessorExecuteError(err_msg)

        # Create download link:
        downloadlink = self.config['download_url'] + downloadfilename

        # Build response containing the link
        # TODO Better naming
        response_object = {
            "outputs": {
                "some_output": {
                    'title': self.metadata['outputs']["some_output"]['title'],
                    'description': self.metadata['outputs']["some_output"]['description'],
                    "href": downloadlink
                }
            }
        }
        LOGGER.debug('Built response including link: %s' % response_object)

        return 'application/json', response_object


