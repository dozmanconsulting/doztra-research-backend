# Contributing to Doztra Auth Service

Thank you for your interest in contributing to the Doztra Auth Service! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Pull Request Process](#pull-request-process)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Documentation](#documentation)
8. [Issue Reporting](#issue-reporting)
9. [Feature Requests](#feature-requests)
10. [Contact](#contact)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others when contributing to this project.

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Docker (optional)

### Setting Up the Development Environment

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/doztra-auth-service.git
   cd doztra-auth-service
   ```

3. Set up the development environment using our setup script:
   ```bash
   ./setup_dev.sh
   ```
   
   This script will:
   - Create a virtual environment
   - Install dependencies
   - Set up the database
   - Configure pre-commit hooks
   
   Alternatively, you can use our Makefile:
   ```bash
   make setup
   ```

4. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

5. Run the application:
   ```bash
   python run.py --reload
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/your-bugfix-name
   ```

2. Make your changes.

3. Run the linters and formatters:
   ```bash
   make lint
   make format
   ```

4. Run the tests:
   ```bash
   make test
   ```

5. Commit your changes:
   ```bash
   git commit -m "Your descriptive commit message"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a Pull Request from your fork to the main repository.

## Pull Request Process

1. Ensure your code passes all tests and linting checks.
2. Update the documentation if necessary.
3. Include a clear description of the changes in your PR.
4. Link any related issues in the PR description.
5. Wait for a maintainer to review your PR and address any feedback.

## Coding Standards

We follow these coding standards:

- **PEP 8**: For Python code style.
- **Black**: For code formatting.
- **isort**: For import sorting.
- **Flake8**: For linting.
- **MyPy**: For static type checking.

Our pre-commit hooks will help enforce these standards.

## Testing

All new code should include appropriate tests:

- **Unit Tests**: For testing individual functions and classes.
- **API Tests**: For testing API endpoints.

Run the tests with:
```bash
make test
```

Or run specific test types:
```bash
make test-unit
make test-api
```

## Documentation

- Update the README.md if you change functionality.
- Document all functions, classes, and modules with docstrings.
- Keep the API documentation up-to-date.
- Update the database schema documentation if you change the models.

## Issue Reporting

- Use the GitHub issue tracker to report bugs.
- Clearly describe the issue including steps to reproduce.
- Include the expected behavior and the actual behavior.
- Include any relevant logs or error messages.

## Feature Requests

- Use the GitHub issue tracker to suggest new features.
- Clearly describe the feature and its benefits.
- Provide examples of how the feature would be used.

## Contact

If you have any questions or need help, please contact:
- Email: support@doztra.ai
- GitHub Issues: [https://github.com/doztra/auth-service/issues](https://github.com/doztra/auth-service/issues)

Thank you for contributing to Doztra Auth Service!
