"""
Feedstock data module for the bioenergy project dashboard.
Contains default parameters for various feedstocks based on the project requirements.
"""

import pandas as pd

# Default feedstock parameters based on the provided data
DEFAULT_FEEDSTOCKS = {
    "Meat": {
        "quantity": 2622,
        "ts": 32.0,  # Total Solids (%)
        "vs": 92.0,  # Volatile Solids (% of TS)
        "bmp": 628.4,  # Biochemical Methane Potential (Nm³/t VS)
        "ch4": 60.0,  # Methane content (%)
        "tkn": 2.75,  # Total Kjeldahl Nitrogen (% of TS)
        "tan": 17.1,  # Total Ammoniacal Nitrogen (% of TKN)
        "distance": 50,  # Default distance in km
        "cost_per_tonne": 20,  # Default cost in $/tonne
    },
    "Digestate Sludge": {
        "quantity": 1495,
        "ts": 20.0,
        "vs": 89.0,
        "bmp": 280.9,
        "ch4": 55.0,
        "tkn": 1.56,
        "tan": 10.0,
        "distance": 10,
        "cost_per_tonne": 5,
    },
    "Blood Filter Cake": {
        "quantity": 3000,
        "ts": 5.3,
        "vs": 96.0,
        "bmp": 660.0,
        "ch4": 68.0,
        "tkn": 13.61,
        "tan": 1.4,
        "distance": 60,
        "cost_per_tonne": 15,
    },
    "Chicken Carcasses": {
        "quantity": 1000,
        "ts": 26.0,
        "vs": 86.0,
        "bmp": 402.5,
        "ch4": 60.0,
        "tkn": 5.00,
        "tan": 10.0,
        "distance": 70,
        "cost_per_tonne": 10,
    },
    "Chicken Litter": {
        "quantity": 10000,
        "ts": 45.0,
        "vs": 75.0,
        "bmp": 500.0,
        "ch4": 60.0,
        "tkn": 4.86,
        "tan": 10.0,
        "distance": 80,
        "cost_per_tonne": 5,
    },
    "Grain Mix": {
        "quantity": 2000,
        "ts": 87.0,
        "vs": 96.0,
        "bmp": 729.8,
        "ch4": 56.5,
        "tkn": 2.99,
        "tan": 10.0,
        "distance": 100,
        "cost_per_tonne": 30,
    },
    "Crop Straw": {
        "quantity": 12500,
        "ts": 85.0,
        "vs": 75.0,
        "bmp": 350.0,
        "ch4": 51.0,
        "tkn": 0.29,
        "tan": 10.0,
        "distance": 120,
        "cost_per_tonne": 25,
    },
}

def get_feedstock_df():
    """
    Convert the default feedstock dictionary to a pandas DataFrame.
    
    Returns:
        pandas.DataFrame: DataFrame containing feedstock parameters
    """
    return pd.DataFrame.from_dict(DEFAULT_FEEDSTOCKS, orient='index')

def calculate_biogas_yield(feedstock_df):
    """
    Calculate the biogas yield for each feedstock.
    
    Args:
        feedstock_df (pandas.DataFrame): DataFrame containing feedstock parameters
        
    Returns:
        pandas.DataFrame: DataFrame with additional biogas yield calculations
    """
    # Create a copy to avoid modifying the original
    df = feedstock_df.copy()
    
    # Calculate VS content in tonnes
    df['vs_tonnes'] = df['quantity'] * (df['ts'] / 100) * (df['vs'] / 100)
    
    # Calculate biogas yield in Nm³/year
    df['biogas_yield'] = df['vs_tonnes'] * df['bmp']
    
    # Calculate methane yield in Nm³/year
    df['methane_yield'] = df['biogas_yield'] * (df['ch4'] / 100)
    
    # Calculate energy content (assuming 9.97 kWh/m³ CH4)
    df['energy_content_kwh'] = df['methane_yield'] * 9.97
    
    # Convert to GJ (1 kWh = 0.0036 GJ)
    df['energy_content_gj'] = df['energy_content_kwh'] * 0.0036
    
    # Calculate transportation cost
    df['transport_cost'] = df['quantity'] * df['distance'] * 0.1  # Assuming $0.1 per tonne-km
    
    # Calculate feedstock cost
    df['feedstock_cost'] = df['quantity'] * df['cost_per_tonne']
    
    # Calculate total cost
    df['total_cost'] = df['transport_cost'] + df['feedstock_cost']
    
    # Calculate cost per GJ
    df['cost_per_gj'] = df['total_cost'] / df['energy_content_gj']
    
    # Calculate cost per MWh (1 MWh = 3.6 GJ)
    df['cost_per_mwh'] = df['cost_per_gj'] * 3.6
    
    return df

def get_total_metrics(feedstock_df):
    """
    Calculate total metrics across all feedstocks.
    
    Args:
        feedstock_df (pandas.DataFrame): DataFrame containing feedstock calculations
        
    Returns:
        dict: Dictionary containing total metrics
    """
    totals = {
        'total_quantity': feedstock_df['quantity'].sum(),
        'total_vs_tonnes': feedstock_df['vs_tonnes'].sum(),
        'total_biogas_yield': feedstock_df['biogas_yield'].sum(),
        'total_methane_yield': feedstock_df['methane_yield'].sum(),
        'total_energy_content_gj': feedstock_df['energy_content_gj'].sum(),
        'total_transport_cost': feedstock_df['transport_cost'].sum(),
        'total_feedstock_cost': feedstock_df['feedstock_cost'].sum(),
        'total_cost': feedstock_df['total_cost'].sum(),
    }
    
    # Calculate weighted averages
    if totals['total_energy_content_gj'] > 0:
        totals['avg_cost_per_gj'] = totals['total_cost'] / totals['total_energy_content_gj']
        totals['avg_cost_per_mwh'] = totals['avg_cost_per_gj'] * 3.6
    else:
        totals['avg_cost_per_gj'] = 0
        totals['avg_cost_per_mwh'] = 0
        
    # Calculate biogas output in Nm³/h (assuming 8760 hours per year)
    totals['biogas_output_nm3h'] = totals['total_biogas_yield'] / 8760
    
    return totals
