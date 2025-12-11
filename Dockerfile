# Dockerfile for IBM-DASHBOARD-PROJECT
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "main_dashboard.py"]