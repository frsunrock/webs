#In this code, the relevant profiles and files from the excel model will be imported  
#importing libraries 
import pandas as pd 
import csv 
import pickle
import numpy as np


def import_data_from_excel(filename):
# Define the filename of the Excel file for the Type-A model (used as a test)

    # Import and read the input sheet from the Excel file
    df_input = pd.read_excel(filename, sheet_name='Input', nrows = 85)
    df_input.columns = ['A', 'B', 'C', 'D', 'E', 'F']  # Rename columns to match Excel columns
    df_input_new = pd.DataFrame(index=range(len(df_input) + 2), columns=df_input.columns) # Creating a new resized df
    df_input_new.iloc[2:] = df_input.values # Shifting index to match excel index in the new df
    df_input = df_input_new

    # Define input values
    grid_supply_capacity = df_input.loc[10, 'E']  # Contracted supply capacity in kVA
    grid_feedin_capacity = df_input.loc[11, 'E']  # Feed-in capacity in kVA

    pv_capacity = df_input.loc[34, 'E']  # PV capacity in kWp
    pv_yield = df_input.loc[35, 'E']  # PV specific yield in kWh/kWp
    pv_overdim = df_input.loc[37, 'E']  # PV DC/AC ratio

    batt_switch = df_input.loc[40, 'E'] # Battery switch. If 1 battery on 
    batt_power_capacity = df_input.loc[41, 'E'] # Battery power capacity in kW
    batt_energy_capacity = df_input.loc[42, 'E'] # Battery power capacity in kW
    batt_efficiency = df_input.loc[44, 'E'] # Battery power capacity in %
    
    gen_switch = df_input.loc[47, 'E'] #generator switch. If 1 generator is on.
    gen_capacity = np.array([df_input.loc[48, 'E'], df_input.loc[49, 'E'], df_input.loc[50, 'E']]) # Power capacity of generators in kW
    gen_soc_trigger = np.array([df_input.loc[54, 'E'], df_input.loc[55, 'E'], df_input.loc[56, 'E']])  # Battery SOC trigger of generators in %
    gen_fuel_consumption = df_input.loc[58, 'E']  # Fuel consumption of generators in L/hr
    gen_fuel_price = df_input.loc[74, 'E']  # Fuel cost of generators in €/hr
    grid_energy_price = df_input.loc[75, 'E'] # Price of energy from the grid in €/MWH
    grid_feedin_price = df_input.loc[77, 'E'] # Price of energy sold to the grid in €/MWh
    consumption_energy_price = df_input.loc[78, 'E'] # Price of energy sold to the grid in €/MWh

    # Import profiles
    df_profiles = pd.read_excel(filename, sheet_name='Profiles')
    consumption_energy = df_profiles['Consumption (kWh)'] #energy consumption array in kWh
    pv_production_energy = df_profiles['Production (kWh) per MWp'] #PV energy production array in kWh per MWp
    df_profiles = df_profiles[['Time','Consumption (kWh)', 'Production (kWh) per MWp']]
    

    # Define the input variables
    data = {
        'pv_capacity': {
            'Description': 'PV capacity (kW)',
            'Value': pv_capacity,
        },
        'pv_yield': {
            'Description': 'PV energy yield (kWh/kWp)',
            'Value': pv_yield,
        },
        'pv_overdim': {
            'Description': 'Overdimension factor',
            'Value': pv_overdim,
        },
        'batt_power_capacity': {
            'Description': 'Battery power capacity (kW)',
            'Value': batt_power_capacity,
        },
        'batt_energy_capacity': {
            'Description': 'Battery energy capacity (kWh)',
            'Value': batt_energy_capacity,
        },
        'batt_efficiency': {
            'Description': 'Battery one way efficiency (%)',
            'Value': batt_efficiency,
        },
        'grid_supply_capacity': {
            'Description': 'Grid supply capacity (kW)',
            'Value': grid_supply_capacity,
        },
        'grid_feedin_capacity': {
            'Description': 'Grid feed-in capacity (kW)',
            'Value': grid_feedin_capacity,
        },
        'number_generators': {
            'Description': 'Number of generators',
            'Value': np.count_nonzero(gen_capacity),
        },
        'gen1_capacity': {
            'Description': 'Generator 1 power capacity',
            'Value': gen_capacity[0],
        },
        'gen2_capacity': {
            'Description': 'Generator 2 power capacity',
            'Value': gen_capacity[1],
        },
        'gen3_capacity': {
            'Description': 'Generator 3 power capacity',
            'Value': gen_capacity[2],
        },
        'gen1_soc_trigger': {
            'Description': 'Generator 1 soc trigger activation (%)',
            'Value': gen_soc_trigger[0],
        },
        'gen2_soc_trigger': {
            'Description': 'Generator 2 soc trigger activation (%)',
            'Value': gen_soc_trigger[1],
        },
        'gen3_soc_trigger': {
            'Description': 'Generator 3 soc trigger activation (%)',
            'Value': gen_soc_trigger[2],
        },
        'gen_fuel_consumption': {
            'Description': 'Generator fuel consumption (kWh/L)',
            'Value': gen_fuel_consumption,
        },
        'gen_fuel_price': {
            'Description': 'Generator fuel price (EUR/L)',
            'Value': gen_fuel_price,
        },
        'grid_energy_price': {
            'Description': 'Grid energy price (EUR/MWh)',
            'Value': grid_energy_price,
        },
        'grid_feedin_price': {
            'Description': 'Grid feed-in price (EUR/MWh)',
            'Value': grid_feedin_price,
        },
        'consumption_energy_price': {
            'Description': 'Consumption energy price',
            'Value': consumption_energy_price,
        },
        'capacity_cost': {
            'Description': 'Capacity cost (EUR/kW/month)',
            'Value': 3.0,
        },
        'pv_lease': {
            'Description': 'PV lease (EUR/kWp/year)',
            'Value': 100,
        },
        'batt_lease': {
            'Description': 'Battery lease (EUR/kWh/year)',
            'Value': 150,
        },
        'gen_lease': {
            'Description': 'Generator lease (EUR/unit/year)',
            'Value': 25000,
        },
    
    }
    df_input = pd.DataFrame(data).T
    df_input.columns = ['Description', 'Value']
    
    return df_input, df_profiles 

def pickle_write(df, filename):
    """
    Serialize and save a DataFrame to a pickle file.

    Parameters:
    df (pd.DataFrame): The DataFrame to be saved.
    filename (str): The name of the pickle file (without the '.pkl' extension).
    """
    with open(filename + '.pkl', 'wb') as file:
        pickle.dump(df, file)

def pickle_read(filename):
    """
    Load and deserialize a DataFrame from a pickle file.

    Parameters:
    filename (str): The name of the pickle file (without the '.pkl' extension).

    Returns:
    pd.DataFrame: The DataFrame loaded from the pickle file.
    """ 
    with open(filename + '.pkl', 'rb') as file:
        df = pickle.load(file)
    return df
     

def data_to_csv(df, filename):
    """
    Write a DataFrame to a CSV file.

    Parameters:
    df (pd.DataFrame): The DataFrame to be saved.
    filename (str): The name of the CSV file (without the '.csv' extension).
    """
    df.to_csv(filename + '.csv', index=True)
    print(df)
    
def read_from_csv(filename):
    """
    Read data from a CSV file and return it as a DataFrame.

    Parameters:
    filename (str): The name of the CSV file (without the '.csv' extension).

    Returns:
    pd.DataFrame: The DataFrame containing data read from the CSV file.
    """
    df_read = pd.read_csv(filename + '.csv', index_col = 0)
    return df_read
    
# dir = "c:/Users/SR/OneDrive - Sunrock Investments B.V/Documenten/type-a/V02/" # Input file directory 
# df_input, df_profiles = import_data_from_excel('Test2_Fullyear.xlsx')
# pickle_write(df_input, 'Input_variables')
# pickle_write(df_profiles, 'Input_profiles')
# data_to_csv(df_input,'Input_variables')
# data_to_csv(df_profiles, 'Input_profiles')

# df = read_from_csv('Input_variables')
# df_series = df['Value']
# print(df_series['pv_capacity'], df_series['pv_yield'])