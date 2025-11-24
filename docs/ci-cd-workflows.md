# CI/CD Workflows

This document describes the CI/CD workflows configured for the tree-climber project.

## Overview

The project uses GitHub Actions for continuous integration and deployment. All workflows are defined in `.github/workflows/`.

## CI Workflow

Location: `.github/workflows/ci.yml`

### Trigger Events

The CI workflow runs on:
- Push to `main` branch
- Pull requests targeting `main` branch

### Jobs

#### 1. Linting

**Purpose**: Ensures code quality and consistency

**Steps**:
- Checkout code
- Set up Python 3.12
- Install uv package manager
- Install project dependencies (including graphviz)
- Run ruff format check
- Run ruff lint
- Run pyright type checking

**Technologies**:
- `ruff`: Python linter and formatter
- `pyright`: Python type checker

#### 2. Testing

**Purpose**: Validates code functionality through unit tests

**Steps**:
- Checkout code
- Set up Python 3.12
- Install uv package manager
- Install project dependencies (including graphviz)
- Run pytest with verbose output

**Technologies**:
- `pytest`: Python testing framework

#### 3. Deploy Review App

**Purpose**: Deploys a review app for pull requests after tests pass

**Conditions**:
- Only runs on pull requests (`github.event_name == 'pull_request'`)
- Only runs after the `test` job completes successfully (`needs: test`)

**Steps**:
- Checkout code
- Deploy to review environment (placeholder implementation)

**Configuration**:

The deployment job is currently configured with a placeholder script. To enable actual deployment, uncomment and configure one of the following platforms:

##### Vercel
```yaml
- name: Deploy to Vercel
  run: |
    npm install -g vercel
    vercel deploy --token=${{ secrets.VERCEL_TOKEN }} --yes
  env:
    VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
    VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

##### Netlify
```yaml
- name: Deploy to Netlify
  run: |
    npm install -g netlify-cli
    netlify deploy --auth=${{ secrets.NETLIFY_AUTH_TOKEN }} --site=${{ secrets.NETLIFY_SITE_ID }}
```

##### Heroku
```yaml
- name: Deploy to Heroku
  run: |
    git push heroku ${{ github.head_ref }}:main
  env:
    HEROKU_API_KEY: ${{ secrets.HEROKU_API_KEY }}
```

##### Railway
```yaml
- name: Deploy to Railway
  run: |
    npm install -g @railway/cli
    railway up
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

##### Custom Deployment Script
```yaml
- name: Deploy with custom script
  run: ./deploy-review.sh
  env:
    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

## Workflow Dependencies

```
lint (independent)
test (independent)
deploy-review-app (depends on: test)
```

The `deploy-review-app` job will only execute if:
1. The workflow was triggered by a pull request
2. The `test` job completed successfully

If the `test` job fails, the `deploy-review-app` job will be skipped automatically.

## Adding Secrets

To configure deployment, you'll need to add secrets to your GitHub repository:

1. Go to Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Add the required secrets for your chosen deployment platform:
   - **Vercel**: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
   - **Netlify**: `NETLIFY_AUTH_TOKEN`, `NETLIFY_SITE_ID`
   - **Heroku**: `HEROKU_API_KEY`
   - **Railway**: `RAILWAY_TOKEN`
   - Or any custom tokens needed for your deployment script

## Local Development

For local development and testing, refer to the main README.md for:
- Setting up the development environment
- Running tests locally
- Starting the backend server
- Starting the frontend development server

## Future Enhancements

Possible improvements to the CI/CD pipeline:
- Add code coverage reporting
- Add security scanning (e.g., Snyk, Dependabot)
- Add performance testing
- Add deployment to staging/production environments
- Add automatic changelog generation
- Add automatic version bumping
