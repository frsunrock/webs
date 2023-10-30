import pandas as pd 
import numpy as np 


def set_limits(vec, min_val, max_val):
    # This function casts the values of the vector vec to be in the range [min_val, max_val].
    if isinstance(vec, float) or isinstance(vec, int): 
        return min(max_val, max(min_val, vec))
    else: 
        return np.array([min(max_val, max(min_val, val)) for val in vec])
    
    

# In this module the main function for carrying power flow calculations is defined 
def calculate_power_flow_new(df_input, df_profiles):

    df_in = df_input['Value'] # Just selecting the Value column for the calculations 
    grid_supply_capacity =  df_in['grid_supply_capacity']
    grid_feedin_capacity = df_in['grid_feedin_capacity']
    pv_capacity = df_in['pv_capacity']
    pv_yield = df_in['pv_yield']
    pv_overdim = df_in['pv_overdim']
    batt_power_capacity = df_in['batt_power_capacity']
    batt_energy_capacity = df_in['batt_energy_capacity']
    batt_efficiency = df_in['batt_efficiency']
    gen_capacity = [df_in['gen1_capacity'], df_in['gen2_capacity'], df_in['gen3_capacity']]
    gen_soc_trigger = [df_in['gen1_soc_trigger'], df_in['gen1_soc_trigger'], df_in['gen1_soc_trigger']]
    gen_fuel_consumption = df_in['gen_fuel_consumption']
    grid_soc_trigger = df_in['grid_soc_trigger']
    batt_soc_minimum = df_in['batt_soc_minimum']
    consumption_energy = df_profiles['Consumption (kWh)']
    pv_production_energy = df_profiles['Production (kWh) per MWp']


    consumption_energy = consumption_energy.to_numpy()
    pv_production_energy =  np.nan_to_num(pv_production_energy, nan = 0.0) #Production energy per MWp converted to array and set NaNs to 0 
    gen_capacity = np.array(gen_capacity)
    gen_soc_trigger = np.array(gen_soc_trigger)
    
    # Compute power consumption and PV production.
    consumption = consumption_energy * 4  # Power consumption in +kWcd
    pv_production = - pv_production_energy * pv_capacity * pv_yield / 947.55 * 4  # PV power production in -kW
    pv_production = set_limits(pv_production, - pv_capacity * pv_yield, 0) # Impose that PV production does not exceed the capacity limit.
    n = len(pv_production)

    # Battery and generator initial conditions
    batt_soc = batt_energy_capacity # Current battery state of charge: full
    gen_activation = np.array([0, 0, 0]) # Generation activation: off
    gen_stored_energy_trigger = gen_soc_trigger * batt_energy_capacity # Minimum energy in the battery in kWh to charge froms generator
    grid_stored_energy_trigger = grid_soc_trigger * batt_energy_capacity # Minimum energy in the battery in kWh to charge from grid 
    
    print(f"Grid stored energy trigger {grid_stored_energy_trigger}")
    
    # Initialization of consumption vectors 
    pv_consumption = np.zeros(n); 
    grid_consumption = np.zeros(n)
    gen_consumption = np.zeros(n)
    batt_consumption = np.zeros(n)
    gen_battery = np.zeros(n)
    pv_battery = np.zeros(n)
    grid_battery = np.zeros(n)
    pv_curtailment = np.zeros(n)
    pv_grid = np.zeros(n)
    pv_balance = np.zeros(n)
    green_batt_consumption = np.zeros(n)
    grey_batt_consumption = np.zeros(n)
    blue_batt_consumption = np.zeros(n)
    gen_production = np.zeros(n)
    batt_flow = np.zeros(n)
    batt_inflow = np.zeros(n)
    batt_outflow = np.zeros(n)
    batt_soc_energy = np.zeros(n)
    grid_interface = np.zeros(n)
    grid_inflow = np.zeros(n)
    grid_outflow = np.zeros(n)
    shortage_consumption = np.zeros(n)

    
    check = []


    for i in range(n): # For all points in time
        
    #----------------------- GENERATOR  ----------------------------------

    
        if (batt_soc >= grid_stored_energy_trigger) or (grid_stored_energy_trigger == 0): # If SOC is more than grid trigger SOC (type B)
            power_balance = consumption[i] + pv_production[i] # Energy balance before battery has no grid
        else: # (type A)
            power_balance = consumption[i] + pv_production[i] - grid_supply_capacity # Extra supply capacity needed by generators (battery and generator) in kW. If + there is excess demand, if - excess supply.
            print('Grid charges battery')
            print(f'Batt soc = {batt_soc}, Grid stored energy = {grid_stored_energy_trigger}')
    #----------------------- GENERATOR  ----------------------------------

        # Condition for generator 1 to be on
        if gen_capacity[0] and ( # If there is generator 1
            power_balance >= batt_power_capacity * batt_efficiency or # If the battery power capacity is not sufficient to meet demand-supply power inbalance 
            (batt_soc < gen_stored_energy_trigger[0]) or  # Or if the battery state of charge is below the limit set for generator 1
            (batt_soc < batt_energy_capacity * gen_activation[0]) # Or if the battery is not fully charged and the generator 1 is currently on
        ):
            gen_activation[0] = 1 # Generator 1 on
        else:
            gen_activation[0] = 0 # Generator 1 off
    
        # Condition for generator 2 to be on
        if gen_capacity[1] and ( # If there is a generator 2
            power_balance - gen_capacity[0] >= batt_power_capacity * batt_efficiency or # If the battery power capacity with generator 1 is not sufficient to meet demand-supply power inbalance 
            (batt_soc < gen_stored_energy_trigger[1]) or  # Or the battery state of charge is below the limit set for generator 2
            (batt_soc < batt_energy_capacity * gen_activation[1]) # Or if the battery is not fully charged and generator 2 is currently on
        ):
            gen_activation[1] = 1 # Generator 2 on
        else:
            gen_activation[1] = 0 # Generator 2 off

        # Condition for third generator to be on
        if gen_capacity[2] and ( #if there is generator 3
            power_balance - gen_capacity[0] - gen_capacity[1] >= batt_power_capacity * batt_efficiency or # if the battery power capacity with first and second generators is not sufficient to satisfy power inbalance 
            (batt_soc < gen_stored_energy_trigger[2]) or  # Or if the battery state of charge is below the limit set for generator 3
            (batt_soc < batt_energy_capacity * gen_activation[2]) # Or if the battery is not fully charged and generator 3 is currently on
        ):
            gen_activation[2] = 1 # Generator 3 on
        else:
            gen_activation[2] = 0 # Generator 3 off
            
            
        # Calculating the overall power produced by diesel generators and adding it to the power balance 
        gen_production[i] = -np.sum(gen_activation * gen_capacity) # Total generators production in -kW
        power_balance += gen_production[i] # Updating power balance to total capacity with generators in +- kW
       
    #----------------------- BATTERY ----------------------------------

        # Computing the power flow through the battery 
        batt_flow_desired = max(0, - power_balance) * batt_efficiency + min(0, - power_balance) / batt_efficiency # Battery to charge +kW or battery to discharge in -kW
        batt_flow_desired = set_limits(batt_flow_desired, - batt_power_capacity, + batt_power_capacity) # Limiting the desired inflow/outflow to the power capacity of the battery  
        batt_soc_new =  batt_soc + batt_flow_desired / 4 # New battery state of charge kWh
        batt_soc_new = set_limits(batt_soc_new, batt_soc_minimum*batt_energy_capacity, batt_energy_capacity) # Limiting the new battery state of charge to the battery energy capacity 
        batt_flow_actual = (batt_soc_new - batt_soc)*4 # Battery actually charged +kW or actually discharged -kW
        batt_soc = batt_soc_new # Updating the battery state of charge 
        if batt_flow_actual < 0:
            batt_loss = -batt_flow_actual * (1 - batt_efficiency) # Power loss in battery discharging kW
        else:
            batt_loss = -batt_flow_actual * (1 - 1 / batt_efficiency) # Power loss in battery charginf kW
        
        power_balance += batt_flow_actual + batt_loss # Updating power balance to include battery flow in +- kW
        
        batt_flow[i] = batt_flow_actual 
        batt_inflow[i] = max(batt_flow[i], 0)
        batt_outflow[i] = min(batt_flow[i], 0)
        batt_soc_energy[i] = batt_soc
    
    #-------------------------------- GRID ----------------------------------

        # Computing the grid interface, curtailments, overproduction and losses
        
        if (batt_soc >= grid_stored_energy_trigger) or (grid_stored_energy_trigger == 0): # If SOC is more than grid trigger SOC (type B)
            grid_interface_desired = - power_balance # Desired grid interface is the current power balance 
            grid_interface[i] = set_limits(grid_interface_desired, -grid_supply_capacity, grid_feedin_capacity)
            
            power_balance += grid_interface[i]
            
            curtailment_total = - min(0, grid_interface_desired-grid_interface[i])
            shortage_consumption[i] = max(0, power_balance + grid_interface[i])
        
        else: # (type A)
            curtailment_total = + max(0, - grid_supply_capacity - grid_feedin_capacity - power_balance ) # Total power curtailed in +kW. If there is excess supply, even if the grid supply is shut down, then it is curtailed
            grid_interface[i] = - (grid_supply_capacity + power_balance + curtailment_total) # Actual gird supply power in - kW. 0 in case of supply curtailment. 
            grid_interface[i] = set_limits(grid_interface[i], -grid_supply_capacity, grid_feedin_capacity) # Set the limits to grid_interface

           
    
        grid_inflow[i] = max(grid_interface[i], 0)
        grid_outflow[i] = min(grid_interface[i], 0)
        gen_loss = 0 # Feature still to be implemented 


    #----------------------- CONSUMPTION and BATTERY FLOWS ----------------------------------

        # Computing consumption breakdown  
        consumption_excess = consumption[i] # Variable that contains the consumption that is not yet satisfied by the production in kW
        pv_consumption[i] = max(0, min(-pv_production[i], consumption_excess)) # Total power flow from pv to consumption in kW
        consumption_excess -= pv_consumption[i] 
        grid_consumption[i] = max(0, min(-max(-grid_supply_capacity, grid_interface[i]), consumption_excess)) # Total power flow from grid to consumption in kW
        consumption_excess -= grid_consumption[i]
        gen_consumption[i] = max(0, min(-gen_production[i], consumption_excess)) # Total power flow from generator to consumption in kW
        consumption_excess -= gen_consumption[i]
        batt_consumption[i] = max(0, min(max(0, -batt_flow_actual), consumption_excess)) # Total power flow from generator to consumption in kW
        consumption_excess -= batt_consumption[i]
        shortage_consumption[i] = consumption_excess
        
        # Computing battery flows
        gen_overproduction = min(0, gen_production[i] + gen_consumption[i] + gen_loss + max(0, batt_flow_actual + batt_loss))
        gen_battery[i] = -min(0, gen_production[i] + gen_consumption[i] + gen_loss - gen_overproduction) # Total flow from generator to battery in kW.
        grid_battery[i] = -min(0, grid_interface[i] + consumption[i]) # Total flow from the grid to the battery in +kW. If there is excess grid supply, it is stored in the battery
        pv_battery[i] = max(0, batt_flow_actual + batt_loss - gen_battery[i] - grid_battery[i])
        green_batt_consumption[i] = pv_battery[i] * batt_efficiency**2
        grey_batt_consumption[i] = gen_battery[i] * batt_efficiency**2
        blue_batt_consumption[i] = grid_battery[i] * batt_efficiency**2
        
        # Computing pv power breakdown
        pv_curtailment[i] = - min(0, pv_consumption[i] + pv_battery[i] + pv_production[i] + max(0, grid_interface[i])) # PV curtailment in +kW. The excess pv power that is not consumed, fed in the battery or int he grid is curtailed 
        pv_grid[i] = -(pv_consumption[i] + pv_battery[i] + pv_production[i] + pv_curtailment[i]) # PV to grid. It is flawed because it takes negative values
        pv_balance[i] = pv_production[i] + pv_consumption[i] + pv_battery[i] + pv_grid[i] + pv_curtailment[i]

        # Changing signs for plotting 
        grid_interface[i] = -grid_interface[i]
        batt_flow[i] = - batt_flow[i]
        
# creating a datframe with all the outputs 
    df_out = pd.DataFrame({
        'consumption': consumption,
        'pv_production': pv_production,
        'pv_consumption': pv_consumption,
        'grid_consumption': grid_consumption,
        'gen_consumption': gen_consumption,
        'batt_consumption': batt_consumption,
        'gen_battery': gen_battery,
        'pv_battery': pv_battery,
        'grid_battery': grid_battery,
        'pv_curtailment': pv_curtailment,
        'pv_grid': pv_grid,
        'pv_balance': pv_balance,
        'green_batt_consumption': green_batt_consumption,
        'grey_batt_consumption': grey_batt_consumption,
        'blue_batt_consumption': blue_batt_consumption,
        'blue_batt_consumption': blue_batt_consumption,
        'gen_production': gen_production,
        'batt_flow': batt_flow,
        'batt_outflow': batt_outflow,
        'batt_inflow': batt_inflow,
        'batt_soc_energy': batt_soc_energy,
        'grid_interface': grid_interface,
        'grid_inflow': grid_inflow,
        'grid_outflow': grid_outflow,
        'shortage_consumption': shortage_consumption,
    })
    return df_out



# In this module the main function for carrying power flow calculations is defined 
def calculate_power_flow_old(df_input, df_profiles):

    df_in = df_input['Value'] # Just selecting the Value column for the calculations 
    grid_supply_capacity =  df_in['grid_supply_capacity']
    grid_feedin_capacity = df_in['grid_feedin_capacity']
    pv_capacity = df_in['pv_capacity']
    pv_yield = df_in['pv_yield']
    pv_overdim = df_in['pv_overdim']
    batt_power_capacity = df_in['batt_power_capacity']
    batt_energy_capacity = df_in['batt_energy_capacity']
    batt_efficiency = df_in['batt_efficiency']
    gen_capacity = [df_in['gen1_capacity'], df_in['gen2_capacity'], df_in['gen3_capacity']]
    gen_soc_trigger = [df_in['gen1_soc_trigger'], df_in['gen1_soc_trigger'], df_in['gen1_soc_trigger']]
    gen_fuel_consumption = df_in['gen_fuel_consumption']
    grid_soc_trigger = df_in['grid_soc_trigger']
    consumption_energy = df_profiles['Consumption (kWh)']
    pv_production_energy = df_profiles['Production (kWh) per MWp']


    consumption_energy = consumption_energy.to_numpy()
    pv_production_energy =  np.nan_to_num(pv_production_energy, nan = 0.0) #Production energy per MWp converted to array and set NaNs to 0 
    gen_capacity = np.array(gen_capacity)
    gen_soc_trigger = np.array(gen_soc_trigger)
    
    # Compute power consumption and PV production.
    consumption = consumption_energy * 4  # Power consumption in +kWcd
    pv_production = - pv_production_energy * pv_capacity * pv_yield / 947.55 * 4  # PV power production in -kW
    pv_production = set_limits(pv_production, - pv_capacity * pv_yield, 0) # Impose that PV production does not exceed the capacity limit.
    n = len(pv_production)

    # Battery and generator initial conditions
    batt_soc = batt_energy_capacity # Current battery state of charge: full
    gen_activation = np.array([0, 0, 0]) # Generation activation: off
    gen_stored_energy_trigger = gen_soc_trigger * batt_energy_capacity # Minimum energy in the battery in kWh to charge froms generator
    grid_stored_energy_trigger = grid_soc_trigger * batt_energy_capacity # Minimum energy in the battery in kWh to charge from grid 

    # Initialization of consumption vectors 
    pv_consumption = np.zeros(n); 
    grid_consumption = np.zeros(n)
    gen_consumption = np.zeros(n)
    batt_consumption = np.zeros(n)
    gen_battery = np.zeros(n)
    pv_battery = np.zeros(n)
    grid_battery = np.zeros(n)
    pv_curtailment = np.zeros(n)
    pv_grid = np.zeros(n)
    pv_balance = np.zeros(n)
    green_batt_consumption = np.zeros(n)
    grey_batt_consumption = np.zeros(n)
    blue_batt_consumption = np.zeros(n)
    gen_production = np.zeros(n)
    batt_flow = np.zeros(n)
    batt_inflow = np.zeros(n)
    batt_outflow = np.zeros(n)
    grid_interface = np.zeros(n)
    grid_inflow = np.zeros(n)
    grid_outflow = np.zeros(n)
    shortage_consumption = np.zeros(n)
    
    check = []


    for i in range(n): # For all points in time
        
    #----------------------- GENERATOR  ----------------------------------

    

        power_balance = consumption[i] + pv_production[i] - grid_supply_capacity # Extra supply capacity needed by generators (battery and generator) in kW. If + there is excess demand, if - excess supply.

        # Condition for generator 1 to be on
        if gen_capacity[0] and ( # If there is generator 1
            power_balance >= batt_power_capacity * batt_efficiency or # If the battery power capacity is not sufficient to meet demand-supply power inbalance 
            (batt_soc < gen_stored_energy_trigger[0]) or  # Or if the battery state of charge is below the limit set for generator 1
            (batt_soc < batt_energy_capacity * gen_activation[0]) # Or if the battery is not fully charged and the generator 1 is currently on
        ):
            gen_activation[0] = 1 # Generator 1 on
        else:
            gen_activation[0] = 0 # Generator 1 off
    
        # Condition for generator 2 to be on
        if gen_capacity[1] and ( # If there is a generator 2
            power_balance - gen_capacity[0] >= batt_power_capacity * batt_efficiency or # If the battery power capacity with generator 1 is not sufficient to meet demand-supply power inbalance 
            (batt_soc < gen_stored_energy_trigger[1]) or  # Or the battery state of charge is below the limit set for generator 2
            (batt_soc < batt_energy_capacity * gen_activation[1]) # Or if the battery is not fully charged and generator 2 is currently on
        ):
            gen_activation[1] = 1 # Generator 2 on
        else:
            gen_activation[1] = 0 # Generator 2 off

        # Condition for third generator to be on
        if gen_capacity[2] and ( #if there is generator 3
            power_balance - gen_capacity[0] - gen_capacity[1] >= batt_power_capacity * batt_efficiency or # if the battery power capacity with first and second generators is not sufficient to satisfy power inbalance 
            (batt_soc < gen_stored_energy_trigger[2]) or  # Or if the battery state of charge is below the limit set for generator 3
            (batt_soc < batt_energy_capacity * gen_activation[2]) # Or if the battery is not fully charged and generator 3 is currently on
        ):
            gen_activation[2] = 1 # Generator 3 on
        else:
            gen_activation[2] = 0 # Generator 3 off
            
            
        # Calculating the overall power produced by diesel generators and adding it to the power balance 
        gen_production[i] = -np.sum(gen_activation * gen_capacity) # Total generators production in -kW
        power_balance += gen_production[i] # Updating power balance to total capacity with generators in +- kW
       
    #----------------------- BATTERY ----------------------------------

        # Computing the power flow through the battery 
        batt_flow_desired = max(0, - power_balance) * batt_efficiency + min(0, - power_balance) / batt_efficiency # Battery to charge +kW or battery to discharge in -kW
        batt_flow_desired = set_limits(batt_flow_desired, - batt_power_capacity, + batt_power_capacity) # Limiting the desired inflow/outflow to the power capacity of the battery  
        batt_soc_new =  batt_soc + batt_flow_desired / 4 # New battery state of charge kWh
        batt_soc_new = set_limits(batt_soc_new, 0, batt_energy_capacity) # Limiting the new battery state of charge to the battery energy capacity 
        batt_flow_actual = (batt_soc_new - batt_soc)*4 # Battery actually charged +kW or actually discharged -kW
        batt_soc = batt_soc_new # Updating the battery state of charge 
        if batt_flow_actual < 0:
            batt_loss = -batt_flow_actual * (1 - batt_efficiency) # Power loss in battery discharging kW
        else:
            batt_loss = -batt_flow_actual * (1 - 1 / batt_efficiency) # Power loss in battery charginf kW
        
        power_balance += batt_flow_actual + batt_loss # Updating power balance to include battery flow in +- kW
        
        batt_flow[i] = batt_flow_actual 
        batt_inflow[i] = max(batt_flow[i], 0)
        batt_outflow[i] = min(batt_flow[i], 0)
    
    #-------------------------------- GRID ----------------------------------

        # Computing the grid interface, curtailments, overproduction and losses
        

        curtailment_total = + max(0, - grid_supply_capacity - grid_feedin_capacity - power_balance ) # Total power curtailed in +kW. If there is excess supply, even if the grid supply is shut down, then it is curtailed
        grid_interface[i] = - (grid_supply_capacity + power_balance + curtailment_total) # Actual gird supply power in - kW. 0 in case of supply curtailment. 
        grid_interface[i] = set_limits(grid_interface[i], -grid_supply_capacity, grid_feedin_capacity) # Set the limits to grid_interface
        grid_inflow[i] = max(grid_interface[i], 0)
        grid_outflow[i] = min(grid_interface[i], 0)
        gen_loss = 0 # Feature still to be implemented 
    

    #----------------------- CONSUMPTION and BATTERY FLOWS ----------------------------------

        # Computing consumption breakdown  
        consumption_excess = consumption[i] # Variable that contains the consumption that is not yet satisfied by the production in kW
        pv_consumption[i] = max(0, min(-pv_production[i], consumption_excess)) # Total power flow from pv to consumption in kW
        consumption_excess -= pv_consumption[i] 
        grid_consumption[i] = max(0, min(-max(-grid_supply_capacity, grid_interface[i]), consumption_excess)) # Total power flow from grid to consumption in kW
        consumption_excess -= grid_consumption[i]
        gen_consumption[i] = max(0, min(-gen_production[i], consumption_excess)) # Total power flow from generator to consumption in kW
        consumption_excess -= gen_consumption[i]
        batt_consumption[i] = max(0, min(max(0, -batt_flow_actual), consumption_excess)) # Total power flow from generator to consumption in kW
        consumption_excess -= batt_consumption[i]
        shortage_consumption[i] = consumption_excess
        
        # Computing battery flows
        gen_overproduction = min(0, gen_production[i] + gen_consumption[i] + gen_loss + max(0, batt_flow_actual + batt_loss))
        gen_battery[i] = -min(0, gen_production[i] + gen_consumption[i] + gen_loss - gen_overproduction) # Total flow from generator to battery in kW.
        grid_battery[i] = -min(0, grid_interface[i] + consumption[i]) # Total flow from the grid to the battery in +kW. If there is excess grid supply, it is stored in the battery
        pv_battery[i] = max(0, batt_flow_actual + batt_loss - gen_battery[i] - grid_battery[i])
        green_batt_consumption[i] = pv_battery[i] * batt_efficiency**2
        grey_batt_consumption[i] = gen_battery[i] * batt_efficiency**2
        blue_batt_consumption[i] = grid_battery[i] * batt_efficiency**2
        
        # Computing pv power breakdown
        pv_curtailment[i] = - min(0, pv_consumption[i] + pv_battery[i] + pv_production[i] + max(0, grid_interface[i])) # PV curtailment in +kW. The excess pv power that is not consumed, fed in the battery or int he grid is curtailed 
        pv_grid[i] = -(pv_consumption[i] + pv_battery[i] + pv_production[i] + pv_curtailment[i]) # PV to grid. It is flawed because it takes negative values
        pv_balance[i] = pv_production[i] + pv_consumption[i] + pv_battery[i] + pv_grid[i] + pv_curtailment[i]

# creating a datframe with all the outputs 
    df_out = pd.DataFrame({
        'consumption': consumption,
        'pv_production': pv_production,
        'pv_consumption': pv_consumption,
        'grid_consumption': grid_consumption,
        'gen_consumption': gen_consumption,
        'batt_consumption': batt_consumption,
        'gen_battery': gen_battery,
        'pv_battery': pv_battery,
        'grid_battery': grid_battery,
        'pv_curtailment': pv_curtailment,
        'pv_grid': pv_grid,
        'pv_balance': pv_balance,
        'green_batt_consumption': green_batt_consumption,
        'grey_batt_consumption': grey_batt_consumption,
        'blue_batt_consumption': blue_batt_consumption,
        'blue_batt_consumption': blue_batt_consumption,
        'gen_production': gen_production,
        'batt_flow': batt_flow,
        'batt_outflow': batt_outflow,
        'batt_inflow': batt_inflow,
        'grid_interface': grid_interface,
        'grid_inflow': grid_inflow,
        'grid_outflow': grid_outflow,
        'shortage_consumption': shortage_consumption,
    })
    return df_out






