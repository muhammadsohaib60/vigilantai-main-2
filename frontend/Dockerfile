# Use the official Python 3.12.7 slim image.
FROM python:3.12.7-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements.txt first to leverage Docker's caching mechanism.
COPY requirements.txt .

# Install the Python dependencies from requirements.txt.
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install streamlit

# Copy the entire app folder to the working directory in the container.
COPY . .

# Expose the default Streamlit port.
EXPOSE 8080

# Set environment variables for Streamlit (optional).
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ENABLECORS=false

# Run the Streamlit app.
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
#CMD ["sh", "-c", "streamlit run app.py"]
