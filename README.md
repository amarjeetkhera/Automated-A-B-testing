# Automated A/B testing

## Project Overview

This project provides an intuitive and automated A/B testing tool designed to help users quickly analyze experiment results for both discrete and continuous metrics. A/B testing is a crucial methodology for data-driven decision-making, allowing businesses to compare two versions of a product, feature, or marketing campaign to determine which performs better. This tool simplifies the statistical analysis process, offering clear conclusions and interactive visualizations, making advanced statistical testing accessible without requiring deep expertise.

## Description

The Automated A/B Testing Tool is built as a Streamlit web application, allowing for easy data upload and interactive analysis. It intelligently selects the appropriate statistical test based on the type of metric (discrete or continuous) and inherent data properties, following a robust decision-making flowchart.

### Key Statistical Features:

* **Discrete Metrics (e.g., Conversion Rates, Click-Through Rates):**
    * **Chi-squared Test:** Used for comparing proportions when expected frequencies are sufficiently large.
    * **Fisher's Exact Test:** Employed for comparing proportions when expected frequencies are small, ensuring accurate results even with limited data.
    * Includes validation for binary outcomes.

* **Continuous Metrics (e.g., Revenue, Time Spent, Page Load Speed):**
    * **Assumption Checks:** Dynamically assesses sample size, normality (using Shapiro-Wilk test for smaller samples), and homogeneity of variances (using Levene's test).
    * **Student's t-test:** Applied when variances between groups are similar.
    * **Welch's t-test:** Used when variances between groups are dissimilar, providing a more robust comparison.
    * **Mann-Whitney U Test:** A non-parametric alternative used for non-normally distributed data or smaller sample sizes where parametric assumptions are not met.

### Data Handling and Visualization:

* Accepts CSV file uploads for experiment data.
* Automatically cleans and processes the selected variant and metric columns.
* Generates **interactive charts** using `Plotly.express` to visualize results:
    * **Discrete:** Bar charts displaying conversion rates with 95% confidence intervals.
    * **Continuous:** Box plots showing the distribution of the metric for each variant, including individual data points.

The tool aims to provide actionable insights, empowering users to make data-backed decisions swiftly.

## Key Features

* **User-Friendly Interface:** Built with Streamlit for an interactive and accessible experience.
* **Automated Test Selection:** Intelligently chooses the correct statistical test based on metric type and data characteristics.
* **Comprehensive Statistical Analysis:** Supports Chi-squared, Fisher's Exact, Student's t-test, Welch's t-test, and Mann-Whitney U test.
* **Assumption Validation:** Includes checks for expected frequencies, normality, and variance homogeneity.
* **Clear Conclusions:** Provides easy-to-understand interpretations of statistical significance (p-values).
* **Interactive Visualizations:** Enhances understanding with dynamic bar charts and box plots.

## Installation and Local Usage

To run this A/B testing tool on your local machine or in a development environment like Gitpod/Codespaces:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your_username/your_repo_name.git](https://github.com/your_username/your_repo_name.git)
    cd your_repo_name
    ```
    (Replace `your_username/your_repo_name.git` with your actual repository path)

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```

3.  **Install the required libraries:**
    Create a `requirements.txt` file in the root of your project with the following content:
    ```
    streamlit
    pandas
    scipy
    numpy
    plotly
    statsmodels
    ```
    Then, install them:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```

5.  Your web browser should automatically open the Streamlit application. If not, open your browser and navigate to the local URL displayed in the terminal (usually `http://localhost:8501`).

## How to Use

1.  **Upload Your Data:** In the sidebar, click "Choose a CSV file" and upload your experiment data. Ensure your CSV has at least two columns: one for variants (e.g., 'control', 'treatment') and one for your metric (e.g., 'conversion', 'revenue').
2.  **Select Columns:** From the dropdowns, choose the correct "Variant Column" and "Metric Column".
3.  **Choose Metric Type:** Select whether your metric is "Discrete" (binary outcomes like conversions) or "Continuous" (numerical values like revenue).
4.  **Run Analysis:** Click the "Run A/B Test Analysis" button.
5.  **View Results:** The main section will display the contingency tables (for discrete), basic statistics, assumption checks, the chosen statistical test, the p-value, and interactive charts illustrating your results.

## Contributing

Feel free to fork this repository, submit pull requests, or open issues if you have suggestions or find bugs.

## License

This project is open-source and available under the [MIT License](LICENSE) (or choose your preferred license).
