FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy the project files
COPY pyproject.toml .
COPY src/ src/

# Install the project
RUN uv pip install --system -e .

# Create data directory
RUN mkdir -p /data

# Expose web interface port
EXPOSE 8080

# Run the application
CMD ["python", "-m", "docker_public_ip"]