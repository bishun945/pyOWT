rm(list = ls())

library(data.table)
library(magrittr)

library(ggplot2)

data.table::setDTthreads(percent = 95)

d <- fread("/Users/Bi/Documents/GitHub/OWT/Paper/Generate_training_data_set/data/OWT_simulated_data.gz")
d[, ID := paste(type, source, SampleID)]

d_sing <- d[wavelen == 440, .(ID, source, type, Chl, ISM, ag440, A_d, G_d, Sal, Temp, a_frac, cocco_frac)][order(ID)]

d_spec <- d[,.(ID, wavelen, Rrs, agp, bp, bbp, aw, bw, ad, aph)]

var_spec <- c("Rrs", "agp", "bp", "bbp", "aw", "bw", "ad", "aph")

d_var_spec <- lapply(var_spec, \(x) dcast(d_spec, ID ~ wavelen, value.var = x)[order(ID)])
names(d_var_spec) <- var_spec

fwrite(d_sing, "/Users/Bi/Documents/GitHub/pyOWT/test_running/reshape_netcdf_temp_data/single_variable.csv")

for(var in var_spec){
    fwrite(d_var_spec[[var]], sprintf("/Users/Bi/Documents/GitHub/pyOWT/test_running/reshape_netcdf_temp_data/spec_%s.csv", var))
}
