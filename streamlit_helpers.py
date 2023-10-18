def numeric_user_input(df_input,variable, value_type = int, max_value = None): 
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
    months_list = calendar.month_abbr[1:]

    fig = go.Figure()

    for j, row in enumerate(settings):

        fig.add_trace(go.Scatter(
            x = months_list,
            y = df_month[row[0]], 
            mode='lines',
            stackgroup='one', # define stack group
            fillcolor=row[2],  # Set the fill color for the patch
            line=dict(color=row[2]), # Set the line color 
            name=row[1]  # Set the legend name
        ))

    fig.update_layout(
        showlegend=False,  # Display legend
        legend=dict( # Select legend size 
                font=dict(size=legend_size)  # Adjust the font size of the labels as needed
            ), 
        yaxis_title=ytitle,
        margin = dict(b = 200, t = 0),
        
    )
    
    return fig 

    
