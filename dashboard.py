import streamlit as st
import pandas as pd 
import os 
import matplotlib as plt
import csv
from helpers import * # Helper functions 
from powerflow import * # Function to carry power flow calculations
from economic import * # Functions to carry economical calcualtions
from streamlit_helpers import * # Functions to carry some streamlit commands (plotting and obtaining inputs)
import numpy as np
import warnings
import plotly.graph_objects as go
import plotly.express as px # Importing plots in website, interative plots
import calendar
from datetime import datetime, date, timedelta
import time

start_time = time.time() # Starting timer
 
#%% ---------------------------- USEFUL FUNCTIONS ----------------------------------
def numeric_user_input(df_input, variable, value_type = int, max_value = None): 
    """
    This function allows the user to input a numeric value for a specific variable in a DataFrame.

    Parameters:
    df_input (pd.DataFrame): The input DataFrame where the variable's value will be updated.
    variable (str): The name of the variable to update in the DataFrame.
    value_type (type, optional): The data type for the input value (int or float). Defaults to int.
    max_value (float, optional): The maximum allowed value for the input. If None, it's set to 10 times the current value of the variable.

    Returns:
    pd.DataFrame: The updated DataFrame with the variable's value modified based on the user input.
    """
    
    old_value = df_input.loc[variable]['Value']
    if max_value == None: # If no max value is provided 
        max_value = 10*old_value # Setting a maximum value 
  
    if value_type == int:
        new_value = st.sidebar.number_input(df_input.loc[variable]['Description'], value = int(old_value), min_value = 0, max_value = int(max_value), step = 1); 
    elif value_type == float:
        new_value = st.sidebar.number_input(df_input.loc[variable]['Description'], value = float(old_value), min_value = 0.0, max_value = float(max_value), step = 0.1); 
    
   
    df_input.loc[variable,'Value'] = new_value # Updating the input dataset 
    
    return df_input

def plot_pie_chart(settings, df_sum): 
    """
    Create a pie chart figure fig based on the provided settings and DataFrame.

    Parameters:
    settings (list): A list containing data settings for the pie chart.
        Each item in the list should be a list with the following format: [data_label, label, color].
    df_sum (pd.DataFrame): The DataFrame from which data is extracted based on data labels.

    Returns:
    go.Figure: A Plotly figure representing the pie chart.
    """
    
    df = pd.DataFrame(settings)
    df.columns =["values", "label", "colors"]
    df['values'] = [df_sum[labels] for labels in df['values']] #Reading data from dataframe based on labels 
    df_total = df['values'].sum()
    df['values'] = [int(value) for value in df['values']] # Converting values to integers for better display
    color_map = dict(zip(df['label'], df['colors']))
    # Create a pie chart using go.Pie
    fig = go.Figure(data=[go.Pie(
        labels=df['label'],
        values=df['values'],
        title= dict(
            text= f'{df_total:.0f} MWh',
            font=dict(size=title_size)  # Adjust the font size as needed
        ),
        textinfo='percent',
        textfont_size=label_size, 
        hole=hole_size / 100,
        pull=[explode_parameter] + [0] * (len(df) - 1), # Exploding the sun (0) pie slice
        marker=dict(colors=[color_map[label] for label in df['label']], line=dict(color='#000000', width=0)),
        rotation=0,  # Set the starting angle at 90%
        direction='clockwise',  # Display the pie chart clockwise
    )])

    fig.update_layout(
        showlegend=True,
        legend=dict(
            font=dict(size=legend_size)  # Adjust the font size of the labels as needed
        ),
        margin = dict(t = 60) # Defining graph vertical positions
    )
    
    return fig

def plot_monthly_chart(settings, df_month, ytitle): 
    """
    Create and display a monthly area chart based on the provided settings and DataFrame.

    Parameters:
    settings (list): A list of data settings for the chart.
        Each item in the list should be a list with the following format: [data_column, legend_label, fill_color].
    df_month (pd.DataFrame): The DataFrame containing monthly data for the chart.
    ytitle (str): The title for the y-axis.

    Returns:
    go.Figure: A Plotly figure representing the monthly line chart.
    """
    
    months_list = calendar.month_abbr[1:] # List of months
    fig = go.Figure() # Initializing figure

    for j, row in enumerate(settings):
          # Add a trace (line) to the chart for each data series
        fig.add_trace(go.Scatter(
            x=months_list,        # X-axis: Months
            y=df_month[row[0]],   # Y-axis: Data from the specified column
            mode='lines',         # Plot as lines
            stackgroup='one',     # Define stack group (used for stacking)
            fillcolor=row[2],     # Set the fill color for the patch
            line=dict(color=row[2]),  # Set the line color
            name=row[1]            # Set the legend name
        ))

    fig.update_layout(
        showlegend=False,  # Do not display legend, since already displayed in pie-charts 
        legend=dict(
            font=dict(size=legend_size)  # Adjust the font size of the labels as needed
        ),
        yaxis_title=ytitle,   # Set the y-axis title
        margin=dict(b=200, t=0),  # Adjust chart margin (bottom and top)
    )

    return fig

def plot_day_chart(settings, df_day):    
    fig = go.Figure() # Initializing figure

    for j, row in enumerate(settings):
          # Add a trace (line) to the chart for each data series
        fig.add_trace(go.Scatter(
            x=df_day.index,      # X-axis: Months
            y=df_day[row[0]],   # Y-axis: Data from the specified column
            mode='lines',         # Plot as lines
            line=dict(color=row[2]),  # Set the line color
            name=row[1]            # Set the legend name
        ))

    fig.update_layout(
        showlegend=True,   
        legend=dict(
            font=dict(size=legend_size)  # Adjust the font size of the labels as needed
        ),
        yaxis_title="Power (kW)",   # Set the y-axis title
        margin=dict(b=100, t=0),  # Adjust chart margin (bottom and top)
    )

    return fig

def plot_day_chart_area(settings, df_day):    
    fig = go.Figure() # Initializing figure

    for j in [0,1,2,3]:
        fig.add_trace(go.Scatter(
            x=df_day.index,      # X-axis: Months
            y=df_day[settings[j][0]],   # Y-axis: Data from the specified column
            mode='lines',  
            stackgroup = 'production', 
            line=dict(color=settings[j][2], width = 0),  # Set the line color
            name=settings[j][1]            # Set the legend name
            ))
        
    for j in [4,5,6,7]:
        fig.add_trace(go.Scatter(
            x=df_day.index,      # X-axis: Months
            y=df_day[settings[j][0]],   # Y-axis: Data from the specified column
            mode='lines',  
            stackgroup = 'consumption', 
            line=dict(color=settings[j][2], width = 0),  # Set the line color
            name=settings[j][1]            # Set the legend name
            ))
        
    fig.update_layout(
        showlegend=True,  
        legend=dict(
            font=dict(size=legend_size)  # Adjust the font size of the labels as needed
        ),
        yaxis_title="Power (kW)",   # Set the y-axis title
        margin=dict(b=100, t=0),  # Adjust chart margin (bottom and top)
    )

    return fig
    


#%% -------------- PRSONALIZE THEME ------------------------------
#Defining theme colors
light_blue = "#429ef540" 
light_light_blue = "#429ef520" 
light_red = '#ffbaba'

# Title of the web-page
st.set_page_config(page_title = "Webs smart grid model", layout = 'wide', page_icon = 	':mostly_sunny:' )

# Set the title and subtitle 
st.title('WeBS model')
st.markdown('<style>div.block-container{padding-top:1rem;} span {color: #429ef5;}</style>', unsafe_allow_html = True)
#st.markdown("<p style='font-size: 18px; color: black; margin-top: -1rem; font-style: italic;'>Wind energy, Battery and Solar combined in one sizing model </p>", unsafe_allow_html=True)

# Changing side bar color
st.markdown(f"""
<style>
    [data-testid=stSidebar] {{
        background-color: {light_blue};
    }}
</style>
""", unsafe_allow_html=True)



#%% ------------ IMPORT INPUT FOR DEFAULT VALUES -------------------------

# Reading from input file
df_input = read_from_csv('Input_variables')
#df_input = pickle_read('Input_variables')

# Reading input data from uploaded file 
st.sidebar.header('Upload inputs')
uploaded_file = st.sidebar.file_uploader("Upload a .csv file with your inputs", type=["csv"])
if uploaded_file is not None:
    # Read the uploaded CSV file into a DataFrame
    df_input = pd.read_csv(uploaded_file, index_col = 0) # Database with inputs 
    
        
# Read consumption and production profiles 
df_profiles = pd.read_csv('Input_profiles.csv')

# Access the data series from the DataFrame
time_index = pd.to_datetime(df_profiles['Time']) 

#%% ------------ IMPORT INPUT FROM SIDEBAR -------------------------

# Set Consumption Inputs
st.sidebar.header("Consumption")
select_consumption = st.sidebar.radio("Select consumption input", ["Standard profile","Upload profile"])

if select_consumption == "Upload profile": # If user uploads a consumption profile
    consumption_csv_file = st.sidebar.file_uploader("Upload a Consumption profile", type=["csv"])
    if consumption_csv_file is not None: 
        df_profile_consumption = pd.read_csv(consumption_csv_file)
        df_profiles['Consumption (kWh)'] =  df_profile_consumption
        
if select_consumption == "Standard profile": # If user uses standard consumption profile
    yearly_consumption = df_profiles['Consumption (kWh)'].sum()/1000
    yearly_consumption_in = st.sidebar.number_input(f"Expected yearly consumption (MWh)", value=int(yearly_consumption), step=1, min_value=0, max_value=1000); 
    df_profiles['Consumption (kWh)'] =  df_profiles['Consumption (kWh)']* yearly_consumption_in/yearly_consumption


st.sidebar.header("PV system")

# Set solar inputs
df_input = numeric_user_input(df_input, 'pv_capacity')
pv_advanced = st.sidebar.toggle("Advanced PV settings", value=False)
if pv_advanced  == True: 
    df_input = numeric_user_input(df_input, 'pv_yield')
    df_input = numeric_user_input(df_input, 'pv_overdim', value_type = float)
  
# Set battery input
st.sidebar.header("Battery ")
df_input = numeric_user_input(df_input, 'batt_energy_capacity')
batt_advanced = st.sidebar.toggle("Advanced battery settings", value=False)
if batt_advanced  == True: 
    df_input = numeric_user_input(df_input, 'batt_power_capacity')
    df_input = numeric_user_input(df_input, 'batt_efficiency', value_type = float)
    
# Set generator input 
st.sidebar.header("Generator ")
number_generators = st.sidebar.radio("Number of generators", ["0","1", "2", "3"], index = int(df_input.loc['number_generators']['Value'])) # One generator active as the standard options

if int(number_generators) > 0:
    df_input = numeric_user_input(df_input, 'gen1_capacity')
    if int(number_generators) > 1:
        df_input = numeric_user_input(df_input, 'gen2_capacity')
        if int(number_generators) > 2:
            df_input = numeric_user_input(df_input, 'gen3_capacity')
        else: 
            df_input.loc['gen3_capacity','Value'] = 0
    else: 
        df_input.loc['gen3_capacity']['Value'], df_input.loc['gen2_capacity']['Value'] = 0, 0
else: 
    df_input.loc['gen3_capacity','Value'], df_input.loc['gen2_capacity','Value'], df_input.loc['gen3_capacity','Value'] = 0, 0, 0
    
if int(number_generators) > 0:     
    gen_advance = st.sidebar.toggle("Advanced generator settings") # Select advanced settings for generator
else: 
    gen_advance = False

if gen_advance == True:
    if int(number_generators) > 0:
        df_input = numeric_user_input(df_input, 'gen1_soc_trigger', value_type = float)
        if int(number_generators) > 1:
            df_input = numeric_user_input(df_input, 'gen2_soc_trigger', value_type = float)
            if int(number_generators) > 2:
                df_input = numeric_user_input(df_input, 'gen3_soc_trigger', value_type = float)


st.sidebar.header("Grid connection")

df_input = numeric_user_input(df_input, 'grid_supply_capacity')
df_input = numeric_user_input(df_input, 'grid_feedin_capacity')


st.sidebar.header("Costs")
select_economic = st.sidebar.toggle("Calculate costs and returns", value = True)

if select_economic == True: 
    # Impoting fixed costs inputs 
    st.sidebar.subheader('Fixed costs')
    df_input = numeric_user_input(df_input, 'pv_lease')  
    df_input = numeric_user_input(df_input, 'batt_lease')  
    df_input = numeric_user_input(df_input, 'gen_lease')  
   
    # Importing variable cost inputs
    st.sidebar.subheader('Variable costs')
    df_input = numeric_user_input(df_input, 'gen_fuel_consumption')  
    df_input = numeric_user_input(df_input, 'grid_energy_price')  
    df_input = numeric_user_input(df_input, 'capacity_cost', float)  
    
    # Importing return inputs 
    st.sidebar.subheader('Variable returns')
    df_input = numeric_user_input(df_input, 'grid_feedin_price')  
    df_input = numeric_user_input(df_input, 'consumption_energy_price')  
  
# Graphics inputs 
st.sidebar.header("Output settings ")
show_battery_breakdown = st.sidebar.toggle("Show battery sources") 
show_monthly_profile = st.sidebar.toggle("Show monthly profile", value = True) 
show_daily_profile = st.sidebar.toggle("Show daily profile") 
modify_chart = st.sidebar.toggle("Chart options") 

# Downloading input file for csv 
csv = df_input.to_csv(index=True)
st.sidebar.download_button(label="Download your inputs", data=csv, file_name='my_inputs.csv')


#%% ------------ RUNNING POWER FLOW CALCULATIONS -----------------
df_in = df_input['Value'] # Local copy to store new inputs

df_out = calculate_power_flow(
    df_in['grid_supply_capacity'],
    df_in['grid_feedin_capacity'],
    df_in['pv_capacity'],
    df_in['pv_yield'],
    df_in['pv_overdim'],
    df_in['batt_power_capacity'],
    df_in['batt_energy_capacity'],
    df_in['batt_efficiency'],
    [df_in['gen1_capacity'], df_in['gen2_capacity'], df_in['gen3_capacity']],
    [df_in['gen1_soc_trigger'], df_in['gen1_soc_trigger'], df_in['gen1_soc_trigger']],
    df_in['gen_fuel_consumption'],
    df_profiles['Consumption (kWh)'],
    df_profiles['Production (kWh) per MWp']
)

df_out.set_index(time_index, inplace = True)
df = df_out.sort_index()
df_sum = df_out.sum()/4000 # Sum of all energy flows in MWh
df_monthly_sum = df_out.resample('M').sum()/4000



#%% ------------ CONSUMPTION AND PV PRODUCTION PIE AND AREA CHARTS ------------------------------------

#Sidebar options for changing graph display 

if modify_chart == True:
    hole_size = st.sidebar.slider("Select hole size", min_value=0, max_value=100, value = 40, step= 1)
    label_size = st.sidebar.slider("Select label size", min_value=0, max_value=20, value = 16, step= 1)
    title_size = st.sidebar.slider("Select title size", min_value=0, max_value=30, value = 20, step= 1)
    legend_size = st.sidebar.slider("Select legend size", min_value=0, max_value=20, value = 16, step= 1)
    explode_parameter = st.sidebar.slider("Explode parameter", min_value=0.0, max_value=0.2, value = 0.0, step= 0.01)
else: 
    hole_size = 40
    label_size = 16 
    title_size = 20 
    legend_size = 16
    explode_parameter = 0.0

# Sample data for the consumption pie chart
if show_battery_breakdown == True: 
    settings_consumption = [
        ["pv_consumption", "Solar", "#FFC400"],
        ["green_batt_consumption", "Battery (green)", "#56C568"],
        ["grey_batt_consumption", "Battery (grey)", "#C4C4C4"],
        ["blue_batt_consumption", "Battery (blue)", "#086675"],
        ["grid_consumption", "Grid", "#0FACD1"],
        ["gen_consumption", "Generator", "#808080"]
    ]
else:
    settings_consumption = [
        ["pv_consumption", "Solar", "#FFC400"],
        ["batt_consumption", "Battery", "#56C568"],
        ["grid_consumption", "Grid", "#0FACD1"],
        ["gen_consumption", "Generator", "#808080"]
    ]

# Sample data for the pv pie chart
settings_pv = [
    ['pv_consumption', "Local", "#FFC400"],
    ['pv_battery', "Battery", "#56C568"],
    ['pv_grid', "Grid", "#0FACD1"],
    ['pv_curtailment', "Curtailment", "#000000"],
]

#%% -------------PLOTTING CHARTS ----------------------------------------
# Printing figures in streamlit columns
col1, colspace, col2, colspace2 = st.columns([1,0.1,1,0.1])

with col1: 
    st.subheader('Client consumption')
    fig1 = plot_pie_chart(settings_consumption, df_sum)
    st.plotly_chart(fig1, use_container_width=True)
    if show_monthly_profile:
        fig3 = plot_monthly_chart(settings_consumption, df_monthly_sum, "Consumption (MWh)")
        st.plotly_chart(fig3, use_container_width=True)
with col2:  
    st.subheader('Solar production')
    fig2 = plot_pie_chart(settings_pv, df_sum)
    st.plotly_chart(fig2, use_container_width=True)
    if show_monthly_profile: 
        fig4 = plot_monthly_chart(settings_pv, df_monthly_sum, "PV production (MWh)")
        st.plotly_chart(fig4, use_container_width=True)

#%% ------------ DAILY PLOT-----------------------------------

min_datetime, max_datetime = min(df_out.index), max(df_out.index) 
min_day, max_day = min_datetime.date(), max_datetime.date()

settings_day =  [
    ["pv_production", "Solar production", "#FFC400"],
    ["consumption", "Consumption", "#8f0202"],
    ["batt_flow", "Battery flow", "#56C568"],
    ["gen_consumption", "Generator", "#808080"], 
    ["grid_interface", "Grid interface", "#0FACD1"], 
    ]


settings_day_area =  [
    ["pv_production", "Solar production", "#FFC400"],
    ["grid_outflow", "Grid outflow",  "#0FACD1"],
    ["gen_production", "Generator", "#808080"], 
    ["batt_outflow", "Battery outflow", "#56C568"],
    ["consumption", "Consumption", "#8f0202"],
    ["batt_inflow", "Battery inflow", "#56C568"],
    ["grid_inflow", "Grid inflow",  "#0FACD1"],
    ["pv_curtailment", "Curtailment",  "#000000"],  
    ]


st.subheader('System power flow')
col7, colspace, col8 = st.columns([0.5,0.2,3])

with col7: 
    start_date = st.date_input("Start date", value = min_day, min_value = min_day, max_value = max_day)
    end_date = st.date_input("End date", value = min_day, min_value = min_day, max_value = max_day)
    select_frequency = st.selectbox('Sampling frequency', ['15T', '30T', '1H', '2H', '6H', 'D', '7D', '30D']) 
    df_out = df_out[~df_out.index.duplicated(keep='first')]  # Remove duplicates while keeping the first occurrence
    date_range = pd.date_range(start=start_date, end=end_date)
    start_date = start_date.strftime('%Y, %m, %d')
    end_date = end_date.strftime('%Y, %m, %d')
    date_range = [dat.strftime('%Y, %m, %d') for dat in date_range]
    df_day = pd.concat([df_out.loc[dates] for dates in date_range ])
    df_day = df_day.resample(select_frequency).sum()
with col8: 
    # df_day = df_out.loc[start_date:end_date]
    # df_day = df_day.resample(select_frequency).sum()
    fig6 = plot_day_chart(settings_day, df_day)
    st.plotly_chart(fig6, use_container_width=True)
    fig7 = plot_day_chart_area(settings_day_area, df_day)
    st.plotly_chart(fig7, use_container_width=True)



#%% ------------ RUNNING AND PRINTING ECONOMICAL CALULATIONS ---------------------

col5, colspace,col6 = st.columns([3,0.5,1])

if select_economic == True:
    df_cost_balance = calculate_costs(df_input, df_out)
    
    total_cost = df_cost_balance.loc['Fixed cost'].sum() + df_cost_balance.loc['Variable cost',:].sum()
    total_revenue = df_cost_balance.loc['Variable revenue',:].sum() 

    # Plotting cost chart 
    fig5 = go.Figure()
    for col in df_cost_balance.columns: 
         fig5.add_trace(go.Bar(x = df_cost_balance.index, y = df_cost_balance.loc[['Fixed cost', 'Variable cost', 'Variable revenue'], col], name = col, marker_color  = df_cost_balance.loc['Color', col], ))
    fig5.update_layout(barmode='stack')
    
    with col5: 
        # Showing the bar chart of the cost breakdown\
        st.subheader('Cost and revenue overview')
        st.plotly_chart(fig5, use_container_width=True)  
                             
    col6.markdown(
        """
        <style>
            .stMetric {
                text-align: center;
            }
        </style>
        <div style="display: flex; align-items: center; height: 200px;">
           
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Print metrics to display prices and revenues 
    col6.metric("Yearly cost", value = f'{total_cost:,.0f} EUR')
    col6.metric("Yearly revenue", value = f'{total_revenue:,.0f} EUR')
    col6.metric("Yearly balance", value = f'{total_cost + total_revenue:,.0f} EUR')



#%%------------- SUMMARY FACTS -------------------------------------------------------------
st.subheader('Summary of key metrics')

df_sum_consumption = [df_sum[values] for values in ["pv_consumption", "batt_consumption", "gen_consumption", "grid_consumption"]]
consumption_sum = sum(df_sum_consumption)
gen_hours = generator_hours(df_out['gen_production'],  [df_in['gen1_capacity'], df_in['gen2_capacity'], df_in['gen3_capacity']]) 
gen_consumption = df_input.loc['gen_fuel_consumption']['Value'] * gen_hours

col9, col10 = st.columns(2)

# Define your text and color
if np.abs((df_sum.consumption - consumption_sum)/df_sum.consumption) < 0.005: # If the difference between the demand and the overall consumption is smaller than a 0.5% tolerance factor then the system supplies enough energy
    with col9:
        st.info(f"The yearly energy demand of {df_sum.consumption:.0f} MWh is satisfied by the selected assets")
        
        st.info(f"{df_input.loc['pv_capacity']['Value']:.0f} kWp solar plant produces {-df_sum.pv_production:.0f} MWh, of which {df_sum.pv_consumption:.0f} MWh consumed and {df_sum.pv_battery:.0f} MWh stored in the battery")

        if df_input.loc['number_generators']['Value'] == 1: 
            text_generator = f"{df_input.loc['gen1_capacity']['Value']:.0f} kW generator "
            
        if df_input.loc['number_generators']['Value'] == 2: 
            if df_input.loc['gen1_capacity']['Value'] == df_input.loc['gen2_capacity']['Value']: 
                text_generator = f"Two {df_input.loc['gen1_capacity']['Value']:.0f} kW generators "
            else:
                text_generator = f"Two {df_input.loc['gen1_capacity']['Value']:.0f} kW and {df_input.loc['gen2_capacity']['Value']:.0f} kW generators"

        if df_input.loc['number_generators']['Value'] == 3: 
                text_generator = f"Three ({df_input.loc['gen1_capacity']['Value']:.0f} kW, {df_input.loc['gen2_capacity']['Value']:.0f} kW and {df_input.loc['gen3_capacity']['Value']:.0f} kW) generators"

        if df_input.loc['number_generators']['Value'] > 0:
            st.info(text_generator + f" active for {gen_hours:.0f} hours, producing {-df_sum.gen_production:.0f} MWh and consuming {gen_consumption:.0f} L in one year.")

        if df_input.loc['grid_supply_capacity']['Value'] > 0:
            text_grid_out = f"{df_input.loc['grid_supply_capacity']['Value']:.0f} kW gird connection supplies {-df_sum.grid_outflow:.0f} MWh of which {df_sum.grid_consumption:.0f} MWh consumed and {df_sum.grid_battery:.0f} MWh stored in the battery "
            st.info(text_grid_out)

        if df_input.loc['grid_feedin_capacity']['Value'] > 0:
            text_grid_in = f"Grid feed-in capacity is {df_input.loc['grid_feedin_capacity']['Value']:.0f} kW. In one year {df_sum.grid_inflow:.0f} MWh are fed in to the grid, of which {df_sum.pv_grid:.0f} kWh come from solar"
            st.info(text_grid_in)

else: 
    with col9: 
        st.error(f"ATTENTION! The yearly energy demand of {df_sum.consumption:.0f} MWh is not satisfied by the selected assets and grid capacities, which provide {consumption_sum:.0f} MWh. Consider expanding generator, grid, solar or battery capacity.")

# Download output data 

st.download_button(label="Download output data as csv", data=df_out.to_csv(index=True), file_name='my_output.csv')

end_time = time.time() # Starting timer

# Display the elapsed time
st.write(f"Time of running simulation: {end_time-start_time:.1f} seconds")

