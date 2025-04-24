# Bioenergy Project Dashboard - README

## Overview
This dashboard allows users to estimate the cost per GJ and MWh for a bioenergy project using anaerobic digestion. It features a drag-and-drop interface for feedstocks, adjustable parameters, and comprehensive calculations for both biogas and CHP (Combined Heat and Power) outputs.

## Features
- Interactive feedstock management with pre-built parameters
- Process calculations for biogas production and CHP outputs
- Financial calculations including CAPEX, OPEX, and LCOE
- Visualization of results with charts and metrics
- Adjustable assumptions and cost functions

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
1. Clone or download this repository
2. Install the required packages:
```
pip install streamlit pandas numpy matplotlib plotly
```

## Usage

### Running the Dashboard
Navigate to the project directory and run:
```
streamlit run app.py
```

### Dashboard Sections

#### 1. Feedstock Management
- Add feedstocks from the library by clicking the "Add" button
- Adjust feedstock quantities and distances using sliders
- View cost per GJ and MWh for each feedstock
- See a summary of total feedstock metrics and composition

#### 2. Process Configuration
- Configure digester parameters
- Choose between biogas or CHP output
- Adjust process-specific parameters
- View process output metrics

#### 3. Financial Results
- See CAPEX and OPEX breakdowns
- View LCOE analysis
- Check financial metrics (NPV, IRR, payback period)
- Explore sensitivity analysis

#### 4. Assumptions
- Adjust process assumptions
- Modify cost functions
- Change financial assumptions

## Project Structure
- `app.py`: Main Streamlit application
- `feedstock_data.py`: Default feedstock parameters and calculations
- `process_calculations.py`: Biogas and CHP process calculations
- `financial_calculations.py`: CAPEX, OPEX, and LCOE calculations

## Customization
- Add new feedstocks by updating the `DEFAULT_FEEDSTOCKS` dictionary in `feedstock_data.py`
- Modify cost functions in the Assumptions tab
- Adjust financial parameters in the sidebar

## Notes
- The dashboard uses a green color theme to match the bioenergy context
- All calculations are based on industry standards and research
- The simple drag-and-drop functionality allows for easy feedstock management
- The dashboard is designed to run locally on your machine
