# Kombucha Batch Logger & CO₂ Tracker

A Streamlit application for tracking kombucha brewing batches and estimating CO₂ production during fermentation.

## Objective
To create an open-source tool that helps kombucha brewers (home or small business) track fermentation batches, log critical data (pH, temperature, time), and predict CO₂ buildup to avoid overcarbonation or bottle explosions.

## Features

### Core Features
1. **Batch Tracking**
   - Create and manage multiple fermentation batches
   - Log info: start date, tea type, sugar amount, SCOBY source, flavoring, etc.
   - Track batches through primary and secondary fermentation phases
   - Prevent accidental batch deletion with confirmation dialog

2. **Data Logging Dashboard**
   - Input data manually:
     - Primary fermentation: pH, temperature, taste, SCOBY thickness, Brix
     - Secondary fermentation: temperature, carbonation level, bottle firmness
   - View data as tables and interactive line graphs
   - Track fermentation progress with visual indicators
   - Prevent duplicate daily readings with smart validation

3. **CO₂ Estimation Module**
   - Estimate CO₂ pressure buildup in sealed bottles during secondary fermentation using:
     - Sugar content (initial and added)
     - Temperature
     - Fermentation duration
     - Batch volume
   - Visual pressure gauge with warning thresholds
   - Safety alerts for potentially dangerous pressure levels

4. **Alerts & Notifications**
   - Set safe thresholds for temperature/pH/CO₂
   - Visual warnings when a batch is at risk (e.g., excessive CO₂ buildup)
   - Customizable alert settings
   - Daily reading reminders with status indicators

5. **Export & Backup**
   - Export logs to CSV for individual batches or all data
   - Export comparison data between multiple batches
   - Data stored in local JSON file with automatic saving

6. **Data Visualization & Analysis**
   - View fermentation progress with interactive charts
   - Compare multiple batches side-by-side
   - Analyze trends across different tea types and fermentation conditions
   - Predict future CO₂ production based on current trends

## Who Can Use It?
- Kombucha hobbyists
- Microbreweries
- Fermentation enthusiasts
- Science classrooms (experiments!)
- For business QC & documentation
  
## Installation

1. Clone this repository:
   ```
   git clone https://github.com/terranos/kombucha-batch-logger-co2-tracker.git
   cd kombucha-batch-logger-co2-tracker
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the Streamlit application:
   ```
   streamlit run app.py
   ```

2. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501).

3. Use the navigation tabs to:
   - **Batch Management**: Create new batches and view all batch data
   - **Primary Fermentation**: Track pH, temperature, and other metrics during initial fermentation
   - **Secondary Fermentation**: Monitor carbonation and pressure during bottling phase
   - **Batch Comparison**: Compare multiple batches side-by-side with visualizations

4. Safety features:
   - The application will display warnings when CO₂ pressure approaches dangerous levels
   - A dashboard at the top of the page shows at-risk batches that need attention
   - Confirmation dialogs prevent accidental data deletion
   - Duplicate reading prevention helps maintain data integrity

## Key Features in Detail

### Primary Fermentation Tracking
- **Main Objective**: Monitor fermentation completion to determine optimal bottling time
- Log pH, temperature, Brix (sugar content), and taste profile
- Track fermentation progress with visual indicators
- Daily reading reminders and duplicate prevention
- Move batches to secondary fermentation when ready
- Visual indicators for last reading status (today, yesterday, or days ago)
- Detailed explanations of what each measurement means and optimal ranges

### Secondary Fermentation Monitoring
- **Main Objective**: Monitor CO₂ pressure buildup to prevent over-carbonation and bottle explosions
- Track carbonation level, bottle firmness, and temperature
- Monitor CO₂ pressure with visual gauge and safety warnings
- Daily reading reminders with safety guidance
- Get recommendations for when to refrigerate based on carbonation level
- Prediction of future CO₂ production to anticipate potential issues
- Clear explanations of reading frequency and safety considerations

### Batch Comparison
- Compare multiple batches with interactive charts
- Analyze trends in pH, temperature, CO₂ production, and fermentation completion
- Export comparison data for further analysis
- Visual representation of tea type distribution across batches

### Data Management
- Secure data storage in local JSON file
- Export functionality for all data or specific comparisons
- Data backup through CSV export
- Confirmation dialogs to prevent accidental data deletion
- Automatic saving of all changes

## CO₂ Calculation Model

The CO₂ production estimation is based on a simplified model that considers:
- Sugar content (primary factor)
- Fermentation time
- Temperature
- Batch volume

The model accounts for:
- Diminishing fermentation rate over time
- Temperature effects on fermentation speed
- Volume effects on fermentation efficiency

### The math..
1. **Basic CO2 Production**:
   Function: `calculate_co2_production(sugar_amount, days, temperature, volume)`
   This function estimates the CO2 production during kombucha fermentation by considering several factors:
   - Sugar Conversion: Sugar is converted into CO2 and ethanol during fermentation, and the function assumes that 46% of the sugar weight is turned into CO2.
   - Temperature: The fermentation rate increases as the temperature rises above 25°C.
   - Time: Fermentation efficiency decreases over time. In the first week, the fermentation is most active, but the rate slows down as sugar is consumed.
   - Volume: Larger batches have slightly less efficient fermentation, so the volume of the batch reduces efficiency as it increases.
   Formula: 𝐶𝑂2 produced = sugar amount × 0.46 × temp factor × time factor × volume factor

2. **Fermentation Completion Percentage**:
   Function: `estimate_fermentation_completion(sugar_amount, co2_produced)`
   This function estimates the percentage of fermentation completion by comparing the actual CO2 produced against the theoretical maximum CO2 that could be produced from the initial sugar.
   Formula: Completion Percentage = (CO2 produced / Maximum CO2) × 100
   where the maximum CO2 is calculated as 46% of the sugar amount.

3. **CO2 Pressure Estimation**:
   Function: `estimate_co2(sugar_content, temp, time_in_days)`
   This function estimates the pressure buildup in a sealed container due to CO2 produced during fermentation. It factors in temperature, time, and sugar content.
   - Temperature Factor: Higher temperatures increase the fermentation rate.
   - Time Factor: As fermentation progresses, the rate slows down.
   - Pressure Conversion: 1 gram of sugar is assumed to produce 0.01 atm of pressure in a typical bottle.
   Formula: CO2 pressure = sugar content × temp factor × time factor × 0.01

These formulas together help to estimate the CO2 production, fermentation progress, and pressure buildup during the kombucha fermentation process.


## Measuring Tools
To effectively track your kombucha fermentation with this application, you'll need the following measuring tools:

- **Digital Scale**: For measuring sugar and other ingredients accurately (precision to 1g)
- **Thermometer**: For monitoring fermentation temperature (range 0-40°C)
- **pH Meter or pH Test Strips**: For measuring acidity (range 2.0-7.0)
- **Refractometer or Hydrometer**: For measuring sugar content (Brix)

## Data Storage
Batch data is stored locally in a JSON file (`kombucha_data.json`). For production use, consider implementing a database backend.

## Future Updates
- **Raspberry Pi Sensor Integration**: Optional support for temperature and pH sensors
- **Machine Learning Integration**: 
  - Train a regression model on past batches to predict best harvest time
  - Use anomaly detection to flag potential contaminations or failed fermentation early
- **Mobile App Integration**: Companion mobile app for notifications and remote monitoring
- **Community Features**: Share recipes and fermentation profiles with other users
- **Advanced Analytics**: More detailed statistical analysis of fermentation patterns

## License

[MIT License](LICENSE)

## Acknowledgements

- Built with [Streamlit](https://streamlit.io/)
- Visualization powered by [Plotly](https://plotly.com/)
- Data analysis with [Pandas](https://pandas.pydata.org/)

If you find this project helpful, consider [buying me a coffee](https://www.buymeacoffee.com/Terranos) ☕.

Deen  
deen.htc@gmail.com

