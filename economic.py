# In this module the economical calculations are performed
import pandas as pd 
import numpy as np 

def fuel_cost(gen_production, gen_capacity, fuel_consumption, fuel_price): 
    """
    Calculate generator cost for a year.

    Args:
        gen_production (list or array): Generator production in kW values over time, output of powerflow calculations.
        gen_capacity (float): Generator capacity in kW.
        diesel_consumption (float): Diesel consumption rate in L/h
        diesel_price (float): Price of diesel fuel in €/L

    Returns:
        list: A list containing [gen_hours, diesel_consumption_year, diesel_price_year].
    """
    # Converting gen_production in array 
    gen_production = np.array(gen_production)
    
    gen_hours = generator_hours(gen_production,  gen_capacity)
    
    # Calculate the yearly diesel cost 
    diesel_consumption_year = fuel_consumption * gen_hours  # Diesel consumption in liters per year
    fuel_price_year = diesel_consumption_year * fuel_price  # Diesel cost in currency units per year
    
    return [gen_hours, diesel_consumption_year, fuel_price_year]

def generator_hours(gen_production,  gen_capacity): 
    # Initialize the variable to keep track of generator hours
    gen_hours = 0

    # Iterate over the generator production values
    for i in range(len(gen_production)):
        if gen_production[i] < 0: 
            if gen_production[i] >= - gen_capacity[0]:
                # If one generator is active, add 15 minutes (1/4 hour) to gen_hours
                gen_hours += 0.25
            elif gen_production[i] >= - (gen_capacity[0] + gen_capacity[1]):
                # If two generators are active, add 30 minutes (0.5 hour) to gen_hours
                gen_hours += 0.5
            else:
                # If three generators are active, add 45 minutes (0.75 hour) to gen_hours
                gen_hours += 0.75
        else:
            # Generator is not active, no hours are accounted for
            gen_hours += 0 
            
    return gen_hours
    
def calculate_costs(df_input, df_out):
    df_in = df_input['Value'] # Using only the input values
    df_sum = df_out.sum()/4000 
    gen_capacity = np.array([df_in['gen1_capacity'], df_in['gen2_capacity'], df_in['gen3_capacity']])
    [gen_hours, fuel_cosnumption_year, fuel_cost_year] = fuel_cost(df_out.gen_production, gen_capacity, df_in['gen_fuel_consumption'], df_in['gen_fuel_price'])
    grid_cost_year = (df_sum.grid_consumption + df_sum.grid_battery) * df_in['grid_energy_price']
    grid_capacity_cost_year = df_in['grid_supply_capacity'] * df_in['capacity_cost']
    grid_return_year = (df_sum.pv_grid) * df_in['grid_feedin_price']
    consumption_return_year = (df_sum.consumption) * df_in['consumption_energy_price'] 
    pv_lease = df_in['pv_lease'] * df_in['pv_capacity']
    batt_lease = df_in['batt_lease'] * df_in['batt_energy_capacity']
    gen_lease = df_in['gen_lease'] * df_in['number_generators']
    
    # Defining the dataset of costs and revenues

    df_cost_balance = pd.DataFrame({
        'Solar': [-pv_lease, 0, 0, "#FFC400"],
        'Battery': [-batt_lease, 0, 0, "#56C568"],
        'Generator': [-gen_lease, -fuel_cost_year, 0, "#808080" ],
        'Grid': [-grid_capacity_cost_year, -int(grid_cost_year), int(grid_return_year), "#0FACD1"],
        'Consumption': [0, 0, consumption_return_year, 'pink']
        }, index = ['Fixed cost', 'Variable cost', 'Variable revenue', 'Color'])
    
    return df_cost_balance
