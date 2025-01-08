FROM python:3.11-slim
LABEL authors="ht-jmetcalf"

# Set the working directory
WORKDIR /app

# Install Git and graphviz
RUN apt-get update && apt-get install -y git graphviz && rm -rf /var/lib/apt/lists/*

# Clone the repo into the current folder (.) instead of /app
RUN git clone https://github.com/jmetdev/CUCCallHandlerDocumentationizer.git .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]
