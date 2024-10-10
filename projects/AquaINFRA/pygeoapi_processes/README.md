# pyOWT as OGC API processes (AquaINFRA project)

## What is the AquaINFRA project?

Read here: https://aquainfra.eu/

## What are OGC processes?

... TODO Write or find a quick introduction ...

Read here: https://ogcapi.ogc.org/

## What is pygeoapi?

...TODO...

Read here: https://pygeoapi.io/

## Steps to deploy this as OGC processes

* Deploy an instance of pygeoapi (https://pygeoapi.io/). We will assume it is running on `localhost:5000`.
* Go to the `process` directory of your installation, i.e. `cd /.../pygeoapi/pygeoapi/process`.
* Clone this repo and checkout this branch
* Open the `plugin.py` file (`vi /.../pygeoapi/pygeoapi/plugin.py`) and add this line to the `'process'` section:

```
    'process': {
        'HelloWorld': 'pygeoapi.process.hello_world.HelloWorldProcessor',
        ...
        'HEREON_PyOWT_Processor': 'pygeoapi.process.pyOWT.pygeoapi_processes.hereon_pyowt.HEREON_PyOWT_Processor',

        ...
```

* Open the `pygeoapi-config.yaml` file (`vi /.../pygeoapi/pygeoapi-config.yaml`) and add these lines to the `resources` section:

```
resources:

    ...

    hereon-pyowt:
        type: process
        processor:
            name: HEREON_PyOWT_Processor

```

* Config file: Make sure you have a `config.json` sitting either in pygeoapi's current working dir (`...TODO...`) or in an arbitrary path that pygeoapi can find through the environment variable `PYOWT_CONFIG_FILE`.
* When running with flask or starlette, you can add that env var by adding the line `os.environ['PYOWT_CONFIG_FILE'] = '/.../config.json'` to `/.../pygeoapi/pygeoapi/starlette_app.py`
* Make sure this config file contains:

```
{
    ...
    "pyowt": {
        "example_input_data_dir": "/.../pygeoapi/process/pyOWT/data/",
        "input_data_dir": "/.../inputs/",
        "path_sensor_band_library": "/.../pygeoapi/process/pyOWT/data/sensor_band_library.yaml"
    },

    ...
}
```

* Downloading of results:
** If you don't need this right now, just put any writeable path into `download_dir`, where you want the results to be written. Put some dummy value into `download_url`.
** If you want users to be able to download results from remote, have some webserver running (e.g. `nginx` or `apache2`) that you can use to serve static files. The directory for the static results and the URL where that is reachable have to be written into `download_dir` and `download_url`.
* Make sure to create a directory for inputs, and write it into `input_data_dir` of the config file. The inputs that the users provide will be downloaded and stored there.


* Install the following python packages: See https://github.com/merretbuurman/pyOWT/blob/main/requirements.txt
* Start pygeoapi following their documentation
* Now you should be able to call the processes using any HTTP client, for example curl. Example requests can be found on top of the `hereon_pyowt.py` file. For the first examepl, call `curl -X POST "http://localhost:5000/processes/hereon-pyowt/execution" -H "Content-Type: application/json" -d "{\"inputs\":{\"input_data_url\": \"https://raw.githubusercontent.com/bishun945/pyOWT/refs/heads/AquaINFRA/data/Rrs_demo_AquaINFRA_hyper.csv\", \"input_option\":\"csv\", \"sensor\":\"HYPER\", \"output_option\": 1}}"
`.


