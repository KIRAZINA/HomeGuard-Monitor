# Contributing to HomeGuard Monitor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional)
- PostgreSQL 14+ (for production)
- Redis 7+ (for caching/tasks)

### Setup Development Environment

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-test.txt
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Full Stack with Docker:**
```bash
docker-compose up -d
```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow PEP 8 for Python
   - Use TypeScript for frontend
   - Write tests for new features
   - Update documentation

3. **Run tests**
   ```bash
   # Backend
   cd backend
   python -m pytest --cov=app
   
   # Frontend
   cd frontend
   npm run build
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: Add new monitoring feature"
   ```
   Use conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `style:`, `chore:`

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Standards

### Python
- Use type hints throughout
- Follow PEP 8 style guide
- Maximum line length: 100 characters
- Use structured logging with `structlog`
- Write docstrings for all public functions

### TypeScript/React
- Use TypeScript strict mode
- Follow ESLint configuration
- Write clear component descriptions
- Use semantic HTML

### Testing
- Minimum 70% code coverage required
- Write unit tests for services
- Write integration tests for APIs
- Use fixtures for test data

## Building Documentation

```bash
# Edit markdown files in docs/
# Use Clear, concise English
# Include code examples where applicable
```

## Reporting Issues

Create an issue with:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- System information
- Screenshots/logs if applicable

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

Open an issue with the `question` label or reach out to the maintainers.

Thank you for contributing!
