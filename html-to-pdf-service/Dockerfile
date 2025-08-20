# html-to-pdf-service/Dockerfile

# Use a base image with Python and necessary libraries
# debian-based images work well for installing wkhtmltopdf
FROM python:3.9-slim-bullseye

# Install wkhtmltopdf, xvfb, procps, xauth, and common fonts
# Using fonts-dejavu-core for Debian Bullseye
RUN apt-get update && \
    apt-get install -y --no-install-recommends wkhtmltopdf xvfb procps xauth fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Explicitly set the FLASK_APP environment variable
ENV FLASK_APP=app.py

# Expose the port the Flask app runs on
EXPOSE 5000

# Use the standard entrypoint for flask, which respects FLASK_APP
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

# Alternatively, run with python directly (less common for Flask production, but works for testing)
# CMD ["python", "app.py"]

# In production, consider using Gunicorn (add 'gunicorn' to requirements.txt)
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
