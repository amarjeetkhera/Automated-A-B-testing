import pandas as pd
from scipy import stats
import numpy as np
import plotly.express as px
import statsmodels.api as sm

def perform_discrete_ab_test(df, variant_col, metric_col):
    """
    Performs A/B test for discrete metrics.
    Decides between Chi-squared and Fisher's exact test based on expected counts.
    Assumes metric_col contains binary outcomes (0/1).

    Args:
        df (pd.DataFrame): The input DataFrame.
        variant_col (str): The name of the column containing A/B test variants.
        metric_col (str): The name of the column containing the binary discrete metric.

    Returns:
        dict: A dictionary containing test results, contingency tables, conversion rates,
              confidence intervals, and a Plotly figure. Returns None if critical errors occur.
    """
    results = {
        "status": "success",
        "error_message": None,
        "contingency_table": None,
        "expected_frequencies": None,
        "percentage_small_expected": None,
        "observed_rates_df": None,
        "plot_figure": None,
        "test_method": None,
        "p_value": None,
        "chi2_statistic": None,
        "dof": None,
        "odds_ratio": None,
        "conclusion": None,
        "interpretation": None,
        "raw_conversion_rates": None
    }

    # Ensure metric column is numerical (0/1) for counting
    df[metric_col] = pd.to_numeric(df[metric_col], errors='coerce')
    df_cleaned = df.dropna(subset=[metric_col])

    if df_cleaned[metric_col].nunique() > 2:
        results["status"] = "error"
        results["error_message"] = (
            f"The selected discrete metric column '{metric_col}' contains more than two unique values. "
            "Please ensure it's a binary outcome (e.g., 0/1 for success/failure)."
        )
        return results

    try:
        contingency_table = pd.crosstab(df_cleaned[variant_col], df_cleaned[metric_col])
    except Exception as e:
        results["status"] = "error"
        results["error_message"] = f"Could not create a contingency table. Check your variant and metric columns. Error: {e}"
        return results

    if contingency_table.empty:
        results["status"] = "error"
        results["error_message"] = "Could not create a contingency table. Check your variant and metric columns."
        return results
    results["contingency_table"] = contingency_table

    # Calculate expected frequencies
    chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
    expected_df = pd.DataFrame(expected, index=contingency_table.index, columns=contingency_table.columns)
    results["expected_frequencies"] = expected_df

    # Check assumptions for Chi-squared test
    small_expected_cells = (expected < 5).sum()
    total_cells = expected.size
    percentage_small_expected = (small_expected_cells / total_cells) * 100
    results["percentage_small_expected"] = percentage_small_expected

    # --- Calculate Conversion Rates and Confidence Intervals for Plotting ---
    total_counts = contingency_table.sum(axis=1)
    # Determine the "success" column. Assuming 1 represents success.
    metric_success_index = 1 if 1 in contingency_table.columns else (0 if 0 in contingency_table.columns else None)

    if metric_success_index is not None and metric_success_index in contingency_table.columns:
        success_counts = contingency_table[metric_success_index]
        conversion_rates = (success_counts / total_counts)

        plot_df = pd.DataFrame({
            variant_col: total_counts.index,
            'Successes': success_counts,
            'Trials': total_counts,
            'Conversion_Rate': conversion_rates * 100
        })
        results["raw_conversion_rates"] = conversion_rates * 100

        # Calculate confidence intervals
        alpha = 0.05
        conf_int_lower = []
        conf_int_upper = []
        for i in range(len(plot_df)):
            count = plot_df['Successes'].iloc[i]
            nobs = plot_df['Trials'].iloc[i]
            ci_low, ci_upp = sm.stats.proportion_confint(count, nobs, alpha=alpha, method='normal')
            conf_int_lower.append(ci_low * 100)
            conf_int_upper.append(ci_upp * 100)

        plot_df['CI_Lower'] = conf_int_lower
        plot_df['CI_Upper'] = conf_int_upper
        results["observed_rates_df"] = plot_df[[variant_col, 'Conversion_Rate', 'CI_Lower', 'CI_Upper']]

        # --- Bar Chart for Discrete Metric ---
        fig_discrete = px.bar(
            plot_df,
            x=variant_col,
            y='Conversion_Rate',
            error_y='CI_Upper',
            error_y_minus='CI_Lower',
            labels={'Conversion_Rate': f'Conversion Rate (%)'},
            title=f'Conversion Rate by {variant_col} (with 95% Confidence Intervals)',
            height=400
        )
        fig_discrete.data[0].error_y.array = plot_df['CI_Upper'] - plot_df['Conversion_Rate']
        fig_discrete.data[0].error_y.arrayminus = plot_df['Conversion_Rate'] - plot_df['CI_Lower']
        results["plot_figure"] = fig_discrete
    else:
        results["error_message"] = "Could not determine success column for observed rates and plotting."

    # --- Statistical Test Logic ---
    if percentage_small_expected <= 20 and np.all(expected >= 1):
        results["test_method"] = "Pearson's Chi-squared Test"
        results["chi2_statistic"] = chi2
        results["dof"] = dof
        results["p_value"] = p_val
        if p_val < 0.05:
            results["conclusion"] = "statistically significant"
            results["interpretation"] = f"This suggests that the '{variant_col}' has a significant effect on the '{metric_col}'."
        else:
            results["conclusion"] = "not statistically significant"
            results["interpretation"] = "We do not have enough evidence to claim a significant difference in outcomes between the variants."

    else:
        # Use Fisher's exact test
        results["test_method"] = "Fisher's Exact Test (due to small expected cell counts)"
        if contingency_table.shape == (2, 2):
            odds_ratio, p_val = stats.fisher_exact(contingency_table)
            results["p_value"] = p_val
            results["odds_ratio"] = odds_ratio
            if p_val < 0.05:
                results["conclusion"] = "statistically significant"
                results["interpretation"] = f"This suggests that the '{variant_col}' has a significant effect on the '{metric_col}'."
            else:
                results["conclusion"] = "not statistically significant"
                results["interpretation"] = "We do not have enough evidence to claim a significant difference in outcomes between the variants."
        else:
            results["status"] = "error"
            results["error_message"] = (
                "Fisher's Exact Test is primarily for 2x2 tables when assumptions for Chi-squared are violated. "
                "Your contingency table is not 2x2. Consider aggregating your variants or checking your data if you expected a 2x2 table."
            )
    
    return results
