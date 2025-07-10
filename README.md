# Docker Public IP Monitor

A simple Docker service that periodically checks your public IP address and provides a web interface to monitor IP changes over time.

## Features

- Periodically checks public IP using various services
- Stores history in SQLite database
- Web interface with charts and statistics
- Tracks IP changes over time
- Shows service performance metrics
- Automatic Docker image builds via GitHub Actions

## Usage

### Using Docker Compose

```yaml
services:
  public-ip-monitor:
    image: ghcr.io/pcaro/docker-public-ip:latest
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
    environment:
      - CHECK_INTERVAL=30  # Check interval in seconds (default: 30)
      - WEB_PORT=8080     # Web interface port (default: 8080)
      - WEB_HOST=0.0.0.0  # Web interface host (default: 0.0.0.0)
      - DB_PATH=/data/ip_history.db  # Database path (default: /data/ip_history.db)
    restart: unless-stopped
```

### Using Docker CLI

```bash
docker run -d \
  --name public-ip-monitor \
  -p 8080:8080 \
  -v $(pwd)/data:/data \
  -e CHECK_INTERVAL=30 \
  ghcr.io/pcaro/docker-public-ip:latest
```

## Environment Variables

- `CHECK_INTERVAL`: Interval between IP checks in seconds (default: 30)
- `WEB_PORT`: Port for the web interface (default: 8080)
- `WEB_HOST`: Host for the web interface (default: 0.0.0.0)
- `DB_PATH`: Path to the SQLite database (default: /data/ip_history.db)

## Web Interface

Access the web interface at `http://localhost:8080` to view:
- Current public IP
- IP change history
- Service statistics and performance
- Response time charts
- Historical data visualization

## IP Check Services

The service randomly selects from these providers:
- icanhazip.com
- checkip.amazonaws.com
- ipinfo.io/ip
- wtfismyip.com/text
- api.ipify.org
- ifconfig.io/ip
- www.moanmyip.com/simple
- ifconfig.co/ip
- ifconfig.me/ip
- ipecho.net/plain

## Development

```bash
# Install dependencies
uv pip install -e .

# Run the service
python -m docker_public_ip
```

## License

MIT