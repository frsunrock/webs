Version V02 of typeA battery model

author: Federico Ravazzolo f.ravazzolo@sunrock.com/ravazzolof@gmail.com
date: 16/10/2023

project description: 
This python module carries the basic functions of the excel model for type A battries, defined in Test2_fullyear.txt

modules: 
input.py  # in this file the input variables on the assets (pv, battery, grid, generator) as well as the profiles (consumption and pv production) are uploaded from the source excel file, converted into dataframes (df_input, df_profiles) and written in two csv (Input_variables.csv and Input_profiles.csv)
powerflow.py # carries the main powerflow calculations through the function calculate_power_flow(). It receives the input variables of the power flow (pv_capacity etc..) and returns a dataframe df_out with the power flow columns ('pv_production' etc) containing the time series over one year
economic.py # performs the economical calculations through the function calculate_costs(df_input, df_out). The df_input dataframe is the daframe containing all the inputs (see input.py) while df_out is the dataframe containing al the power_flows (see powerflow.py)
helpers.py # some basic functions to convert dataframe in csv or pickle dataframes
dsahboard.py # main module that controls the streamlit app. It reads inputs from the csv files, reads user inputs, performs economical and power flow calculations and prints the results. Results are shown through pie charts and monthly breakdown of consumption and solar production, an interactive time series of all power flows and a bar-chart containing information on the econoic balance 
	

use: 
1- streamlit run dashboard.py

further developments: 
- expand features: include economical calcualtions, wind asset, heat pump
- expand functions and modularity: structure the code in objects and functions, change hierarchy of power flows 
- dashboard: create a streamlit user interface of the code 