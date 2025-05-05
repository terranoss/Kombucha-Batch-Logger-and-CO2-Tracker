import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import json
import os
from co2_calculator import calculate_co2_production, estimate_fermentation_completion, estimate_co2

# File path for persistent storage
DATA_FILE = "kombucha_data.json"
print(f"Data file path: {os.path.abspath(DATA_FILE)}")

# Function to save data to file - define this BEFORE using it
def save_data():
    data = {
        'batches': st.session_state.batches,
        'settings': st.session_state.settings
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(st.session_state.batches)} batches to {DATA_FILE}")

# Set page configuration
st.set_page_config(
    page_title="Kombucha Batch Logger",
    page_icon="🍵",
    layout="wide"
)

# Initialize session state for batch data and settings
if 'batches' not in st.session_state:
    st.session_state.batches = []

# Initialize settings if they don't exist
if 'settings' not in st.session_state:
    st.session_state.settings = {
        'danger_threshold': 2.5,
        'warning_threshold': 1.5,
        'show_alerts': True,
        'alert_check_frequency': 'always'  # Options: 'always', 'daily', 'never'
    }

# Initialize confirmation flags
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

# Load data from file if it exists (do this AFTER initializing session state)
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            st.session_state.batches = data.get('batches', [])
            
            # Update settings if they exist in the file
            if 'settings' in data:
                st.session_state.settings.update(data['settings'])
                
        print(f"Loaded {len(st.session_state.batches)} batches from {DATA_FILE}")
    except Exception as e:
        st.error(f"Error loading data: {e}")

# Sidebar for settings
with st.sidebar:
    st.title("Settings")

    # Carbonation Alert Settings
    st.header("Carbonation Alert Settings")

    # Enable/disable alerts
    show_alerts = st.checkbox("Show Over-Carbonation Alerts",
                             value=st.session_state.settings['show_alerts'],
                             help="Enable or disable alerts for batches at risk of over-carbonation")

    # Danger threshold slider
    danger_threshold = st.slider(
        "Danger Threshold (atm)",
        min_value=1.0,
        max_value=5.0,
        value=float(st.session_state.settings['danger_threshold']),
        step=0.1,
        help="CO₂ pressure level that triggers a danger alert (risk of bottle explosion)"
    )

    # Warning threshold slider
    warning_threshold = st.slider(
        "Warning Threshold (atm)",
        min_value=0.5,
        max_value=danger_threshold - 0.1,
        value=min(float(st.session_state.settings['warning_threshold']), danger_threshold - 0.1),
        step=0.1,
        help="CO₂ pressure level that triggers a warning alert"
    )

    # Alert check frequency
    alert_check_frequency = st.radio(
        "Alert Check Frequency",
        options=["Always", "Daily", "Never"],
        index=["always", "daily", "never"].index(st.session_state.settings['alert_check_frequency']),
        help="How often to check for over-carbonation alerts"
    )

    # Save settings button
    if st.button("Save Settings"):
        st.session_state.settings['danger_threshold'] = danger_threshold
        st.session_state.settings['warning_threshold'] = warning_threshold
        st.session_state.settings['show_alerts'] = show_alerts
        st.session_state.settings['alert_check_frequency'] = alert_check_frequency.lower()
        save_data()  # Save data to file
        st.success("Settings saved successfully!")

    st.markdown("---")

# App title and description
st.title("Kombucha Batch Logger")
st.markdown("""
This application helps you track your kombucha brewing batches.
Log your batch details and view your brewing history.

⚠️ **SAFETY DISCLAIMER**: The CO₂ pressure estimates provided by this application are based on simplified models and should be used as general guidance only, not as a definitive safety measure. Always follow proper brewing safety practices:
- Use pressure-rated bottles designed for fermentation
- Store bottles in a safe location, preferably in a container that can contain potential breakage
- Never ignore signs of excessive pressure (bulging caps, hissing sounds)
- When in doubt, refrigerate your brew to slow fermentation

The developers of this application are not responsible for any damage, injury, or loss resulting from reliance on these estimates.
""")

# Check if alerts are enabled
if st.session_state.settings['show_alerts']:
    # Determine if we should check for alerts based on frequency setting
    should_check_alerts = False

    if st.session_state.settings['alert_check_frequency'] == 'always':
        should_check_alerts = True
    elif st.session_state.settings['alert_check_frequency'] == 'daily':
        # Check if we've already checked today
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if 'last_alert_check' not in st.session_state.settings or st.session_state.settings['last_alert_check'] != today:
            should_check_alerts = True
            st.session_state.settings['last_alert_check'] = today

    if should_check_alerts and st.session_state.batches:
        # Get the danger and warning thresholds from settings
        danger_threshold = st.session_state.settings['danger_threshold']
        warning_threshold = st.session_state.settings['warning_threshold']

        # Check all batches for over-carbonation risk
        at_risk_batches = []

        for batch in st.session_state.batches:
            # Skip if the batch doesn't have measurements
            if "measurements" not in batch or not batch["measurements"]:
                continue

            # Get the latest measurement
            latest_measurement = sorted(batch["measurements"], key=lambda m: m["date"], reverse=True)[0]

            # Check if CO₂ pressure exceeds thresholds
            if "co2_pressure" in latest_measurement:
                pressure = latest_measurement["co2_pressure"]
                risk_level = None

                if pressure >= danger_threshold:
                    risk_level = "danger"
                elif pressure >= warning_threshold:
                    risk_level = "warning"

                if risk_level:
                    at_risk_batches.append({
                        "name": batch["name"],
                        "pressure": pressure,
                        "risk_level": risk_level,
                        "date": latest_measurement["date"]
                    })

        # Display alerts if any batches are at risk
        if at_risk_batches:
            st.markdown("### ⚠️ Carbonation Alerts")

            # Create columns for the alerts
            alert_cols = st.columns([1, 1, 1, 1])
            alert_cols[0].markdown("**Batch Name**")
            alert_cols[1].markdown("**CO₂ Pressure**")
            alert_cols[2].markdown("**Risk Level**")
            alert_cols[3].markdown("**Last Measured**")

            # Sort batches by risk level (danger first) and then by pressure
            at_risk_batches.sort(key=lambda b: (0 if b["risk_level"] == "danger" else 1, -b["pressure"]))

            for batch in at_risk_batches:
                cols = st.columns([1, 1, 1, 1])
                cols[0].write(batch["name"])
                cols[1].write(f"{batch['pressure']:.2f} atm")

                if batch["risk_level"] == "danger":
                    cols[2].error("DANGER")
                else:
                    cols[2].warning("Warning")

                cols[3].write(batch["date"])

            # Replace the View Fermentation Data button with clearer guidance
            st.info("""
            **To view detailed fermentation data:**
            1. Click on the "Primary Fermentation" tab above for batches in initial fermentation
            2. Click on the "Secondary Fermentation" tab for bottled batches
            
            This will allow you to view and update measurements for your at-risk batches.
            """)

            st.markdown("---")

# Initialize the active tab in session state if it doesn't exist
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "batch"  # Default to batch management

# Create radio buttons for tab selection instead of tabs
tab_options = ["Batch Management", "Primary Fermentation", "Secondary Fermentation", "Batch Comparison"]

# Map session state values to tab indices
tab_mapping = {
    "batch": 0,
    "primary": 1,
    "secondary": 2,
    "comparison": 3
}

# Set the default index based on session state
default_index = tab_mapping.get(st.session_state.active_tab, 0)

# Define a callback function to update session state when radio button changes
def on_tab_change():
    # This function will be called when the radio button value changes
    # The new value is already in st.session_state.tab_selector
    if st.session_state.tab_selector == "Batch Management":
        st.session_state.active_tab = "batch"
    elif st.session_state.tab_selector == "Primary Fermentation":
        st.session_state.active_tab = "primary"
    elif st.session_state.tab_selector == "Secondary Fermentation":
        st.session_state.active_tab = "secondary"
    elif st.session_state.tab_selector == "Batch Comparison":
        st.session_state.active_tab = "comparison"

# Create the tab selector with on_change callback
selected_tab = st.radio(
    "Select Tab:", 
    tab_options, 
    index=default_index, 
    horizontal=True,
    key="tab_selector",
    on_change=on_tab_change
)

# Display content based on the active_tab in session state
if st.session_state.active_tab == "batch":
    st.header("Batch Management")
    st.markdown("""
    ### 📝 Create and manage your kombucha batches
    
    **Fermentation Phases Explained:**
    - **Primary Fermentation**: The initial open-air fermentation with SCOBY in a jar/vessel covered with breathable cloth
    - **Secondary Fermentation**: Bottling with optional flavoring in sealed containers to build carbonation
    """)
    
    # Create two columns for the main layout
    col1, col2 = st.columns([1, 1])

    # Batch input form
    with col1:
        st.header("Log a New Batch")

        with st.form("batch_form"):
            batch_name = st.text_input("Batch Name", "My Kombucha Batch")

            tea_type = st.selectbox(
                "Tea Type",
                ["Black", "Green", "Oolong", "White", "Herbal", "Mixed"]
            )

            sugar_content = st.number_input(
                "Sugar Content (grams)",
                min_value=1,
                max_value=1000,
                value=200
            )

            start_date = st.date_input(
                "Start Date",
                datetime.datetime.now()
            )
            
            # Add SCOBY source field
            scoby_source = st.text_input(
                "SCOBY Source",
                placeholder="e.g., Home-grown, Friend, Commercial",
                help="Where did you get your SCOBY from?"
            )
            
            # Add flavoring field
            flavoring = st.text_input(
                "Flavoring (if any)",
                placeholder="e.g., Ginger, Fruit, Herbs",
                help="Any flavoring ingredients added to this batch"
            )

            # Optional additional fields
            st.markdown("### Optional Details")
            volume = st.number_input(
                "Batch Volume (liters)",
                min_value=0.1,
                max_value=50.0,
                value=2.0,
                step=0.1
            )

            notes = st.text_area("Notes", "")

            # Submit button
            submitted = st.form_submit_button("Log Batch")

            if submitted:
                # Check if a batch with the same name already exists
                existing_batch_names = [batch["name"].lower() for batch in st.session_state.batches]
                
                if batch_name.lower() in existing_batch_names:
                    st.error(f"A batch with the name '{batch_name}' already exists. Please use a different name.")
                else:
                    # Create a new batch entry
                    new_batch = {
                        "name": batch_name,
                        "tea_type": tea_type,
                        "sugar_content": sugar_content,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "scoby_source": scoby_source,
                        "flavoring": flavoring,
                        "volume": volume,
                        "notes": notes,
                        "logged_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "fermentation_phase": "primary"  # Default to primary fermentation
                    }

                    # Add to session state
                    st.session_state.batches.append(new_batch)
                    save_data()  # Save data to file

                    st.success("Batch logged successfully!")

    # Display logged batches in the first tab
    with col2:
        st.header("Logged Batches")

        if not st.session_state.batches:
            st.info("No batches logged yet. Use the form to log your first batch!")
        else:
            # Add batch management options
            st.subheader("Batch Management")
            
            # Create a selection for batch to delete
            batch_names = [batch["name"] for batch in st.session_state.batches]
            batch_to_delete = st.selectbox(
                "Select a batch to delete",
                options=batch_names,
                key="batch_delete_selectbox"
            )
            
            # Add delete button with confirmation
            delete_col1, delete_col2 = st.columns([1, 3])
            
            with delete_col1:
                if st.button("Delete Batch", key="delete_batch_button", type="primary"):
                    st.session_state.confirm_delete = True
            
            with delete_col2:
                if st.session_state.get("confirm_delete", False):
                    st.warning(f"Are you sure you want to delete '{batch_to_delete}'? This cannot be undone.")
                    confirm_col1, confirm_col2 = st.columns([1, 1])
                    
                    with confirm_col1:
                        if st.button("Yes, Delete", key="confirm_delete_yes"):
                            # Find and remove the selected batch
                            st.session_state.batches = [
                                batch for batch in st.session_state.batches 
                                if batch["name"] != batch_to_delete
                            ]
                            save_data()  # Save data to file
                            st.success(f"Batch '{batch_to_delete}' deleted successfully!")
                            st.session_state.confirm_delete = False
                            st.rerun()
                    
                    with confirm_col2:
                        if st.button("Cancel", key="confirm_delete_cancel"):
                            st.session_state.confirm_delete = False
                            st.rerun()
            
            st.markdown("---")

            # Convert the batches to a DataFrame for display
            batches_df = pd.DataFrame(st.session_state.batches)
            
            # Handle the measurements column - either exclude it or format it
            if "measurements" in batches_df.columns:
                # Option 1: Drop the measurements column
                batches_df = batches_df.drop(columns=["measurements"])
                
                # Option 2 (alternative): Format the measurements column to show count
                # batches_df["measurements"] = batches_df["measurements"].apply(
                #     lambda m: f"{len(m)} readings" if isinstance(m, list) else "No readings"
                # )

            # Display the table with all batch information
            st.dataframe(
                batches_df,
                column_config={
                    "name": "Batch Name",
                    "tea_type": "Tea Type",
                    "sugar_content": st.column_config.NumberColumn(
                        "Sugar (g)",
                        format="%d g"
                    ),
                    "start_date": "Start Date",
                    "scoby_source": "SCOBY Source",
                    "flavoring": "Flavoring",
                    "volume": st.column_config.NumberColumn(
                        "Volume",
                        format="%.1f L"
                    ),
                    "notes": "Notes",
                    "logged_at": "Logged At"
                },
                hide_index=True,
                use_container_width=True
            )

            # Summary statistics
            st.subheader("Batch Statistics")

            total_batches = len(st.session_state.batches)
            total_sugar = sum(batch["sugar_content"] for batch in st.session_state.batches)
            total_volume = sum(batch["volume"] for batch in st.session_state.batches)

            st.markdown(f"""
            - **Total Batches**: {total_batches}
            - **Total Sugar Used**: {total_sugar} grams
            - **Total Volume**: {total_volume:.1f} liters
            """)

            # Tea type distribution
            tea_counts = batches_df["tea_type"].value_counts()

            st.subheader("Tea Type Distribution")
            st.bar_chart(tea_counts)

            # Add export to CSV functionality
            st.subheader("Export Data")

            if st.button("Export All Batch Data to CSV", key="export_all_data"):
                # Create a comprehensive dataframe with all batch data
                export_data = []

                for batch in st.session_state.batches:
                    # Basic batch info
                    batch_info = {
                        "batch_name": batch["name"],
                        "tea_type": batch["tea_type"],
                        "sugar_content": batch["sugar_content"],
                        "start_date": batch["start_date"],
                        "volume": batch["volume"],
                        "notes": batch["notes"]
                    }

                    # If there are measurements, add each as a row
                    if "measurements" in batch and batch["measurements"]:
                        for measurement in batch["measurements"]:
                            # Combine batch info with measurement data
                            measurement_row = batch_info.copy()
                            measurement_row.update({
                                "measurement_date": measurement["date"],
                                "temperature": measurement["temperature"],
                                "ph": measurement["ph"],
                                "co2_estimate": measurement["co2_estimate"],
                                "co2_pressure": measurement.get("co2_pressure", "N/A"),
                                "completion": measurement.get("completion", "N/A")
                            })
                            export_data.append(measurement_row)
                    else:
                        # If no measurements, just add the batch info
                        batch_info.update({
                            "measurement_date": "N/A",
                            "temperature": "N/A",
                            "ph": "N/A",
                            "co2_estimate": "N/A",
                            "co2_pressure": "N/A",
                            "completion": "N/A"
                        })
                        export_data.append(batch_info)

                # Create dataframe from the collected data
                export_df = pd.DataFrame(export_data)

                # Convert dataframe to CSV
                csv = export_df.to_csv(index=False)

                # Create a download button
                st.download_button(
                    label="Download CSV File",
                    data=csv,
                    file_name="kombucha_batch_data.csv",
                    mime="text/csv",
                    help="Click to download all batch data as a CSV file"
                )

elif st.session_state.active_tab == "primary":
    st.header("Primary Fermentation Tracking")
    st.markdown("""
    ### 🍵 Track your primary fermentation progress
    
    Primary fermentation is the first stage where your SCOBY converts sugar to acids and produces flavor compounds.
    This phase typically occurs in an open container covered with a breathable cloth and lasts 7-14 days.
    
    **Main Objective**: Monitor the fermentation completion to determine the optimal time to move to secondary fermentation.
    """)
    
    # Create columns with better proportions for the fermentation data section
    fcol1, fcol2 = st.columns([1, 1.2])

    with fcol1:
        # Add a container with border styling
        with st.container():
            st.subheader("Input Fermentation Data")
            
            # Select a batch if any exist
            if not st.session_state.batches:
                st.warning("No batches available. Please log a batch first.")
                selected_batch = None
            else:
                # Filter for primary fermentation batches
                primary_batches = [b for b in st.session_state.batches 
                                  if b.get("fermentation_phase", "primary") == "primary"]
                
                if not primary_batches:
                    st.warning("No batches in primary fermentation phase. Please create a batch first.")
                    selected_batch = None
                else:
                    # Add a more visually appealing batch selector
                    st.markdown("##### Select Your Batch")
                    batch_options = [f"{b['name']} (started {b['start_date']})" for b in primary_batches]
                    selected_batch_idx = st.selectbox(
                        "Select Batch",
                        range(len(batch_options)),
                        format_func=lambda i: batch_options[i]
                    )
                    selected_batch = primary_batches[selected_batch_idx]
                    
                    # Calculate days fermenting
                    start_date = datetime.datetime.strptime(selected_batch['start_date'], "%Y-%m-%d")
                    today = datetime.datetime.now()
                    days_fermenting = (today - start_date).days
                    
                    # Display batch info with last reading date
                    last_reading_date = "No readings yet"
                    if "measurements" in selected_batch and selected_batch["measurements"]:
                        # Filter for primary phase measurements
                        primary_measurements = [m for m in selected_batch["measurements"] if m.get("phase") == "primary"]
                        if primary_measurements:
                            # Get the most recent reading
                            last_reading = sorted(primary_measurements, key=lambda x: x["date"], reverse=True)[0]
                            last_reading_date = last_reading["date"]
                            days_since_reading = (today - datetime.datetime.strptime(last_reading_date, "%Y-%m-%d")).days
                            if days_since_reading == 0:
                                last_reading_status = "✅ Today"
                            elif days_since_reading == 1:
                                last_reading_status = "⚠️ Yesterday"
                            else:
                                last_reading_status = f"❗ {days_since_reading} days ago"
                        else:
                            last_reading_status = "❓ No primary readings"
                    else:
                        last_reading_status = "❓ No readings"
                    
                    st.markdown(f"""
                    <div style="background-color: #1E1E1E; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <h5 style="color: #FFFFFF;">Batch Information</h5>
                        <p style="color: #E5E7EB;"><strong>Tea Type:</strong> {selected_batch['tea_type']}</p>
                        <p style="color: #E5E7EB;"><strong>Sugar Content:</strong> {selected_batch['sugar_content']}g</p>
                        <p style="color: #E5E7EB;"><strong>Volume:</strong> {selected_batch['volume']}L</p>
                        <p style="color: #E5E7EB;"><strong>Days Fermenting:</strong> {days_fermenting} days</p>
                        <p style="color: #E5E7EB;"><strong>Last Reading:</strong> {last_reading_status}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Primary fermentation specific inputs
                    st.markdown("---")
                    st.subheader("Current Readings")

                    # Use columns for the sliders to make them more compact
                    temp_col, ph_col = st.columns(2)
                    
                    with temp_col:
                        temperature = st.slider(
                            "Temperature (°C)",
                            min_value=15.0,
                            max_value=35.0,
                            value=25.0,
                            step=0.5,
                            help="The current temperature of your kombucha batch"
                        )
                    
                    with ph_col:
                        ph_level = st.slider(
                            "pH Level",
                            min_value=2.0,
                            max_value=7.0,
                            value=3.5,
                            step=0.1,
                            help="The current pH level of your kombucha batch"
                        )
                    
                    # Primary fermentation specific metrics
                    taste = st.select_slider(
                        "Taste Profile",
                        options=["Very Sweet", "Sweet", "Balanced", "Tart", "Sour", "Very Sour"],
                        value="Balanced",
                        help="How does your kombucha taste currently?"
                    )
                    
                    # Add Brix measurement
                    brix = st.number_input(
                        "Brix (°Bx)",
                        min_value=0.0,
                        max_value=20.0,
                        value=6.0,
                        step=0.1,
                        help="Sugar content measured with a refractometer or hydrometer (in degrees Brix)"
                    )
                    
                    # Remove SCOBY thickness input field
                    # scoby_thickness = st.number_input(
                    #     "SCOBY Thickness (mm)",
                    #     min_value=0,
                    #     max_value=50,
                    #     value=5,
                    #     step=1,
                    #     help="Approximate thickness of your SCOBY in millimeters"
                    # )
                    
                    # Check if there's already a reading for today
                    today_str = today.strftime("%Y-%m-%d")
                    has_reading_today = False
                    
                    if "measurements" in selected_batch:
                        for measurement in selected_batch["measurements"]:
                            if measurement["date"] == today_str and measurement["phase"] == "primary":
                                has_reading_today = True
                                break
                    
                    # Display reading frequency guidance
                    st.markdown("---")
                    st.subheader("Reading Frequency")
                    
                    st.info("""
                    **Recommended Reading Schedule**:
                    - Take readings once daily, ideally at the same time each day
                    - More frequent readings during the first 3-5 days can help track the initial fermentation curve
                    - Consistent daily readings provide the most accurate fermentation progress tracking
                    
                    **What These Readings Tell You**:
                    - **pH**: Decreases as fermentation progresses (starts ~4.5, finishes ~2.8-3.2)
                    - **Brix**: Measures sugar content, decreases as sugar is consumed (starts ~8-12, finishes ~2-4)
                    - **Temperature**: Affects fermentation speed (optimal: 23-28°C)
                    - **Taste**: Subjective assessment that helps correlate with objective measurements
                    """)
                    
                    # Save readings button with improved styling
                    st.markdown("---")
                    
                    # Show warning if already has reading for today
                    if has_reading_today:
                        st.warning("⚠️ You've already recorded a reading for today. Adding another will create a duplicate entry for today's date.")
                    else:
                        st.success("✅ No reading recorded for today yet. It's a good time to add your daily measurement!")
                    
                    if st.button("💾 Record Readings", use_container_width=True, key="save_primary_readings"):
                        # Initialize measurements list if it doesn't exist
                        if "measurements" not in selected_batch:
                            selected_batch["measurements"] = []

                        # Add new measurement (without SCOBY thickness)
                        selected_batch["measurements"].append({
                            "date": today.strftime("%Y-%m-%d"),
                            "temperature": temperature,
                            "ph": ph_level,
                            "taste": taste,
                            "brix": brix,
                            "phase": "primary"
                        })
                        save_data()  # Save data to file

                        st.success("Readings saved successfully!")
                        
                    # Add option to move to secondary fermentation
                    st.markdown("---")
                    st.subheader("Ready for Bottling?")
                    
                    if st.button("Move to Secondary Fermentation", use_container_width=True, key="move_to_secondary"):
                        # Update the batch to secondary phase
                        selected_batch["fermentation_phase"] = "secondary"
                        selected_batch["bottling_date"] = today.strftime("%Y-%m-%d")
                        save_data()
                        
                        st.success("Batch moved to secondary fermentation! Please go to the Secondary Fermentation tab to add bottling details.")
                        st.balloons()

    with fcol2:
        if selected_batch:
            # Add a container with styling
            with st.container():
                st.subheader("CO₂ Production Estimate")
                
                # Calculate CO2 production and completion percentage
                co2_produced = calculate_co2_production(
                    sugar_amount=selected_batch['sugar_content'],
                    days=days_fermenting,
                    temperature=temperature,
                    volume=selected_batch['volume']
                )
                
                completion_pct = estimate_fermentation_completion(
                    sugar_amount=selected_batch['sugar_content'],
                    co2_produced=co2_produced
                )
                
                # Create a two-column layout for the metrics
                metric_col1, metric_col2 = st.columns(2)
                
                with metric_col1:
                    # Display CO₂ production estimate with icon
                    st.markdown("##### 🧪 CO₂ Produced")
                    st.metric(
                        "Amount",
                        f"{co2_produced:.2f} g",
                        delta=f"{completion_pct:.1f}% of potential"
                    )
                
                with metric_col2:
                    # Calculate CO₂ pressure
                    co2_pressure = estimate_co2(
                        sugar_content=selected_batch['sugar_content'],
                        temp=temperature,
                        time_in_days=days_fermenting
                    )

                    # Get thresholds from settings
                    danger_threshold = st.session_state.settings['danger_threshold']
                    warning_threshold = st.session_state.settings['warning_threshold']

                    # Display CO₂ pressure estimate with warning levels and icon
                    st.markdown("##### 📊 CO₂ Pressure")
                    pressure_color = "normal"
                    if co2_pressure >= danger_threshold:
                        pressure_color = "off"
                        pressure_warning = f"⚠️ Danger! (>{danger_threshold} atm)"
                    elif co2_pressure >= warning_threshold:
                        pressure_color = "inverse"
                        pressure_warning = f"⚠️ High (>{warning_threshold} atm)"
                    else:
                        pressure_warning = f"✅ Safe (<{warning_threshold} atm)"

                    st.metric(
                        "Pressure",
                        f"{co2_pressure:.2f} atm",
                        delta=pressure_warning,
                        delta_color=pressure_color
                    )

                # Create a progress bar for fermentation completion with better styling
                st.markdown("---")
                st.markdown("### Fermentation Progress")
                
                # Add percentage text above progress bar
                st.markdown(f"<h4 style='text-align: center; color: {'green' if completion_pct < 70 else 'orange' if completion_pct < 90 else 'red'};'>{completion_pct:.1f}%</h4>", unsafe_allow_html=True)
                
                # Progress bar
                progress_color = "green" if completion_pct < 70 else "orange" if completion_pct < 90 else "red"
                st.progress(min(completion_pct / 100, 1.0))
                
                # Add interpretation text
                if completion_pct < 30:
                    st.info("🌱 Early fermentation stage - sweet with mild acidity")
                elif completion_pct < 70:
                    st.success("🍵 Mid fermentation stage - balanced sweetness and acidity")
                elif completion_pct < 90:
                    st.warning("🔶 Late fermentation stage - becoming more acidic")
                else:
                    st.error("🔴 Final fermentation stage - highly acidic, minimal sweetness")
                
                # Add Brix interpretation
                st.markdown("---")
                st.markdown("### Brix Interpretation")
                
                if brix > 8:
                    st.info("🍯 High sugar content - fermentation is in early stages")
                elif brix > 5:
                    st.success("🍵 Medium sugar content - fermentation is progressing well")
                elif brix > 3:
                    st.warning("🔶 Low sugar content - fermentation is nearing completion")
                else:
                    st.error("🔴 Very low sugar content - fermentation is complete or nearly complete")
                
                st.markdown("""
                **Brix Measurement Guide**:
                - Starting kombucha tea: ~8-12 °Bx
                - Mid-fermentation: ~5-8 °Bx
                - Ready to bottle: ~3-5 °Bx
                - Fully fermented: <3 °Bx
                
                A steady decrease in Brix readings over time indicates active fermentation.
                """)
                
                # Display pressure gauge visualization with improved styling
                st.markdown("---")
                st.markdown("### CO₂ Pressure Gauge")

                # Add disclaimer about pressure estimates
                st.info("""
                **Note on Accuracy**: This pressure estimate is based on a simplified model that doesn't account for all variables in real fermentation environments. Factors like microbial composition, oxygen levels, and previous fermentation history can all affect actual CO₂ production. Always use physical signs (bottle firmness, cap bulging) alongside these estimates.
                """)

                # Calculate gauge range and steps based on thresholds
                max_gauge_value = max(3.0, danger_threshold * 1.2)  # Set max to at least 20% above danger threshold

                # Create steps for the gauge
                gauge_steps = [
                    {"range": [0, warning_threshold], "color": "green"},
                    {"range": [warning_threshold, danger_threshold], "color": "yellow"},
                    {"range": [danger_threshold, max_gauge_value], "color": "red"},
                ]

                pressure_gauge = {
                    "data": [
                        {
                            "type": "indicator",
                            "mode": "gauge+number",
                            "value": co2_pressure,
                            "title": {"text": "Pressure (atm)"},
                            "gauge": {
                                "axis": {"range": [0, max_gauge_value], "tickwidth": 1},
                                "bar": {"color": "darkblue"},
                                "bgcolor": "white",
                                "borderwidth": 2,
                                "bordercolor": "gray",
                                "steps": gauge_steps,
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": danger_threshold,
                                },
                            },
                        }
                    ],
                    "layout": {"height": 250, "margin": {"t": 25, "b": 25, "l": 25, "r": 25}},
                }
                st.plotly_chart(pressure_gauge, use_container_width=True)

                # Display pH level interpretation
                st.markdown("### pH Level Interpretation")
                if ph_level > 4.5:
                    st.warning("pH is high. Fermentation may be just starting.")
                elif ph_level > 3.5:
                    st.info("pH is in a good range for early fermentation.")
                elif ph_level > 2.8:
                    st.success("pH is in the ideal range for kombucha.")
                else:
                    st.warning("pH is getting low. Your kombucha may be very sour.")

                # Display temperature interpretation
                st.markdown("### Temperature Interpretation")
                if temperature < 20:
                    st.warning("Temperature is low. Fermentation will be slower.")
                elif temperature < 24:
                    st.info("Temperature is in a good range, but slightly cool.")
                elif temperature <= 29:
                    st.success("Temperature is in the ideal range for kombucha fermentation.")
                else:
                    st.warning("Temperature is high. Watch for mold or over-fermentation.")

                # Show CO₂ production over time if measurements exist
                if "measurements" in selected_batch and selected_batch["measurements"]:
                    st.markdown("---")
                    st.subheader("📈 Measurement History")

                    # Create a dataframe from measurements
                    measurements_df = pd.DataFrame(selected_batch["measurements"])
                    measurements_df["date"] = pd.to_datetime(measurements_df["date"])

                    # Create tabs for different charts with custom styling
                    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 CO₂ Production", "📈 CO₂ Pressure", "🔍 Data Table"])

                    with chart_tab1:
                        # Create a line chart of CO₂ production over time with improved styling
                        fig1 = px.line(
                            measurements_df,
                            x="date",
                            y="co2_estimate",
                            title="CO₂ Production Over Time",
                            labels={"date": "Date", "co2_estimate": "CO₂ (g)"},
                            markers=True
                        )
                        
                        # Customize the chart appearance
                        fig1.update_traces(line=dict(width=3), marker=dict(size=8))
                        fig1.update_layout(
                            plot_bgcolor="rgba(240, 242, 246, 0.8)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=12),
                            height=400
                        )

                        st.plotly_chart(fig1, use_container_width=True)

                    with chart_tab2:
                        # Create a line chart of CO₂ pressure over time with improved styling
                        fig2 = px.line(
                            measurements_df,
                            x="date",
                            y="co2_pressure",
                            title="CO₂ Pressure Over Time",
                            labels={"date": "Date", "co2_pressure": "Pressure (atm)"},
                            markers=True
                        )
                        
                        # Customize the chart appearance
                        fig2.update_traces(line=dict(width=3, color="#2E86C1"), marker=dict(size=8))
                        fig2.update_layout(
                            plot_bgcolor="rgba(240, 242, 246, 0.8)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=12),
                            height=400
                        )

                        # Get thresholds from settings
                        danger_threshold = st.session_state.settings['danger_threshold']
                        warning_threshold = st.session_state.settings['warning_threshold']

                        # Add danger threshold line
                        fig2.add_hline(
                            y=danger_threshold,
                            line_dash="dash",
                            line_color="red",
                            line_width=2,
                            annotation_text=f"Danger Level ({danger_threshold} atm)",
                            annotation_font=dict(color="red")
                        )

                        # Add warning threshold line
                        fig2.add_hline(
                            y=warning_threshold,
                            line_dash="dot",
                            line_color="orange",
                            line_width=2,
                            annotation_text=f"Warning Level ({warning_threshold} atm)",
                            annotation_font=dict(color="orange")
                        )

                        st.plotly_chart(fig2, use_container_width=True)

                    with chart_tab3:
                        # Display the measurements table with improved styling
                        st.dataframe(
                            measurements_df,
                            column_config={
                                "date": "Date",
                                "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.1f °C"),
                                "ph": st.column_config.NumberColumn("pH", format="%.1f"),
                                "brix": st.column_config.NumberColumn("Brix", format="%.1f °Bx"),
                                "co2_estimate": st.column_config.NumberColumn("CO₂ (g)", format="%.2f g"),
                                "co2_pressure": st.column_config.NumberColumn("Pressure (atm)", format="%.2f atm"),
                                "completion": st.column_config.ProgressColumn("Completion", format="%.1f%%", min_value=0, max_value=100)
                            },
                            hide_index=True,
                            use_container_width=True
                        )

                        # Add export button for this specific batch's measurements
                        if st.button("Export This Batch's Data to CSV", key="export_primary_batch_data"):
                            # Create a comprehensive dataframe with batch info and measurements
                            export_data = []

                            # Basic batch info
                            batch_info = {
                                "batch_name": selected_batch["name"],
                                "tea_type": selected_batch["tea_type"],
                                "sugar_content": selected_batch["sugar_content"],
                                "start_date": selected_batch["start_date"],
                                "volume": selected_batch["volume"],
                                "notes": selected_batch.get("notes", "")
                            }

                            # Add each measurement as a row
                            for measurement in selected_batch["measurements"]:
                                # Combine batch info with measurement data
                                measurement_row = batch_info.copy()
                                measurement_row.update({
                                    "measurement_date": measurement["date"],
                                    "temperature": measurement["temperature"],
                                    "ph": measurement["ph"],
                                    "co2_estimate": measurement["co2_estimate"],
                                    "co2_pressure": measurement.get("co2_pressure", "N/A"),
                                    "completion": measurement.get("completion", "N/A")
                                })
                                export_data.append(measurement_row)

                            # Create dataframe from the collected data
                            export_df = pd.DataFrame(export_data)

                            # Convert dataframe to CSV
                            csv = export_df.to_csv(index=False)

                            # Create a download button
                            st.download_button(
                                label=f"Download {selected_batch['name']} Data",
                                data=csv,
                                file_name=f"kombucha_{selected_batch['name'].replace(' ', '_').lower()}_data.csv",
                                mime="text/csv",
                                help=f"Click to download {selected_batch['name']} data as a CSV file"
                            )

            # Show a prediction of CO₂ production for the next week
            st.subheader("CO₂ Production Prediction")

            # Add model limitations disclaimer
            st.warning("""
            **Model Limitations**: Predictions become less accurate the further into the future they extend. Environmental changes, temperature fluctuations, and microbial activity variations can all cause actual results to differ from predictions. Use these projections as a general guide rather than exact forecasts.
            """)

            # Generate prediction data
            prediction_days = list(range(days_fermenting, days_fermenting + 8))
            prediction_co2 = [
                calculate_co2_production(
                    sugar_amount=selected_batch['sugar_content'],
                    days=day,
                    temperature=temperature,
                    volume=selected_batch['volume']
                )
                for day in prediction_days
            ]

            # Create a dataframe for the prediction
            prediction_df = pd.DataFrame({
                "day": prediction_days,
                "co2": prediction_co2
            })

            # Create a line chart of the prediction
            fig = px.line(
                prediction_df,
                x="day",
                y="co2",
                title="Predicted CO₂ Production",
                labels={"day": "Fermentation Day", "co2": "CO₂ (g)"}
            )

            # Add a vertical line at the current day
            fig.add_vline(
                x=days_fermenting,
                line_dash="dash",
                line_color="red",
                annotation_text="Today"
            )

            st.plotly_chart(fig, use_container_width=True)

elif st.session_state.active_tab == "secondary":
    st.header("Secondary Fermentation Tracking")
    st.markdown("""
    ### 🍾 Track your secondary fermentation (bottling phase)
    
    Secondary fermentation occurs in sealed bottles and builds carbonation.
    This is when CO₂ pressure builds up and safety monitoring becomes critical.
    
    **Main Objective**: Monitor CO₂ pressure buildup to prevent over-carbonation and ensure bottle safety. Since secondary fermentation is a slower process, readings are not required daily. However, it is recommended to check at least once a week. Due to bottles being sealed, it is not possible to determine the exact CO₂ pressure inside the bottle. Therefore, the readings you log are more about monitoring the trend of carbonation and not the exact pressure.
    
    ⚠️ **SAFETY WARNING**: Pressure buildup in bottles can cause explosions if not monitored carefully.
    Always use proper bottles, store safely, and regularly check carbonation levels.
    """)
    
    # Create columns for the secondary fermentation section
    scol1, scol2 = st.columns([1, 1.2])
    
    with scol1:
        with st.container():
            st.subheader("Bottling Details")
            
            # Select a batch if any exist
            if not st.session_state.batches:
                st.warning("No batches available. Please log a batch first.")
                selected_batch = None
            else:
                # Filter for secondary fermentation batches
                secondary_batches = [b for b in st.session_state.batches 
                                    if b.get("fermentation_phase", "primary") == "secondary"]
                
                if not secondary_batches:
                    st.warning("No batches in secondary fermentation phase. Please move a batch to secondary fermentation first.")
                    selected_batch = None
                else:
                    # Batch selector
                    st.markdown("##### Select Your Bottled Batch")
                    batch_options = [f"{b['name']} (bottled {b.get('bottling_date', 'unknown')})" for b in secondary_batches]
                    selected_batch_idx = st.selectbox(
                        "Select Batch",
                        range(len(batch_options)),
                        format_func=lambda i: batch_options[i],
                        key="secondary_batch_selector"
                    )
                    selected_batch = secondary_batches[selected_batch_idx]
                    
                    # Calculate days since bottling
                    if "bottling_date" in selected_batch:
                        bottling_date = datetime.datetime.strptime(selected_batch['bottling_date'], "%Y-%m-%d")
                        today = datetime.datetime.now()
                        days_bottled = (today - bottling_date).days
                    else:
                        # If bottling date is not recorded, use start date + 14 days as an estimate
                        start_date = datetime.datetime.strptime(selected_batch['start_date'], "%Y-%m-%d")
                        estimated_bottling = start_date + datetime.timedelta(days=14)
                        today = datetime.datetime.now()
                        days_bottled = (today - estimated_bottling).days
                        if days_bottled < 0:
                            days_bottled = 0
                    
                    # Display batch info with last reading date
                    last_reading_date = "No readings yet"
                    if "measurements" in selected_batch and selected_batch["measurements"]:
                        # Filter for secondary phase measurements
                        secondary_measurements = [m for m in selected_batch["measurements"] if m.get("phase") == "secondary"]
                        if secondary_measurements:
                            # Get the most recent reading
                            last_reading = sorted(secondary_measurements, key=lambda x: x["date"], reverse=True)[0]
                            last_reading_date = last_reading["date"]
                            days_since_reading = (today - datetime.datetime.strptime(last_reading_date, "%Y-%m-%d")).days
                            if days_since_reading == 0:
                                last_reading_status = "✅ Today"
                            elif days_since_reading == 1:
                                last_reading_status = "⚠️ Yesterday"
                            else:
                                last_reading_status = f"❗ {days_since_reading} days ago"
                        else:
                            last_reading_status = "❓ No secondary readings"
                    else:
                        last_reading_status = "❓ No readings"
                    
                    st.markdown(f"""
                    <div style="background-color: #1E1E1E; padding: 15px; border-radius: 5px; margin-top: 10px;">
                        <h5 style="color: #FFFFFF;">Batch Information</h5>
                        <p style="color: #E5E7EB;"><strong>Tea Type:</strong> {selected_batch['tea_type']}</p>
                        <p style="color: #E5E7EB;"><strong>Original Sugar:</strong> {selected_batch['sugar_content']}g</p>
                        <p style="color: #E5E7EB;"><strong>Days Since Bottling:</strong> {days_bottled} days</p>
                        <p style="color: #E5E7EB;"><strong>Flavoring:</strong> {selected_batch.get('flavoring', 'None')}</p>
                        <p style="color: #E5E7EB;"><strong>Last Reading:</strong> {last_reading_status}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # If bottling details are incomplete, allow updating them
                    if not selected_batch.get('bottle_type') or not selected_batch.get('added_sugar'):
                        st.markdown("---")
                        st.subheader("Complete Bottling Details")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            bottle_type = st.selectbox(
                                "Bottle Type",
                                options=["Standard Glass", "Swing-Top", "Champagne", "PET Plastic", "Growler", "Other"],
                                index=0 if not selected_batch.get('bottle_type') else ["Standard Glass", "Swing-Top", "Champagne", "PET Plastic", "Growler", "Other"].index(selected_batch.get('bottle_type')),
                                help="What type of bottles are you using for secondary fermentation?"
                            )
                        
                        with col2:
                            added_sugar = st.number_input(
                                "Added Sugar (g/L)",
                                min_value=0.0,
                                max_value=50.0,
                                value=selected_batch.get('added_sugar', 5.0),
                                step=1.0,
                                help="How much sugar did you add per liter for carbonation?"
                            )
                        
                        flavoring = st.text_input(
                            "Flavoring Added",
                            value=selected_batch.get('flavoring', ''),
                            help="What flavoring ingredients did you add when bottling?"
                        )
                        
                        if st.button("Update Bottling Details", use_container_width=True, key="update_bottling_details"):
                            selected_batch['bottle_type'] = bottle_type
                            selected_batch['added_sugar'] = added_sugar
                            selected_batch['flavoring'] = flavoring
                            save_data()
                            st.success("Bottling details updated successfully!")
                    
                    # Secondary fermentation specific inputs
                    st.markdown("---")
                    st.subheader("Current Readings")
                    
                    temperature = st.slider(
                        "Storage Temperature (°C)",
                        min_value=15.0,
                        max_value=35.0,
                        value=23.0,
                        step=0.5,
                        help="The current storage temperature of your bottled kombucha"
                    )
                    
                    carbonation_level = st.select_slider(
                        "Observed Carbonation Level",
                        options=["Flat", "Slightly Fizzy", "Moderately Carbonated", "Well Carbonated", "Highly Carbonated"],
                        value="Moderately Carbonated",
                        help="How carbonated does your kombucha appear to be?"
                    )
                    
                    bottle_firmness = st.select_slider(
                        "Bottle Firmness",
                        options=["Soft", "Slightly Firm", "Firm", "Very Firm", "Hard (Caution)"],
                        value="Slightly Firm",
                        help="How firm do the bottles feel when squeezed? (Only applicable for plastic bottles)"
                    )
                    
                    # Save readings button
                    st.markdown("---")
                    if st.button("💾 Record Secondary Readings", use_container_width=True, key="save_secondary_readings"):
                        # Initialize measurements list if it doesn't exist
                        if "measurements" not in selected_batch:
                            selected_batch["measurements"] = []

                        # Add new measurement with secondary phase data
                        selected_batch["measurements"].append({
                            "date": today.strftime("%Y-%m-%d"),
                            "temperature": temperature,
                            "carbonation_level": carbonation_level,
                            "bottle_firmness": bottle_firmness,
                            "co2_estimate": co2_produced,
                            "co2_pressure": co2_pressure,
                            "completion": completion_pct,
                            "phase": "secondary"
                        })
                        save_data()  # Save data to file
                        st.success("Secondary fermentation readings saved successfully!")

    with scol2:
        if selected_batch:
            # Add a container with styling
            with st.container():
                st.subheader("CO₂ Production Estimate")
                
                # Calculate CO2 production and completion percentage
                co2_produced = calculate_co2_production(
                    sugar_amount=selected_batch['sugar_content'],
                    days=days_bottled,
                    temperature=temperature,
                    volume=selected_batch['volume']
                )
                
                completion_pct = estimate_fermentation_completion(
                    sugar_amount=selected_batch['sugar_content'],
                    co2_produced=co2_produced
                )
                
                # Create a two-column layout for the metrics
                metric_col1, metric_col2 = st.columns(2)
                
                with metric_col1:
                    # Display CO₂ production estimate with icon
                    st.markdown("##### 🧪 CO₂ Produced")
                    st.metric(
                        "Amount",
                        f"{co2_produced:.2f} g",
                        delta=f"{completion_pct:.1f}% of potential"
                    )
                
                with metric_col2:
                    # Calculate CO₂ pressure
                    co2_pressure = estimate_co2(
                        sugar_content=selected_batch['sugar_content'],
                        temp=temperature,
                        time_in_days=days_bottled
                    )

                    # Get thresholds from settings
                    danger_threshold = st.session_state.settings['danger_threshold']
                    warning_threshold = st.session_state.settings['warning_threshold']

                    # Display CO₂ pressure estimate with warning levels and icon
                    st.markdown("##### 📊 CO₂ Pressure")
                    pressure_color = "normal"
                    if co2_pressure >= danger_threshold:
                        pressure_color = "off"
                        pressure_warning = f"⚠️ Danger! (>{danger_threshold} atm)"
                    elif co2_pressure >= warning_threshold:
                        pressure_color = "inverse"
                        pressure_warning = f"⚠️ High (>{warning_threshold} atm)"
                    else:
                        pressure_warning = f"✅ Safe (<{warning_threshold} atm)"

                    st.metric(
                        "Pressure",
                        f"{co2_pressure:.2f} atm",
                        delta=pressure_warning,
                        delta_color=pressure_color
                    )

                # Create a progress bar for fermentation completion with better styling
                st.markdown("---")
                st.markdown("### Fermentation Progress")
                
                # Add percentage text above progress bar
                st.markdown(f"<h4 style='text-align: center; color: {'green' if completion_pct < 70 else 'orange' if completion_pct < 90 else 'red'};'>{completion_pct:.1f}%</h4>", unsafe_allow_html=True)
                
                # Progress bar
                progress_color = "green" if completion_pct < 70 else "orange" if completion_pct < 90 else "red"
                st.progress(min(completion_pct / 100, 1.0))
                
                # Add interpretation text
                if completion_pct < 30:
                    st.info("🌱 Early fermentation stage - sweet with mild acidity")
                elif completion_pct < 70:
                    st.success("🍵 Mid fermentation stage - balanced sweetness and acidity")
                elif completion_pct < 90:
                    st.warning("🔶 Late fermentation stage - becoming more acidic")
                else:
                    st.error("🔴 Final fermentation stage - highly acidic, minimal sweetness")

                # Display pressure gauge visualization with improved styling
                st.markdown("---")
                st.markdown("### CO₂ Pressure Gauge")

                # Add disclaimer about pressure estimates
                st.info("""
                **Note on Accuracy**: This pressure estimate is based on a simplified model that doesn't account for all variables in real fermentation environments. Factors like microbial composition, oxygen levels, and previous fermentation history can all affect actual CO₂ production. Always use physical signs (bottle firmness, cap bulging) alongside these estimates.
                """)

                # Calculate gauge range and steps based on thresholds
                max_gauge_value = max(3.0, danger_threshold * 1.2)  # Set max to at least 20% above danger threshold

                # Create steps for the gauge
                gauge_steps = [
                    {"range": [0, warning_threshold], "color": "green"},
                    {"range": [warning_threshold, danger_threshold], "color": "yellow"},
                    {"range": [danger_threshold, max_gauge_value], "color": "red"},
                ]

                # Create the gauge chart
                pressure_gauge = {
                    "data": [
                        {
                            "type": "indicator",
                            "mode": "gauge+number",
                            "value": co2_pressure,
                            "title": {"text": "CO₂ Pressure (atm)"},
                            "gauge": {
                                "axis": {"range": [None, max_gauge_value]},
                                "steps": gauge_steps,
                                "threshold": {
                                    "line": {"color": "red", "width": 4},
                                    "thickness": 0.75,
                                    "value": danger_threshold
                                },
                                "bar": {"color": "darkblue"}
                            }
                        }
                    ],
                    "layout": {
                        "height": 300,
                        "margin": {"t": 25, "r": 25, "l": 25, "b": 25}
                    }
                }
                
                st.plotly_chart(pressure_gauge, use_container_width=True)

                # Remove pH level interpretation section since we don't collect pH in secondary fermentation
                # Instead, add carbonation level interpretation
                st.markdown("### Carbonation Level Interpretation")
                if carbonation_level == "Flat":
                    st.warning("No carbonation detected. Fermentation may be slow or sugar may be depleted.")
                elif carbonation_level == "Slightly Fizzy":
                    st.info("Carbonation is beginning to develop. Continue monitoring.")
                elif carbonation_level == "Moderately Carbonated":
                    st.success("Good carbonation level. May be ready for refrigeration soon.")
                elif carbonation_level == "Well Carbonated":
                    st.success("Excellent carbonation level. Consider refrigerating to slow fermentation.")
                elif carbonation_level == "Highly Carbonated":
                    st.warning("Very high carbonation. Refrigerate immediately and release pressure carefully.")

                # Display temperature interpretation
                st.markdown("### Temperature Interpretation")
                if temperature < 20:
                    st.warning("Temperature is low. Carbonation will develop more slowly.")
                elif temperature < 24:
                    st.info("Temperature is in a good range, but slightly cool.")
                elif temperature <= 29:
                    st.success("Temperature is in the ideal range for developing carbonation.")
                else:
                    st.warning("Temperature is high. Carbonation may develop quickly, increasing explosion risk.")

                # Show CO₂ production over time if measurements exist
                if "measurements" in selected_batch and selected_batch["measurements"]:
                    st.markdown("---")
                    st.subheader("📈 Measurement History")

                    # Create a dataframe from measurements
                    measurements_df = pd.DataFrame(selected_batch["measurements"])
                    measurements_df["date"] = pd.to_datetime(measurements_df["date"])

                    # Create tabs for different charts with custom styling
                    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 CO₂ Production", "📈 CO₂ Pressure", "🔍 Data Table"])

                    with chart_tab1:
                        # Create a line chart of CO₂ production over time with improved styling
                        fig1 = px.line(
                            measurements_df,
                            x="date",
                            y="co2_estimate",
                            title="CO₂ Production Over Time",
                            labels={"date": "Date", "co2_estimate": "CO₂ (g)"},
                            markers=True
                        )
                        
                        # Customize the chart appearance
                        fig1.update_traces(line=dict(width=3), marker=dict(size=8))
                        fig1.update_layout(
                            plot_bgcolor="rgba(240, 242, 246, 0.8)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=12),
                            height=400
                        )

                        st.plotly_chart(fig1, use_container_width=True)

                    with chart_tab2:
                        # Create a line chart of CO₂ pressure over time with improved styling
                        fig2 = px.line(
                            measurements_df,
                            x="date",
                            y="co2_pressure",
                            title="CO₂ Pressure Over Time",
                            labels={"date": "Date", "co2_pressure": "Pressure (atm)"},
                            markers=True
                        )
                        
                        # Customize the chart appearance
                        fig2.update_traces(line=dict(width=3, color="#2E86C1"), marker=dict(size=8))
                        fig2.update_layout(
                            plot_bgcolor="rgba(240, 242, 246, 0.8)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(size=12),
                            height=400
                        )

                        # Get thresholds from settings
                        danger_threshold = st.session_state.settings['danger_threshold']
                        warning_threshold = st.session_state.settings['warning_threshold']

                        # Add danger threshold line
                        fig2.add_hline(
                            y=danger_threshold,
                            line_dash="dash",
                            line_color="red",
                            line_width=2,
                            annotation_text=f"Danger Level ({danger_threshold} atm)",
                            annotation_font=dict(color="red")
                        )

                        # Add warning threshold line
                        fig2.add_hline(
                            y=warning_threshold,
                            line_dash="dot",
                            line_color="orange",
                            line_width=2,
                            annotation_text=f"Warning Level ({warning_threshold} atm)",
                            annotation_font=dict(color="orange")
                        )

                        st.plotly_chart(fig2, use_container_width=True)

                    with chart_tab3:
                        # Display the measurements table with improved styling
                        st.dataframe(
                            measurements_df,
                            column_config={
                                "date": "Date",
                                "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.1f °C"),
                                "ph": st.column_config.NumberColumn("pH", format="%.1f"),
                                "co2_estimate": st.column_config.NumberColumn("CO₂ (g)", format="%.2f g"),
                                "co2_pressure": st.column_config.NumberColumn("Pressure (atm)", format="%.2f atm"),
                                "completion": st.column_config.ProgressColumn("Completion", format="%.1f%%", min_value=0, max_value=100)
                            },
                            hide_index=True,
                            use_container_width=True
                        )

                        # Add export button for this specific batch's measurements
                        if st.button("Export This Batch's Data to CSV", key="export_secondary_batch_data"):
                            # Create a comprehensive dataframe with batch info and measurements
                            export_data = []

                            # Basic batch info
                            batch_info = {
                                "batch_name": selected_batch["name"],
                                "tea_type": selected_batch["tea_type"],
                                "sugar_content": selected_batch["sugar_content"],
                                "start_date": selected_batch["start_date"],
                                "volume": selected_batch["volume"],
                                "notes": selected_batch.get("notes", "")
                            }

                            # Add each measurement as a row
                            for measurement in selected_batch["measurements"]:
                                # Combine batch info with measurement data
                                measurement_row = batch_info.copy()
                                measurement_row.update({
                                    "measurement_date": measurement["date"],
                                    "temperature": measurement["temperature"],
                                    "ph": measurement["ph"],
                                    "co2_estimate": measurement["co2_estimate"],
                                    "co2_pressure": measurement.get("co2_pressure", "N/A"),
                                    "completion": measurement.get("completion", "N/A")
                                })
                                export_data.append(measurement_row)

                            # Create dataframe from the collected data
                            export_df = pd.DataFrame(export_data)

                            # Convert dataframe to CSV
                            csv = export_df.to_csv(index=False)

                            # Create a download button
                            st.download_button(
                                label=f"Download {selected_batch['name']} Data",
                                data=csv,
                                file_name=f"kombucha_{selected_batch['name'].replace(' ', '_').lower()}_data.csv",
                                mime="text/csv",
                                help=f"Click to download {selected_batch['name']} data as a CSV file"
                            )

            # Show a prediction of CO₂ production for the next week
            st.subheader("CO₂ Production Prediction")

            # Add model limitations disclaimer
            st.warning("""
            **Model Limitations**: Predictions become less accurate the further into the future they extend. Environmental changes, temperature fluctuations, and microbial activity variations can all cause actual results to differ from predictions. Use these projections as a general guide rather than exact forecasts.
            """)

            # Generate prediction data
            prediction_days = list(range(days_bottled, days_bottled + 8))
            prediction_co2 = [
                calculate_co2_production(
                    sugar_amount=selected_batch['sugar_content'],
                    days=day,
                    temperature=temperature,
                    volume=selected_batch['volume']
                )
                for day in prediction_days
            ]

            # Create a dataframe for the prediction
            prediction_df = pd.DataFrame({
                "day": prediction_days,
                "co2": prediction_co2
            })

            # Create a line chart of the prediction
            fig = px.line(
                prediction_df,
                x="day",
                y="co2",
                title="Predicted CO₂ Production",
                labels={"day": "Fermentation Day", "co2": "CO₂ (g)"}
            )

            # Add a vertical line at the current day
            fig.add_vline(
                x=days_bottled,
                line_dash="dash",
                line_color="red",
                annotation_text="Today"
            )

            st.plotly_chart(fig, use_container_width=True)

elif st.session_state.active_tab == "comparison":
    st.header("Batch Comparison")
    st.markdown("""
    ### 📊 Compare different batches side by side
    
    This tool helps you analyze and compare multiple batches to identify patterns and improve your brewing process.
    """)
    
    # Select batches to compare
    st.subheader("Select Batches to Compare")
    
    if len(st.session_state.batches) < 2:
        st.warning("You need at least 2 batches to make a comparison. Please create more batches.")
    else:
        # Get all batch names
        batch_names = [batch["name"] for batch in st.session_state.batches]
        
        # Multi-select for batches
        selected_batch_names = st.multiselect(
            "Select batches to compare",
            options=batch_names,
            default=batch_names[:2] if len(batch_names) >= 2 else [batch_names[0]]
        )
        
        if len(selected_batch_names) < 2:
            st.warning("Please select at least 2 batches to compare.")
        else:
            # Get the selected batch objects
            selected_batches = [batch for batch in st.session_state.batches if batch["name"] in selected_batch_names]
            
            # Create comparison dataframe
            comparison_data = []
            for batch in selected_batches:
                # Basic batch info
                batch_info = {
                    "Batch Name": batch["name"],
                    "Tea Type": batch["tea_type"],
                    "Sugar Content (g)": batch["sugar_content"],
                    "Volume (L)": batch["volume"],
                    "Start Date": batch["start_date"],
                    "Phase": batch["fermentation_phase"].capitalize(),
                    "SCOBY Source": batch.get("scoby_source", "Unknown")
                }
                
                # Add to comparison data
                comparison_data.append(batch_info)
            
            # Create dataframe
            comparison_df = pd.DataFrame(comparison_data)
            
            # Display comparison table
            st.subheader("Basic Batch Comparison")
            st.dataframe(comparison_df, use_container_width=True)
            
            # Visualization options
            st.subheader("Visualization")
            
            viz_type = st.selectbox(
                "Select visualization type",
                options=["pH Over Time", "Temperature Over Time", "CO₂ Production", "Fermentation Completion"],
                key="comparison_viz_type"
            )
            
            # Create visualization based on selection
            if viz_type:
                # Prepare data for plotting
                plot_data = []
                
                for batch in selected_batches:
                    if "measurements" in batch and batch["measurements"]:
                        for measurement in batch["measurements"]:
                            # Skip if this is a secondary measurement and we're looking at pH
                            if measurement.get("phase") == "secondary" and viz_type == "pH Over Time":
                                continue
                                
                            # Create a row for this measurement
                            measurement_data = {
                                "Batch Name": batch["name"],
                                "Date": pd.to_datetime(measurement["date"]),
                                "Days": (pd.to_datetime(measurement["date"]) - pd.to_datetime(batch["start_date"])).days
                            }
                            
                            # Add the specific metric we're visualizing
                            if viz_type == "pH Over Time" and "ph" in measurement:
                                measurement_data["Value"] = measurement["ph"]
                                measurement_data["Metric"] = "pH"
                            elif viz_type == "Temperature Over Time" and "temperature" in measurement:
                                measurement_data["Value"] = measurement["temperature"]
                                measurement_data["Metric"] = "Temperature (°C)"
                            elif viz_type == "CO₂ Production" and "co2_estimate" in measurement:
                                measurement_data["Value"] = measurement["co2_estimate"]
                                measurement_data["Metric"] = "CO₂ (g)"
                            elif viz_type == "Fermentation Completion" and "completion" in measurement:
                                measurement_data["Value"] = measurement["completion"]
                                measurement_data["Metric"] = "Completion (%)"
                            
                            # Add to plot data if we have a value
                            if "Value" in measurement_data:
                                plot_data.append(measurement_data)
                
                # Create dataframe for plotting
                if plot_data:
                    plot_df = pd.DataFrame(plot_data)
                    
                    # Create plot
                    fig = px.line(
                        plot_df, 
                        x="Days", 
                        y="Value", 
                        color="Batch Name",
                        title=f"{viz_type} Comparison",
                        labels={"Value": plot_df["Metric"].iloc[0] if not plot_df.empty else "Value"}
                    )
                    
                    # Customize plot
                    fig.update_layout(
                        xaxis_title="Days Since Start",
                        legend_title="Batch",
                        height=500
                    )
                    
                    # Display plot
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"No data available for {viz_type} comparison. Make sure you have recorded measurements for the selected batches.")
            
            # Export comparison data
            st.subheader("Export Comparison")
            
            if st.button("Export Comparison Data to CSV", key="export_comparison_button"):
                # Create a comprehensive dataframe with all batch data
                export_data = []
                
                for batch in selected_batches:
                    # Basic batch info
                    batch_info = {
                        "batch_name": batch["name"],
                        "tea_type": batch["tea_type"],
                        "sugar_content": batch["sugar_content"],
                        "start_date": batch["start_date"],
                        "volume": batch["volume"],
                        "notes": batch.get("notes", "")
                    }
                    
                    # If there are measurements, add each as a row
                    if "measurements" in batch and batch["measurements"]:
                        for measurement in batch["measurements"]:
                            # Combine batch info with measurement data
                            measurement_row = batch_info.copy()
                            measurement_row.update({
                                "measurement_date": measurement["date"],
                                "temperature": measurement.get("temperature", "N/A"),
                                "ph": measurement.get("ph", "N/A"),
                                "co2_estimate": measurement.get("co2_estimate", "N/A"),
                                "co2_pressure": measurement.get("co2_pressure", "N/A"),
                                "completion": measurement.get("completion", "N/A"),
                                "phase": measurement.get("phase", "primary")
                            })
                            export_data.append(measurement_row)
                    else:
                        # If no measurements, just add the batch info
                        batch_info.update({
                            "measurement_date": "N/A",
                            "temperature": "N/A",
                            "ph": "N/A",
                            "co2_estimate": "N/A",
                            "co2_pressure": "N/A",
                            "completion": "N/A",
                            "phase": "N/A"
                        })
                        export_data.append(batch_info)
                
                # Create dataframe from the collected data
                export_df = pd.DataFrame(export_data)
                
                # Convert dataframe to CSV
                csv = export_df.to_csv(index=False)
                
                # Create a download button
                st.download_button(
                    label="Download Comparison CSV",
                    data=csv,
                    file_name="kombucha_batch_comparison.csv",
                    mime="text/csv",
                    help="Click to download comparison data as a CSV file",
                    key="download_comparison_button"
                )

# Clear data button at the bottom of the page with confirmation
if st.session_state.batches:
    st.markdown("---")
    st.subheader("Data Management")
    
    # Initialize confirmation state if it doesn't exist
    if 'confirm_clear_all' not in st.session_state:
        st.session_state.confirm_clear_all = False
    
    # First stage - show the clear data button
    if not st.session_state.confirm_clear_all:
        if st.button("Clear All Batch Data", type="primary", key="clear_all_data_button"):
            st.session_state.confirm_clear_all = True
    # Second stage - show confirmation
    else:
        st.warning("⚠️ **WARNING**: This will permanently delete ALL batch data. This action cannot be undone!")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Yes, Delete Everything", type="primary", key="confirm_clear_yes"):
                st.session_state.batches = []
                save_data()  # Save data to file
                st.session_state.confirm_clear_all = False
                st.success("All batch data has been cleared.")
                st.rerun()
        
        with col2:
            if st.button("Cancel", key="confirm_clear_cancel"):
                st.session_state.confirm_clear_all = False
                st.rerun()

# Footer
st.markdown("---")
st.markdown("© 2025 Kombucha Batch Logger | Made with Streamlit | deen.htc@gmail.com")





































































