# Security Policy

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in HomeGuard Monitor, please report it responsibly.

### How to Report

**Do not** create a public GitHub issue for security vulnerabilities.

Instead:
1. Email your findings to security@homeguard-monitor.local
2. Include detailed information about the vulnerability
3. Provide proof of concept if possible
4. Allow reasonable time for a fix before public disclosure

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Your contact information

### Response Timeline

- **Initial Response:** Within 24 hours
- **Status Updates:** Every 72 hours
- **Fix Release:** As soon as technically feasible (typically 7-30 days)
- **Public Disclosure:** After patch is released or 90 days have passed

## Security Best Practices

### For Users

1. Keep the application and dependencies updated
2. Use strong, unique passwords
3. Enable HTTPS in production
4. Regularly backup your data
5. Monitor system logs for unauthorized access
6. Use the application in a secure network environment

### For Developers

- All contributions are scanned with Bandit security analyzer
- Type hints are mandatory (prevents many classes of bugs)
- Dependency updates are tracked and tested
- Security headers are configured in production
- SQL injection prevention via SQLAlchemy ORM
- CORS properly configured
- Rate limiting implemented

## Known Security Considerations

### Authentication
- Bearer token authentication via JWT
- Passwords hashed with bcrypt
- No credentials in code or .env files

### Database
- Connection pooling with proper SSL support
- No raw SQL queries (SQLAlchemy ORM)
- Prepared statements for all queries

### API
- CORS restricted to allowed origins
- Rate limiting on sensitive endpoints
- HTTPS required in production
- Input validation on all endpoints

## Responsible Disclosure

We are committed to:
- Taking all security reports seriously
- Responding promptly
- Providing fixes in a timely manner
- Crediting researchers (if desired)
- Not taking legal action against good-faith researchers

## Updates and Patches

Security patches are released as:
- Critical: Immediately
- High: Within 48 hours
- Medium: Within 1 week
- Low: With next release

## Dependencies

Regular security audits of dependencies are performed using:
- `npm audit` (frontend)
- `safety` (Python backend)
- `bandit` (Python code analysis)

Subscribe to security advisories for:
- Python packages: pyup.io
- npm packages: npm security advisories
