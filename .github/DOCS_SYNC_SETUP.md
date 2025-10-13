# Documentation Site Auto-Sync Setup

## Overview

When you push changes to the OpenWorkflow-Specification repository, the documentation site at OpenWorkflow-Docs automatically rebuilds and deploys with the latest changes.

## How It Works

1. **You push changes** to `main` branch in OpenWorkflow-Specification
2. **GitHub Actions workflow** (`.github/workflows/trigger-docs-deploy.yml`) detects changes to:
   - `specs/**` (specification files)
   - `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` (root docs)
   - `examples/**` (example implementations)
3. **Workflow triggers** a repository dispatch event to OpenWorkflow-Docs
4. **Docs repository** receives the `spec-updated` event
5. **Docs deploy workflow** runs:
   - Checks out latest specification
   - Syncs content to `docs/` directory
   - Builds Docusaurus site
   - Deploys to GitHub Pages

## Setup Required

### 1. Create Personal Access Token (PAT)

You need a GitHub Personal Access Token with `repo` scope:

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name: `Docs Deploy Token`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### 2. Add Token as Secret

In the **OpenWorkflow-Specification** repository:

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `DOCS_DEPLOY_TOKEN`
4. Value: Paste your PAT
5. Click "Add secret"

## Testing

After setup:

1. Make a change to any file in `specs/`
2. Commit and push to `main`
3. Check Actions tab in OpenWorkflow-Specification (should see "Trigger Docs Deployment" workflow)
4. Check Actions tab in OpenWorkflow-Docs (should see "Deploy to GitHub Pages" workflow triggered)
5. Wait ~2 minutes for deployment
6. Visit your docs site - changes should be live!

## Manual Trigger

You can also manually trigger the docs deployment:

1. Go to OpenWorkflow-Docs repository
2. Click "Actions" tab
3. Select "Deploy to GitHub Pages" workflow
4. Click "Run workflow"

## Troubleshooting

### Workflow doesn't trigger
- Check that `DOCS_DEPLOY_TOKEN` secret exists in OpenWorkflow-Specification
- Verify the PAT has `repo` scope
- Ensure you're pushing to `main` branch
- Check that your changes are in tracked paths (`specs/`, `README.md`, etc.)

### Deployment fails
- Check the Actions logs in OpenWorkflow-Docs
- Common issues:
  - Sync script can't find specification files
  - Build errors in Docusaurus
  - Link checker failures

### Token expired
- PATs expire after set period (default 90 days)
- Generate a new token and update the secret
- Consider using a fine-grained token with longer expiration
