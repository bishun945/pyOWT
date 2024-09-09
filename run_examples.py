""" 
(1) Test for simulated Rrs data (Bi et al. 2023 model)
"""

if True:
    
    import pandas as pd
    from OpticalVariables import OpticalVariables
    from OWT import OWT

    d0 = pd.read_csv("./data/Rrs_demo.csv")
    d = d0.pivot_table(index='SampleID', columns='wavelen', values='Rrs')
    owt_train = d0[d0['wavelen']==350].sort_values(by="SampleID").type.values

    # data preparation for `ov` and `owt` classes
    Rrs = d.values.reshape(d.shape[0], 1, d.shape[1])
    band = d.columns.tolist()

    # create `ov` class to calculate three optical variables
    ov = OpticalVariables(Rrs=Rrs, band=band)

    # create `owt` class to run optical classification
    owt = OWT(ov.AVW, ov.Area, ov.NDI)

    owt_result = owt.type_str.flatten()

    # print(owt_train)
    print('Result OWT:', owt_result)

    # OWT result visualization
    from PlotOWT import PlotOV, PlotSpec
    PlotOV(owt)
    # PlotSpec(owt, ov)



"""
(2) Test for satellite data (A4O results)
"""

if True:

    # OWT
    from OpticalVariables import OpticalVariables
    from OWT import OWT

    # data processing
    from netCDF4 import Dataset as ds
    import re
    import numpy as np
    import os

    # plot
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    def str_match(input, pattern, ind=False):
        """Find out the matched strings

        Args:
            input (list): list of strings
            pattern (character): the string to be matched
            ind (bool, optional): True will return the index in the input list; 
                otherwise, the matched strings. Defaults to False.

        Returns:
            list: characters or indices of matched variables
        """    
        pattern = re.compile(pattern)
        if ind:
            indices = [i for i in range(len(input)) if pattern.match(input[i])]
        else:
            indices = [v for v in input if pattern.match(v)]
        return indices

    # data preparation for `ov` and `owt` classes
    # this nc file is about 327MB 
    # and can be downloaded from https://drive.google.com/file/d/14ZBq2bUw-dzrXGz2wnCxR-cN09iCA_6v/view?usp=sharing
    fn = "data/GermanBight_20160720T093421_subset.nc"
    nc_link = "https://drive.google.com/file/d/14ZBq2bUw-dzrXGz2wnCxR-cN09iCA_6v/view?usp=sharing"

    if not os.path.exists(fn):
        print(f"File {fn} doesn't exist.")
        print(f"Please download it via {nc_link}")
        exit()

    else:
        print(f"Found nc file in {fn}!")

    d = ds(fn, mode="r")
    name_var = list(d.variables.keys())
    var_A4O_Rrs = str_match(name_var, "A4O_Rrs_\d+$")
    wavelen_A4O_Rrs = np.array([float(i.split("_")[-1]) for i in var_A4O_Rrs])
    Rrs_A4O = np.array([d.variables[x][:] for x in var_A4O_Rrs]).transpose(1, 2, 0)

    ## the required variables are:
    # >>> Rrs_A4O.shape
    # (1006, 1509, 16) # a 3d np.array where 1006 and 1509 for lon-lat coord and 16 is for sixteen bands
    # >>> wavelen_A4O_Rrs
    # array([ 400.,  412.,  442.,  490.,  510.,  560.,  620.,  665.,  674.,
    #         681.,  709.,  754.,  779.,  865.,  885., 1020.])

    # create `ov` class to calculate three optical variables
    ov = OpticalVariables(Rrs=Rrs_A4O, band=wavelen_A4O_Rrs, sensor="OLCI_S3A")

    # create `owt` class to run optical classification
    owt = OWT(ov.AVW, ov.Area, ov.NDI)

    # setup colarbar
    cmap = mcolors.ListedColormap(owt.dict_idx_color.values())
    bounds = np.arange(-1.5, 10.5)
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

    plt.figure(figsize=(8, 6))

    plt.imshow(owt.type_idx, cmap=cmap, norm=norm)
    cbar = plt.colorbar(ticks = np.arange(-1, 10), orientation="horizontal")
    cbar.ax.set_xticklabels(owt.dict_idx_name.values())

    # plt.show()
    plt.savefig("type_owt.png", dpi=300, bbox_inches="tight")

    plt.close()
