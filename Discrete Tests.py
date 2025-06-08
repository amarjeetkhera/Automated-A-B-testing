import streamlit as st
import pandas as pd
from scipy import stats
import numpy as np
import plotly.express as px
import statsmodels.api as sm

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

        # --- Bar Chart for Discrete Metric ---
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