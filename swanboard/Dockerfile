FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY ../requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY .. /app/

# Set Python path to include the project root
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5173

# Environment variables for MySQL connection
ENV MYSQL_DATABASE=swanlab
ENV MYSQL_USER=swanlab
ENV MYSQL_PASSWORD=swanlab123
ENV MYSQL_HOST=mysql
ENV MYSQL_PORT=3306

# Create logs directory
RUN mkdir -p /app/logs

# Run the SwanBoard server
CMD ["python", "-c", "from swanboard.run.run import SwanBoardRun; SwanBoardRun.run(path='/app/logs', host='0.0.0.0', port=5173)"]