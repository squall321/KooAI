# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the KooAI project.

## Table of Contents

1. [Overview](#overview)
2. [Workflows](#workflows)
3. [Branch Strategy](#branch-strategy)
4. [Environment Setup](#environment-setup)
5. [Pipeline Stages](#pipeline-stages)
6. [Secrets Configuration](#secrets-configuration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

KooAI uses GitHub Actions for CI/CD automation. The pipeline includes:

- **Continuous Integration**: Automated testing, linting, and code quality checks
- **Continuous Deployment**: Automated Docker builds and deployments to staging/production
- **Release Management**: Automated versioning and GitHub releases
- **Security Scanning**: Vulnerability scanning and dependency audits

### Pipeline Architecture

```
┌──────────────────────────────────────────────────┐
│   Developer Push/PR                              │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│   CI Workflow                                    │
│   - Lint (Black, isort, Ruff)                   │
│   - Type Check (mypy)                            │
│   - Tests (pytest + coverage)                    │
│   - Security Scan (Bandit, Safety)              │
│   - Docker Build Test                            │
└────────────┬─────────────────────────────────────┘
             │ (On success)
             ▼
┌──────────────────────────────────────────────────┐
│   Code Quality Workflow                          │
│   - Code coverage report                         │
│   - Complexity analysis                          │
│   - Documentation check                          │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│   Docker Workflow (main/develop)                 │
│   - Build multi-arch images                      │
│   - Push to GHCR                                 │
│   - Vulnerability scan (Trivy)                   │
│   - Image testing                                │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│   Deploy Workflow                                │
│   - Deploy to staging (main branch)              │
│   - Deploy to production (tags)                  │
│   - Health checks & smoke tests                  │
└──────────────────────────────────────────────────┘
```

---

## Workflows

### 1. CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
1. **lint**: Code formatting and style checks
   - Black: Python code formatting
   - isort: Import sorting
   - Ruff: Fast Python linter

2. **type-check**: Static type analysis
   - mypy: Type checking

3. **test**: Unit and integration tests
   - Matrix: Python 3.11 and 3.12
   - Services: PostgreSQL, Redis
   - Coverage: pytest-cov with Codecov upload

4. **security**: Security scanning
   - Bandit: Python security linter
   - Safety: Dependency vulnerability checker

5. **build**: Docker image build test
   - Validates Dockerfile
   - Tests image build process

**Example:**
```yaml
# Runs on every push and PR
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
```

### 2. Docker Workflow (`docker.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Tags matching `v*.*.*`
- Pull requests
- Manual dispatch

**Jobs:**
1. **build-and-push**: Build and publish Docker images
   - Multi-architecture (amd64, arm64)
   - Push to GitHub Container Registry
   - Automated tagging (branch, version, SHA)
   - Build provenance attestation

2. **scan-image**: Security scanning
   - Trivy vulnerability scanner
   - Upload results to GitHub Security

3. **test-image**: Image validation
   - Pull and run image
   - Health check test
   - Image inspection

**Image Tags:**
- `main` → `latest`
- `develop` → `develop`
- `v1.2.3` → `1.2.3`, `1.2`, `1`, `latest`
- `feature-branch` → `feature-branch-<sha>`

**Example:**
```bash
# Pull latest image
docker pull ghcr.io/yourusername/kooai:latest

# Pull specific version
docker pull ghcr.io/yourusername/kooai:1.2.3
```

### 3. Deploy Workflow (`deploy.yml`)

**Triggers:**
- Push to `main` branch (staging)
- Tags matching `v*.*.*` (production)
- Manual dispatch with environment selection

**Jobs:**
1. **deploy-staging**: Deploy to staging environment
   - SSH to staging server
   - Pull latest images
   - Rolling update with health checks
   - Automatic rollback on failure

2. **deploy-production**: Deploy to production
   - Requires tag (e.g., `v1.0.0`)
   - Database backup before deployment
   - Zero-downtime rolling update
   - Smoke tests
   - Rollback capability

3. **kubernetes-deploy**: K8s deployment (optional)
   - Apply K8s manifests
   - Monitor rollout status

**Deployment Flow:**
```
Developer → Tag v1.0.0 → GitHub Release
                        ↓
                  Deploy Staging
                        ↓
                  Manual Approval
                        ↓
                  Deploy Production
                        ↓
                  Smoke Tests
                        ↓
                  Success/Rollback
```

**Example:**
```bash
# Create a release
git tag v1.0.0
git push origin v1.0.0

# Triggers production deployment
```

### 4. Code Quality Workflow (`code-quality.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests
- Weekly schedule (Monday 00:00 UTC)

**Jobs:**
1. **lint-and-format**: Multiple linters
   - Black, isort, Ruff, Flake8, Pylint

2. **type-checking**: Type analysis
   - mypy, pyright

3. **security-scan**: Security tools
   - Bandit, Safety, pip-audit

4. **dependency-review**: Dependency analysis
   - GitHub Dependency Review

5. **code-coverage**: Test coverage
   - Generate coverage reports
   - Comment on PRs with coverage delta

6. **complexity-check**: Code complexity
   - Radon: Cyclomatic complexity
   - Maintainability index

7. **documentation-check**: Docstring coverage
   - interrogate, pydocstyle

8. **code-metrics**: Advanced analysis
   - CodeQL: Semantic code analysis
   - SonarCloud (optional)

**Example PR Comment:**
```
📊 Code Coverage Report

Coverage: 85.3% (+2.1%)

New Files:
✅ src/new_module.py: 92% coverage
⚠️  src/another_module.py: 45% coverage (below 80% threshold)
```

### 5. Release Workflow (`release.yml`)

**Triggers:**
- Tags matching `v*.*.*`
- Manual dispatch

**Jobs:**
1. **validate-release**: Tag validation
   - Check tag format
   - Verify tag exists

2. **run-tests**: Full test suite
   - All tests must pass

3. **build-artifacts**: Create release artifacts
   - Python package (wheel, sdist)
   - Documentation

4. **build-docker**: Docker images
   - Multi-arch builds
   - Version-specific tags

5. **generate-changelog**: Automated changelog
   - Compare with previous tag
   - Generate commit list

6. **create-release**: GitHub Release
   - Create release with changelog
   - Attach artifacts
   - Generate release notes

7. **publish-pypi**: PyPI publication (optional)
   - Publish to Python Package Index

8. **notify-release**: Notifications
   - Slack/Discord/Email alerts
   - GitHub Discussion post

**Release Process:**
```bash
# 1. Update version
echo "1.0.0" > VERSION

# 2. Commit and tag
git add VERSION
git commit -m "Bump version to 1.0.0"
git tag -a v1.0.0 -m "Release version 1.0.0"

# 3. Push tag
git push origin v1.0.0

# 4. Workflow creates GitHub release automatically
```

---

## Branch Strategy

### Main Branches

- **`main`**: Production-ready code
  - Protected branch
  - Requires PR reviews
  - Auto-deploys to staging
  - Source for production releases

- **`develop`**: Development integration branch
  - Latest development changes
  - Feature branches merge here first
  - CI runs on every push

### Feature Branches

```
feature/<feature-name>
bugfix/<bug-name>
hotfix/<issue-number>
```

**Workflow:**
```bash
# 1. Create feature branch from develop
git checkout -b feature/new-parser develop

# 2. Make changes and commit
git commit -m "feat: add HDF5 parser support"

# 3. Push and create PR
git push origin feature/new-parser

# 4. CI runs automatically on PR
# 5. After approval, merge to develop
# 6. Delete feature branch
```

### Release Branches

```
release/v<major>.<minor>.<patch>
```

**Release Workflow:**
```bash
# 1. Create release branch from develop
git checkout -b release/v1.0.0 develop

# 2. Bump version, update changelog
# 3. Create PR to main
# 4. After merge, tag main
git checkout main
git tag v1.0.0
git push origin v1.0.0

# 5. Merge back to develop
git checkout develop
git merge main
```

---

## Environment Setup

### GitHub Repository Settings

#### 1. Secrets Configuration

Navigate to **Settings → Secrets and variables → Actions**

**Required Secrets:**

```bash
# Deployment
DEPLOY_SSH_KEY          # SSH private key for deployment
STAGING_HOST            # Staging server hostname
PRODUCTION_HOST         # Production server hostname
DEPLOY_USER             # SSH username

# Container Registry
GITHUB_TOKEN            # Automatically provided by GitHub

# Optional
PYPI_API_TOKEN          # For PyPI publication
SLACK_WEBHOOK_URL       # Slack notifications
DISCORD_WEBHOOK_URL     # Discord notifications
SONAR_TOKEN             # SonarCloud integration
```

#### 2. Environment Configuration

Create environments: **Settings → Environments**

**Staging Environment:**
- Deployment branch: `main`
- No required reviewers
- Environment secrets:
  - `STAGING_HOST`
  - `STAGING_DB_PASSWORD`

**Production Environment:**
- Deployment branch: Tags (`v*`)
- Required reviewers: 1-2 team members
- Environment secrets:
  - `PRODUCTION_HOST`
  - `PRODUCTION_DB_PASSWORD`
  - `PRODUCTION_SECRET_KEY`

#### 3. Branch Protection Rules

**Main Branch:**
- ✅ Require pull request reviews (1 approval)
- ✅ Require status checks to pass
  - CI / test
  - CI / lint
  - CI / build
- ✅ Require branches to be up to date
- ✅ Include administrators
- ✅ Require linear history

**Develop Branch:**
- ✅ Require status checks to pass
  - CI / test
  - CI / lint

### Local Development Setup

```bash
# 1. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 2. Configure git
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Run tests locally before pushing
pytest
black src tests
isort src tests
ruff check src tests
```

---

## Pipeline Stages

### Stage 1: Code Quality Checks (< 2 minutes)

```yaml
Jobs: lint, type-check
Tools: black, isort, ruff, mypy
Fail Fast: Yes
```

**What it does:**
- Ensures code follows style guidelines
- Validates type hints
- Catches common errors

### Stage 2: Testing (< 5 minutes)

```yaml
Jobs: test
Matrix: Python 3.11, 3.12
Services: PostgreSQL, Redis
Coverage: Required
```

**What it does:**
- Runs 73+ unit and integration tests
- Measures code coverage
- Uploads coverage to Codecov

### Stage 3: Security Scanning (< 3 minutes)

```yaml
Jobs: security
Tools: bandit, safety, pip-audit
Severity: Moderate+
```

**What it does:**
- Scans code for security vulnerabilities
- Checks dependencies for known CVEs
- Reports to GitHub Security tab

### Stage 4: Docker Build (< 10 minutes)

```yaml
Jobs: build-and-push
Platforms: linux/amd64, linux/arm64
Registry: ghcr.io
Cache: GitHub Actions cache
```

**What it does:**
- Builds multi-architecture Docker images
- Pushes to container registry
- Generates SBOM and provenance

### Stage 5: Deployment (< 5 minutes)

```yaml
Jobs: deploy-staging, deploy-production
Strategy: Rolling update
Health Check: Required
Rollback: Automatic on failure
```

**What it does:**
- SSHs to target server
- Pulls latest images
- Updates services with zero downtime
- Runs health checks
- Rolls back on failure

---

## Secrets Configuration

### Setting Up SSH Keys

```bash
# 1. Generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions" -f deploy_key

# 2. Add public key to deployment server
ssh-copy-id -i deploy_key.pub user@server

# 3. Add private key to GitHub Secrets
# Settings → Secrets → New secret
# Name: DEPLOY_SSH_KEY
# Value: (paste contents of deploy_key)
```

### Container Registry Authentication

GitHub Actions automatically has access to GitHub Container Registry using `GITHUB_TOKEN`.

**Manual login:**
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### Database Credentials

Store in GitHub Secrets:
```bash
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
SECRET_KEY=<generated-secret-key>
```

Generate secure keys:
```bash
# Secret key
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Password
openssl rand -base64 32
```

---

## Best Practices

### 1. Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: add HDF5 parser support
fix: resolve memory leak in VAE model
docs: update deployment guide
test: add tests for spatial analysis
refactor: simplify mesh operations
chore: update dependencies
```

**Benefits:**
- Automated changelog generation
- Semantic versioning
- Better git history

### 2. Pull Requests

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
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

### 3. Testing

```bash
# Run tests locally before pushing
pytest -v

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/simulation/test_simulation.py

# Fast tests only
pytest -m "not slow"
```

### 4. Docker Best Practices

```dockerfile
# Multi-stage builds
FROM python:3.11-slim as builder
# ... build dependencies

FROM python:3.11-slim
# ... copy artifacts

# Non-root user
USER kooai

# Health check
HEALTHCHECK CMD curl http://localhost:8000/health
```

### 5. Version Management

**Semantic Versioning:**
```
MAJOR.MINOR.PATCH

1.0.0 → 1.0.1 (patch - bug fix)
1.0.1 → 1.1.0 (minor - new feature)
1.1.0 → 2.0.0 (major - breaking change)
```

---

## Troubleshooting

### Common Issues

#### 1. CI Tests Failing

**Problem:** Tests pass locally but fail in CI

**Solutions:**
```bash
# Check Python version
python --version  # Should match CI (3.11+)

# Check dependencies
pip list

# Run tests with same settings as CI
pytest tests/ -v --override-ini="addopts=-ra -q --strict-markers"

# Check environment variables
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
```

#### 2. Docker Build Fails

**Problem:** Docker build works locally but fails in CI

**Solutions:**
```bash
# Check Dockerfile path
ls -la Dockerfile

# Test build locally
docker build -t kooai:test .

# Check .dockerignore
cat .dockerignore

# Build with same platform as CI
docker buildx build --platform linux/amd64 -t kooai:test .
```

#### 3. Deployment Fails

**Problem:** Deployment workflow fails to connect

**Solutions:**
```bash
# Verify SSH key
ssh-add deploy_key
ssh user@server "echo Connection successful"

# Check secrets
# Settings → Secrets → Verify all required secrets exist

# Test deployment manually
ssh user@server "cd /opt/kooai && docker-compose ps"
```

#### 4. Permission Denied

**Problem:** GitHub Actions can't push to registry

**Solutions:**
```yaml
# Ensure correct permissions in workflow
permissions:
  contents: read
  packages: write

# Verify GitHub token has package permissions
# Settings → Actions → General → Workflow permissions
```

### Debugging Workflows

**Enable debug logging:**
```bash
# Settings → Secrets
# Add secret: ACTIONS_STEP_DEBUG = true
```

**Check workflow logs:**
1. Go to **Actions** tab
2. Select failing workflow run
3. Click on failed job
4. Expand failed step
5. Check error messages

**Test workflow locally with `act`:**
```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash

# Run workflow locally
act -j test  # Run test job
act -j build  # Run build job
```

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Check README.md and DEPLOYMENT.md
- **Workflow Logs**: Check detailed logs in Actions tab

---

## Maintenance

### Regular Tasks

**Weekly:**
- ✅ Review security alerts
- ✅ Update dependencies
- ✅ Check workflow success rate

**Monthly:**
- ✅ Review and update workflows
- ✅ Clean up old Docker images
- ✅ Audit secrets and permissions

**Quarterly:**
- ✅ Review CI/CD performance
- ✅ Update documentation
- ✅ Evaluate new tools and practices

### Monitoring

**Metrics to track:**
- CI success rate (target: >95%)
- Average CI duration (target: <10 min)
- Deployment frequency
- Mean time to recovery (MTTR)
- Change failure rate

**Tools:**
- GitHub Actions insights
- Codecov coverage trends
- Docker Hub image pulls
- Deployment logs

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Codecov Documentation](https://docs.codecov.com/)

---

## License

This CI/CD pipeline configuration is part of the KooAI project and is licensed under the MIT License.
