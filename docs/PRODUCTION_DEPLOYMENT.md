# Jesse MCP Production Deployment Guide

This guide covers deploying jesse-mcp in a production environment with proper security, monitoring, and reliability.

## Pre-Deployment Checklist

- [ ] Jesse instance is configured and running
- [ ] Jesse REST API is accessible at configured host/port
- [ ] Python 3.8+ is installed
- [ ] Network connectivity between MCP server and Jesse API verified
- [ ] SSL certificates (if using HTTPS)
- [ ] Firewall rules configured for MCP server port

## Installation for Production

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-org/jesse-mcp.git
cd jesse-mcp

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with production dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Jesse API Configuration
JESSE_HOST=your-jesse-api-host.com
JESSE_PORT=8000
JESSE_USE_HTTPS=true

# Authentication - Choose one method:

# Option A: Password Authentication (Simple, suitable for private networks)
JESSE_PASSWORD=your-secure-password

# Option B: API Token Authentication (Recommended for production)
JESSE_API_TOKEN=your-api-token-from-jesse-ui

# MCP Server Configuration
MCP_HOST=0.0.0.0  # Listen on all interfaces
MCP_PORT=5000
MCP_TIMEOUT=300  # Request timeout in seconds

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/var/log/jesse-mcp/server.log

# Optional: Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

### 3. Set Up API Token in Jesse UI

For production, use API token authentication instead of password:

1. **In Jesse UI**:
   - Navigate to Settings → Security
   - Click "Generate API Token"
   - Copy the generated token
   - Store it securely (password manager, secrets vault)

2. **In jesse-mcp .env**:
   ```bash
   JESSE_API_TOKEN=your-token-here
   JESSE_PASSWORD=  # Leave empty when using token
   ```

3. **Security Benefits**:
   - Tokens can be revoked independently
   - Tokens can have expiration dates
   - Better audit trail
   - Separates MCP server credentials from user accounts

### 4. Directory Structure for Production

```
/opt/jesse-mcp/
├── jesse-mcp/                 # Application directory
│   ├── jesse_mcp/
│   ├── tests/
│   ├── docs/
│   ├── requirements.txt
│   ├── setup.py
│   └── .env
├── logs/                       # Log directory
│   └── jesse-mcp.log
├── cache/                      # Optional cache directory
└── venv/                       # Virtual environment
```

### 5. Create Systemd Service (Linux/macOS)

Create `/etc/systemd/system/jesse-mcp.service`:

```ini
[Unit]
Description=Jesse MCP Server
Documentation=https://github.com/your-org/jesse-mcp
After=network.target

[Service]
Type=simple
User=jesse-mcp
WorkingDirectory=/opt/jesse-mcp/jesse-mcp
EnvironmentFile=/opt/jesse-mcp/jesse-mcp/.env

# Using gunicorn for production WSGI server
ExecStart=/opt/jesse-mcp/venv/bin/gunicorn \
    --bind 0.0.0.0:5000 \
    --workers 4 \
    --timeout 300 \
    --access-logfile /opt/jesse-mcp/logs/access.log \
    --error-logfile /opt/jesse-mcp/logs/error.log \
    jesse_mcp.server:app

Restart=on-failure
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

# Resource limits
MemoryLimit=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable jesse-mcp
sudo systemctl start jesse-mcp
sudo systemctl status jesse-mcp
```

## Network Security

### 1. Firewall Configuration

```bash
# Linux (UFW)
sudo ufw allow 5000/tcp  # MCP server port
sudo ufw allow from TRUSTED_IP to any port 5000

# Only allow from specific networks
sudo ufw allow from 192.168.0.0/16 to any port 5000
```

### 2. TLS/SSL Configuration

For secure communication, use a reverse proxy (nginx):

```nginx
upstream jesse_mcp {
    server 127.0.0.1:5000;
}

server {
    listen 443 ssl http2;
    server_name jesse-mcp.example.com;

    ssl_certificate /etc/letsencrypt/live/jesse-mcp.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jesse-mcp.example.com/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000" always;

    location / {
        proxy_pass http://jesse_mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (for streaming if implemented)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name jesse-mcp.example.com;
    return 301 https://$server_name$request_uri;
}
```

### 3. Authentication & Authorization

For production MCP servers with multiple users:

```python
# In jesse_mcp/server.py or custom middleware
from functools import wraps
import jwt

def require_mcp_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or not verify_mcp_token(token):
            return {'error': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/tools', methods=['GET'])
@require_mcp_token
def list_tools():
    # Return tools only to authenticated clients
    pass
```

## Monitoring & Observability

### 1. Logging Configuration

```python
# In jesse_mcp/server.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/jesse-mcp/server.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'jesse_mcp': {
            'handlers': ['file', 'console'],
            'level': os.getenv('LOG_LEVEL', 'INFO')
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### 2. Health Check Endpoint

```python
@app.route('/health', methods=['GET'])
def health_check():
    """Health check for monitoring."""
    try:
        # Quick connectivity test
        client.call_tool('ping')
        return {
            'status': 'healthy',
            'jesse_api': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 503
```

### 3. Metrics Collection

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
tool_calls = Counter('jesse_mcp_tool_calls_total', 'Total tool calls', ['tool_name'])
tool_duration = Histogram('jesse_mcp_tool_duration_seconds', 'Tool call duration', ['tool_name'])
errors = Counter('jesse_mcp_errors_total', 'Total errors', ['error_type'])

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(), 200, {'Content-Type': 'text/plain'}
```

## Backup & Recovery

### 1. Configuration Backup

```bash
# Automated backup of sensitive config
#!/bin/bash
BACKUP_DIR="/opt/jesse-mcp/backups"
mkdir -p $BACKUP_DIR

# Backup .env (without credentials in some cases)
cp /opt/jesse-mcp/jesse-mcp/.env $BACKUP_DIR/env.backup.$(date +%Y%m%d)

# Keep only last 30 days
find $BACKUP_DIR -name "env.backup.*" -mtime +30 -delete
```

### 2. Log Rotation

```bash
# /etc/logrotate.d/jesse-mcp
/opt/jesse-mcp/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 jesse-mcp jesse-mcp
    sharedscripts
    postrotate
        systemctl reload jesse-mcp > /dev/null 2>&1 || true
    endscript
}
```

## Performance Tuning

### 1. Gunicorn Configuration

```bash
# More workers for higher concurrency
gunicorn --workers 8 \
         --worker-class sync \
         --bind 0.0.0.0:5000 \
         --timeout 300 \
         --keep-alive 5 \
         jesse_mcp.server:app
```

### 2. Connection Pooling

```python
# In jesse_mcp/core/jesse_rest_client.py
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

## Troubleshooting

### MCP Server Won't Start

```bash
# Check logs
sudo journalctl -u jesse-mcp -f

# Verify configuration
python3 -c "from jesse_mcp.server import app; print('Server OK')"

# Check port availability
sudo lsof -i :5000
```

### Connection Issues to Jesse API

```bash
# Test connectivity
curl -X GET http://JESSE_HOST:JESSE_PORT/api/test

# Check network routing
traceroute JESSE_HOST

# Verify firewall
sudo iptables -L -n | grep 5000
```

### High Memory Usage

```bash
# Monitor process
watch -n 1 'ps aux | grep jesse-mcp'

# Check for memory leaks
python3 -m memory_profiler jesse_mcp/server.py

# Restart service
sudo systemctl restart jesse-mcp
```

## Security Best Practices

1. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   pip check  # Check for vulnerable packages
   ```

2. **Secrets Management**
   - Use environment variables (never hardcode credentials)
   - Use a secrets vault (HashiCorp Vault, AWS Secrets Manager)
   - Rotate API tokens regularly

3. **Access Control**
   - Restrict network access to trusted IPs
   - Use VPN/private network when possible
   - Implement rate limiting
   - Log all API calls

4. **Regular Updates**
   - Keep OS patched
   - Update Python dependencies
   - Review security advisories

## Performance Benchmarks

Expected performance (single server, no optimization):

- **Tool discovery**: < 50ms
- **Simple backtest**: 1-5 seconds
- **Comprehensive backtest**: 5-30 seconds
- **Risk analysis**: 1-3 seconds
- **Concurrent requests**: 10-50 requests/sec (depends on tool complexity)

## Scaling for High Load

For high-volume production use:

1. **Horizontal Scaling**
   - Deploy multiple MCP server instances
   - Use load balancer (nginx, HAProxy)
   - Each instance connects to same Jesse API

2. **Caching Layer**
   - Add Redis for strategy list caching
   - Cache backtest results (with invalidation)
   - Cache pair correlations

3. **Async Processing**
   - Use Celery for long-running tasks
   - Background job queue for batch operations
   - Webhooks for result delivery

## See Also

- [USING_WITH_LLMS.md](USING_WITH_LLMS.md) - LLM integration guide
- [AGENT_SYSTEM.md](AGENT_SYSTEM.md) - Specialized agents documentation
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current project status
