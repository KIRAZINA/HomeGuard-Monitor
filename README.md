# HomeGuard Monitor

[![CI/CD Pipeline](https://github.com/yourusername/HomeGuard-Monitor/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/yourusername/HomeGuard-Monitor/actions)
[![codecov](https://codecov.io/gh/yourusername/HomeGuard-Monitor/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/HomeGuard-Monitor)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, production-ready monitoring and alerting system for personal servers and IoT devices. Built with FastAPI, PostgreSQL, Redis, and React.

## 🌟 Features

- ✅ **Real-time Device Monitoring** - Track device status and metrics with millisecond precision
- ✅ **Intelligent Alerting** - Create custom alert rules with flexible conditions and thresholds
- ✅ **Multi-channel Notifications** - Telegram, Discord, SMS (Twilio), Email (SMTP)
- ✅ **Time-series Storage** - PostgreSQL + TimescaleDB for efficient metrics storage
- ✅ **Advanced Analytics** - Anomaly detection using machine learning
- ✅ **Interactive Dashboard** - React-based UI with real-time updates
- ✅ **Async Task Queue** - Celery with Redis for background jobs
- ✅ **Production Ready** - Docker support, comprehensive logging, security hardening
- ✅ **Type-Safe** - Full Python type hints and Pydantic validation
- ✅ **Well-Tested** - Extensive test coverage with pytest and asyncio support

## 🏗️ Architecture

### Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| API Framework | FastAPI | 0.109+ |
| Language | Python | 3.10+ |
| Database | PostgreSQL | 14+ |
| Cache/Queue | Redis | 6.0+ |
| Async Tasks | Celery | 5.3+ |
| Frontend | React | 18+ |
| Containerization | Docker | Latest |

### Project Structure

```
HomeGuard-Monitor/
├── backend/                   # FastAPI Python backend
│   ├── app/
│   │   ├── api/              # API v1 endpoints
│   │   ├── core/             # Core utilities (config, database, logging)
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic layer
│   │   ├── tasks/            # Celery async tasks
│   │   ├── celery_app.py     # Celery configuration
│   │   └── main.py           # FastAPI application
│   ├── tests/                # Comprehensive test suite
│   ├── Dockerfile            # Backend container image
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # React components
│   │   └── pages/            # Page components
│   ├── Dockerfile            # Frontend container image
│   └── package.json          # Dependencies
│
├── agents/                    # Monitoring agent scripts
├── scripts/                   # Database initialization scripts
├── docker-compose.yml        # Full stack orchestration
├── pyproject.toml            # Modern Python project configuration
├── .pre-commit-config.yaml   # Pre-commit hooks
├── .github/workflows/        # CI/CD pipelines
├── Makefile                  # Development commands
└── DEVELOPMENT.md            # Detailed development guide
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose 20.10+
- Git
- (Optional) Python 3.10+ for local development

### Start All Services (5 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/HomeGuard-Monitor.git
cd HomeGuard-Monitor

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Initialize database (wait for services to be ready)
sleep 5
docker-compose exec -T backend alembic upgrade head
```

Wait for services to start:
- **PostgreSQL + TimescaleDB**: localhost:5432
- **Redis**: localhost:6379
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000

Access the application:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend**: http://localhost:3000
- **Backend Health**: http://localhost:8000/health

### Create First User & Device

```bash
# Register a user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-secure-password",
    "full_name": "Administrator"
  }'

# Set up monitoring agent
cd agents
pip install -r requirements.txt

# Register new device
python monitoring_agent.py --server http://localhost:8000 --register \
  --name "My Server" --description "Main production server"

# Start monitoring (replace 1 with device ID)
python monitoring_agent.py --server http://localhost:8000 --device-id 1
```

### Local Development

```bash
# Install Python dependencies
pip install -e "backend/[dev]"

# Setup pre-commit hooks (optional)
pre-commit install

# Run tests with coverage
make test-cov

# Start development server (with auto-reload)
make dev-server

# Start Celery worker in another terminal
make dev-celery

# Start Celery beat scheduler (optional)
make dev-celery-beat
```

## 📦 Installation

### Using Docker Compose (Recommended)

```bash
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Manual Setup

#### Backend

```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://user:password@localhost/homeguard
export REDIS_URL=redis://localhost:6379/0
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🛠️ Development

### Code Quality

Run all quality checks:
```bash
make all-checks
```

Individual tools:
```bash
make format    # Auto-format code with Black & isort
make lint      # Run Ruff linter
make type-check # Run MyPy type checker
make test      # Run test suite
make test-cov  # Run tests with coverage
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Common Development Tasks

```bash
make dev-server        # Start FastAPI dev server
make dev-celery        # Start Celery worker
make dev-celery-beat   # Start Celery beat scheduler
make docker-up         # Start Docker services
make docker-down       # Stop Docker services
make clean             # Clean cache files
```

See [Makefile](Makefile) for all available commands.

## 📚 Documentation

- [Development Guide](backend/DEVELOPMENT.md) - Complete guide for developers
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (Swagger)
- [Architecture & Design](docs/) - System design decisions

## 🤖 Monitoring Agents

The `agents/` directory contains system monitoring agents that collect metrics and send them to the backend.

### Agent Installation & Usage

```bash
cd agents
pip install -r requirements.txt

# Register a new device (get device ID)
python monitoring_agent.py --server http://localhost:8000 --register \
  --name "My Server" --description "Main production server" \
  --device-type server

# Start monitoring with device ID
python monitoring_agent.py --server http://localhost:8000 --device-id 1 --interval 30
```

### Agent Command Line Options

- `--server` (required): HomeGuard Monitor server URL
- `--device-id`: Device ID if already registered
- `--name`: Device name (required for registration)
- `--description`: Device description (optional)
- `--device-type`: server | iot_sensor | network_device | camera | other
- `--interval`: Metrics collection interval in seconds (default: 30)
- `--register`: Register device before starting monitoring

### Collected Metrics

The agent collects:
- **CPU**: Usage percentage, load averages
- **Memory**: Usage percentage, available bytes
- **Disk**: Usage percentage, free bytes
- **Network**: Bytes sent/received
- **Process Count**: Number of running processes
- **System**: Uptime, temperature sensors (if available)

## 🧪 Testing

The project includes comprehensive tests for all components.

### Test Coverage

- **API Endpoints**: Authentication, devices, metrics, alerts
- **Services**: Business logic, data processing, notifications
- **Models**: Data validation and constraints
- **Tasks**: Celery background jobs
- **Integration**: End-to-end workflows

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test category
make test-unit          # Unit tests only
make test-integration   # Integration tests only

# Run tests without slow tests
make test-fast

# Watch mode (auto-run on file changes)
make test-watch
```

### Test Configuration

Tests use environment variables from `.env.example`. For testing:

```bash
# Test environment
ENVIRONMENT=testing
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/homeguard_test
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=test-secret-key-minimum-32-characters-long
```

## 🚢 Deployment

### Production Security Checklist

1. **Generate Strong Secret Key**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Set Environment Variables**
   ```bash
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=<generated-secret-key>
   ALLOWED_HOSTS=["yourdomain.com"]
   DATABASE_URL=postgresql+asyncpg://user:strong-password@db-host/homeguard
   ```

3. **Database Security**
   - Use strong passwords
   - Enable SSL connections: add `?sslmode=require` to DATABASE_URL
   - Restrict network access to database

4. **Network Security**
   - Use reverse proxy (Nginx/Apache)
   - Enable HTTPS with SSL certificates
   - Hide internal ports (5432, 6379)
   - Configure firewall rules

5. **Reverse Proxy Configuration (Nginx)**

```nginx
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
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
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

### Docker Deployment

```bash
# Build image
docker build -t homeguard-monitor:latest -f backend/Dockerfile .

# Run with production settings
docker run -d \
  -e ENVIRONMENT=production \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e SECRET_KEY=<strong-key> \
  -p 8000:8000 \
  homeguard-monitor:latest
```

## 📚 Documentation

See individual guides for detailed information:
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (Swagger)
- [Architecture & Design](docs/) - System design decisions

## 🔧 Configuration

All configuration is managed through environment variables. See [.env.example](.env.example) for all available options.

Key variables:
```bash
ENVIRONMENT=development          # development, testing, production
DEBUG=true                       # Enable debug mode
DATABASE_URL=postgresql+...      # Database connection
REDIS_URL=redis://localhost      # Redis connection
SECRET_KEY=your-secret-key       # JWT secret (min 32 chars)
ALLOWED_HOSTS=localhost          # CORS allowed hosts
```

## 🔒 Security

- ✅ CORS configuration with explicit allowed origins
- ✅ Secure password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Input validation with Pydantic
- ✅ HTTPS support (configurable)
- ✅ Rate limiting (configurable)
- ✅ Security headers (configurable)
- ✅ Pre-commit security scanning with Bandit

Run security checks:
```bash
make security-check
```

## 📊 Performance

### Database Optimization
- Connection pooling (20 default)
- Strategic indexes on common queries
- Unique constraints to prevent duplicates
- Automatic connection health checks

### API Optimization
- GZIP compression for responses >1KB
- Pagination on list endpoints
- Async request handling
- Redis caching support

### Backend Performance
- Async/await for non-blocking I/O
- Connection pooling for database
- Celery for long-running tasks
- JSON serialization for logs

## 🧪 Testing

```bash
# Run all tests
pytest backend/tests -v

# With coverage report
pytest backend/ --cov=app --cov-report=html

# Only unit tests
pytest backend/ -m unit -v

# Only integration tests
pytest backend/ -m integration -v

# Watch mode (requires pytest-watch)
ptw backend/tests
```

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t homeguard-monitor:latest -f backend/Dockerfile .

# Run container
docker run -e DATABASE_URL=... -p 8000:8000 homeguard-monitor:latest
```

### Cloud Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions for:
- AWS (ECS, RDS, ElastiCache)
- Google Cloud (Cloud Run, Cloud SQL)
- Azure (App Service, Database for PostgreSQL)
- DigitalOcean (Droplets, Managed Database)

## 📊 Monitoring & Metrics

- Prometheus metrics exposed at `/metrics`
- Structured JSON logging for better observability
- Performance monitoring with custom metrics
- Database query logging (configurable)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters (`make all-checks`)
5. Commit with clear messages
6. Push to the branch
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- 📖 **Documentation**: [Development Guide](backend/DEVELOPMENT.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/HomeGuard-Monitor/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/HomeGuard-Monitor/discussions)

## 🎯 Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Advanced metrics visualization with charts
- [ ] Mobile app (React Native)
- [ ] Kubernetes deployment support
- [ ] Multi-tenant support
- [ ] Machine learning-based anomaly detection
- [ ] Custom notification integrations
- [ ] API rate limiting per user
- [ ] Audit logging for compliance
- [ ] Dark mode for frontend

## 🙏 Acknowledgments

Built with modern Python and JavaScript best practices in mind.

---

**Made with ❤️ for monitoring and alerting**
