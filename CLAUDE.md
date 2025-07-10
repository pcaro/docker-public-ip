# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker-based public IP monitoring service that periodically checks your public IP address and provides a web interface to monitor IP changes over time. The service is built in Python using Flask for the web interface, APScheduler for periodic tasks, and SQLite for data storage.

## Architecture

The application follows a modular architecture:

- **Main entry point** (`src/docker_public_ip/__main__.py`): Coordinates between the IP checker and web server using separate threads
- **IP Checker** (`src/docker_public_ip/ip_checker.py`): Handles periodic IP checks using random service selection with retry logic
- **Database layer** (`src/docker_public_ip/database.py`): SQLite operations for storing IP checks, changes, and generating statistics
- **Web interface** (`src/docker_public_ip/web.py`): Flask app serving dashboard with charts and statistics
- **Configuration** (`src/docker_public_ip/config.py`): Environment-based configuration with IP service loading

## Development Commands

```bash
# Install dependencies using uv
uv pip install -e .

# Run the application locally
python -m docker_public_ip

# Build and run with Docker Compose
docker-compose up --build

# Build Docker image
docker build -t docker-public-ip .
```

## Configuration

The application uses environment variables for configuration:

- `CHECK_INTERVAL`: Interval between IP checks in seconds (default: 300)
- `WEB_PORT`: Port for the web interface (default: 8080)
- `WEB_HOST`: Host for the web interface (default: 0.0.0.0)
- `DB_PATH`: Path to SQLite database (default: /data/ip_history.db)
- `SERVICES_FILE`: Path to IP services config (default: /config/services.txt)

## Key Implementation Details

- **IP Service Management**: Services are loaded from `/config/services.txt` with fallback to hardcoded defaults. The checker randomly selects services and retries up to 5 times on failure.
- **Database Schema**: Single table `ip_checks` with indexes on timestamp and IP address for efficient queries.
- **Threading**: Main thread runs the IP checker scheduler, web server runs in a daemon thread.
- **Logging**: Uses loguru for structured logging throughout the application.
- **Error Handling**: Failed IP checks are recorded with error messages and response times.

## IP Services Configuration

The application supports configurable IP checking services via `/config/services.txt`:
- One URL per line
- Lines starting with `#` are comments
- Protocol (https://) is optional and added automatically
- Falls back to hardcoded services if file doesn't exist or is invalid

## Testing and Validation

The application includes a fixture creation script (`create_fixtures.py`) for testing the database and web interface with sample data.

## Deployment

The application is designed for Docker deployment with:
- Multi-stage build using uv for Python dependency management
- Volume mounts for data persistence and configuration
- GitHub Actions for automated Docker image builds
- Published to GitHub Container Registry as `ghcr.io/pcaro/docker-public-ip`