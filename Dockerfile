# Use the official lightweight Python image.
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in logs
ENV PYTHONUNBUFFERED True

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the web server (Cloud Run expects a process listening on $PORT)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 subscriber_pipeline:app
