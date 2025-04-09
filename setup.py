from setuptools import setup, find_packages
import pyowt

setup(
    name=pyowt.__package__,
    version=pyowt.__version__,
    author='Shun Bi',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'scipy',
        'PyYAML',
        'netCDF4',
        'xarray',
        'matplotlib'
    ],
    extras_require={
        'geeowt': [
            'geemap',
            'earthengine-api'
        ],
        'satellite_handlers': [
            'osgeo',
            'lxml'
        ]
    },
    include_package_data=True,
    package_data={
        'pyowt': ['data/*']
    },
    license_files=('LICENSE')
)

# Please use the command to install the package in terminal
# pip install -e .
