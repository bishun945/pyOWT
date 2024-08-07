'''

Version history
===============

0.32:
    - Use absolute file path of OWT_centroids.nc
    - Clean the root folder

0.40:
    - Deprecated run and run_classification functions in OpticalVariables and OWT, respectively
    - Add manipulation of input Rrs for OpticalVariables which now supports any input shapes
    - Add new classes `PlotOV` and `PlotSpec` for plotting
    - Add new csv file (data/OWT_mean_spec.csv) for mean spectra of OWTs
    - run_examples.py revised accordingly

0.41:
    - Fig bugs in satellite sensor waveband settings and add new setups
    - Add new subcalss in `OpticalVariables`, `ArrayWithAttributes`, to allow attributes for np.array
    - A new demo of Rrs updated in the folder `data`
    - `run_examples.py` add Google Drive link for demo satellite data

'''

__package__ = "pyOWT"
__version__ = "0.41"

