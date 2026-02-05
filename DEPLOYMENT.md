# HomeGuard Monitor - Deployment Guide

## Production Deployment

This guide covers deploying HomeGuard Monitor in a production environment.

## Prerequisites

- Docker and Docker Compose
- Domain name (optional but recommended)
- SSL certificates (for HTTPS)

## Security Considerations

### 1. Change Default Credentials

```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update backend/.env
SECRET_KEY=your-generated-secret-key-here
```

### 2. Database Security

```bash
# Use strong database passwords
POSTGRES_PASSWORD=your-strong-db-password

# Enable SSL connections (if supported by your database)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname?sslmode=require
```

### 3. Network Security

```yaml
# In docker-compose.yml, expose only necessary ports
services:
  backend:
    # Remove ports section, use reverse proxy
    # ports:
    #   - "8000:8000"
  
  postgres:
    # Remove external port exposure
    # ports:
    #   - "5432:5432"
  
  redis:
    # Remove external port exposure
    # ports:
    #   - "6379:6379"
```

## Reverse Proxy Configuration

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/homeguard
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Compose with Reverse Proxy

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    networks:
      - homeguard-network

  # Other services (no external ports)
  backend:
    # ... remove ports section
    networks:
      - homeguard-network

  frontend:
    # ... remove ports section
    networks:
      - homeguard-network
```

## Database Optimization

### PostgreSQL Configuration

```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### TimescaleDB Tuning

```sql
-- Enable compression for older data
ALTER TABLE metrics SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'device_id'
);

-- Add compression policy
SELECT add_compression_policy('metrics', INTERVAL '7 days');
```

## Monitoring and Logging

### Application Logging

```python
# In production, use structured logging
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

### Log Aggregation

```yaml
# Add to docker-compose.yml
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
    networks:
      - homeguard-network

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail.yml:/etc/promtail.yml
    networks:
      - homeguard-network
```

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Create backup
docker exec homeguard-postgres pg_dump -U postgres homeguard > "$BACKUP_DIR/homeguard_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/homeguard_$DATE.sql"

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "homeguard_*.sql.gz" -mtime +30 -delete
```

### Automated Backups

```yaml
# Add to docker-compose.yml
  backup:
    image: postgres:15
    volumes:
      - ./scripts:/scripts
      - backup_data:/backups
    depends_on:
      - postgres
    networks:
      - homeguard-network
    command: >
      sh -c "
      while true; do
        /scripts/backup.sh
        sleep 86400
      done
      "
```

## Scaling

### Horizontal Scaling

```yaml
# Multiple backend instances
  backend:
    build: ./backend
    deploy:
      replicas: 3
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@postgres:5432/homeguard
      REDIS_URL: redis://redis:6379/0

# Load balancer
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx-lb.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
```

### Celery Worker Scaling

```yaml
  celery-worker:
    build: ./backend
    deploy:
      replicas: 2
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
```

## Performance Optimization

### Caching Strategy

```python
# Redis caching for frequently accessed data
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
```

### Database Connection Pooling

```python
# In database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

## Monitoring the Monitor

### Health Checks

```python
# Add to main.py
@app.get("/health/detailed")
async def detailed_health_check():
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "celery": await check_celery(),
    }
    return {
        "status": "healthy" if all(checks.values()) else "unhealthy",
        "checks": checks
    }
```

### Metrics Collection

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(duration)
    
    return response
```

## Security Hardening

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

### Input Validation

```python
from pydantic import validator, constr

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   - Check connection pool settings
   - Monitor Celery worker memory
   - Review metric retention policies

2. **Slow Database Queries**
   - Add appropriate indexes
   - Use TimescaleDB continuous aggregates
   - Optimize query patterns

3. **Missing Notifications**
   - Verify notification service credentials
   - Check Celery task queue
   - Review alert rule configurations

### Debug Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Database connection test
docker exec homeguard-postgres psql -U postgres -d homeguard -c "SELECT 1;"

# Redis connection test
docker exec homeguard-redis redis-cli ping
```

## Maintenance

### Regular Tasks

1. **Weekly**: Review system logs and performance metrics
2. **Monthly**: Update dependencies and Docker images
3. **Quarterly**: Review and update security configurations
4. **Annually**: Disaster recovery testing

### Update Process

```bash
# Backup current deployment
docker-compose down
./backup.sh

# Update images
docker-compose pull

# Apply database migrations
docker-compose run --rm backend alembic upgrade head

# Restart services
docker-compose up -d
```

This deployment guide provides a comprehensive approach to running HomeGuard Monitor in production with proper security, monitoring, and scaling considerations.
