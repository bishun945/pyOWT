from setuptools import setup, find_packages
import pyowt

setup(
    name=pyowt.__package__,
    version=pyowt.__version__,
    packages=find_packages(),
    install_requires=[
        req.strip() for req in open('requirements.txt').readlines()
    ],
)

# Please use the command to install the package in terminal
# pip install -e .
