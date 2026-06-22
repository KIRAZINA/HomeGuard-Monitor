# HomeGuard Monitor

A monitoring and alerting system for personal servers and IoT devices. Built with FastAPI, PostgreSQL, Redis, Celery, and React.

Status: [CI/CD Pipeline](https://github.com/KIRAZINA/HomeGuard-Monitor/actions) | [codecov](https://codecov.io/gh/KIRAZINA/HomeGuard-Monitor)

## Features

- Device monitoring with metric collection via agents
- Custom alert rules with threshold and anomaly detection
- Multi-channel notifications (Telegram, Discord, Email, SMS)
- Time-series metric storage with aggregation
- Interactive React dashboard with real-time updates (WebSocket + React Query)
- Async background tasks via Celery
- Rate limiting per endpoint
- Multi-tenant architecture (user-device ownership)
- Agent API key authentication for IoT devices
- JWT-based user authentication
- Docker Compose deployment

## Quick Start

```
# Clone
git clone https://github.com/KIRAZINA/HomeGuard-Monitor.git
cd HomeGuard-Monitor

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Initialize database (wait for services to be ready)
sleep 5
docker-compose exec -T backend alembic upgrade head
```

Services:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Create First User

```
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-secure-password", "full_name": "Administrator"}'
```

### Register Device and Start Agent

```
cd agents
pip install -r requirements.txt

# Register a new device (this returns an api_key)
python monitoring_agent.py --server http://localhost:8000 --register \
  --name "My Server" --description "Main production server"

# Start monitoring with device ID and optional API key
python monitoring_agent.py --server http://localhost:8000 --device-id 1 --interval 30

# Or use the api_key returned during registration
python monitoring_agent.py --server http://localhost:8000 --device-id 1 --api-key <key>
```

## Project Structure

```
HomeGuard-Monitor/
  backend/
    app/
      api/v1/endpoints/   # FastAPI route handlers (auth, devices, metrics, alerts)
      core/               # Configuration, database, auth deps, rate limiting, WebSocket
      models/             # SQLAlchemy ORM models
      schemas/            # Pydantic request/response validation
      services/           # Business logic layer
      tasks/              # Celery background tasks (alerting, data processing)
    tests/
  frontend/
    src/
      api/                # API client with axios
      components/         # React components (Dashboard, AlertNotification, Login)
      hooks/              # useWebSocket hook
  agents/                 # Monitoring agent scripts (Python)
  docker-compose.yml
```

## Architecture

### Backend (FastAPI)

The API uses JWT bearer tokens for user authentication and X-Agent-API-Key headers for agent authentication. Protected endpoints verify the current user via the `get_current_active_user` dependency. The `/metrics/ingest` endpoint authenticates agents via their API key and overrides the device_id from the authenticated device.

Rate limiting is applied via middleware with per-endpoint limits defined in `EndpointRateLimiter`. Response headers include X-RateLimit-Limit, X-RateLimit-Remaining, and X-RateLimit-Reset.

Real-time alerts are pushed to connected WebSocket clients via Redis pub/sub. The `ConnectionManager` in `core/ws.py` subscribes to a Redis "alerts" channel and broadcasts messages to all connected browser clients.

Celery tasks use a separate synchronous SQLAlchemy engine (`SyncSessionLocal`) instead of the async engine to avoid event-loop conflicts. Tasks are defined in `tasks/alerting.py` (evaluate alert rules, threshold/anomaly detection) and `tasks/data_processing.py` (cleanup old metrics, aggregate metrics).

Multi-tenancy is enforced at the service layer. Every device query filters by `user_id` so users only see their own devices.

### Frontend (React)

The dashboard uses React Query (`@tanstack/react-query`) for data fetching with automatic re-fetch intervals (30s for devices, 15s for metrics). Mutations (create device, ingest metric) use `useMutation` and invalidate relevant queries on success.

A custom `useWebSocket` hook connects to `ws://host/api/v1/alerts/ws?token=<jwt>` and displays incoming alerts via the `AlertNotification` component at the top of the page. The hook auto-reconnects with a 5-second backoff on disconnect.

### Agent

The monitoring agent collects CPU, memory, disk, network, and system metrics and sends them to the backend via `POST /api/v1/metrics/ingest` with the `X-Agent-API-Key` header. The agent can register itself (returns device ID and API key) before starting collection.

## Configuration

All configuration is managed through environment variables. See `.env.example` for all options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT signing key (min 32 characters)
- `ENVIRONMENT` - development, testing, or production
- `ALLOWED_HOSTS` - CORS allowed origins

## Development

### Running locally

Backend:
```
cd backend
pip install -r requirements.txt -r requirements-test.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:
```
cd frontend
npm install
npm run dev
```

### Running tests

```
cd backend
python -m pytest tests/ -v
python -m pytest tests/ --cov=app
```

### Code quality

```
cd backend
ruff check .
mypy app/
black --check .
```

## Deployment

### Docker

```
docker build -t homeguard-monitor:backend -f backend/Dockerfile .
docker build -t homeguard-monitor:frontend -f frontend/Dockerfile .
docker-compose up -d
```

### Production checklist

1. Generate a strong SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Set ENVIRONMENT=production and DEBUG=false
3. Enable HTTPS with a reverse proxy (Nginx)
4. Restrict database access to the application only
5. Configure rate limits for production traffic levels
6. Rotate SECRET_KEY periodically

## License

MIT License - see LICENSE file.

## Support

- Issues: https://github.com/KIRAZINA/HomeGuard-Monitor/issues
- Discussions: https://github.com/KIRAZINA/HomeGuard-Monitor/discussions
