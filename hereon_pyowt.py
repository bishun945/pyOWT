import logging

from pygeoapi.process.base import BaseProcessor, ProcessorExecuteError
from pygeoapi.process.pyOWT.run_AquaINFRA import run_owt_csv
from pygeoapi.process.pyOWT.run_AquaINFRA import run_owt_sat
import os


LOGGER = logging.getLogger(__name__)


'''
curl -X POST "https://aqua.igb-berlin.de/pygeoapi-dev/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data\": \"Rrs_demo_AquaINFRA_hyper.csv\", \"input_option\":\"csv\", \"sensor\":\"HYPER\", \"output_option\": 1}}"

curl -X POST "https://aqua.igb-berlin.de/pygeoapi-dev/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data\": \"Rrs_demo_AquaINFRA_msi.csv\", \"input_option\":\"csv\", \"sensor\":\"MSI_S2A\", \"output_option\": 1}}"

curl -X POST "https://aqua.igb-berlin.de/pygeoapi-dev/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data\": \"Rrs_demo_AquaINFRA_olci.csv\", \"input_option\":\"csv\", \"sensor\":\"OLCI_S3A\", \"output_option\": 1}}"

curl -X POST "https://aqua.igb-berlin.de/pygeoapi-dev/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data\": \"Rrs_demo_AquaINFRA_hyper.csv\", \"input_option\":\"csv\", \"sensor\":\"HYPER\", \"output_option\": 2}}"

'''

#: Process metadata and description
PROCESS_METADATA = {
    'version': '0.0.1',
    'id': 'hereon-pyowt',
    'title': {'en': 'Hello pyOWT'},
    'description': {
        'en': 'An example process that ...'
    },
    'jobControlOptions': ['sync-execute', 'async-execute'],
    'keywords': ['hello world', 'example', 'echo'],
    'links': [{
        'type': 'text/html',
        'rel': 'about',
        'title': 'information',
        'href': 'https://github.com/bishun945/pyOWT',
        'hreflang': 'en-US'
    }],
    'inputs': {
        'input_data': {
            'title': 'Input data',
            'description': 'URL to your input file. For the moment, try just file name: Rrs_demo_AquaINFRA_hyper.csv or Rrs_demo_AquaINFRA_msi.csv or Rrs_demo_AquaINFRA_olci.csv',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['hereon', 'pyOWT']
        },
        'input_option': {
            'title': 'Type of input',
            'description': 'Type of input: "csv" for text data input; "sat" for satellite products input (e.g., Sentinel-3 OLCI Level-2)',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['hereon', 'pyOWT']
        },
        'sensor': {
            'title': 'Sensor name', # TODO Make enum!
            'description': 'Name of you sensor. Which sensors are supported? Examples: MSI_S2A, HYPER, OLCI_S3A.',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['hereon', 'pyOWT']
        },
        'output_option': {
            'title': 'Output option',
            'description': 'Output option. 1: for standard output; 2: for extensive output with memberships of all types',
            'schema': {
                'type': 'string'
            },
            'minOccurs': 1,
            'maxOccurs': 1,
            'keywords': ['hereon', 'pyOWT']
        }
    },
    'outputs': {
        'some_output': {
            'title': 'Standard output',
            'description': 'Standard output or extensive output',
            'schema': {
                'type': 'object',
                'contentMediaType': 'application/json'
            }
        }
        
    },
    'example': {
        'inputs': {
            'input_data': 'https://....Rrs_demo_AquaINFRA_hyper.csv',
            'input_option': 'csv',
            'sensor': 'MSI_S2A',
            'output_option': '1'
        }
    }
}




class HEREON_PyOWT_Processor(BaseProcessor):

    def __init__(self, processor_def):
        super().__init__(processor_def, PROCESS_METADATA)
        self.supports_outputs = True
        self.job_id = None

    def __repr__(self):
        return f'<HEREON_PyOWT_Processor> {self.name}'

    def set_job_id(self, job_id: str):
        self.job_id = job_id

    def execute(self, data, outputs=None):
        input_data = data.get('input_data', 'bla')
        input_option = data.get('input_option')
        sensor = data.get('sensor')
        output_option = int(data.get('output_option'))

        # Download input file:
        # TODO: We are faking the path to the input data, as we have no URL right now!
        LOGGER.info('Using input data file: %s' % input_data)
        # TODO Not hardcode path!!
        input_path = '/opt/pyg_upstream_dev/pygeoapi/pygeoapi/process/pyOWT/data/%s' % input_data
        LOGGER.info('Using input data file: %s' % input_path)

        # Where to store output
        downloadfilename = 'pyowt_output_%s-%s.txt' % (sensor.lower(), self.job_id)
        downloadfilepath = '/var/www/nginx/download'+os.sep+downloadfilename

        # https://github.com/bishun945/pyOWT/blob/AquaINFRA/run_AquaINFRA.py
        if input_option.lower() == 'csv':
            run_owt_csv(input_path_to_csv=input_path, input_sensor=sensor, output_path=downloadfilepath, output_option=output_option)
        elif input_option.lower() == 'sat':
            run_owt_sat(input_path_to_sat=input_path, input_sensor=sensor, output_path=downloadfilepath, output_option=output_option)
        else:
            err_msg = 'The input_option should be either "csv" or "sat"'
            raise ProcessorExecuteError(err_msg)

        # Create download link:
        downloadlink = 'https://aqua.igb-berlin.de/download/'+downloadfilename
        # TODO: Not hardcode that URL! Get from my config file, or can I even get it from pygeoapi config?
        # TODO: Again, carefully consider permissions of that directory!

        # Build response containing the link
        response_object = {
            "outputs": {
                "some_output": {
                    "title": "this is what you asked for...",
                    "description": "please ask bi shun / martin hieronymi...",
                    "href": downloadlink
                }
            }
        }
        LOGGER.debug('Built response including link: %s' % response_object)

        return 'application/json', response_object


