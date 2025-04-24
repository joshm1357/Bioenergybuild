"""
Financial calculations module for the bioenergy project dashboard.
Contains functions for calculating CAPEX, OPEX, and LCOE.
"""

def calculate_capex(digester_volume, output_type, chp_capacity=0):
    """
    Calculate capital expenditure (CAPEX) for the bioenergy project.
    
    Args:
        digester_volume (float): Digester volume in m³
        output_type (str): Type of output ('biogas' or 'chp')
        chp_capacity (float): CHP capacity in kW (only used if output_type is 'chp')
    
    Returns:
        dict: Dictionary containing CAPEX breakdown
    """
    # Base cost for digester ($ per m³)
    digester_cost_per_m3 = 500
    
    # Calculate digester cost
    digester_cost = digester_volume * digester_cost_per_m3
    
    # Reception and pre-treatment systems (based on digester size)
    reception_cost = 0.15 * digester_cost
    
    # Biogas handling systems
    biogas_handling_cost = 0.1 * digester_cost
    
    # Digestate handling systems
    digestate_handling_cost = 0.12 * digester_cost
    
    # Control systems
    control_systems_cost = 0.08 * digester_cost
    
    # Output-specific costs
    if output_type == 'biogas':
        # Biogas upgrading system ($ per m³/h of raw biogas, assuming 8760 hours per year)
        biogas_output_m3h = (digester_volume * 1.5) / 8760  # Rough estimate of biogas output
        upgrading_cost_per_m3h = 10000
        upgrading_cost = biogas_output_m3h * upgrading_cost_per_m3h
        
        output_specific_cost = upgrading_cost
        output_specific_name = "Biogas Upgrading System"
    else:  # CHP
        # CHP system ($ per kW)
        chp_cost_per_kw = 1500
        chp_cost = chp_capacity * chp_cost_per_kw
        
        output_specific_cost = chp_cost
        output_specific_name = "CHP System"
    
    # Engineering, procurement, and construction (EPC) costs
    epc_cost = 0.15 * (digester_cost + reception_cost + biogas_handling_cost + 
                      digestate_handling_cost + control_systems_cost + output_specific_cost)
    
    # Contingency
    contingency = 0.1 * (digester_cost + reception_cost + biogas_handling_cost + 
                        digestate_handling_cost + control_systems_cost + output_specific_cost + epc_cost)
    
    # Total CAPEX
    total_capex = (digester_cost + reception_cost + biogas_handling_cost + 
                  digestate_handling_cost + control_systems_cost + output_specific_cost + 
                  epc_cost + contingency)
    
    return {
        'Digester System': digester_cost,
        'Reception and Pre-treatment': reception_cost,
        'Biogas Handling': biogas_handling_cost,
        'Digestate Handling': digestate_handling_cost,
        'Control Systems': control_systems_cost,
        output_specific_name: output_specific_cost,
        'EPC Costs': epc_cost,
        'Contingency': contingency,
        'Total CAPEX': total_capex
    }

def calculate_opex(total_feedstock, digester_volume, output_type, capex, chp_capacity=0):
    """
    Calculate operational expenditure (OPEX) for the bioenergy project.
    
    Args:
        total_feedstock (float): Total feedstock input in tonnes per year
        digester_volume (float): Digester volume in m³
        output_type (str): Type of output ('biogas' or 'chp')
        capex (dict): CAPEX breakdown dictionary
        chp_capacity (float): CHP capacity in kW (only used if output_type is 'chp')
    
    Returns:
        dict: Dictionary containing OPEX breakdown
    """
    # Maintenance costs (% of CAPEX per year)
    maintenance_percentage = 0.03
    maintenance_cost = maintenance_percentage * capex['Total CAPEX']
    
    # Labor costs (based on plant size)
    if digester_volume < 2000:
        labor_cost = 150000  # Small plant
    elif digester_volume < 5000:
        labor_cost = 250000  # Medium plant
    else:
        labor_cost = 350000  # Large plant
    
    # Consumables (chemicals, water, etc.) - based on feedstock volume
    consumables_cost_per_tonne = 2.5
    consumables_cost = total_feedstock * consumables_cost_per_tonne
    
    # Insurance (% of CAPEX per year)
    insurance_percentage = 0.01
    insurance_cost = insurance_percentage * capex['Total CAPEX']
    
    # Output-specific operational costs
    if output_type == 'biogas':
        # Biogas upgrading operational costs
        upgrading_opex_percentage = 0.05
        output_specific_cost = upgrading_opex_percentage * capex[f'Biogas Upgrading System']
        output_specific_name = "Biogas Upgrading O&M"
    else:  # CHP
        # CHP maintenance costs ($ per kWh, assuming 8000 operating hours per year)
        chp_operating_hours = 8000
        chp_output_kwh = chp_capacity * chp_operating_hours
        chp_maintenance_per_kwh = 0.02
        output_specific_cost = chp_output_kwh * chp_maintenance_per_kwh
        output_specific_name = "CHP Maintenance"
    
    # Utilities (electricity, heat) - based on digester volume
    utilities_cost_per_m3 = 15
    utilities_cost = digester_volume * utilities_cost_per_m3
    
    # Total OPEX
    total_opex = (maintenance_cost + labor_cost + consumables_cost + 
                 insurance_cost + output_specific_cost + utilities_cost)
    
    return {
        'Maintenance': maintenance_cost,
        'Labor': labor_cost,
        'Consumables': consumables_cost,
        'Insurance': insurance_cost,
        output_specific_name: output_specific_cost,
        'Utilities': utilities_cost,
        'Total OPEX': total_opex
    }

def calculate_lcoe(capex, opex, annual_energy_output, project_lifetime=20, discount_rate=0.08):
    """
    Calculate Levelized Cost of Energy (LCOE) for the bioenergy project.
    
    Args:
        capex (dict): CAPEX breakdown dictionary
        opex (dict): OPEX breakdown dictionary
        annual_energy_output (float): Annual energy output in GJ or MWh
        project_lifetime (int): Project lifetime in years
        discount_rate (float): Discount rate for NPV calculation
    
    Returns:
        float: LCOE in $ per unit of energy
    """
    if annual_energy_output <= 0:
        return 0
    
    total_capex = capex['Total CAPEX']
    annual_opex = opex['Total OPEX']
    
    # Calculate present value of costs
    pv_costs = total_capex
    for year in range(1, project_lifetime + 1):
        pv_costs += annual_opex / ((1 + discount_rate) ** year)
    
    # Calculate present value of energy
    pv_energy = 0
    for year in range(1, project_lifetime + 1):
        pv_energy += annual_energy_output / ((1 + discount_rate) ** year)
    
    # Calculate LCOE
    lcoe = pv_costs / pv_energy if pv_energy > 0 else 0
    
    return lcoe

def calculate_financial_metrics(capex, opex, annual_revenue, project_lifetime=20, 
                               discount_rate=0.08, debt_percentage=0.7, debt_interest=0.05, 
                               debt_term=10, tax_rate=0.3):
    """
    Calculate financial metrics for the bioenergy project.
    
    Args:
        capex (dict): CAPEX breakdown dictionary
        opex (dict): OPEX breakdown dictionary
        annual_revenue (float): Annual revenue in $
        project_lifetime (int): Project lifetime in years
        discount_rate (float): Discount rate for NPV calculation
        debt_percentage (float): Percentage of CAPEX financed by debt
        debt_interest (float): Annual interest rate on debt
        debt_term (int): Debt term in years
        tax_rate (float): Corporate tax rate
    
    Returns:
        dict: Dictionary containing financial metrics
    """
    total_capex = capex['Total CAPEX']
    annual_opex = opex['Total OPEX']
    
    # Calculate debt and equity amounts
    debt_amount = total_capex * debt_percentage
    equity_amount = total_capex * (1 - debt_percentage)
    
    # Calculate annual debt service
    if debt_interest > 0:
        annual_debt_service = debt_amount * debt_interest * (1 + debt_interest) ** debt_term / ((1 + debt_interest) ** debt_term - 1)
    else:
        annual_debt_service = debt_amount / debt_term
    
    # Initialize cash flow arrays
    cash_flows = []
    
    # Initial investment (equity portion)
    cash_flows.append(-equity_amount)
    
    # Calculate annual cash flows
    for year in range(1, project_lifetime + 1):
        # Revenue
        cf = annual_revenue
        
        # OPEX
        cf -= annual_opex
        
        # Debt service (only for debt term years)
        if year <= debt_term:
            cf -= annual_debt_service
        
        # Simplified tax calculation (no depreciation)
        taxable_income = annual_revenue - annual_opex
        if year <= debt_term:
            taxable_income -= annual_debt_service * 0.3  # Assume 30% of debt service is interest
        
        tax = max(0, taxable_income * tax_rate)
        cf -= tax
        
        cash_flows.append(cf)
    
    # Calculate NPV
    npv = cash_flows[0]  # Initial investment
    for year, cf in enumerate(cash_flows[1:], 1):
        npv += cf / ((1 + discount_rate) ** year)
    
    # Calculate IRR
    # Simple approximation method
    irr = 0.1  # Starting guess
    step = 0.05
    direction = 1
    
    for _ in range(20):  # Maximum 20 iterations
        npv_at_irr = cash_flows[0]
        for year, cf in enumerate(cash_flows[1:], 1):
            npv_at_irr += cf / ((1 + irr) ** year)
        
        if abs(npv_at_irr) < 1:
            break
        
        if npv_at_irr * direction < 0:
            direction = -direction
            step /= 2
        
        irr += step * direction
    
    # Calculate payback period
    cumulative_cf = cash_flows[0]
    payback_period = 0
    
    for year, cf in enumerate(cash_flows[1:], 1):
        cumulative_cf += cf
        if cumulative_cf >= 0 and payback_period == 0:
            payback_period = year
    
    if payback_period == 0 and cumulative_cf < 0:
        payback_period = project_lifetime + 1  # No payback within project lifetime
    
    return {
        'NPV': npv,
        'IRR': irr,
        'Payback Period': payback_period,
        'Debt Service Coverage Ratio': (annual_revenue - annual_opex) / annual_debt_service if annual_debt_service > 0 else float('inf'),
        'Equity Return': irr,
    }
