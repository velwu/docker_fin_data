# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask to run in development mode
ENV FLASK_ENV=development
ENV FLASK_APP=financial/app.py

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]
