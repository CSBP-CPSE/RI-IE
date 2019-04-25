# CSD to PopCtr agglomeration level calculation.
# Remoteness Index code ported from SAS to Python.
import pandas as pd
from pathlib import Path

# Set paths.
riwd = Path().resolve()  # Remoteness Index working directory.
inputs = riwd.joinpath("data", "csd2pc")  # Path to data read into the script.
outputs = riwd.joinpath("results", "csd2pc")  # Path to data written out of the script.

# Derive agglomeration level estimates.
def calc_csd2pc_ri(year, cost_km):
  year2 = int(str(year)[-2:])  # Two digit year format.
  km_h = 80  # Average distance travelled per hour.
  isochrone_hours = 2.5  # Travel radius in hours.
  # Travel radius in dollars; 2016: (2.5 * 80 * 0.16) = 32, 2011: (2.5 * 80 * 0.17) = 34.
  isochrone_dollars = isochrone_hours * km_h * cost_km
  min_travel_cost = 3 # Minimum cost of travelling regardless of distance.
  oos = -1  # A travel cost of -1 denotes CSDs that are further than 300 km away from the origin CSD.

  # Read the CSD to PopCtr travel cost matrix (with names).
  # 2016: Based on 16 cents/km driving or $32 radius, 2011: Based on 17 cents/km driving or $34 radius.
  # Note: costs are rounded to dollars.
  distance = pd.read_csv(inputs.joinpath(f"cost-matrix{year2}.txt"), sep="\t", index_col="CSDUID")

  # Read the Population Centres data.
  pop = pd.read_csv(inputs.joinpath(f"pop{year2}.txt"), sep="\t", index_col="PopCtr")

  # Read the CSD data.
  csd = pd.read_csv(inputs.joinpath(f"names{year2}.txt"), sep="\t", index_col="CSDUID")

  # Transposing the travel cost matrix so that PopCtrs are all in one column.
  prox = pd.melt(distance.reset_index(), id_vars="CSDUID", value_vars=distance.columns.values,
                 var_name="PopCtr", value_name="TravelCost")
  # Delete all values where TravelCost = -1.
  prox = prox.loc[prox["TravelCost"] != oos].set_index("CSDUID")
  # Bring in the population counts for each PopCtr into the data set.
  prox = pd.merge(prox, pop, "left", left_on="PopCtr", right_index=True)

  # Calculating the sum of the ratios of population to travel cost for each of the two cases.
  # Case 1: The CSD is inside the $32 (2016) or $34 (2011) isochrone.
  # First, delete if travel cost > $32 (2016) or travel cost > $34 (2011).
  prox_case1 = prox.loc[prox["TravelCost"] <= isochrone_dollars]
  # Set the minimum travel cost to $3 and create the population to travel cost ratio.
  prox_case1["AdjTravelCost"] = prox_case1["TravelCost"].clip(lower=min_travel_cost)
  prox_case1["UnitAggLvl"] = prox_case1["Pop"] / prox_case1["AdjTravelCost"]
  # Sum the unit agglomeration levels (pop to tc ratio) to give remoteness in level terms.
  prox_case1 = prox_case1.groupby(level="CSDUID")[["UnitAggLvl"]].sum().rename(columns={"UnitAggLvl": "AL1"})

  # Case 2: Find the minimum travel cost to a PopCtr for the CSDs who don't have a PopCtr within their isochrone.
  prox_case2 = prox.copy()
  # Set minimum travel cost to $3.
  prox_case2["AdjTravelCost"] = prox_case2["TravelCost"].clip(lower=min_travel_cost)
  # Keep the minimum travel cost for each CSD.
  idx = prox_case2.groupby(level="CSDUID")["AdjTravelCost"].transform(min) == prox_case2["AdjTravelCost"]
  prox_case2 = prox_case2[idx]
  # Keep the first PopCtr with minimum travel cost for each CSD if multiple exist.
  prox_case2 = prox_case2[~prox_case2.index.duplicated(keep="first")]
  # Remove all Case 1 CSDs.
  prox_case2 = prox_case2.loc[prox_case2["AdjTravelCost"] > isochrone_dollars]
  prox_case2["AL2"] = prox_case2["Pop"] / prox_case2["AdjTravelCost"]
  prox_case2 = prox_case2.loc[:, ["AL2"]]

  # Merge the Case 1 and Case 2 data sets.
  agg_lvl = prox_case1.merge(prox_case2, "outer", left_index=True, right_index=True) \
                      .merge(csd, "outer", left_index=True, right_index=True)
  # Create one variable for the agglomeration level.
  agg_lvl["AggLvl"] = agg_lvl["AL1"].combine_first(agg_lvl["AL2"])
  agg_lvl = agg_lvl.drop(columns=["AL1", "AL2"]).sort_index()

  # Write to csv file.
  agg_lvl.to_csv(outputs.joinpath(f"RI-{year}-Py.csv"))
