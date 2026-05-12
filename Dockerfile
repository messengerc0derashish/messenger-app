# Use official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (optional if you don't need any)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install eventlet gunicorn

# Expose port
EXPOSE 8080

# Run the app using eventlet (SocketIO production-compatible)
CMD ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:8080", "app:app"]

