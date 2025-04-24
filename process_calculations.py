"""
Process calculations module for the bioenergy project dashboard.
Contains functions for calculating biogas production, CHP outputs, and related metrics.
"""

def calculate_digester_size(total_vs_tonnes, loading_rate=3.5):
    """
    Calculate the required digester size based on volatile solids input.
    
    Args:
        total_vs_tonnes (float): Total volatile solids in tonnes per year
        loading_rate (float): Organic loading rate in kg VS/m³/day
    
    Returns:
        float: Required digester volume in m³
    """
    # Convert tonnes per year to kg per day
    vs_kg_per_day = total_vs_tonnes * 1000 / 365
    
    # Calculate digester volume
    digester_volume = vs_kg_per_day / loading_rate
    
    return digester_volume

def calculate_biogas_to_energy(methane_yield, output_type='biogas'):
    """
    Calculate energy outputs based on methane yield.
    
    Args:
        methane_yield (float): Methane yield in Nm³ per year
        output_type (str): Type of output ('biogas' or 'chp')
    
    Returns:
        dict: Dictionary containing energy output metrics
    """
    # Energy content of methane (kWh/Nm³)
    methane_energy_content = 9.97
    
    # Total energy content (kWh)
    total_energy_kwh = methane_yield * methane_energy_content
    
    # Initialize results dictionary
    results = {
        'total_energy_kwh': total_energy_kwh,
        'total_energy_mwh': total_energy_kwh / 1000,
        'total_energy_gj': total_energy_kwh * 0.0036,
    }
    
    if output_type == 'biogas':
        # Biogas upgrading efficiency (loss during cleaning and compression)
        upgrading_efficiency = 0.98
        
        # Calculate upgraded biogas energy
        results['biogas_energy_kwh'] = total_energy_kwh * upgrading_efficiency
        results['biogas_energy_mwh'] = results['biogas_energy_kwh'] / 1000
        results['biogas_energy_gj'] = results['biogas_energy_kwh'] * 0.0036
        
    elif output_type == 'chp':
        # CHP electrical efficiency
        electrical_efficiency = 0.40
        
        # CHP thermal efficiency
        thermal_efficiency = 0.45
        
        # Calculate electrical output
        results['electrical_output_kwh'] = total_energy_kwh * electrical_efficiency
        results['electrical_output_mwh'] = results['electrical_output_kwh'] / 1000
        
        # Calculate thermal output
        results['thermal_output_kwh'] = total_energy_kwh * thermal_efficiency
        results['thermal_output_mwh'] = results['thermal_output_kwh'] / 1000
        results['thermal_output_gj'] = results['thermal_output_kwh'] * 0.0036
        
        # Calculate power capacity (assuming 8760 hours per year)
        results['power_capacity_kw'] = results['electrical_output_kwh'] / 8760
        results['heat_capacity_kw'] = results['thermal_output_kwh'] / 8760
        
    return results

def calculate_parasitic_load(digester_volume, output_type='biogas'):
    """
    Calculate parasitic load for the anaerobic digestion system.
    
    Args:
        digester_volume (float): Digester volume in m³
        output_type (str): Type of output ('biogas' or 'chp')
    
    Returns:
        dict: Dictionary containing parasitic load metrics
    """
    # Base parasitic load per m³ of digester (kWh/m³/year)
    base_load_per_m3 = 80
    
    # Additional load for biogas upgrading (if applicable)
    upgrading_load_factor = 1.5 if output_type == 'biogas' else 1.0
    
    # Calculate total parasitic load
    total_parasitic_kwh = digester_volume * base_load_per_m3 * upgrading_load_factor
    
    return {
        'parasitic_load_kwh': total_parasitic_kwh,
        'parasitic_load_mwh': total_parasitic_kwh / 1000,
        'parasitic_load_percentage': 0,  # Will be calculated later when we have total energy
    }

def calculate_digestate_production(total_feedstock, total_vs_tonnes, vs_destruction=0.7):
    """
    Calculate digestate production from the anaerobic digestion process.
    
    Args:
        total_feedstock (float): Total feedstock input in tonnes per year
        total_vs_tonnes (float): Total volatile solids in tonnes per year
        vs_destruction (float): Fraction of volatile solids destroyed in digestion
    
    Returns:
        dict: Dictionary containing digestate production metrics
    """
    # Calculate VS destroyed
    vs_destroyed = total_vs_tonnes * vs_destruction
    
    # Calculate digestate quantity (original feedstock minus VS destroyed)
    digestate_tonnes = total_feedstock - vs_destroyed
    
    # Estimate solid and liquid fractions after separation
    solid_fraction = 0.25  # 25% of digestate mass in solid fraction
    liquid_fraction = 0.75  # 75% of digestate mass in liquid fraction
    
    # Calculate solid and liquid digestate quantities
    solid_digestate = digestate_tonnes * solid_fraction
    liquid_digestate = digestate_tonnes * liquid_fraction
    
    return {
        'total_digestate_tonnes': digestate_tonnes,
        'solid_digestate_tonnes': solid_digestate,
        'liquid_digestate_tonnes': liquid_digestate,
    }

def size_chp_units(power_capacity_kw):
    """
    Determine the appropriate CHP unit configuration based on power capacity.
    
    Args:
        power_capacity_kw (float): Required power capacity in kW
    
    Returns:
        dict: Dictionary containing CHP unit configuration
    """
    # Available CHP unit sizes
    available_sizes = [100, 250, 500, 800, 1000, 1500, 2000]
    
    # Find the best combination of units
    units = []
    remaining_capacity = power_capacity_kw
    
    # Start with the largest units
    for size in sorted(available_sizes, reverse=True):
        while remaining_capacity >= size * 0.8:  # Allow units to run at minimum 80% capacity
            units.append(size)
            remaining_capacity -= size
    
    # If we still have significant capacity to cover, add one more smaller unit
    if remaining_capacity > 50:
        for size in sorted(available_sizes):
            if size >= remaining_capacity:
                units.append(size)
                remaining_capacity = 0
                break
    
    # Calculate total installed capacity
    total_capacity = sum(units)
    
    return {
        'chp_units': units,
        'number_of_units': len(units),
        'total_installed_capacity_kw': total_capacity,
        'capacity_utilization': power_capacity_kw / total_capacity if total_capacity > 0 else 0,
    }
