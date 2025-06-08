import streamlit as st
import pandas as pd
from scipy import stats
import numpy as np
import plotly.express as px
import statsmodels.api as sm

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

    # --- Check for Normality ---
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