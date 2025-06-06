import streamlit as st
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Automated A/B Testing Tool",
    layout="wide", # Use wide layout for better space utilization
    initial_sidebar_state="expanded" # Keep sidebar expanded by default
)

# --- Main Content Area ---
st.title("Automated A/B Testing Tool")
st.markdown("""
Welcome to your automated A/B testing platform!
Use the sidebar on the left to upload your experiment data and configure your test.
""")

# Initialize session state for DataFrame if not already present
if 'df' not in st.session_state:
    st.session_state['df'] = None

# --- Sidebar for User Inputs ---
st.sidebar.header("Configure Your A/B Test")

# 1. File Uploader in Sidebar
st.sidebar.subheader("1. Upload Your Data")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state['df'] = df # Store DataFrame in session state
        st.sidebar.success("File uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
        st.session_state['df'] = None # Reset df if error
        st.sidebar.write("Please ensure your file is a valid CSV format.")
else:
    st.sidebar.info("Awaiting CSV file upload.")

# Proceed with other inputs only if a DataFrame is available
if st.session_state['df'] is not None:
    st.sidebar.markdown("---")

    # 2. Experiment Naming
    st.sidebar.subheader("2. Experiment Details")
    experiment_name = st.sidebar.text_input(
        "Name your Experiment",
        value=st.session_state.get('experiment_name', 'My A/B Test') # Remember previous input
    )
    st.session_state['experiment_name'] = experiment_name # Store in session state

    # Get columns from the uploaded DataFrame
    all_columns = st.session_state['df'].columns.tolist()
    if not all_columns: # Handle case with empty DataFrame (unlikely but good for robustness)
        all_columns = ["No columns found"]

    # 3. Choose Columns for Test (Variant and Metric)
    st.sidebar.subheader("3. Select Test Columns")
    # Using 'st.columns' in sidebar for a slightly nicer layout if desired, otherwise st.selectbox works fine.
    col1, col2 = st.sidebar.columns(2)

    with col1:
        variant_column = st.selectbox(
            "Select Variant Column (e.g., 'group', 'control_treatment')",
            options=all_columns,
            key='variant_col_select' # Unique key for this widget
        )
        st.session_state['variant_column'] = variant_column

    with col2:
        metric_column = st.selectbox(
            "Select Metric Column (e.g., 'conversion', 'revenue')",
            options=all_columns,
            key='metric_col_select' # Unique key for this widget
        )
        st.session_state['metric_column'] = metric_column

    # 4. Choose Metric Type (Discrete or Continuous)
    st.sidebar.subheader("4. Metric Type")
    metric_type = st.sidebar.radio(
        "Is your metric discrete (e.g., conversions, clicks) or continuous (e.g., revenue, time)?",
        ('Discrete', 'Continuous'),
        key='metric_type_radio'
    )
    st.session_state['metric_type'] = metric_type

    # 5. Choose Sample Size (or indicate current observed sample size)
    st.sidebar.subheader("5. Sample Size (Optional for Planning)")
    st.sidebar.write("If you are planning an experiment, enter your target sample size. If analyzing completed data, this will be automatically derived.")
    # For now, let's allow an optional input. We'll derive it later from data.
    target_sample_size = st.sidebar.number_input(
        "Target Sample Size per group",
        min_value=10, # Minimum reasonable sample size
        value=st.session_state.get('target_sample_size', 1000), # Default value
        step=100,
        key='sample_size_input'
    )
    st.session_state['target_sample_size'] = target_sample_size

    st.sidebar.markdown("---")
    st.sidebar.write("Ready to analyze? Click the button below!")
    run_analysis_button = st.sidebar.button("Run Analysis", type="primary")

    # --- Main Content: Display Data Preview ---
    st.subheader("Data Preview")
    st.write("Here's the first few rows of your uploaded data:")
    st.dataframe(st.session_state['df'].head())

    st.subheader("Selected Columns & Metric Type")
    st.write(f"**Experiment Name:** {experiment_name}")
    st.write(f"**Variant Column:** `{variant_column}`")
    st.write(f"**Metric Column:** `{metric_column}`")
    st.write(f"**Metric Type:** `{metric_type}`")
    st.write(f"**Target Sample Size (per group):** `{target_sample_size}`")

    st.markdown("---")
    if run_analysis_button:
        st.success("Analysis triggered! (Logic to be added in the next step)")
        # This is where we'll call your A/B test analysis functions
        # For now, just a placeholder.
        # Your analysis logic will use:
        # st.session_state['df']
        # st.session_state['variant_column']
        # st.session_state['metric_column']
        # st.session_state['metric_type']
        # and potentially st.session_state['target_sample_size'] for sample size check/power analysis
        # etc.
else:
    st.info("Please upload a CSV file in the sidebar to configure your A/B test.")
    st.markdown("---")
    st.write("### Next Steps:")
    st.write("Upload your data using the file uploader in the sidebar. Once uploaded, new options will appear to configure your A/B test.")
