# Contributing to HomeGuard Monitor

Thanks for your interest. This document covers how to contribute.

## Getting Started

Prerequisites:
- Python 3.10+
- Node.js 18+
- Docker and Docker Compose (optional)

Setup:
- Backend: `cd backend; pip install -r requirements.txt -r requirements-test.txt`
- Frontend: `cd frontend; npm install`
- Full stack: `docker-compose up -d`

## Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run the test suite: `cd backend; python -m pytest tests/ -v`
4. Run linters: `cd backend; ruff check .; mypy app/`
5. Commit with a clear message
6. Push and open a Pull Request

## Code Standards

### Python
- Use type hints everywhere
- Follow PEP 8 (100 character line limit)
- Use structlog for logging
- Write docstrings for all public functions

### TypeScript / React
- Use TypeScript strict mode
- Follow the existing ESLint configuration
- Use @tanstack/react-query for all data fetching
- Use the useWebSocket hook for real-time alerts

### Testing
- Write tests for new services and endpoints
- Use the fixtures in conftest.py (db_session, test_user, test_device, auth_headers)
- Update existing tests when changing signatures
- Run all tests before pushing

## Reporting Issues

Include:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- System information and logs

## License

By contributing, you agree your contributions will be licensed under the same license as the project.

## Questions

Open an issue with the `question` label.
