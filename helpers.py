import csv 
import pickle
import pandas as pd 

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