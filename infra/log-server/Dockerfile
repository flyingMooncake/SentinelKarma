FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    solders \
    requests \
    python-multipart

# Copy server code
COPY server.py .

# Create data directory
RUN mkdir -p /data/logs

# Expose port
EXPOSE 9000

# Run server
CMD ["python", "server.py"]
