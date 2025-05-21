FROM python:3.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Create a non-root user
RUN useradd -m -u 1000 streamlit
USER streamlit

# Command to run the application
CMD ["streamlit", "run", "graph-streamlit.py", "--server.address", "0.0.0.0"] 