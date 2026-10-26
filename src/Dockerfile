FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and system libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set timezone
ENV TZ=Asia/Ho_Chi_Minh
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY config ./config
COPY scripts ./scripts
COPY run.py .
COPY yolov8n.pt .

# Create necessary directories
RUN mkdir -p uploads logs

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Run the application using Gunicorn on the Render-injected PORT (defaults to 10000)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} run:app"]
