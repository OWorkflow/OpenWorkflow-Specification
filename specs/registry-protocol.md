# Registry Protocol Specification

**Version:** 0.1.0

## Overview

The OpenWorkflow Plugin Registry enables discovery, publication, and versioning of plugins. It provides both a public community registry and support for private registries.

## Registry Types

### Public Registry

Community-maintained registry at `registry.openworkflowspec.org`:
- Open for public plugin submissions
- Searchable and browsable
- Version tracking and deprecation support
- Usage analytics

### Private Registry

Self-hosted or organization-specific:
- Full control over plugins
- Internal plugins not shared publicly
- Enterprise compliance requirements
- Custom approval workflows

## Registry Operations

### 1. Search Plugins

**Endpoint:** `GET /plugins/search`

Query parameters:
- `q`: Search query (matches name, description, tags)
- `tag`: Filter by tag
- `limit`: Results per page (default: 20, max: 100)
- `offset`: Pagination offset

**Example:**
```bash
curl "https://registry.openworkflowspec.org/plugins/search?q=github&tag=vcs"
```

**Response:**
```json
{
  "total": 1,
  "results": [
    {
      "slug": "github",
      "name": "GitHub Integration",
      "description": "Interact with GitHub repositories",
      "version": "1.2.0",
      "author": "OpenWorkflow Community",
      "tags": ["vcs", "github", "git"],
      "downloads": 15420,
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-09-20T14:30:00Z"
    }
  ]
}
```

### 2. Get Plugin Details

**Endpoint:** `GET /plugins/{slug}`

Query parameters:
- `version`: Specific version (default: latest)

**Example:**
```bash
curl "https://registry.openworkflowspec.org/plugins/github?version=1.2.0"
```

**Response:**
```json
{
  "slug": "github",
  "version": "1.2.0",
  "name": "GitHub Integration",
  "description": "Interact with GitHub repositories, issues, and pull requests",
  "author": "OpenWorkflow Community",
  "homepage": "https://docs.openworkflowspec.org/plugins/github",
  "repository": "https://github.com/Open-Workflow/connector-github",
  "license": "MIT",
  "tags": ["vcs", "github", "git", "development"],
  "actions": [
    {
      "name": "create_issue",
      "description": "Create a new issue"
    },
    {
      "name": "list_repos",
      "description": "List repositories"
    }
  ],
  "runtime": {
    "memory": "512MB",
    "timeout": 60
  },
  "environment": [
    {
      "name": "GITHUB_TOKEN",
      "description": "GitHub personal access token",
      "required": true
    }
  ],
  "versions": ["1.2.0", "1.1.0", "1.0.0"],
  "downloads": 15420,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-09-20T14:30:00Z",
  "schema_url": "https://registry.openworkflowspec.org/plugins/github/1.2.0/schema"
}
```

### 3. Download Plugin Schema

**Endpoint:** `GET /plugins/{slug}/{version}/schema`

Returns the complete plugin YAML/JSON definition.

**Example:**
```bash
curl "https://registry.openworkflowspec.org/plugins/github/1.2.0/schema"
```

**Response:** Complete plugin schema (YAML or JSON)

### 4. Publish Plugin

**Endpoint:** `POST /plugins`

Headers:
- `Authorization: Bearer <api_key>`
- `Content-Type: application/json` or `application/yaml`

**Body:** Complete plugin schema

**Example:**
```bash
curl -X POST https://registry.openworkflowspec.org/plugins \
  -H "Authorization: Bearer sk_..." \
  -H "Content-Type: application/yaml" \
  --data-binary @my-plugin.yaml
```

**Response:**
```json
{
  "status": "published",
  "slug": "my-plugin",
  "version": "1.0.0",
  "url": "https://registry.openworkflowspec.org/plugins/my-plugin"
}
```

### 5. Update Plugin

**Endpoint:** `PUT /plugins/{slug}`

Headers:
- `Authorization: Bearer <api_key>`
- `Content-Type: application/json` or `application/yaml`

**Body:** Updated plugin schema (version must be incremented)

**Response:**
```json
{
  "status": "updated",
  "slug": "my-plugin",
  "version": "1.1.0",
  "previous_version": "1.0.0"
}
```

### 6. Deprecate Version

**Endpoint:** `POST /plugins/{slug}/{version}/deprecate`

Headers:
- `Authorization: Bearer <api_key>`

**Body:**
```json
{
  "reason": "Security vulnerability fixed in 1.2.0",
  "replacement_version": "1.2.0"
}
```

### 7. Unpublish Plugin

**Endpoint:** `DELETE /plugins/{slug}/{version}`

Headers:
- `Authorization: Bearer <api_key>`

Only allowed if:
- No active workflows using this version
- Version is deprecated
- Within 72 hours of publication (for mistakes)

## CLI Integration

### Install Plugin

```bash
# From public registry
openworkflow plugin install github

# Specific version
openworkflow plugin install github@1.2.0

# From private registry
openworkflow plugin install github --registry=https://registry.mycompany.com

# Save to project
openworkflow plugin install github --save
# Creates ./plugins/github.yaml
```

### Publish Plugin

```bash
# Validate before publishing
openworkflow plugin validate my-plugin.yaml

# Publish to public registry
openworkflow plugin publish my-plugin.yaml

# Publish to private registry
openworkflow plugin publish my-plugin.yaml --registry=https://registry.mycompany.com

# Dry run
openworkflow plugin publish my-plugin.yaml --dry-run
```

### Update Plugin

```bash
# Update version in schema file first
openworkflow plugin publish my-plugin.yaml --update
```

### List Installed Plugins

```bash
openworkflow plugin list

# Output:
# github          1.2.0   https://registry.openworkflowspec.org
# weather         1.0.0   local
# my-plugin       0.1.0   https://registry.mycompany.com
```

## SDK Integration

### Load Plugin from Registry

**Python:**
```python
from openworkflow import OpenWorkflow

openworkflow = OpenWorkflow()

# Load from public registry
openworkflow.install_plugin("github", version="1.2.0")

# Load from private registry
openworkflow.install_plugin(
    "internal-tool",
    registry="https://registry.mycompany.com",
    api_key="..."
)

# Use in workflow
workflow = Workflow.from_file("workflow.yaml")
result = workflow.execute()  # Auto-downloads missing plugins
```

**JavaScript:**
```javascript
import { OpenWorkflow } from '@openworkflow/sdk';

const openworkflow = new OpenWorkflow();

await openworkflow.installPlugin('github', { version: '1.2.0' });

// Or auto-install on workflow execution
const workflow = await Workflow.fromFile('workflow.yaml');
await workflow.execute({ autoInstall: true });
```

## MCP Router Registration

When running self-hosted or in OpenWorkflow Cloud, plugins register with the MCP Router for dynamic routing.

### Registration

**Endpoint:** `POST /register`

**Body:**
```json
{
  "plugin_slug": "weather",
  "version": "1.0.0",
  "url": "http://weather-service:8000",
  "actions": ["get_current_weather", "get_forecast"],
  "health_check_url": "http://weather-service:8000/healthz",
  "metadata": {
    "instance_id": "weather-abc123",
    "region": "us-east-1"
  }
}
```

**Response:**
```json
{
  "status": "registered",
  "plugin_slug": "weather",
  "instance_id": "weather-abc123",
  "registered_at": "2025-10-07T12:00:00Z"
}
```

### Deregistration

**Endpoint:** `DELETE /register/{plugin_slug}/{instance_id}`

Called on shutdown to remove instance from router.

### Health Checks

Router periodically calls `health_check_url` to verify plugin availability:

**Expected response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "checks": {
    "external_api": "healthy",
    "database": "healthy"
  }
}
```

If health check fails multiple times, router removes plugin from routing table.

## Plugin Verification

### Checksum Verification

Published plugins include SHA256 checksum:

```bash
openworkflow plugin verify github@1.2.0
# ✓ Checksum verified: a3b2c1d4e5f6...
```

### Code Signing (Optional)

Plugins can be GPG-signed:

```yaml
plugin:
  slug: github
  version: 1.2.0
  signature:
    type: gpg
    key_id: "0x1234ABCD"
    signature: |
      -----BEGIN PGP SIGNATURE-----
      ...
      -----END PGP SIGNATURE-----
```

Verify signatures:
```bash
openworkflow plugin verify github@1.2.0 --check-signature
```

## Private Registry Setup

### Self-Hosted Registry

Deploy the registry service:

```bash
docker run -d \
  -p 8080:8080 \
  -e DATABASE_URL=postgres://... \
  -e STORAGE_BACKEND=s3 \
  -e S3_BUCKET=my-plugin-registry \
  openworkflow/registry:latest
```

### Configure SDK

```python
from openworkflow import OpenWorkflow

openworkflow = OpenWorkflow(
    registry_url="https://registry.mycompany.com",
    registry_api_key="sk_..."
)
```

Or via environment:
```bash
export OPENWORKFLOW_REGISTRY_URL=https://registry.mycompany.com
export OPENWORKFLOW_REGISTRY_API_KEY=sk_...
```

### Registry Authentication

API keys required for:
- Publishing plugins
- Updating plugins
- Accessing private registries
- Viewing usage analytics

Create API keys:
```bash
smartify auth create-key --name "CI/CD Pipeline"
# Returns: sk_...
```

## Metadata Fields

### Required Fields

- `slug`: Unique plugin identifier
- `version`: Semantic version
- `name`: Human-readable name
- `description`: Clear description of functionality
- `actions`: At least one action definition

### Recommended Fields

- `author`: Maintainer name/org
- `homepage`: Documentation URL
- `repository`: Source code URL
- `license`: SPDX license identifier
- `tags`: Searchable keywords
- `icon`: Plugin icon URL

### Optional Fields

- `changelog`: Release notes
- `dependencies`: Other plugins required
- `compatibility`: Min/max OpenWorkflow version
- `security`: Security policy URL
- `support`: Support contact/URL

## Versioning Policy

Plugins follow semantic versioning:

- **Major (x.0.0)**: Breaking changes to action signatures or behavior
- **Minor (1.x.0)**: New actions or backward-compatible features
- **Patch (1.0.x)**: Bug fixes and improvements

Example breaking change:
```yaml
# v1.0.0
actions:
  - name: get_weather
    input:
      location: string

# v2.0.0 (breaking: renamed parameter)
actions:
  - name: get_weather
    input:
      city: string  # Was "location"
```

## Best Practices

1. **Complete metadata**: Fill all recommended fields
2. **Clear descriptions**: Help users understand what actions do
3. **Semantic versioning**: Follow SemVer strictly
4. **Test before publishing**: Use `--dry-run` flag
5. **Changelog**: Document changes in each version
6. **Deprecation warnings**: Notify users before removing features
7. **Security updates**: Promptly patch vulnerabilities
8. **Examples**: Include usage examples in homepage

## Next Steps

- [Plugin Schema](./plugin-schema.md) - Define your plugin
- [SDK Contract](./sdk-contract.md) - Integrate with SDK
- [Workflow Schema](./workflow-schema.md) - Use plugins in workflows
