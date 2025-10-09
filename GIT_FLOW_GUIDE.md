# Git Flow Guide for Doztra AI

This document outlines the Git Flow branching strategy used in the Doztra AI project.

## Branch Structure

- **main**: Production code that is deployed to users
- **develop**: Main development branch where features are integrated
- **feature/**: Feature-specific branches for new development
- **release/**: Release preparation branches
- **hotfix/**: Emergency fixes for production
- **support/**: Long-term maintenance branches for older versions

## Workflow

### Feature Development

1. Start a new feature:
   ```bash
   git flow feature start feature-name
   ```
   This creates a new branch `feature/feature-name` based on `develop`.

2. Work on the feature, committing changes as needed.

3. Finish the feature:
   ```bash
   git flow feature finish feature-name
   ```
   This merges the feature branch back into `develop` and deletes the feature branch.

### Release Process

1. Start a new release:
   ```bash
   git flow release start 1.0.0
   ```
   This creates a new branch `release/1.0.0` based on `develop`.

2. Make any final adjustments, version bumps, and bug fixes.

3. Finish the release:
   ```bash
   git flow release finish 1.0.0
   ```
   This:
   - Merges the release branch into `main`
   - Tags the release with `v1.0.0`
   - Merges the release branch back into `develop`
   - Deletes the release branch

### Hotfix Process

1. Start a hotfix:
   ```bash
   git flow hotfix start 1.0.1
   ```
   This creates a new branch `hotfix/1.0.1` based on `main`.

2. Fix the critical bug.

3. Finish the hotfix:
   ```bash
   git flow hotfix finish 1.0.1
   ```
   This:
   - Merges the hotfix branch into `main`
   - Tags the release with `v1.0.1`
   - Merges the hotfix branch back into `develop`
   - Deletes the hotfix branch

## Version Naming Convention

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

## Examples

### Creating a New Feature

```bash
# Start a new feature
git flow feature start user-authentication

# Make changes and commit
git add .
git commit -m "Implement user authentication"

# Finish the feature
git flow feature finish user-authentication
```

### Creating a Release

```bash
# Start a new release
git flow release start 1.0.0

# Make final adjustments
git add .
git commit -m "Bump version to 1.0.0"

# Finish the release
git flow release finish 1.0.0

# Push changes to remote
git push origin --all
git push origin --tags
```

### Creating a Hotfix

```bash
# Start a hotfix
git flow hotfix start 1.0.1

# Fix the bug
git add .
git commit -m "Fix critical security issue"

# Finish the hotfix
git flow hotfix finish 1.0.1

# Push changes to remote
git push origin --all
git push origin --tags
```

## Repository-Specific Notes

### Frontend Repository
- Production branch: `main`
- Development branch: `dev`

### Backend Repository
- Production branch: `main`
- Development branch: `develop`
