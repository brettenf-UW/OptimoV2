FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Gurobi
RUN wget https://packages.gurobi.com/10.0/gurobi10.0.0_linux64.tar.gz \
    && tar -xzf gurobi10.0.0_linux64.tar.gz \
    && mv gurobi1000 /opt/ \
    && rm gurobi10.0.0_linux64.tar.gz

# Set Gurobi environment
ENV GUROBI_HOME=/opt/gurobi1000/linux64
ENV PATH="${GUROBI_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${GUROBI_HOME}/lib:${LD_LIBRARY_PATH}"

# Copy application code
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create batch job script
RUN mkdir -p /app/scripts
COPY scripts/run_batch_job.py /app/scripts/

# Make the script executable
RUN chmod +x /app/scripts/run_batch_job.py

# Entry point for batch job
ENTRYPOINT ["python", "/app/scripts/run_batch_job.py"]
