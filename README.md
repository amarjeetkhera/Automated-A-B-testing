# Automated A/B testing

## Project Overview

This project provides an intuitive and automated A/B testing tool designed to help users quickly analyze experiment results for both discrete and continuous metrics. A/B testing is a crucial methodology for data-driven decision-making, allowing businesses to compare two versions of a product, feature or marketing campaign to determine which version performs better and if the changes made are making any significant impact. This tool simplifies the statistical analysis process, offering clear conclusions and interactive visualizations, making advanced statistical testing accessible without requiring deep expertise.

## Description

The Automated A/B Testing Tool is built using Python and deployed on Streamlit as a webapp, allowing for easy data upload and interactive analysis. It intelligently selects the appropriate statistical test based on the type of metric (discrete or continuous) and inherent data properties, following a robust decision-making flowchart.

![Discrete Metric__20250610_212126_0000](https://github.com/user-attachments/assets/e64d6b23-4678-4617-8970-2094c100e409)

(Kindly cite this repository if you use this flow chart)

## Correlation vs Causation
While A/B testing is designed to establish causality by comparing randomized groups, it's crucial to remember a fundamental principle of statistics: Correlation does not imply causation.

This tool helps identify statistical differences between groups, which, when combined with a properly designed experiment (e.g., random assignment, controlled variables, sufficient sample size), can indicate a causal relationship. However, the tool itself cannot guarantee the design or execution of a flawless experiment. Always ensure your experiment setup adheres to best practices to confidently infer causation from the observed statistical significance. The tool aims to provide actionable insights, empowering users to make initial data-backed decisions swiftly.


## Deployment

The tool was built keeping best-practices in mind such as usage of modular functions for better reusability and understanding. Initially, it was deployed as a web application using Streamlit Cloud for quick accessibility and demonstration.

Streamlit App link: https://automated-a-b-testing-e9xnkpkiday2bdq9tfsvcv.streamlit.app

How to Use:

1. Visit the Streamlit app link.
2. Upload your experiment data in .csv format in the sidebar and configure your test.
3. View the statistical test results.

### Automated Deployment to Azure (Production-Ready CI/CD)

To elevate the project to a more robust, scalable, and automated environment, the application has also been deployed to Azure as a Container App leveraging a Continuous Integration/Continuous Delivery (CI/CD) pipeline with GitHub Actions.

This pipeline automatically builds and deploys the latest version of the application to Azure whenever changes are pushed to the main branch.

Azure Deployed App link: https://ab-testing-tool-aca.yellowwater-7ebb3e08.westeurope.azurecontainerapps.io

Feel free to fork this repository, submit pull requests, or open issues if you have suggestions or find bugs.

