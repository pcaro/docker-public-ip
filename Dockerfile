FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir uv \
    && uv pip install --system -r requirements.txt

# Create data directory
RUN mkdir -p /data

# Expose web interface port
EXPOSE 8080

# Run the application
CMD ["uv", "run", "python", "-m", "docker_public_ip"]