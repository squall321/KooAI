# CI/CD Guide

Complete guide for Continuous Integration and Continuous Deployment of KooAI.

## Table of Contents

1. [Overview](#overview)
2. [GitHub Actions Workflows](#github-actions-workflows)
3. [Apptainer Images](#apptainer-images)
4. [Release Process](#release-process)
5. [Deployment](#deployment)
6. [Pre-commit Hooks](#pre-commit-hooks)
7. [Troubleshooting](#troubleshooting)

---

## Overview

KooAI uses GitHub Actions for automated CI/CD with focus on HPC environments using Apptainer.

### CI/CD Pipeline

```
┌──────────────┐
│  Push/PR     │
└──────┬───────┘
       │
       ├─────▶ test.yml         (Unit & Integration Tests)
       ├─────▶ quality.yml      (Linting, Type Checking)
       │
       ▼
┌──────────────┐
│  Tag Release │
└──────┬───────┘
       │
       ├─────▶ release.yml      (Build Python Package)
       ├─────▶ apptainer.yml    (Build SIF Images)
       │
       ▼
┌──────────────┐
│  Deploy      │
└──────────────┘
```

---

## GitHub Actions Workflows

### 1. test.yml - Automated Testing

**Triggers**: Push, Pull Request

**Jobs**:
- Unit tests (Python 3.10, 3.11, 3.12)
- Integration tests (with PostgreSQL, Redis)
- Example script tests
- Security scanning
- Code coverage

**Usage**:
```bash
# Runs automatically on PR
# View results in PR checks
```

### 2. quality.yml - Code Quality

**Triggers**: Push, Pull Request

**Jobs**:
- Linting (flake8, pylint)
- Type checking (mypy)
- Code complexity analysis
- Dependency checks
- Documentation coverage

**Local execution**:
```bash
# Run flake8
flake8 src/ --max-line-length=100

# Run black
black src/ tests/

# Run isort
isort src/ tests/

# Run mypy
mypy src/
```

### 3. apptainer.yml - Container Builds

**Triggers**: Push to main, Tags

**Jobs**:
- Build minimal image (~500MB)
- Build standard image (~1.5GB)
- Build full image (~4GB)
- HPC compatibility tests
- Upload to release

**Local build**:
```bash
# Build standard image
sudo apptainer build --fakeroot kooai-standard.sif containers/kooai.def

# Or use script
./scripts/build-apptainer.sh standard
```

### 4. release.yml - Release Automation

**Triggers**: Git tags (v*.*.*)

**Jobs**:
- Build Python package (wheel, sdist)
- Create GitHub Release
- Upload to PyPI
- Generate changelog

**Create release**:
```bash
# Tag and push
git tag v1.2.3
git push origin v1.2.3

# Or use script
./scripts/release.sh v1.2.3
```

### 5. deploy.yml - Deployment

**Triggers**: Manual (workflow_dispatch)

**Usage**:
```bash
# Deploy via GitHub UI:
# Actions → Deploy → Run workflow → Select environment
```

### 6. docs.yml - Documentation

**Triggers**: Push to main

**Jobs**:
- Build Sphinx documentation
- Generate API docs
- Deploy to GitHub Pages

---

## Apptainer Images

### Available Images

#### 1. kooai-minimal.sif (~500MB)
```bash
# Basic functionality only
apptainer run kooai-minimal.sif
```

**Includes**:
- FastAPI, Uvicorn
- SQLAlchemy, Alembic
- Basic dependencies

#### 2. kooai-standard.sif (~1.5GB)
```bash
# Recommended for most users
apptainer run kooai-standard.sif
```

**Includes**:
- All minimal packages
- VTK, PyVista (3D file support)
- HDF5 support

#### 3. kooai-full.sif (~4GB)
```bash
# Complete installation with AI/ML
apptainer run kooai-full.sif
```

**Includes**:
- All standard packages
- PyTorch, TensorFlow
- Advanced analysis tools

### Building Images Locally

```bash
# Build specific profile
./scripts/build-apptainer.sh minimal
./scripts/build-apptainer.sh standard
./scripts/build-apptainer.sh full

# Manual build
sudo apptainer build --fakeroot output.sif definition.def
```

### Using Images

#### Run API Server
```bash
apptainer run kooai-standard.sif

# With custom port
apptainer run --env PORT=9000 kooai-standard.sif

# With data mount
apptainer run --bind /data:/data kooai-standard.sif
```

#### Execute Commands
```bash
# Run Python script
apptainer exec kooai-standard.sif python your_script.py

# Interactive shell
apptainer shell kooai-standard.sif

# Check version
apptainer exec kooai-standard.sif python --version
```

### HPC Usage

```bash
# On HPC cluster (no root required)
apptainer exec --fakeroot kooai-standard.sif python script.py

# With Slurm
sbatch << EOF
#!/bin/bash
#SBATCH --job-name=kooai
#SBATCH --ntasks=1

apptainer run kooai-standard.sif
EOF
```

---

## Release Process

### Semantic Versioning

KooAI follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Incompatible API changes (1.0.0 → 2.0.0)
- **MINOR**: New features, backwards-compatible (1.0.0 → 1.1.0)
- **PATCH**: Bug fixes (1.0.0 → 1.0.1)

### Release Steps

#### 1. Prepare Release

```bash
# Update version in pyproject.toml
vim pyproject.toml

# Update CHANGELOG.md
vim CHANGELOG.md

# Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "chore: Prepare release v1.2.3"
git push
```

#### 2. Create Tag

```bash
# Create annotated tag
git tag -a v1.2.3 -m "Release v1.2.3"

# Push tag (triggers release workflow)
git push origin v1.2.3
```

#### 3. Verify Release

1. Check GitHub Actions (all jobs should pass)
2. Verify release created: https://github.com/your-org/KooAI/releases
3. Verify PyPI upload: https://pypi.org/project/kooai/
4. Download and test Apptainer images

### Automated Release Workflow

When tag is pushed:

1. **Build Package**: Creates wheel and source distribution
2. **Run Tests**: Full test suite
3. **Build Images**: All three Apptainer images
4. **Create Release**: GitHub Release with changelog
5. **Upload Assets**:
   - Python packages
   - Apptainer SIF files
   - Checksums
6. **Publish PyPI**: Upload to PyPI
7. **Notify**: Send notifications (Slack, email)

---

## Deployment

### Staging Deployment

```bash
# Via GitHub Actions
# 1. Go to Actions → Deploy
# 2. Select "staging" environment
# 3. Run workflow

# Manual deployment
ssh staging-server
cd /opt/kooai
git pull origin main
systemctl restart kooai
```

### Production Deployment

```bash
# Via GitHub Actions (requires approval)
# 1. Go to Actions → Deploy
# 2. Select "production" environment
# 3. Approve and run

# Manual deployment
ssh production-server
cd /opt/kooai
git fetch origin
git checkout v1.2.3  # Specific version
systemctl restart kooai

# Verify
curl https://api.example.com/health
```

### Rollback

```bash
# Quick rollback to previous version
ssh production-server
cd /opt/kooai
git checkout v1.2.2
systemctl restart kooai
```

---

## Pre-commit Hooks

### Setup

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Hooks Configured

1. **black**: Code formatting
2. **isort**: Import sorting
3. **flake8**: Linting
4. **trailing-whitespace**: Remove trailing spaces
5. **end-of-file-fixer**: Ensure newline at EOF
6. **check-yaml**: Validate YAML files
7. **check-added-large-files**: Prevent large file commits

### Manual Formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check linting
flake8 src/
```

---

## Dependency Updates

### Dependabot

Dependabot automatically creates PRs for:
- Python package updates (weekly)
- GitHub Actions updates (weekly)
- Security updates (daily)

### Manual Update

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all development dependencies
pip install --upgrade -e ".[dev]"

# Update pyproject.toml
vim pyproject.toml
```

---

## Troubleshooting

### Test Failures

**Problem**: Tests fail in CI

**Solutions**:
```bash
# Run tests locally
pytest tests/ -v

# Run specific test
pytest tests/unit/test_file.py::test_function

# Check coverage
pytest --cov=src tests/

# Run with same environment as CI
export USE_TEST_DB=true
pytest tests/
```

### Build Failures

**Problem**: Apptainer build fails

**Solutions**:
```bash
# Check definition file syntax
apptainer check containers/kooai.def

# Build with verbose output
sudo apptainer build --fakeroot -v output.sif definition.def

# Check logs
cat /var/log/apptainer/apptainer.log
```

### Release Failures

**Problem**: Release workflow fails

**Solutions**:
```bash
# Verify tag format
git tag -l

# Check pyproject.toml version
grep version pyproject.toml

# Test package build locally
python -m build
twine check dist/*

# Delete and recreate tag
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3
git tag v1.2.3
git push origin v1.2.3
```

### Pre-commit Issues

**Problem**: Pre-commit hooks fail

**Solutions**:
```bash
# Update hooks
pre-commit autoupdate

# Run specific hook
pre-commit run black --all-files

# Skip hooks (emergency only)
git commit --no-verify -m "message"
```

---

## Best Practices

### Git Workflow

1. **Feature branches**: Create from `develop`
2. **Commit messages**: Follow conventional commits
   ```
   feat: Add new feature
   fix: Fix bug
   docs: Update documentation
   test: Add tests
   ```
3. **Pull requests**: Required for `main` and `develop`
4. **Code review**: At least one approval

### Testing

1. **Write tests first** (TDD when possible)
2. **Maintain >80% coverage**
3. **Run tests locally before pushing**
4. **Add integration tests for new features**

### Releases

1. **Test thoroughly** in staging
2. **Update CHANGELOG.md**
3. **Use semantic versioning**
4. **Create detailed release notes**
5. **Announce releases** (Slack, email)

### Security

1. **Never commit secrets**
2. **Use GitHub Secrets for tokens**
3. **Review Dependabot PRs promptly**
4. **Run security scans regularly**

---

## GitHub Secrets Required

### Repository Secrets

- `PYPI_TOKEN`: PyPI upload token
- `TEST_PYPI_TOKEN`: TestPyPI upload token (optional)
- `SLACK_WEBHOOK_URL`: Slack notifications (optional)

### Setup Secrets

```bash
# In GitHub repo:
# Settings → Secrets and variables → Actions → New repository secret

# PyPI token:
# 1. Go to https://pypi.org/manage/account/token/
# 2. Create new API token
# 3. Add as PYPI_TOKEN secret
```

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Apptainer Documentation](https://apptainer.org/docs/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Semantic Versioning](https://semver.org/)

---

**Last Updated**: 2025-11-07
**Version**: 1.0
