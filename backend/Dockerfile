# Use PyTorch image with CUDA support
FROM pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy ML models and extract only .pt files
# Context is set to project root in docker-compose, so we can access ml/runs
COPY ml/runs/detect /tmp/ml_runs/
RUN mkdir -p /app/ml_models && \
    for model_dir in /tmp/ml_runs/*/; do \
        if [ -f "$model_dir/weights/best.pt" ]; then \
            model_name=$(basename "$model_dir"); \
            cp "$model_dir/weights/best.pt" "/app/ml_models/${model_name}.pt"; \
            echo "Copied model: ${model_name}.pt"; \
        fi \
    done && \
    rm -rf /tmp/ml_runs && \
    echo "Models copied:" && ls -lh /app/ml_models/

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
