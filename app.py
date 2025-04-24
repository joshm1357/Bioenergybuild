"""
Main application file for the Bioenergy Project Dashboard.
This file contains the Streamlit UI components and application logic.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from feedstock_data import DEFAULT_FEEDSTOCKS, get_feedstock_df, calculate_biogas_yield, get_total_metrics
from process_calculations import (calculate_digester_size, calculate_biogas_to_energy, 
                                 calculate_parasitic_load, calculate_digestate_production, size_chp_units)
from financial_calculations import calculate_capex, calculate_opex, calculate_lcoe, calculate_financial_metrics

# Set page configuration
st.set_page_config(
    page_title="Bioenergy Project Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for green theme
st.markdown("""
<style>
    .main {
        background-color: #f5f9f5;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    .stSlider>div>div>div {
        background-color: #4CAF50;
    }
    .stProgress>div>div>div {
        background-color: #4CAF50;
    }
    h1, h2, h3 {
        color: #2E7D32;
    }
    .feedstock-card {
        background-color: #E8F5E9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #4CAF50;
    }
    .results-card {
        background-color: #E8F5E9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #2E7D32;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'active_feedstocks' not in st.session_state:
    st.session_state.active_feedstocks = {}
    
if 'output_type' not in st.session_state:
    st.session_state.output_type = 'biogas'
    
if 'project_scale' not in st.session_state:
    st.session_state.project_scale = 1.0

# Function to add a feedstock to active feedstocks
def add_feedstock(feedstock_name):
    if feedstock_name not in st.session_state.active_feedstocks:
        st.session_state.active_feedstocks[feedstock_name] = DEFAULT_FEEDSTOCKS[feedstock_name].copy()
        st.success(f"Added {feedstock_name} to active feedstocks")

# Function to remove a feedstock from active feedstocks
def remove_feedstock(feedstock_name):
    if feedstock_name in st.session_state.active_feedstocks:
        del st.session_state.active_feedstocks[feedstock_name]
        st.success(f"Removed {feedstock_name} from active feedstocks")

# Main title
st.title("Bioenergy Project Dashboard")
st.markdown("Estimate the cost per GJ and MWh for your bioenergy project")

# Sidebar for global controls
with st.sidebar:
    st.header("Project Configuration")
    
    # Output type selection
    output_type = st.radio("Output Type", ["Biogas", "CHP"], 
                          index=0 if st.session_state.output_type == 'biogas' else 1)
    st.session_state.output_type = output_type.lower()
    
    # Project scale slider
    project_scale = st.slider("Project Scale", 0.1, 2.0, st.session_state.project_scale, 0.1,
                             help="Scale all feedstock quantities proportionally")
    st.session_state.project_scale = project_scale
    
    # Financial parameters
    st.subheader("Financial Parameters")
    
    project_lifetime = st.slider("Project Lifetime (years)", 10, 30, 20, 1)
    discount_rate = st.slider("Discount Rate (%)", 5, 15, 8, 1) / 100
    
    st.subheader("Financing Structure")
    debt_percentage = st.slider("Debt Percentage (%)", 0, 90, 70, 5) / 100
    debt_interest = st.slider("Debt Interest Rate (%)", 2, 10, 5, 1) / 100
    debt_term = st.slider("Loan Term (years)", 5, 20, 10, 1)
    equity_return = st.slider("Target Equity Return (%)", 8, 25, 15, 1) / 100
    
    # Recalculate button
    recalculate = st.button("Recalculate", type="primary")

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["Feedstock Management", "Process Configuration", "Financial Results", "Assumptions"])

# Tab 1: Feedstock Management
with tab1:
    st.header("Feedstock Management")
    
    # Two-column layout
    col1, col2 = st.columns([1, 2])
    
    # Feedstock library (left column)
    with col1:
        st.subheader("Feedstock Library")
        st.markdown("Drag feedstocks to your project by clicking the Add button")
        
        # Display available feedstocks as cards
        for feedstock_name in DEFAULT_FEEDSTOCKS.keys():
            with st.container():
                st.markdown(f"""
                <div class="feedstock-card">
                    <h4>{feedstock_name}</h4>
                    <p>TS: {DEFAULT_FEEDSTOCKS[feedstock_name]['ts']}% | 
                    VS: {DEFAULT_FEEDSTOCKS[feedstock_name]['vs']}% | 
                    BMP: {DEFAULT_FEEDSTOCKS[feedstock_name]['bmp']} Nm³/t VS</p>
                </div>
                """, unsafe_allow_html=True)
                st.button(f"Add {feedstock_name}", key=f"add_{feedstock_name}", 
                         on_click=add_feedstock, args=(feedstock_name,))
    
    # Active feedstocks (right column)
    with col2:
        st.subheader("Active Feedstocks")
        
        if not st.session_state.active_feedstocks:
            st.info("No feedstocks added yet. Add feedstocks from the library on the left.")
        else:
            # Create a DataFrame from active feedstocks for calculations
            active_df = pd.DataFrame.from_dict(st.session_state.active_feedstocks, orient='index')
            
            # Apply project scale to quantities
            active_df['original_quantity'] = active_df['quantity']
            active_df['quantity'] = active_df['original_quantity'] * st.session_state.project_scale
            
            # Display each active feedstock with sliders
            for feedstock_name, feedstock_data in st.session_state.active_feedstocks.items():
                with st.expander(feedstock_name, expanded=True):
                    cols = st.columns([3, 1])
                    
                    with cols[0]:
                        # Quantity slider
                        quantity = st.slider(
                            f"Quantity (tonnes/year)",
                            min_value=0,
                            max_value=int(feedstock_data['original_quantity'] * 3),
                            value=int(feedstock_data['original_quantity'] * st.session_state.project_scale),
                            key=f"quantity_{feedstock_name}"
                        )
                        st.session_state.active_feedstocks[feedstock_name]['quantity'] = quantity
                        
                        # Distance slider
                        distance = st.slider(
                            f"Distance (km)",
                            min_value=0,
                            max_value=500,
                            value=feedstock_data['distance'],
                            key=f"distance_{feedstock_name}"
                        )
                        st.session_state.active_feedstocks[feedstock_name]['distance'] = distance
                        
                        # Display key parameters
                        st.markdown(f"""
                        **Parameters:**
                        - TS: {feedstock_data['ts']}%
                        - VS: {feedstock_data['vs']}%
                        - BMP: {feedstock_data['bmp']} Nm³/t VS
                        - CH₄: {feedstock_data['ch4']}%
                        - TKN: {feedstock_data['tkn']}%
                        - TAN: {feedstock_data['tan']}%
                        """)
                    
                    with cols[1]:
                        st.button("Remove", key=f"remove_{feedstock_name}", 
                                 on_click=remove_feedstock, args=(feedstock_name,))
                        
                        # Calculate and display cost per GJ and MWh
                        if quantity > 0:
                            # Create a single-row DataFrame for this feedstock
                            single_df = pd.DataFrame([feedstock_data])
                            single_df = calculate_biogas_yield(single_df)
                            
                            cost_per_gj = single_df['cost_per_gj'].values[0]
                            cost_per_mwh = single_df['cost_per_mwh'].values[0]
                            
                            st.markdown(f"""
                            **Cost Metrics:**
                            - ${cost_per_gj:.2f}/GJ
                            - ${cost_per_mwh:.2f}/MWh
                            """)
            
            # Calculate and display total metrics
            if active_df.shape[0] > 0:
                st.subheader("Feedstock Summary")
                
                # Calculate biogas yield and costs
                calculated_df = calculate_biogas_yield(active_df)
                totals = get_total_metrics(calculated_df)
                
                # Display summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Feedstock", f"{totals['total_quantity']:.0f} tonnes/year")
                    st.metric("Total VS", f"{totals['total_vs_tonnes']:.1f} tonnes/year")
                
                with col2:
                    st.metric("Biogas Yield", f"{totals['total_biogas_yield']:.0f} Nm³/year")
                    st.metric("Biogas Output", f"{totals['biogas_output_nm3h']:.1f} Nm³/hour")
                
                with col3:
                    st.metric("Avg. Cost per GJ", f"${totals['avg_cost_per_gj']:.2f}/GJ")
                    st.metric("Avg. Cost per MWh", f"${totals['avg_cost_per_mwh']:.2f}/MWh")
                
                # Feedstock composition chart
                st.subheader("Feedstock Composition")
                fig = px.pie(
                    calculated_df, 
                    values='quantity', 
                    names=calculated_df.index,
                    title='Feedstock Composition by Weight',
                    color_discrete_sequence=px.colors.sequential.Greens
                )
                st.plotly_chart(fig, use_container_width=True)

# Tab 2: Process Configuration
with tab2:
    st.header("Process Configuration")
    
    # Check if we have active feedstocks
    if not st.session_state.active_feedstocks:
        st.info("Please add feedstocks in the Feedstock Management tab first.")
    else:
        # Create a DataFrame from active feedstocks for calculations
        active_df = pd.DataFrame.from_dict(st.session_state.active_feedstocks, orient='index')
        
        # Apply project scale to quantities
        active_df['quantity'] = active_df['original_quantity'] * st.session_state.project_scale
        
        # Calculate biogas yield and costs
        calculated_df = calculate_biogas_yield(active_df)
        totals = get_total_metrics(calculated_df)
        
        # Process configuration columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Digester Configuration")
            
            # Calculate recommended digester size
            recommended_digester_size = calculate_digester_size(totals['total_vs_tonnes'])
            
            # Digester size slider
            digester_size = st.slider(
                "Digester Size (m³)",
                min_value=int(recommended_digester_size * 0.5),
                max_value=int(recommended_digester_size * 2),
                value=int(recommended_digester_size),
                step=100
            )
            
            # Number of digesters
            num_digesters = st.number_input(
                "Number of Digesters",
                min_value=1,
                max_value=5,
                value=2 if digester_size > 5000 else 1
            )
            
            # Operating temperature
            operating_temp = st.radio(
                "Operating Temperature",
                ["Mesophilic (35-40°C)", "Thermophilic (50-55°C)"],
                index=0
            )
            
            # Hydraulic retention time
            hrt = st.slider(
                "Hydraulic Retention Time (days)",
                min_value=15,
                max_value=40,
                value=25
            )
        
        with col2:
            if st.session_state.output_type == 'biogas':
                st.subheader("Biogas Upgrading Configuration")
                
                # Biogas upgrading technology
                upgrading_tech = st.selectbox(
                    "Upgrading Technology",
                    ["Water Scrubbing", "PSA", "Membrane", "Amine Scrubbing"],
                    index=0
                )
                
                # Biomethane purity
                biomethane_purity = st.slider(
                    "Biomethane Purity (%)",
                    min_value=95,
                    max_value=99,
                    value=97
                )
                
                # Methane recovery
                methane_recovery = st.slider(
                    "Methane Recovery (%)",
                    min_value=90,
                    max_value=99,
                    value=98
                )
                
                # Compression pressure
                compression_pressure = st.slider(
                    "Compression Pressure (bar)",
                    min_value=4,
                    max_value=250,
                    value=200
                )
            else:  # CHP
                st.subheader("CHP Configuration")
                
                # Calculate energy outputs
                energy_outputs = calculate_biogas_to_energy(
                    totals['total_methane_yield'], 
                    output_type='chp'
                )
                
                # Recommended CHP size
                recommended_chp_size = energy_outputs['power_capacity_kw']
                
                # CHP sizing
                chp_units = size_chp_units(recommended_chp_size)
                
                # Display CHP units
                st.markdown(f"""
                **Recommended CHP Configuration:**
                - Power Capacity: {recommended_chp_size:.0f} kW
                - Recommended Units: {', '.join([f"{unit} kW" for unit in chp_units['chp_units']])}
                - Total Installed Capacity: {chp_units['total_installed_capacity_kw']:.0f} kW
                - Capacity Utilization: {chp_units['capacity_utilization']*100:.1f}%
                """)
                
                # Electrical efficiency
                electrical_efficiency = st.slider(
                    "Electrical Efficiency (%)",
                    min_value=35,
                    max_value=45,
                    value=40
                )
                
                # Thermal efficiency
                thermal_efficiency = st.slider(
                    "Thermal Efficiency (%)",
                    min_value=40,
                    max_value=50,
                    value=45
                )
                
                # Heat utilization
                heat_utilization = st.slider(
                    "Heat Utilization (%)",
                    min_value=0,
                    max_value=100,
                    value=50
                )
        
        # Process outputs
        st.subheader("Process Outputs")
        
        # Calculate energy outputs based on output type
        energy_outputs = calculate_biogas_to_energy(
            totals['total_methane_yield'], 
            output_type=st.session_state.output_type
        )
        
        # Calculate parasitic load
        parasitic_load = calculate_parasitic_load(
            digester_size * num_digesters, 
            output_type=st.session_state.output_type
        )
        
        # Calculate digestate production
        digestate = calculate_digestate_production(
            totals['total_quantity'], 
            totals['total_vs_tonnes']
        )
        
        # Display output metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.session_state.output_type == 'biogas':
                st.metric("Biogas Output", f"{totals['biogas_output_nm3h']:.1f} Nm³/hour")
                st.metric("Biomethane Output", f"{totals['biogas_output_nm3h'] * biomethane_purity/100 * methane_recovery/100:.1f} Nm³/hour")
                st.metric("Energy Content", f"{energy_outputs['biogas_energy_gj']:.0f} GJ/year")
            else:  # CHP
                st.metric("Electrical Output", f"{energy_outputs['electrical_output_mwh']:.0f} MWh/year")
                st.metric("Power Capacity", f"{energy_outputs['power_capacity_kw']:.0f} kW")
                st.metric("Capacity Factor", "91%" if energy_outputs['power_capacity_kw'] > 0 else "0%")
        
        with col2:
            if st.session_state.output_type == 'biogas':
                st.metric("Methane Content", f"{totals['total_methane_yield'] / totals['total_biogas_yield'] * 100:.1f}%")
                st.metric("CO₂ Content", f"{100 - totals['total_methane_yield'] / totals['total_biogas_yield'] * 100:.1f}%")
                st.metric("Parasitic Load", f"{parasitic_load['parasitic_load_mwh']:.0f} MWh/year")
            else:  # CHP
                st.metric("Thermal Output", f"{energy_outputs['thermal_output_mwh']:.0f} MWh/year")
                st.metric("Heat Capacity", f"{energy_outputs['heat_capacity_kw']:.0f} kW")
                st.metric("Usable Heat", f"{energy_outputs['thermal_output_mwh'] * heat_utilization/100:.0f} MWh/year")
        
        with col3:
            st.metric("Total Digestate", f"{digestate['total_digestate_tonnes']:.0f} tonnes/year")
            st.metric("Solid Digestate", f"{digestate['solid_digestate_tonnes']:.0f} tonnes/year")
            st.metric("Liquid Digestate", f"{digestate['liquid_digestate_tonnes']:.0f} tonnes/year")

# Tab 3: Financial Results
with tab3:
    st.header("Financial Results")
    
    # Check if we have active feedstocks
    if not st.session_state.active_feedstocks:
        st.info("Please add feedstocks in the Feedstock Management tab first.")
    else:
        # Create a DataFrame from active feedstocks for calculations
        active_df = pd.DataFrame.from_dict(st.session_state.active_feedstocks, orient='index')
        
        # Apply project scale to quantities
        active_df['quantity'] = active_df['original_quantity'] * st.session_state.project_scale
        
        # Calculate biogas yield and costs
        calculated_df = calculate_biogas_yield(active_df)
        totals = get_total_metrics(calculated_df)
        
        # Calculate digester size
        recommended_digester_size = calculate_digester_size(totals['total_vs_tonnes'])
        digester_size = recommended_digester_size  # Use recommended size for calculations
        num_digesters = 2 if digester_size > 5000 else 1
        
        # Calculate energy outputs
        energy_outputs = calculate_biogas_to_energy(
            totals['total_methane_yield'], 
            output_type=st.session_state.output_type
        )
        
        # Calculate CAPEX
        if st.session_state.output_type == 'chp':
            chp_capacity = energy_outputs['power_capacity_kw']
            capex = calculate_capex(
                digester_size * num_digesters, 
                st.session_state.output_type, 
                chp_capacity
            )
        else:
            capex = calculate_capex(
                digester_size * num_digesters, 
                st.session_state.output_type
            )
        
        # Calculate OPEX
        opex = calculate_opex(
            totals['total_quantity'], 
            digester_size * num_digesters, 
            st.session_state.output_type, 
            capex,
            energy_outputs.get('power_capacity_kw', 0)
        )
        
        # Calculate LCOE
        if st.session_state.output_type == 'biogas':
            annual_energy = energy_outputs['biogas_energy_gj']
            energy_unit = "GJ"
        else:  # CHP
            annual_energy = energy_outputs['electrical_output_mwh']
            energy_unit = "MWh"
        
        lcoe = calculate_lcoe(
            capex, 
            opex, 
            annual_energy, 
            project_lifetime, 
            discount_rate
        )
        
        # Estimate revenue
        if st.session_state.output_type == 'biogas':
            biogas_price = 15  # $/GJ
            annual_revenue = annual_energy * biogas_price
        else:  # CHP
            electricity_price = 100  # $/MWh
            heat_price = 10  # $/GJ
            heat_utilization = 0.5  # 50%
            annual_revenue = (
                energy_outputs['electrical_output_mwh'] * electricity_price + 
                energy_outputs['thermal_output_gj'] * heat_utilization * heat_price
            )
        
        # Calculate financial metrics
        financial_metrics = calculate_financial_metrics(
            capex, 
            opex, 
            annual_revenue, 
            project_lifetime, 
            discount_rate, 
            debt_percentage, 
            debt_interest, 
            debt_term
        )
        
        # Display financial results
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("CAPEX Breakdown")
            
            # CAPEX breakdown chart
            capex_df = pd.DataFrame({
                'Component': list(capex.keys())[:-1],  # Exclude total
                'Cost ($)': list(capex.values())[:-1]
            })
            
            fig = px.bar(
                capex_df, 
                x='Cost ($)', 
                y='Component', 
                orientation='h',
                title=f'CAPEX Breakdown (Total: ${capex["Total CAPEX"]:,.0f})',
                color='Cost ($)',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # OPEX breakdown chart
            st.subheader("OPEX Breakdown")
            
            opex_df = pd.DataFrame({
                'Component': list(opex.keys())[:-1],  # Exclude total
                'Cost ($/year)': list(opex.values())[:-1]
            })
            
            fig = px.bar(
                opex_df, 
                x='Cost ($/year)', 
                y='Component', 
                orientation='h',
                title=f'OPEX Breakdown (Total: ${opex["Total OPEX"]:,.0f}/year)',
                color='Cost ($/year)',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("LCOE Analysis")
            
            # LCOE metric
            st.metric(
                f"Levelized Cost of Energy (${energy_unit})",
                f"${lcoe:.2f}/{energy_unit}",
                delta=None
            )
            
            # Financial metrics
            st.subheader("Financial Metrics")
            
            metrics_col1, metrics_col2 = st.columns(2)
            
            with metrics_col1:
                st.metric("Net Present Value", f"${financial_metrics['NPV']:,.0f}")
                st.metric("Internal Rate of Return", f"{financial_metrics['IRR']*100:.1f}%")
            
            with metrics_col2:
                st.metric("Payback Period", f"{financial_metrics['Payback Period']:.1f} years")
                st.metric("Debt Service Coverage", f"{financial_metrics['Debt Service Coverage Ratio']:.2f}")
            
            # LCOE Sensitivity Analysis
            st.subheader("Sensitivity Analysis")
            
            # Create sensitivity data
            sensitivity_data = []
            
            # CAPEX sensitivity
            for capex_factor in [0.8, 0.9, 1.0, 1.1, 1.2]:
                capex_adj = {k: v * capex_factor for k, v in capex.items()}
                lcoe_adj = calculate_lcoe(
                    capex_adj, 
                    opex, 
                    annual_energy, 
                    project_lifetime, 
                    discount_rate
                )
                sensitivity_data.append({
                    'Parameter': 'CAPEX',
                    'Change': f"{(capex_factor-1)*100:+.0f}%",
                    'LCOE': lcoe_adj,
                    'Factor': capex_factor
                })
            
            # OPEX sensitivity
            for opex_factor in [0.8, 0.9, 1.0, 1.1, 1.2]:
                opex_adj = {k: v * opex_factor for k, v in opex.items()}
                lcoe_adj = calculate_lcoe(
                    capex, 
                    opex_adj, 
                    annual_energy, 
                    project_lifetime, 
                    discount_rate
                )
                sensitivity_data.append({
                    'Parameter': 'OPEX',
                    'Change': f"{(opex_factor-1)*100:+.0f}%",
                    'LCOE': lcoe_adj,
                    'Factor': opex_factor
                })
            
            # Energy output sensitivity
            for output_factor in [0.8, 0.9, 1.0, 1.1, 1.2]:
                lcoe_adj = calculate_lcoe(
                    capex, 
                    opex, 
                    annual_energy * output_factor, 
                    project_lifetime, 
                    discount_rate
                )
                sensitivity_data.append({
                    'Parameter': 'Energy Output',
                    'Change': f"{(output_factor-1)*100:+.0f}%",
                    'LCOE': lcoe_adj,
                    'Factor': output_factor
                })
            
            # Create sensitivity chart
            sensitivity_df = pd.DataFrame(sensitivity_data)
            
            fig = px.line(
                sensitivity_df, 
                x='Change', 
                y='LCOE', 
                color='Parameter',
                title=f'LCOE Sensitivity Analysis (${energy_unit})',
                markers=True,
                color_discrete_sequence=['#2E7D32', '#4CAF50', '#81C784']
            )
            
            fig.update_layout(
                xaxis_title="Parameter Change",
                yaxis_title=f"LCOE (${energy_unit})",
                legend_title="Parameter"
            )
            
            st.plotly_chart(fig, use_container_width=True)

# Tab 4: Assumptions
with tab4:
    st.header("Assumptions")
    
    # Create tabs for different assumption categories
    assumptions_tab1, assumptions_tab2, assumptions_tab3 = st.tabs([
        "Process Assumptions", 
        "Cost Functions", 
        "Financial Assumptions"
    ])
    
    # Process Assumptions
    with assumptions_tab1:
        st.subheader("Biogas Production")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Biogas Calculation Assumptions:**
            - Biogas yield is calculated based on VS content and BMP
            - Methane content is based on feedstock characteristics
            - Energy content of methane: 9.97 kWh/Nm³
            - 1 kWh = 0.0036 GJ
            """)
            
            st.markdown("""
            **Digester Assumptions:**
            - Organic loading rate: 3.5 kg VS/m³/day
            - VS destruction rate: 70%
            - Hydraulic retention time: 25 days (default)
            - Operating temperature: 35-40°C (mesophilic, default)
            """)
        
        with col2:
            st.markdown("""
            **CHP Assumptions:**
            - Electrical efficiency: 40% (default)
            - Thermal efficiency: 45% (default)
            - Annual operating hours: 8,000
            - Capacity factor: 91%
            """)
            
            st.markdown("""
            **Biogas Upgrading Assumptions:**
            - Methane recovery: 98% (default)
            - Biomethane purity: 97% (default)
            - Parasitic load: 0.25 kWh/Nm³ of raw biogas
            """)
    
    # Cost Functions
    with assumptions_tab2:
        st.subheader("Cost Functions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**CAPEX Cost Functions:**")
            
            # Digester cost function
            digester_cost_per_m3 = st.number_input(
                "Digester Cost ($/m³)",
                min_value=300,
                max_value=800,
                value=500
            )
            
            # CHP cost function
            chp_cost_per_kw = st.number_input(
                "CHP Cost ($/kW)",
                min_value=1000,
                max_value=2500,
                value=1500
            )
            
            # Biogas upgrading cost function
            upgrading_cost_per_m3h = st.number_input(
                "Biogas Upgrading Cost ($/Nm³/h)",
                min_value=5000,
                max_value=15000,
                value=10000
            )
        
        with col2:
            st.markdown("**OPEX Cost Functions:**")
            
            # Maintenance percentage
            maintenance_percentage = st.number_input(
                "Maintenance (% of CAPEX/year)",
                min_value=1.0,
                max_value=5.0,
                value=3.0
            ) / 100
            
            # Labor costs
            labor_cost_small = st.number_input(
                "Labor Cost - Small Plant ($/year)",
                min_value=100000,
                max_value=200000,
                value=150000
            )
            
            # Consumables cost
            consumables_cost_per_tonne = st.number_input(
                "Consumables Cost ($/tonne feedstock)",
                min_value=1.0,
                max_value=5.0,
                value=2.5
            )
    
    # Financial Assumptions
    with assumptions_tab3:
        st.subheader("Financial Assumptions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Revenue Assumptions:**")
            
            # Biogas price
            biogas_price = st.number_input(
                "Biogas Price ($/GJ)",
                min_value=5.0,
                max_value=30.0,
                value=15.0
            )
            
            # Electricity price
            electricity_price = st.number_input(
                "Electricity Price ($/MWh)",
                min_value=50.0,
                max_value=200.0,
                value=100.0
            )
            
            # Heat price
            heat_price = st.number_input(
                "Heat Price ($/GJ)",
                min_value=5.0,
                max_value=20.0,
                value=10.0
            )
        
        with col2:
            st.markdown("**Tax and Depreciation Assumptions:**")
            
            # Tax rate
            tax_rate = st.number_input(
                "Corporate Tax Rate (%)",
                min_value=15.0,
                max_value=40.0,
                value=30.0
            ) / 100
            
            # Depreciation period
            depreciation_period = st.number_input(
                "Depreciation Period (years)",
                min_value=5,
                max_value=20,
                value=10
            )
            
            # Depreciation method
            depreciation_method = st.selectbox(
                "Depreciation Method",
                ["Straight Line", "Declining Balance"],
                index=0
            )

# Run the app
if __name__ == "__main__":
    pass  # The app is already running via Streamlit
