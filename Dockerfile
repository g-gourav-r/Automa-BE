FROM python:3.11-slim-buster

# Install system dependencies for Poppler, Tesseract, OpenCV, and others
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \        
    tesseract-ocr \        
    libsm6 \
    libxext6 \
    libxrender1 \        
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src src

# Run the app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
