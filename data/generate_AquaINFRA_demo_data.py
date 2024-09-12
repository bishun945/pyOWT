import pandas as pd

d0 = pd.read_csv('data/Rrs_demo.csv')
d = d0.pivot_table(index='SampleID', columns='wavelen', values='Rrs').round(7)

# Hyperspectral version
d.to_csv('data/Rrs_demo_AquaINFRA_hyper.csv', index=False)

# OLCI version
wavelen_olci_nominal = [400, 412, 444, 490, 510, 560, 620, 666, 674, 682, 710, 754, 780, 866]
d[wavelen_olci_nominal].to_csv('data/Rrs_demo_AquaINFRA_olci.csv', index=False)

# MSI version
wavelen_msi_nomial = [444, 492, 560, 666, 704, 740, 784, 836]
d[wavelen_msi_nomial].to_csv('data/Rrs_demo_AquaINFRA_msi.csv', index=False)
