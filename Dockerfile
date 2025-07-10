FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN uv sync

# Create data directory
RUN mkdir -p /data

# Expose web interface port
EXPOSE 8080

# Run the application
CMD ["uv", "run", "python", "-m", "docker_public_ip"]