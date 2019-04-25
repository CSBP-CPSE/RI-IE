from pathlib import Path
import os
import sys

# Remoteness Index working directory (the path to the "RI-IE" directory).
riwd = Path("").absolute()  # E.g., Path("C:/Users/user/Documents/RI-IE").absolute()
os.chdir(riwd)
# Path to derivation scripts.
derive_scripts = riwd.joinpath("scripts", "derive")
sys.path.append(str(derive_scripts))
# Import derivation script.
import csd2pc_ri as drv

# Which analyses to run:
derive_csd2pc_ri_2011 = True  # Derive 2011 CSD-to-PopCtr Remoteness Index values.
derive_csd2pc_ri_2016 = True  # Derive 2016 CSD-to-PopCtr Remoteness Index values.

if derive_csd2pc_ri_2011:
  drv.calc_csd2pc_ri(2011, cost_km=0.17)

if derive_csd2pc_ri_2016:
  drv.calc_csd2pc_ri(2016, cost_km=0.16)
