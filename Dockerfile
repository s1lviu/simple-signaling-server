# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Make port 443 available to the world outside this container
EXPOSE 443

# Define environment variable
ENV FLASK_APP=app.py

# Run gunicorn when the container launches. Note: Adjust the worker number as needed
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:443", "app:app"]
