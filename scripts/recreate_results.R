library(tidyverse)
library(glue)
library(here)
library(magrittr)

# Path to derivation scripts.
derive <- here("scripts", "derive")
# Import derivation script.
source(file.path(derive, "csd2pc_ri.R"))

# Which analyses to run:
derive_csd2pc_ri_2011 <- TRUE  # Derive 2011 CSD-to-PopCtr Remoteness Index values.
derive_csd2pc_ri_2016 <- TRUE  # Derive 2016 CSD-to-PopCtr Remoteness Index values.

# Derive 2011 Remoteness Index.
if (derive_csd2pc_ri_2011) {
  calc_csd2pc_ri(2011, cost_km = 0.17)
}

# Derive 2016 Remoteness Index.
if (derive_csd2pc_ri_2016) {
  calc_csd2pc_ri(2016, cost_km = 0.16)
}
