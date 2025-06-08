import streamlit as st
import pandas as pd
from scipy import stats
import numpy as np
import plotly.express as px
import statsmodels.api as sm

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

    st.write("---")
    # --- Calculate Conversion Rates and Confidence Intervals for Plotting ---
    total_counts = contingency_table.sum(axis=1)
    metric_success_index = 1 if 1 in contingency_table.columns else (0 if 0 in contingency_table.columns else None)

    if metric_success_index is not None and metric_success_index in contingency_table.columns:
        success_counts = contingency_table[metric_success_index]
        conversion_rates = (success_counts / total_counts)

        # Create a DataFrame for plotting
        plot_df = pd.DataFrame({
            variant_col: total_counts.index,
            'Successes': success_counts,
            'Trials': total_counts,
            'Conversion_Rate': conversion_rates * 100 # Convert to percentage for display
        })

        # Calculate confidence intervals
        alpha = 0.05 # For 95% confidence interval
        conf_int_lower = []
        conf_int_upper = []
        for i in range(len(plot_df)):
            count = plot_df['Successes'].iloc[i]
            nobs = plot_df['Trials'].iloc[i]
            # Use normal approximation for confidence interval for proportions
            # For very small N, other methods (e.g., Agresti-Coull) might be better, but normal is standard for larger N
            ci_low, ci_upp = sm.stats.proportion_confint(count, nobs, alpha=alpha, method='normal')
            conf_int_lower.append(ci_low * 100) # Convert to percentage
            conf_int_upper.append(ci_upp * 100) # Convert to percentage

        plot_df['CI_Lower'] = conf_int_lower
        plot_df['CI_Upper'] = conf_int_upper

        st.write("### Observed Metric Rates (% with 95% CI):")
        st.dataframe(plot_df[[variant_col, 'Conversion_Rate', 'CI_Lower', 'CI_Upper']].round(2))

        # --- NEW: Bar Chart for Discrete Metric ---
        st.write("### Visualizing Conversion Rates:")
        fig_discrete = px.bar(
            plot_df,
            x=variant_col,
            y='Conversion_Rate',
            error_y='CI_Upper', # Upper bound for error bar
            error_y_minus='CI_Lower', # Lower bound for error bar (since error_y takes absolute value, we give lower as negative)
            labels={'Conversion_Rate': f'Conversion Rate (%)'},
            title=f'Conversion Rate by {variant_col} (with 95% Confidence Intervals)',
            height=400
        )
        # Manually adjust error bar values based on CI bounds
        # Plotly's error_y expects the *difference* from y, so we adjust
        fig_discrete.data[0].error_y.array = plot_df['CI_Upper'] - plot_df['Conversion_Rate']
        fig_discrete.data[0].error_y.arrayminus = plot_df['Conversion_Rate'] - plot_df['CI_Lower']

        st.plotly_chart(fig_discrete, use_container_width=True)

    else:
        st.warning("Could not determine success column for observed rates and plotting.")

    # --- Statistical Test Output ---
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

def perform_continuous_ab_test(df, variant_col, metric_col):
    """
    Performs A/B test for continuous metrics (e.g., revenue, time).
    Decides between Student's t-test, Welch's t-test, and Mann-Whitney U test.
    """
    st.subheader("Results for Continuous Metric Test")

    df[metric_col] = pd.to_numeric(df[metric_col], errors='coerce')
    df_cleaned = df.dropna(subset=[metric_col])

    if df_cleaned[metric_col].nunique() < 2:
        st.error(f"The selected metric column '{metric_col}' does not have enough unique values for continuous analysis.")
        return

    # Get unique variants
    variants = df_cleaned[variant_col].unique()
    if len(variants) != 2:
        st.error(f"Expected exactly two variants in column '{variant_col}' for A/B test. Found: {len(variants)}.")
        st.write("Please ensure your variant column only contains two distinct groups (e.g., 'control' and 'treatment').")
        return

    group_a = df_cleaned[df_cleaned[variant_col] == variants[0]][metric_col]
    group_b = df_cleaned[df_cleaned[variant_col] == variants[1]][metric_col]

    st.write(f"**Group '{variants[0]}' (N={len(group_a)}):** Mean = `{group_a.mean():.3f}`, Std Dev = `{group_a.std():.3f}`")
    st.write(f"**Group '{variants[1]}' (N={len(group_b)}):** Mean = `{group_b.mean():.3f}`, Std Dev = `{group_b.std():.3f}`")

    # --- Box Plot for Continuous Metric ---
    st.write("### Visualizing Metric Distribution:")
    fig_continuous = px.box(
        df_cleaned,
        x=variant_col,
        y=metric_col,
        points="all", # Show individual data points
        labels={metric_col: f'{metric_col.replace("_", " ").title()}'},
        title=f'Distribution of {metric_col.replace("_", " ").title()} by {variant_col}',
        height=450
    )
    st.plotly_chart(fig_continuous, use_container_width=True)
    st.write("---")

    # --- Check for Normality (especially for smaller samples) ---
    # Rule of thumb for "large sample": > 30 per group to rely on CLT for t-test
    is_large_sample = len(group_a) >= 30 and len(group_b) >= 30

    # Shapiro-Wilk Test for normality (null hypothesis: data is normal)
    # p-value > 0.05 indicates failure to reject normality (i.e., appears normal)
    shapiro_a_stat, shapiro_a_p = stats.shapiro(group_a)
    shapiro_b_stat, shapiro_b_p = stats.shapiro(group_b)

    is_normal_a = shapiro_a_p > 0.05
    is_normal_b = shapiro_b_p > 0.05

    st.write("---")
    st.write("### Assumption Checks:")
    if not is_large_sample: # Only show explicit normality tests for smaller samples
        st.write(f"Normality Test (Shapiro-Wilk for '{variants[0]}'): p={shapiro_a_p:.3f} ({'Appears Normal' if is_normal_a else 'Not Normal'})")
        st.write(f"Normality Test (Shapiro-Wilk for '{variants[1]}'): p={shapiro_b_p:.3f} ({'Appears Normal' if is_normal_b else 'Not Normal'})")
    else:
        st.info("Sample size is large (N >= 30 per group), so t-test robustness relies on the Central Limit Theorem. Normality assumption is less critical.")

    # Levene's Test for Homogeneity of Variances (null hypothesis: variances are equal)
    # p-value > 0.05 indicates failure to reject equal variances
    levene_stat, levene_p = stats.levene(group_a, group_b)
    st.write(f"Homogeneity of Variances Test (Levene's): p={levene_p:.3f} ({'Variances Appear Similar' if levene_p > 0.05 else 'Variances Appear Dissimilar'})")
    st.write("---")

    # --- Choose and Perform the Statistical Test ---
    p_val = None
    test_method = "Unknown"

    if not is_large_sample and (not is_normal_a or not is_normal_b):
        # Path: Not large sample AND not normally distributed -> Mann-Whitney U
        u_stat, p_val = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
        test_method = "Mann-Whitney U Test (Non-parametric)"
        st.write(f"### Test Method: {test_method}")
        st.write(f"U statistic: `{u_stat:.3f}`")
    else:
        # Paths for large samples (rely on CLT) or small-but-normal samples (parametric)
        if levene_p > 0.05: # Variances are similar -> Student's t-test
            t_stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=True, alternative='two-sided')
            test_method = "Student's t-Test (Equal Variances)"
            st.write(f"### Test Method: {test_method}")
            st.write(f"t-statistic: `{t_stat:.3f}`")
        else: # Variances are dissimilar -> Welch's t-test
            t_stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=False, alternative='two-sided')
            test_method = "Welch's t-Test (Unequal Variances)"
            st.write(f"### Test Method: {test_method}")
            st.write(f"t-statistic: `{t_stat:.3f}`")

    # --- Display Conclusion ---
    if p_val is not None:
        st.write(f"P-value: `{p_val:.5f}`")
        if p_val < 0.05: # Common significance level
            st.success("Conclusion: The difference in means between variants is **statistically significant** (p < 0.05).")
            st.markdown(f"This suggests that **'{variants[1]}'** has a significant impact on the **'{metric_col}'** compared to **'{variants[0]}'**.")
        else:
            st.info("Conclusion: The difference in means between variants is **not statistically significant** (p >= 0.05).")
            st.markdown("We do not have enough evidence to claim a significant difference in outcomes between the variants.")
    else:
        st.error("Could not perform statistical test. Please check your data and selections.")

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
                   perform_continuous_ab_test(
                       st.session_state['df'].copy(),
                       variant_column,
                       metric_column
                )
             else:
                 st.error("Unknown metric type selected.")
else:
    st.info("Please upload a CSV file in the sidebar to configure your A/B test.")
    st.markdown("---")
    st.write("### Next Steps:")
    st.write("Upload your data using the file uploader in the sidebar. Once uploaded, new options will appear to configure your A/B test.")
