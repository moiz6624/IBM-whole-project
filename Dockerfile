# Dockerfile for IBM-DASHBOARD-PROJECT
FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose port the app will listen on inside the container
EXPOSE 5000

# Run the application using gunicorn. Worker/thread counts are configurable
# via env vars so you can tune at runtime without rebuilding the image.
# Defaults chosen for moderate concurrency; override at `docker run`.
ENV WEB_CONCURRENCY=4
ENV GUNICORN_THREADS=8
# -k gthread : threaded worker class
# Bind to 0.0.0.0:5000 and use the WSGI callable `application` from main_dashboard
CMD ["sh", "-c", "gunicorn --preload -b 0.0.0.0:5000 -w $WEB_CONCURRENCY -k gthread --threads $GUNICORN_THREADS main_dashboard:application"]