# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Streamlit uses port 8501 by default, but Cloud Run expects 8080
# This command tells Streamlit to listen on the port Google provides
EXPOSE 8080

# Run the web service on container startup.
# We use the --server.port 8080 flag to match Cloud Run's requirements
CMD ["streamlit", "run", "oracle_ui.py", "--server.port=8080", "--server.address=0.0.0.0"]