# **pyOWT**: python library for Optical Water Type classification

[Shun Bi](Shun.Bi@hereon.de) 

18.01.2024

Note: this repo is translated from the R repo [`OWT`](https://github.com/bishun945/OWT) for the water type classification and has been maintained independently from its original version.

# Install

Clone the whole repo and cd to the folder. 

Then, install the requirements.
```console
pip install -r requirements.txt
```

# How to use it

Vectorized functions are recommended to run the satellite data, e.g., `classification.classification_vec`.

A detailed [example](/examples/example_satellite.py) is provided. 

The example below uses the demo data in the repo:

```python
import classification

# prepare the wavelen and Rrs variables
df = classification.read_Rrs_demo()
ID_uniques = df.ID.unique()
df_sub = df[df["ID"] == ID_uniques[0]]
wavelen = df_sub.wavelen.values
Rrs = df_sub.Rrs.values

# run the classification function
print(classification.classification(wavelen, Rrs))
```

Should return

```console
[5.1411e-02 6.2110e-03 4.1097e-02 6.7700e-04 1.0000e-06 0.0000e+00
 0.0000e+00 0.0000e+00 0.0000e+00 4.0000e-06]
```