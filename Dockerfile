FROM python:3.11-slim
LABEL authors="ht-jmetcalf"

# Set the working directory
WORKDIR /app

# Install Git so we can clone the repo
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && apt-get install graphviz

# Clone the repository directly into /app
RUN git clone https://github.com/jmetdev/CUCCallHandlerDocumentationizer.git /app

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]
