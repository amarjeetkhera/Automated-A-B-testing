import streamlit as st
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Automated A/B Testing Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Title and Introduction ---
st.title("📊 Automated A/B Testing Tool")
st.markdown("""
Welcome to your automated A/B testing platform!
Upload your experiment data below to get started with analyzing your test results.
""")

st.subheader("1. Upload Your Data")
st.write("Please upload a CSV file containing your A/B test data.")

# --- File Uploader ---
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

# --- Data Display and Initial Processing ---
if uploaded_file is not None:
    # Read the CSV file into a pandas DataFrame
    try:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully!")

        st.markdown("---")
        st.subheader("Preview of Your Data")
        st.write("Here's the first few rows of your uploaded data:")
        st.dataframe(df.head()) # Display the first 5 rows

        st.markdown("---")
        st.subheader("Data Overview")
        # Display basic information about the DataFrame
        st.write(f"**Number of rows:** {df.shape[0]}")
        st.write(f"**Number of columns:** {df.shape[1]}")
        st.write("Columns in your dataset:")
        st.write(df.columns.tolist())

        # You might want to save the dataframe to Streamlit's session state
        # so it persists across reruns. We'll explore this more later.
        st.session_state['df'] = df

    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.write("Please ensure your file is a valid CSV format.")
else:
    st.info("Awaiting CSV file upload.")

st.markdown("---")
st.write("### Next Steps:")
st.write("Once your data is uploaded, we'll guide you through selecting your metrics and variants for analysis.")