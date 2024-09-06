# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the entire project directory into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# Assuming requirements.txt is in the root of the project
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose the port your Gradio app will run on
EXPOSE 7860

# Run the application
CMD ["python", "/app/gradio/gradio_main.py"]
