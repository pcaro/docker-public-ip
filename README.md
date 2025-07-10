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
    image: pcarorevuelta/docker-public-ip:latest
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - CHECK_INTERVAL=300  # Check interval in seconds (default: 300)
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
  -v $(pwd)/config:/config \
  -e CHECK_INTERVAL=300 \
  pcarorevuelta/docker-public-ip:latest
```

## Environment Variables

- `CHECK_INTERVAL`: Interval between IP checks in seconds (default: 300)
- `WEB_PORT`: Port for the web interface (default: 8080)
- `WEB_HOST`: Host for the web interface (default: 0.0.0.0)
- `DB_PATH`: Path to the SQLite database (default: /data/ip_history.db)
- `SERVICES_FILE`: Path to the IP services configuration file (default: /config/services.txt)

## Web Interface

Access the web interface at `http://localhost:8080` to view:
- Current public IP
- IP change history
- Service statistics and performance
- Response time charts
- Historical data visualization

## IP Check Services

By default, the service randomly selects from these providers:
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

### Customizing IP Services

You can customize the list of IP check services by:

1. **Creating a custom services file**: Create a `config/services.txt` file with one service URL per line:
   ```
   # Custom IP services
   https://ipv4.icanhazip.com
   https://checkip.amazonaws.com
   https://api.ipify.org
   ```

2. **Mounting it as a volume**: The container will automatically use your custom file:
   ```bash
   # Create your custom services file
   mkdir -p config
   echo "https://ipv4.icanhazip.com" > config/services.txt
   echo "https://checkip.amazonaws.com" >> config/services.txt
   
   # Run with custom config
   docker-compose up
   ```

3. **File format**:
   - One URL per line
   - Lines starting with `#` are comments
   - Protocol (https://) is optional - will be added automatically
   - Empty lines are ignored

## Development

```bash
# Install dependencies
uv pip install -e .

# Run the service
python -m docker_public_ip
```

## License

MIT