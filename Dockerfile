# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

WORKDIR /app

# Copy only necessary files for installing dependencies first
COPY pyproject.toml ./
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install openpyxl pandas

# Copy the rest of the application code
COPY src/ ./src
COPY README.md ./

# Create a volume mount point for data
VOLUME ["/data"]

# Set the entrypoint to the Python interpreter
ENTRYPOINT ["python"]

# Default command to show help
CMD ["-m", "src.vtt", "--help"]
