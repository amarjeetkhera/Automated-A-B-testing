# continuous_tests.py

import pandas as pd
from scipy import stats
import numpy as np
import plotly.express as px
import statsmodels.api as sm

def perform_continuous_ab_test(df, variant_col, metric_col):
    """
    Performs A/B test for continuous metrics (e.g., revenue, time).
    Decides between Student's t-test, Welch's t-test, and Mann-Whitney U test.

    Args:
        df (pd.DataFrame): The input DataFrame.
        variant_col (str): The name of the column containing A/B test variants.
        metric_col (str): The name of the column containing the continuous metric.

    Returns:
        dict: A dictionary containing test results, group statistics, assumption checks,
              a Plotly figure, and the statistical conclusion. Returns None if critical errors occur.
    """
    results = {
        "status": "success",
        "error_message": None,
        "group_stats": None,
        "plot_figure": None,
        "is_large_sample": False,
        "shapiro_a_p": None,
        "shapiro_b_p": None,
        "is_normal_a": None,
        "is_normal_b": None,
        "levene_p": None,
        "variances_similar": None,
        "test_method": None,
        "statistic": None, # For t-stat or U-stat
        "p_value": None,
        "conclusion": None,
        "interpretation": None
    }

    df[metric_col] = pd.to_numeric(df[metric_col], errors='coerce')
    df_cleaned = df.dropna(subset=[metric_col])

    if df_cleaned[metric_col].nunique() < 2:
        results["status"] = "error"
        results["error_message"] = (
            f"The selected metric column '{metric_col}' does not have enough unique values "
            "for continuous analysis."
        )
        return results

    variants = df_cleaned[variant_col].unique()
    if len(variants) != 2:
        results["status"] = "error"
        results["error_message"] = (
            f"Expected exactly two variants in column '{variant_col}' for A/B test. "
            f"Found: {len(variants)}. Please ensure your variant column only contains two distinct groups "
            "(e.g., 'control' and 'treatment')."
        )
        return results

    group_a = df_cleaned[df_cleaned[variant_col] == variants[0]][metric_col]
    group_b = df_cleaned[df_cleaned[variant_col] == variants[1]][metric_col]

    # Store group statistics
    results["group_stats"] = {
        variants[0]: {"N": len(group_a), "Mean": group_a.mean(), "Std Dev": group_a.std()},
        variants[1]: {"N": len(group_b), "Mean": group_b.mean(), "Std Dev": group_b.std()}
    }

    # --- Box Plot for Continuous Metric ---
    fig_continuous = px.box(
        df_cleaned,
        x=variant_col,
        y=metric_col,
        points="all", # Show individual data points
        labels={metric_col: f'{metric_col.replace("_", " ").title()}'},
        title=f'Distribution of {metric_col.replace("_", " ").title()} by {variant_col}',
        height=450
    )
    results["plot_figure"] = fig_continuous

    # --- Check for Normality ---
    is_large_sample = len(group_a) >= 30 and len(group_b) >= 30
    results["is_large_sample"] = is_large_sample

    shapiro_a_stat, shapiro_a_p = stats.shapiro(group_a)
    shapiro_b_stat, shapiro_b_p = stats.shapiro(group_b)

    results["shapiro_a_p"] = shapiro_a_p
    results["shapiro_b_p"] = shapiro_b_p
    results["is_normal_a"] = shapiro_a_p > 0.05
    results["is_normal_b"] = shapiro_b_p > 0.05

    # Levene's Test for Homogeneity of Variances
    levene_stat, levene_p = stats.levene(group_a, group_b)
    results["levene_p"] = levene_p
    results["variances_similar"] = levene_p > 0.05

    # --- Choose and Perform the Statistical Test ---
    p_val = None
    statistic = None
    test_method = "Unknown"
    conclusion = None
    interpretation = None

    if not is_large_sample and (not results["is_normal_a"] or not results["is_normal_b"]):
        # Path: Not large sample AND not normally distributed -> Mann-Whitney U
        statistic, p_val = stats.mannwhitneyu(group_a, group_b, alternative='two-sided')
        test_method = "Mann-Whitney U Test (Non-parametric)"
    else:
        # Paths for large samples (rely on CLT) or small-but-normal samples (parametric)
        if results["variances_similar"]: # Variances are similar -> Student's t-test
            statistic, p_val = stats.ttest_ind(group_a, group_b, equal_var=True, alternative='two-sided')
            test_method = "Student's t-Test (Equal Variances)"
        else: # Variances are dissimilar -> Welch's t-test
            statistic, p_val = stats.ttest_ind(group_a, group_b, equal_var=False, alternative='two-sided')
            test_method = "Welch's t-Test (Unequal Variances)"

    results["test_method"] = test_method
    results["statistic"] = statistic
    results["p_value"] = p_val

    # --- Determine Conclusion ---
    if p_val is not None:
        if p_val < 0.05:
            conclusion = "statistically significant"
            interpretation = (
                f"This suggests that **'{variants[1]}'** has a significant impact on the "
                f"**'{metric_col}'** compared to **'{variants[0]}'**."
            )
        else:
            conclusion = "not statistically significant"
            interpretation = (
                "We do not have enough evidence to claim a significant difference in outcomes "
                "between the variants."
            )
    else:
        results["status"] = "error"
        results["error_message"] = "Could not perform statistical test. Please check your data and selections."

    results["conclusion"] = conclusion
    results["interpretation"] = interpretation

    return results
