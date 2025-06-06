import streamlit as st
import pandas as pd
from scipy import stats
import numpy as np

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

# --- Functions for Statistical Tests ---

def perform_discrete_ab_test(df, variant_col, metric_col):
    """
    Performs A/B test for discrete metrics.
    Decides between Chi-squared and Fisher's exact test based on expected counts.
    Assumes metric_col contains binary outcomes.
    """
    st.subheader("Results for Discrete Metric Test")

    # Ensure metric column is numerical (0/1) for counting
    # Attempt to convert to numeric, coercing errors to NaN
    df[metric_col] = pd.to_numeric(df[metric_col], errors='coerce')
    # Drop rows where metric is not a valid number
    df_cleaned = df.dropna(subset=[metric_col])

    if df_cleaned[metric_col].nunique() > 2:
        st.error(f"The selected discrete metric column '{metric_col}' contains more than two unique values. "
                 "Please ensure it's a binary outcome (e.g., 0/1 for success/failure).")
        return

    # Create a contingency table
    # Rows: Variants (Control, Treatment/Variant A, B, etc.)
    # Columns: Metric outcome (e.g., Not Converted (0), Converted (1))
    contingency_table = pd.crosstab(df_cleaned[variant_col], df_cleaned[metric_col])

    if contingency_table.empty:
        st.error("Could not create a contingency table. Check your variant and metric columns.")
        return

    st.write("### Contingency Table:")
    st.dataframe(contingency_table)

    # Calculate expected frequencies
    chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
    expected_df = pd.DataFrame(expected, index=contingency_table.index, columns=contingency_table.columns)

    st.write("### Expected Frequencies:")
    st.dataframe(expected_df.round(2)) # Round for display

    # Check assumptions for Chi-squared test
    # Rule of thumb: no more than 20% of expected cell counts are less than 5, and none less than 1.
    small_expected_cells = (expected < 5).sum()
    total_cells = expected.size
    percentage_small_expected = (small_expected_cells / total_cells) * 100

    st.write(f"Percentage of cells with expected frequency < 5: `{percentage_small_expected:.2f}%`")

    if percentage_small_expected <= 20 and np.all(expected >= 1):
        # Use Pearson's Chi-squared test
        st.write("---")
        st.write("### Test Method: Pearson's Chi-squared Test")
        st.write(f"Chi-squared statistic: `{chi2:.3f}`")
        st.write(f"Degrees of freedom (dof): `{dof}`")

        # Interpretation of p-value
        st.write(f"P-value: `{p_val:.5f}`")
        if p_val < 0.05: # Common significance level
            st.success("Conclusion: The difference between variants is **statistically significant** (p < 0.05).")
            st.markdown(f"This suggests that the **'{variant_col}'** has a significant effect on the **'{metric_col}'**.")
        else:
            st.info("Conclusion: The difference between variants is **not statistically significant** (p >= 0.05).")
            st.markdown("We do not have enough evidence to claim a significant difference in outcomes between the variants.")

        # Display actual rates
        total_counts = contingency_table.sum(axis=1)
        metric_success_index = 1 if 1 in contingency_table.columns else (0 if 0 in contingency_table.columns else None) # Assuming 1 is success
        if metric_success_index is not None and metric_success_index in contingency_table.columns:
            conversion_rates = (contingency_table[metric_success_index] / total_counts) * 100
            st.write("### Observed Metric Rates (%):")
            st.dataframe(conversion_rates.rename('Rate (%)'))
        else:
            st.warning("Could not determine success column for observed rates.")


    else:
        # Use Fisher's exact test
        st.write("---")
        st.write("### Test Method: Fisher's Exact Test (due to small expected cell counts)")
        # Fisher's exact test for 2x2 table
        if contingency_table.shape == (2, 2):
            odds_ratio, p_val = stats.fisher_exact(contingency_table)
            st.write(f"P-value: `{p_val:.5f}`")
            st.write(f"Odds Ratio: `{odds_ratio:.3f}`")
            if p_val < 0.05:
                st.success("Conclusion: The difference between variants is **statistically significant** (p < 0.05).")
                st.markdown(f"This suggests that the **'{variant_col}'** has a significant effect on the **'{metric_col}'**.")
            else:
                st.info("Conclusion: The difference between variants is **not statistically significant** (p >= 0.05).")
                st.markdown("We do not have enough evidence to claim a significant difference in outcomes between the variants.")
        else:
            st.error("Fisher's Exact Test is primarily for 2x2 tables when assumptions for Chi-squared are violated. Your contingency table is not 2x2.")
            st.warning("Consider aggregating your variants or checking your data if you expected a 2x2 table.")

        # Display actual rates (similar to Chi-squared)
        total_counts = contingency_table.sum(axis=1)
        metric_success_index = 1 if 1 in contingency_table.columns else (0 if 0 in contingency_table.columns else None) # Assuming 1 is success
        if metric_success_index is not None and metric_success_index in contingency_table.columns:
            conversion_rates = (contingency_table[metric_success_index] / total_counts) * 100
            st.write("### Observed Metric Rates (%):")
            st.dataframe(conversion_rates.rename('Rate (%)'))
        else:
            st.warning("Could not determine success column for observed rates.")

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

    st.markdown("---")
    if run_analysis_button:
         st.header("A/B Test Analysis Results")

         if st.session_state['df'] is None:
             st.error("Please upload data before running analysis.")
         elif variant_column not in st.session_state['df'].columns or metric_column not in st.session_state['df'].columns:
             st.error("Selected variant or metric column not found in the uploaded data. Please check your selections.")
         else:
             st.info(f"Running analysis for Experiment: **{experiment_name}**")

             if metric_type == 'Discrete':
                 perform_discrete_ab_test(
                     st.session_state['df'].copy(), # Pass a copy to avoid modifying original df in session state
                     variant_column,
                     metric_column
                )
             elif metric_type == 'Continuous':
                 st.warning("Continuous metric analysis logic is not yet implemented. Please select 'Discrete' for now.")
                 # We'll implement this in the next step!
             else:
                 st.error("Unknown metric type selected.")
else:
    st.info("Please upload a CSV file in the sidebar to configure your A/B test.")
    st.markdown("---")
    st.write("### Next Steps:")
    st.write("Upload your data using the file uploader in the sidebar. Once uploaded, new options will appear to configure your A/B test.")
