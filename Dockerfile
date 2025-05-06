# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster # Choose a suitable Python version

WORKDIR /app

# Copy only necessary files for installing dependencies first
COPY pyproject.toml ./
COPY requirements.txt ./ # If you use requirements.txt for Docker
# COPY setup.py ./ # If needed

# Install dependencies
# Using requirements.txt might be simpler in Docker
RUN pip install --no-cache-dir -r requirements.txt
# Or install from pyproject.toml
# RUN pip install --no-cache-dir .

# Copy the rest of the application code
COPY src/ ./src
COPY README.md . # etc.

# Make port 80 available if it's a web app
# EXPOSE 80

# Command to run the application
# Adjust based on your project's entry point
CMD ["python", "src/main.py"]
