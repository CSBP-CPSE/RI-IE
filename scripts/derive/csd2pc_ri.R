# CSD to PopCtr agglomeration level calculation.
# Remoteness Index code ported from SAS to R.

# Set paths.
inputs <- here("data", "csd2pc") # Path to data read into the script.
outputs <- here("results", "csd2pc") # Path to data written out of the script.

# Clip variable to lower and/or upper bounds.
bound <- function(x, lower = pmin(x), upper = pmax(x)) {pmax(lower, pmin(x, upper))}

# Derive agglomeration level estimates.
calc_csd2pc_ri <- function(year, cost_km) {
  # Set constants.
  year2 <- as.integer(str_sub(as.character(year), -2)) # Two digit year format.
  km_h <- 80 # Average distance travelled per hour.
  isochrone_hours <- 2.5 # Travel radius in hours.
  # Travel radius in dollars; 2016: (2.5 * 80 * 0.16) = 32, 2011: (2.5 * 80 * 0.17) = 34.
  isochrone_dollars <- isochrone_hours * km_h * cost_km
  min_travel_cost <- 3L # Minimum cost of travelling regardless of distance.
  oos <- -1L # A travel cost of -1 denotes CSDs that are further than 300 km away from the origin CSD.
  
  # Read the CSD to PopCtr travel cost matrix (with names).
  # 2016: Based on 16 cents/km driving or $32 radius, 2011: Based on 17 cents/km driving or $34 radius.
  # Note: costs are rounded to dollars.
  distance <- read_tsv(file.path(inputs, glue("cost-matrix{year2}.txt"))) 
  
  # Read the Population Centres data.
  pop <- read_tsv(file.path(inputs, glue("pop{year2}.txt")))
  
  # Read the CSD data.
  csd <- read_tsv(file.path(inputs, glue("names{year2}.txt")))
  
  # Transposing the travel cost matrix so that PopCtrs are all in one column.
  prox <- distance %>%
    gather(PopCtr, TravelCost, -CSDUID) %>%
    # Delete all values where travelcost = -1.
    filter(TravelCost != oos) %>%
    mutate_at(vars(PopCtr), as.character) %>%
    mutate_at(vars(TravelCost), as.integer) %>%
    # Bring in the population counts for each PopCtr into the data set.
    left_join(pop, by = "PopCtr")
  
  # Calculating the sum of the ratios of population to travel cost for each of the two cases.
  # Case 1: The CSD is inside the $32 (2016) or $34 (2011) isochrone.
  prox_case1 <- prox %>%
    # First, delete if travel cost > $32 (2016) or travel cost > $34 (2011).
    filter(TravelCost <= isochrone_dollars) %>%
    # Set the minimum travel cost to $3 and create the population to travel cost ratio.
    mutate(
      AdjTravelCost = bound(TravelCost, min_travel_cost),
      UnitAggLvl = Pop/AdjTravelCost
    ) %>%
    # Sum the unit agglomeration levels (pop to tc ratio) to give remoteness in level terms.
    group_by(CSDUID) %>%
    summarise(AL1 = sum(UnitAggLvl, na.rm = TRUE))
  
  # Case 2: Find the minimum travel cost to a PopCtr for the CSDs who don't have a PopCtr within their isochrone.
  prox_case2 <- prox %>%
    # Set minimum travel cost to $3.
    mutate(AdjTravelCost = bound(TravelCost, min_travel_cost)) %>%
    group_by(CSDUID) %>%
    # Keep the minimum travel cost for each CSD and
    # if multiple exist, keep the first PopCtr with the minimum travel cost for each CSD.
    slice(which.min(AdjTravelCost)) %>%
    # Remove all Case 1 CSDs.
    filter(AdjTravelCost > isochrone_dollars) %>%
    mutate(AL2 = Pop/AdjTravelCost) %>%
    select(CSDUID, AL2)
  
  # Merge the Case 1 and Case 2 data sets.
  agg_lvl <- full_join(prox_case1, prox_case2, by = "CSDUID") %>%
    full_join(csd, by = "CSDUID") %>%
    # Create one variable for the agglomeration level.
    mutate(AggLvl = coalesce(AL1, AL2)) %>%
    arrange(CSDUID) %>%
    select(-c(AL1, AL2))
  
  # Write to csv file.
  agg_lvl %>% write_csv(file.path(outputs, glue("RI-{year}-R.csv")))
}





