# Base image
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg mp3gain && rm -rf /var/lib/apt/lists/*

# Install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY app.py /app/app.py
WORKDIR /app

# Expose port for Streamlit
EXPOSE 8501

# Run Streamlit
#CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["streamlit", "run", "app.py", "--server.maxUploadSize=1000"]
