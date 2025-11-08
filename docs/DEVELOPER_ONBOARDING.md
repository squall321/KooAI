# Developer Onboarding Guide

Welcome to the KooAI project! This guide will help you set up your development environment and start contributing.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Architecture Overview](#architecture-overview)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.9+ | Primary language |
| Poetry | 1.5+ | Dependency management |
| Git | 2.30+ | Version control |
| Docker | 20.10+ | Containerization |
| PostgreSQL | 13+ | Database (optional, SQLite fallback) |
| Redis | 6+ | Caching & queues (optional) |

### Recommended Tools

- **IDE**: VS Code, PyCharm, or similar
- **API Testing**: Postman, Insomnia, or HTTPie
- **Database Client**: DBeaver, pgAdmin, or psql
- **Terminal**: iTerm2 (macOS), Windows Terminal, or tmux

### Required Skills

- Python 3.9+ (intermediate level)
- FastAPI or Flask experience
- SQL and database concepts
- Git and GitHub workflow
- REST API design
- Basic Docker knowledge

### Helpful Knowledge

- Computational Fluid Dynamics (CFD)
- LLM integration (OpenAI, Anthropic)
- PyVista/VTK for 3D visualization
- WebSocket programming
- Pytest testing framework

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/kooai/kooai.git
cd kooai

# 2. Install dependencies
poetry install

# 3. Set up environment
cp .env.example .env
# Edit .env with your settings

# 4. Run database migrations
poetry run alembic upgrade head

# 5. Start development server
poetry run uvicorn src.presentation.api.main:app --reload

# 6. Open browser
# http://localhost:8000/docs
```

You're ready to develop! 🚀

---

## Development Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/kooai/kooai.git
cd kooai
```

### 2. Install Poetry

**macOS/Linux:**
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

**Windows (PowerShell):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

**Verify installation:**
```bash
poetry --version
```

### 3. Install Python Dependencies

```bash
# Install all dependencies (including dev)
poetry install

# Install only production dependencies
poetry install --only main

# Activate virtual environment
poetry shell
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings
nano .env  # or vim, code, etc.
```

**Required environment variables:**

```bash
# Application
APP_NAME=KooAI
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kooai
# Or use SQLite for development
# DATABASE_URL=sqlite:///./kooai.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# LLM
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# File Storage
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=500

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### 5. Set Up Database

**Option A: PostgreSQL (Recommended for production-like development)**

```bash
# Install PostgreSQL
# macOS
brew install postgresql

# Ubuntu
sudo apt install postgresql

# Start PostgreSQL
# macOS
brew services start postgresql

# Ubuntu
sudo systemctl start postgresql

# Create database
createdb kooai

# Run migrations
poetry run alembic upgrade head
```

**Option B: SQLite (Quick start)**

```bash
# Just set DATABASE_URL in .env
DATABASE_URL=sqlite:///./kooai.db

# Run migrations
poetry run alembic upgrade head
```

### 6. Set Up Redis (Optional)

```bash
# Install Redis
# macOS
brew install redis

# Ubuntu
sudo apt install redis

# Start Redis
# macOS
brew services start redis

# Ubuntu
sudo systemctl start redis

# Test connection
redis-cli ping  # Should return PONG
```

### 7. Install Development Tools

```bash
# Code quality tools (included in pyproject.toml)
poetry install --with dev

# Pre-commit hooks
poetry run pre-commit install

# Verify installation
poetry run black --version
poetry run ruff --version
poetry run mypy --version
poetry run pytest --version
```

### 8. IDE Configuration

**VS Code (.vscode/settings.json):**

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.rulers": [88]
  }
}
```

**PyCharm:**

1. Open project
2. Settings → Project → Python Interpreter → Add → Poetry Environment
3. Settings → Tools → Black → Enable "Black on save"
4. Settings → Editor → Code Style → Python → Set line length to 88

### 9. Verify Setup

```bash
# Run tests
poetry run pytest

# Start server
poetry run uvicorn src.presentation.api.main:app --reload

# Open API docs
# http://localhost:8000/docs

# Health check
curl http://localhost:8000/api/v1/health
```

---

## Project Structure

```
kooai/
├── src/
│   ├── domain/               # Business logic & entities
│   │   ├── models/          # Domain models (User, Simulation, etc.)
│   │   ├── services/        # Business logic services
│   │   └── repositories/    # Repository interfaces
│   │
│   ├── infrastructure/       # External concerns
│   │   ├── database/        # Database connection & ORM
│   │   ├── llm/            # LLM clients (OpenAI, Anthropic)
│   │   ├── auth/           # Authentication & authorization
│   │   ├── file_processing/ # File upload & processing
│   │   ├── visualization/   # 3D rendering & charts
│   │   ├── tasks/          # Background tasks (Celery)
│   │   └── config/         # Configuration management
│   │
│   └── presentation/         # API layer
│       └── api/
│           ├── routes/      # FastAPI route handlers
│           ├── dependencies/ # Dependency injection
│           └── main.py      # Application entry point
│
├── tests/                    # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
│
├── docs/                     # Documentation
├── scripts/                  # Utility scripts
├── migrations/               # Database migrations (Alembic)
├── uploads/                  # Uploaded files (gitignored)
├── .env                      # Environment variables (gitignored)
├── .env.example             # Environment template
├── pyproject.toml           # Project dependencies
├── poetry.lock              # Locked dependencies
└── README.md                # Project overview
```

### Architecture Layers

```
┌─────────────────────────────────────┐
│      Presentation Layer             │  FastAPI routes, WebSocket, OpenAPI
├─────────────────────────────────────┤
│      Application Layer              │  Use cases, orchestration
├─────────────────────────────────────┤
│      Domain Layer                   │  Business logic, entities
├─────────────────────────────────────┤
│      Infrastructure Layer           │  Database, LLM, file storage, auth
└─────────────────────────────────────┘
```

**Key Principles:**
- **Dependency Inversion**: Domain doesn't depend on infrastructure
- **Separation of Concerns**: Each layer has a clear responsibility
- **Testability**: Business logic is isolated and easily testable
- **Flexibility**: Easy to swap implementations (e.g., change LLM provider)

---

## Architecture Overview

### Clean Architecture

KooAI follows Clean Architecture principles:

1. **Domain Layer** (innermost)
   - Business entities and logic
   - No external dependencies
   - Pure Python code

2. **Application Layer**
   - Use cases and orchestration
   - Depends only on domain layer
   - Implements business workflows

3. **Infrastructure Layer**
   - External services (database, LLM, storage)
   - Implements domain interfaces
   - Framework-specific code

4. **Presentation Layer** (outermost)
   - API routes and responses
   - Request validation
   - Error handling

### Key Components

#### 1. API Routes (`src/presentation/api/routes/`)

```python
# Example route handler
@router.post("/simulations/upload")
async def upload_simulation(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate
    # Process
    # Return response
    pass
```

#### 2. Domain Models (`src/domain/models/`)

```python
# Example domain model
class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    simulation_type = Column(String)
    status = Column(String)
    created_at = Column(DateTime)
```

#### 3. Services (`src/domain/services/`)

```python
# Example service
class SimulationService:
    def __init__(self, repository: SimulationRepository):
        self.repository = repository

    def create_simulation(self, data: SimulationCreate) -> Simulation:
        # Business logic here
        pass
```

#### 4. Infrastructure (`src/infrastructure/`)

```python
# Example infrastructure service
class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def analyze(self, prompt: str) -> str:
        # External API call
        pass
```

### Request Flow

```
HTTP Request
    ↓
FastAPI Route Handler (presentation)
    ↓
Dependency Injection (get_current_user, get_db)
    ↓
Service Call (domain/services)
    ↓
Repository/Infrastructure (database, LLM, etc.)
    ↓
Response Model (Pydantic)
    ↓
HTTP Response
```

---

## Development Workflow

### 1. Git Workflow

We use **Git Flow** with feature branches:

```bash
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 2. Make changes
# ... code, code, code ...

# 3. Commit changes (follow conventional commits)
git add .
git commit -m "feat: add streaming upload support"

# 4. Push to remote
git push origin feature/your-feature-name

# 5. Create Pull Request on GitHub
# ... wait for review ...

# 6. After approval, merge to main
# ... PR is merged ...

# 7. Delete feature branch
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

### 2. Conventional Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Add or update tests
- `chore`: Build process, dependencies, etc.
- `perf`: Performance improvements

**Examples:**
```bash
feat(auth): add JWT refresh token support

fix(upload): handle large file uploads correctly

docs(api): update authentication documentation

test(llm): add streaming analysis tests

refactor(database): simplify session management
```

### 3. Branch Naming

- Feature: `feature/description`
- Bugfix: `fix/description`
- Hotfix: `hotfix/description`
- Documentation: `docs/description`
- Refactoring: `refactor/description`

### 4. Pull Request Process

1. **Create PR** with descriptive title and description
2. **Link Issues** if applicable (#123)
3. **Request Reviewers** (at least 1 reviewer required)
4. **Ensure CI Passes** (tests, linting, type checking)
5. **Address Review Comments**
6. **Squash and Merge** when approved

**PR Template:**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

---

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

- **Line Length**: 88 characters (Black default)
- **Quotes**: Double quotes for strings
- **Imports**: Organized by stdlib, third-party, local
- **Type Hints**: Required for all functions
- **Docstrings**: Google style

### Code Quality Tools

```bash
# Format code (auto-fixes)
poetry run black .

# Lint code (auto-fix some issues)
poetry run ruff --fix .

# Type checking
poetry run mypy src/

# All checks
poetry run black . && poetry run ruff --fix . && poetry run mypy src/
```

### Type Hints

**Always use type hints:**

```python
# Good ✅
def upload_file(file: UploadFile, user_id: str) -> Simulation:
    pass

async def analyze_simulation(
    simulation_id: str,
    options: AnalysisOptions
) -> AnalysisResult:
    pass

# Bad ❌
def upload_file(file, user_id):
    pass
```

### Docstrings

**Use Google-style docstrings:**

```python
def calculate_reynolds_number(
    velocity: float,
    length: float,
    kinematic_viscosity: float
) -> float:
    """
    Calculate Reynolds number for flow analysis.

    Args:
        velocity: Flow velocity in m/s
        length: Characteristic length in meters
        kinematic_viscosity: Kinematic viscosity in m²/s

    Returns:
        Reynolds number (dimensionless)

    Raises:
        ValueError: If kinematic_viscosity is zero

    Example:
        >>> calculate_reynolds_number(10.0, 1.0, 1.5e-5)
        666666.67
    """
    if kinematic_viscosity == 0:
        raise ValueError("Kinematic viscosity cannot be zero")

    return (velocity * length) / kinematic_viscosity
```

### Error Handling

**Use specific exceptions:**

```python
# Good ✅
from fastapi import HTTPException, status

@router.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str, db: Session = Depends(get_db)):
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()

    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found"
        )

    return simulation

# Bad ❌
@router.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str, db: Session = Depends(get_db)):
    simulation = db.query(Simulation).filter(Simulation.id == simulation_id).first()

    if not simulation:
        return {"error": "Not found"}  # Don't do this!
```

### Dependency Injection

**Use FastAPI's Depends():**

```python
# Good ✅
@router.post("/simulations/upload")
async def upload_simulation(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service)
):
    # Use injected dependencies
    pass

# Bad ❌
@router.post("/simulations/upload")
async def upload_simulation(file: UploadFile):
    # Don't create dependencies inside route handlers
    db = SessionLocal()
    llm_service = LLMService(api_key=settings.OPENAI_API_KEY)
    pass
```

---

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
│
├── integration/             # Tests with external dependencies
│   ├── test_database.py
│   ├── test_llm.py
│   └── test_file_upload.py
│
└── e2e/                    # End-to-end workflow tests
    └── test_complete_workflow.py
```

### Writing Tests

**Use pytest fixtures:**

```python
import pytest
from fastapi.testclient import TestClient
from src.presentation.api.main import app

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)

@pytest.fixture
def test_user(db):
    """Create test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("password")
    )
    db.add(user)
    db.commit()
    return user

def test_upload_simulation(client, test_user):
    """Test simulation upload."""
    # Login
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password"
    })
    token = response.json()["access_token"]

    # Upload
    with open("tests/fixtures/test_simulation.vtk", "rb") as f:
        response = client.post(
            "/api/v1/simulations/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": f}
        )

    assert response.status_code == 200
    assert "simulation_id" in response.json()
```

### Test Coverage

```bash
# Run tests with coverage
poetry run pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Coverage targets:**
- Overall: > 80%
- Critical paths: 100% (auth, file upload, data processing)
- New features: > 90%

### Running Tests

```bash
# All tests
poetry run pytest

# Specific test file
poetry run pytest tests/unit/test_models.py

# Specific test
poetry run pytest tests/unit/test_models.py::test_user_creation

# With verbose output
poetry run pytest -v

# With print statements
poetry run pytest -s

# Stop at first failure
poetry run pytest -x

# Run only failed tests
poetry run pytest --lf

# Parallel execution
poetry run pytest -n auto
```

---

## Debugging

### VS Code Debugger

**`.vscode/launch.json`:**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.presentation.api.main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Python: Current Test File",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "${file}",
        "-v"
      ]
    }
  ]
}
```

### Logging

**Use structured logging:**

```python
import logging

logger = logging.getLogger(__name__)

def process_simulation(simulation_id: str):
    logger.info(f"Processing simulation {simulation_id}")

    try:
        # Process
        logger.debug("Simulation processing started")
        result = do_processing()
        logger.info(f"Simulation processed successfully: {result}")
        return result

    except Exception as e:
        logger.error(f"Error processing simulation {simulation_id}: {e}", exc_info=True)
        raise
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

### Debug Database Queries

```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or in .env
LOG_LEVEL=DEBUG
```

---

## Common Tasks

### Adding a New API Endpoint

1. **Create route handler** in `src/presentation/api/routes/`:

```python
# src/presentation/api/routes/simulations.py

@router.post("/simulations/{simulation_id}/export")
async def export_simulation(
    simulation_id: str,
    export_format: str = "vtk",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export simulation in specified format."""
    # Implementation
    pass
```

2. **Add tests**:

```python
# tests/integration/test_simulation_export.py

def test_export_simulation(client, test_user, test_simulation):
    response = client.post(
        f"/api/v1/simulations/{test_simulation.id}/export",
        headers={"Authorization": f"Bearer {token}"},
        params={"export_format": "vtk"}
    )

    assert response.status_code == 200
```

3. **Update documentation** (docstrings automatically show in OpenAPI)

### Adding a Database Model

1. **Create model** in `src/domain/models/`:

```python
# src/domain/models/analysis.py

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: f"ana_{uuid.uuid4().hex[:12]}")
    simulation_id = Column(String, ForeignKey("simulations.id"))
    analysis_type = Column(String)
    result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. **Create migration**:

```bash
poetry run alembic revision --autogenerate -m "add analysis table"
poetry run alembic upgrade head
```

3. **Add repository** (if needed):

```python
# src/domain/repositories/analysis_repository.py

class AnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, analysis: Analysis) -> Analysis:
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
```

### Adding a New Service

1. **Create service** in `src/infrastructure/`:

```python
# src/infrastructure/mesh_analysis/service.py

class MeshAnalysisService:
    """Analyze mesh quality and characteristics."""

    def analyze_quality(self, mesh_file: Path) -> MeshQuality:
        """Analyze mesh quality metrics."""
        # Implementation
        pass
```

2. **Add dependency**:

```python
# src/presentation/api/dependencies.py

def get_mesh_analysis_service() -> MeshAnalysisService:
    return MeshAnalysisService()
```

3. **Use in routes**:

```python
@router.post("/simulations/{simulation_id}/mesh-quality")
async def analyze_mesh_quality(
    simulation_id: str,
    mesh_service: MeshAnalysisService = Depends(get_mesh_analysis_service)
):
    quality = mesh_service.analyze_quality(mesh_file)
    return quality
```

### Running Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history

# View current version
poetry run alembic current
```

---

## Troubleshooting

### Common Issues

#### 1. Poetry Install Fails

```bash
# Clear cache
poetry cache clear pypi --all

# Update poetry
poetry self update

# Retry
poetry install
```

#### 2. Database Connection Error

```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### 3. Import Errors

```bash
# Make sure you're in poetry shell
poetry shell

# Or use poetry run
poetry run python -c "import src"

# Check PYTHONPATH
echo $PYTHONPATH
```

#### 4. Tests Fail

```bash
# Run with verbose output
poetry run pytest -v -s

# Check test database is clean
poetry run alembic downgrade base
poetry run alembic upgrade head

# Clear pytest cache
rm -rf .pytest_cache
```

#### 5. Port Already in Use

```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
kill -9 $(lsof -ti:8000)

# Or use different port
poetry run uvicorn src.presentation.api.main:app --port 8001
```

### Getting Help

- **Documentation**: Check `/docs` folder
- **API Docs**: http://localhost:8000/docs
- **Team Chat**: Slack #kooai-dev
- **GitHub Issues**: For bugs and feature requests
- **Architecture Questions**: Ask in team meetings

---

## Next Steps

Now that you're set up, here are some good first tasks:

1. **Read the codebase**: Start with `src/presentation/api/main.py`
2. **Run the test suite**: `poetry run pytest`
3. **Pick a "good first issue"**: Check GitHub issues with this label
4. **Set up your IDE**: Configure linting and formatting
5. **Review open PRs**: See what others are working on
6. **Join team standup**: Meet the team!

Welcome to the team! 🎉

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for project history.
