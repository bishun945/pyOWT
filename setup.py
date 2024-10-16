from setuptools import setup, find_packages
import pyowt

setup(
    name=pyowt.__package__,
    version=pyowt.__version__,
    author='Shun Bi',
    packages=find_packages(),
    install_requires=[
        req.strip() for req in open('requirements.txt').readlines()
    ],
    include_package_data=True,
    package_data={
        'pyowt': ['data/*']
    },
    license_files=('LICENSE')
)

# Please use the command to install the package in terminal
# pip install -e .
