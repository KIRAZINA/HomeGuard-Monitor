# HomeGuard Monitor - Quick Start Guide

## Overview

HomeGuard Monitor is a comprehensive monitoring and alerting system for personal servers and IoT devices. This guide will help you get it running quickly.

## Prerequisites

- Docker and Docker Compose
- Git

## Quick Start

1. **Clone and Start Services**
   ```bash
   git clone <repository-url>
   cd HomeGuard-Monitor
   docker-compose up -d
   ```

2. **Wait for Services to Start**
   - PostgreSQL + TimescaleDB: `localhost:5432`
   - Redis: `localhost:6379`
   - Backend API: `http://localhost:8000`
   - Frontend: `http://localhost:3000` (when enabled)

3. **Create a User Account**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d '{
          "email": "admin@example.com",
          "password": "your-secure-password",
          "full_name": "Administrator"
        }'
   ```

4. **Set Up a Monitoring Agent**
   ```bash
   # Install agent dependencies
   cd agents
   pip install -r requirements.txt
   
   # Register a new device
   python monitoring_agent.py --server http://localhost:8000 --register \
        --name "My Server" --description "Main production server"
   
   # Start monitoring (use the device ID from registration)
   python monitoring_agent.py --server http://localhost:8000 --device-id 1
   ```

5. **Access the Dashboard**
   - Navigate to `http://localhost:3000`
   - Login with your credentials
   - View real-time metrics and device status

## Configuration

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/homeguard

# Security
SECRET_KEY=your-super-secret-key-change-this

# Notifications (optional)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
DISCORD_WEBHOOK_URL=your-discord-webhook-url
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Alert Rules

Create alert rules via the API or dashboard:

```bash
curl -X POST "http://localhost:8000/api/v1/alerts/rules" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "High CPU Usage",
       "metric_type": "cpu_usage_percent",
       "rule_type": "threshold",
       "severity": "warning",
       "threshold_value": 80,
       "comparison_operator": "gt",
       "notification_channels": ["email"]
     }'
```

## Architecture

- **Backend**: FastAPI with async SQLAlchemy
- **Database**: PostgreSQL + TimescaleDB for time-series data
- **Cache/Queue**: Redis for caching and Celery tasks
- **Frontend**: React with TypeScript
- **Agents**: Python scripts using psutil

## Monitoring Metrics

The agent automatically collects:
- CPU usage percentage
- Memory usage and available memory
- Disk usage and free space
- Network I/O statistics
- System uptime
- Process count
- Temperature sensors (if available)
- Load average (Linux/Unix)

## Alert Types

- **Threshold-based**: Trigger when metrics exceed/fall below values
- **Anomaly detection**: Trigger on unusual patterns using statistical analysis

## Notification Channels

- Email (SMTP)
- Telegram (Bot API)
- Discord (Webhooks)
- SMS (Twilio)

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Production Deployment

1. **Update Environment Variables**
   - Set strong secrets
   - Configure production database
   - Set up notification services

2. **Enable HTTPS**
   - Configure reverse proxy (nginx/caddy)
   - Update CORS settings

3. **Scale Services**
   - Multiple Celery workers
   - Database replication
   - Load balancing

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running: `docker ps`
   - Verify connection string in `.env`

2. **Agent Can't Connect**
   - Check backend is accessible: `curl http://localhost:8000/health`
   - Verify firewall settings

3. **No Metrics Showing**
   - Check agent is running and sending data
   - Verify device registration was successful

### Logs

```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs celery-worker
```

## Support

- Check the documentation in the `docs/` directory
- Review API docs at `http://localhost:8000/docs`
- Monitor system logs for errors

## Next Steps

- Configure additional notification channels
- Set up custom alert rules
- Add more devices to monitor
- Explore the API for integrations
- Configure data retention policies
