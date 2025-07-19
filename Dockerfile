# Setting Python runtime as the parent image
FROM python:3.10-slim

# Setting the working directory
WORKDIR /app

# Copying requirements file into the container at /app
COPY requirements.txt ./

# Installing packages from requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copying application code to the working directory
COPY . .

# Port for running the Streamlit app on Azure
EXPOSE 8080

# Running the app
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
