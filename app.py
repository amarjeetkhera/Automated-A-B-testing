import streamlit as st
import pandas as pd
from discrete_tests import perform_discrete_ab_test
from continuous_tests import perform_continuous_ab_test

# --- Page Configuration ---
st.set_page_config(
    page_title="Automated A/B Testing Tool",
    layout="wide", # Use wide layout for better space utilization
    initial_sidebar_state="expanded" # Keep sidebar expanded by default
)

# --- Main Content Area ---
st.title("Automated A/B Testing")
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
    if not all_columns: # Handle case with empty DataFrame
        all_columns = ["No columns found"]

    # 3. Choose Columns for Test (Variant and Metric)
    st.sidebar.subheader("3. Select Test Columns")
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

    # --- Analysis Results Section ---
    if run_analysis_button:
        st.header("A/B Test Analysis Results")

        if st.session_state['df'] is None:
            st.error("Please upload data before running analysis.")
        elif variant_column not in st.session_state['df'].columns or metric_column not in st.session_state['df'].columns:
            st.error("Selected variant or metric column not found in the uploaded data. Please check your selections.")
        else:
            st.info(f"Running analysis for Experiment: **{experiment_name}**")

            # --- Discrete Test Handling ---
            if metric_type == 'Discrete':
                results = perform_discrete_ab_test(
                    st.session_state['df'].copy(), # Pass a copy to avoid modifying original df in session state
                    variant_column,
                    metric_column
                )

                if results["status"] == "error":
                    st.error(results["error_message"])
                else:
                    st.subheader("Results for Discrete Metric Test")

                    st.write("### Contingency Table:")
                    st.dataframe(results["contingency_table"])

                    st.write("### Expected Frequencies:")
                    st.dataframe(results["expected_frequencies"].round(2))

                    st.write(f"Percentage of cells with expected frequency < 5: `{results['percentage_small_expected']:.2f}%`")
                    st.write("---")

                    if results["observed_rates_df"] is not None:
                        st.write("### Observed Metric Rates (% with 95% CI):")
                        st.dataframe(results["observed_rates_df"].round(2))
                        st.write("### Visualizing Conversion Rates:")
                        st.plotly_chart(results["plot_figure"], use_container_width=True)
                    else:
                        st.warning("Could not determine success column for observed rates and plotting.")

                    st.write("---")
                    st.write(f"### Test Method: {results['test_method']}")

                    if results["chi2_statistic"] is not None:
                        st.write(f"Chi-squared statistic: `{results['chi2_statistic']:.3f}`")
                        st.write(f"Degrees of freedom (dof): `{results['dof']}`")

                    if results["odds_ratio"] is not None:
                        st.write(f"Odds Ratio: `{results['odds_ratio']:.3f}`")

                    st.write(f"P-value: `{results['p_value']:.5f}`")

                    if results["conclusion"] == "statistically significant":
                        st.success(f"Conclusion: The difference between variants is **{results['conclusion']}** (p < 0.05).")
                        st.markdown(results["interpretation"])
                    else:
                        st.info(f"Conclusion: The difference between variants is **{results['conclusion']}** (p >= 0.05).")
                        st.markdown(results["interpretation"])

                    if results["raw_conversion_rates"] is not None:
                        st.write("### Observed Metric Rates (%):")
                        st.dataframe(results["raw_conversion_rates"].rename('Rate (%)'))
                    else:
                        st.warning("Could not determine success column for observed rates.")

            # --- Continuous Test Handling ---
            elif metric_type == 'Continuous':
                results = perform_continuous_ab_test(
                    st.session_state['df'].copy(),
                    variant_column,
                    metric_column
                )

                if results["status"] == "error":
                    st.error(results["error_message"])
                else:
                    st.subheader("Results for Continuous Metric Test")

                    st.write("### Group Statistics:")
                    # Display group_stats nicely from the dictionary
                    for variant, stats_data in results["group_stats"].items():
                        st.write(f"**Group '{variant}' (N={stats_data['N']}):** Mean = `{stats_data['Mean']:.3f}`, Std Dev = `{stats_data['Std Dev']:.3f}`")

                    st.write("### Visualizing Metric Distribution:")
                    st.plotly_chart(results["plot_figure"], use_container_width=True)
                    st.write("---")

                    st.write("### Assumption Checks:")
                    if not results["is_large_sample"]:
                        # Assuming variants[0] and variants[1] are accessible or passed from the main df in app.py
                        # Let's get them from the original df to ensure they match
                        variants = st.session_state['df'][variant_column].dropna().unique()
                        if len(variants) >= 2:
                            st.write(f"Normality Test (Shapiro-Wilk for '{variants[0]}'): p={results['shapiro_a_p']:.3f} ({'Appears Normal' if results['is_normal_a'] else 'Not Normal'})")
                            st.write(f"Normality Test (Shapiro-Wilk for '{variants[1]}'): p={results['shapiro_b_p']:.3f} ({'Appears Normal' if results['is_normal_b'] else 'Not Normal'})")
                    else:
                        st.info("Sample size is large (N >= 30 per group), so t-test robustness relies on the Central Limit Theorem. Normality assumption is less critical.")

                    st.write(f"Homogeneity of Variances Test (Levene's): p={results['levene_p']:.3f} ({'Variances Appear Similar' if results['variances_similar'] else 'Variances Appear Dissimilar'})")
                    st.write("---")

                    st.write(f"### Test Method: {results['test_method']}")
                    if results["statistic"] is not None:
                        st.write(f"Statistic: `{results['statistic']:.3f}`")

                    if results["p_value"] is not None:
                        st.write(f"P-value: `{results['p_value']:.5f}`")
                        if results["conclusion"] == "statistically significant":
                            st.success(f"Conclusion: The difference in means between variants is **{results['conclusion']}** (p < 0.05).")
                            st.markdown(results["interpretation"])
                        else:
                            st.info(f"Conclusion: The difference in means between variants is **{results['conclusion']}** (p >= 0.05).")
                            st.markdown(results["interpretation"])
                    else:
                        st.error("Could not determine test conclusion.")
            else:
                st.error("Unknown metric type selected.")
else:
    st.info("Please upload a CSV file in the sidebar to configure your A/B test.")
    st.markdown("---")
    st.write("### Next Steps:")
    st.write("Upload your data using the file uploader in the sidebar. Once uploaded, new options will appear to configure your A/B test.")
