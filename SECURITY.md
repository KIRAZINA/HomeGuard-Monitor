# Security Policy

## Reporting a Vulnerability

Do not create a public GitHub issue for security vulnerabilities.

Instead, open a GitHub Security Advisory at https://github.com/KIRAZINA/HomeGuard-Monitor/security/advisories

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Contact information

Response timeline:
- Initial response within 24 hours
- Status updates every 72 hours
- Fix released as soon as feasible (typically 7-30 days)

## Security Features

- JWT bearer token authentication for users
- X-Agent-API-Key header authentication for IoT agents
- Rate limiting per endpoint with configurable limits
- CORS restricted to allowed origins
- Password hashing with bcrypt
- SQL injection prevention via SQLAlchemy ORM
- Input validation with Pydantic schemas
- Multi-tenant isolation (user scoping on all queries)
- HTTPS support (configure via reverse proxy)

## Best Practices for Users

- Keep the application and dependencies updated
- Use strong, unique passwords
- Enable HTTPS in production
- Regularly backup your data
- Monitor system logs for unauthorized access
- Restrict network access to the application

## Dependencies

Regular security audits:
- `npm audit` for frontend
- `safety` for Python backend
- `bandit` for Python code analysis
