# Connector Schema Specification

**Version:** 0.1.0
**Status:** Draft

## Overview

The Connector Schema is a declarative format that describes capability providers without dictating implementation details. Connectors package integrations with external services (APIs, MCP servers, SDKs, etc.) and expose them as reusable actions.

Connectors are implementation-agnostic: authentication, secret storage, and execution enforcement are handled by the runtime, not specified in the schema.

**Why "connector"?** This terminology avoids collision with MCP's "tool" concept while clearly indicating the resource connects workflows to external capabilities.

## Core Concepts

- **Connector**: A packaged capability provider (e.g., "GitHub MCP", "Slack API", "AWS Lambda")
- **Action**: A single executable capability with defined inputs and outputs
- **Handler**: The implementation that executes when an action is invoked (HTTP, MCP, SDK function, etc.)
- **Kind**: The connector type (mcp-server, http, sdk, lambda, custom)

## Naming Convention

Connectors use the registry naming format:

```
connector:<namespace>/<name>@<version>
```

Examples:
- `connector:community/slack@1.2.0`
- `connector:github/mcp@0.4.1`
- `connector:acme/custom-api@2.0.0`

## Schema Structure

### Connector Metadata

```yaml
connector:
  type: connector           # Required: resource type
  kind: string              # Required: mcp-server | http | sdk | lambda | custom
  name: string              # Required: unique name (kebab-case)
  namespace: string         # Required: publisher namespace
  version: string           # Required: semantic version (e.g., "1.0.0")
  displayName: string       # Required: human-readable name
  description: string       # Required: what this connector does
  author: string            # Optional: maintainer name or organization
  homepage: string          # Optional: documentation URL
  icon: string              # Optional: URL to connector icon
  categories: [string]      # Optional: searchable categories

  # Runtime requirements (optional)
  runtime:
    memory: string          # e.g., "512MB", "1GB"
    timeout: integer        # seconds, default 300
    environment:            # Required environment variables
      - name: API_KEY
        description: "Service API key"
        required: true

  # Approval workflow (optional)
  approval:
    required: never | first_use | always | admin_approval  # Default: never
    approvers: [string]     # Roles or user IDs who can approve
    timeout: integer        # Seconds to wait for approval (default: 3600)
    onTimeout: reject | allow | escalate  # Default: reject

  # Security and capability hints (optional)
  security:
    dataFlow: inbound | outbound | bidirectional  # Data movement direction
    requiredScopes: [string]  # OAuth scopes or permissions required
    trustLevel: official | verified | community | unverified  # Registry trust level

  # Adapter compatibility hints (optional)
  supports: [string]  # e.g., ["mcp", "openapi", "langchain"] for runtime adapters
```

### Actions

Each connector defines one or more actions:

```yaml
actions:
  - name: string            # Required: action identifier (snake_case)
    description: string     # Required: what this action does

    # Input schema (JSON Schema)
    input:
      type: object
      properties:
        param_name:
          type: string|number|boolean|object|array
          description: string
          default: any        # Optional default value
          enum: [values]      # Optional allowed values
      required: [string]      # List of required properties

    # Output schema (JSON Schema)
    output:
      type: object
      properties:
        result_field:
          type: string
          description: string

    # Handler implementation (see Handler Types below)
    handler:
      # ... handler configuration
```

## Authentication

Connectors declare authentication requirements using vendor-neutral descriptors. The runtime handles credential storage, rotation, and injection.

### Auth Types

```yaml
# API Key
auth:
  type: apiKey
  in: header | query | cookie
  name: Authorization | X-API-Key | ...
  prefix: Bearer | API-Key | ...  # Optional

# OAuth 2.0
auth:
  type: oauth2
  flow: authorization_code | client_credentials | implicit
  authorizationUrl: https://...
  tokenUrl: https://...
  scopes: [read, write, admin]

# Bearer Token
auth:
  type: bearer
  scheme: bearer | jwt

# HTTP Basic
auth:
  type: basic

# Custom (runtime-specific)
auth:
  type: custom
  scheme: string
  parameters: object
```

**Note:** The connector schema only declares authentication requirements. Storage (vault, secrets manager) and enforcement are runtime responsibilities.

## Handler Types

Connectors can be implemented using any of these handler types:

### 1. HTTP Handler

Invoke an external HTTP service:

```yaml
handler:
  http:
    url: string             # Required: endpoint URL
    method: string          # Required: GET, POST, PUT, DELETE, PATCH
    headers:                # Optional: static headers
      Authorization: "Bearer ${API_KEY}"
      Content-Type: "application/json"
    timeout: integer        # Optional: request timeout in seconds
    retry:                  # Optional: retry configuration
      max_attempts: 3
      backoff: exponential  # or "fixed", "linear"
      backoff_factor: 2

    # Security: URL validation (recommended for user-provided URLs)
    urlValidation:
      allowedDomains: ["*.example.com"]  # Domain allowlist
      blockedDomains: ["169.254.169.254"]  # Block AWS metadata
      requireHTTPS: true
```

**Request format:**
The OpenWorkflow runtime sends the action input as the request body:
```json
{
  "param1": "value1",
  "param2": "value2"
}
```

**Expected response:**
```json
{
  "status": "success",
  "data": { /* matches output schema */ }
}
```

Or on error:
```json
{
  "status": "error",
  "message": "Human-readable error description",
  "code": "ERROR_CODE"  // Optional
}
```

### 2. SDK Function Handler

Reference a function in your SDK-integrated application:

```yaml
handler:
  function: module.function_name    # e.g., "weather.get_current_weather"
```

**Requirements:**
- Function must be registered with the OpenWorkflow SDK before workflow execution
- Function receives input as keyword arguments (Python) or object (JS)
- Function returns data matching the output schema or raises an exception

**Example (Python):**
```python
from openworkflow import register_action

@register_action("weather.get_current_weather")
def get_current_weather(location: str) -> dict:
    # Implementation
    return {"temperature": 72, "conditions": "sunny"}
```

### 3. Command Handler

Execute a shell command or script:

```yaml
handler:
  command: string           # Required: command to execute
  args: [string]            # Optional: command arguments
  env:                      # Optional: environment variables
    KEY: value
  working_dir: string       # Optional: execution directory
```

**Input/Output:**
- Input is passed as JSON to stdin
- Output is expected as JSON on stdout
- Non-zero exit code indicates error (stderr captured as error message)

**Example:**
```yaml
handler:
  command: "./scripts/process_data.py"
  args: ["--format", "json"]
```

### 4. Kafka Handler

Publish to a Kafka topic and optionally wait for a response:

```yaml
handler:
  kafka:
    topic: string           # Required: topic to publish to
    response_topic: string  # Optional: topic to listen for response
    timeout: integer        # Optional: how long to wait for response (seconds)
    key: string             # Optional: message key (supports templating)
```

**Message format:**
```json
{
  "action": "plugin.action_name",
  "input": { /* action input */ },
  "correlation_id": "uuid",
  "timestamp": "2025-10-07T12:00:00Z"
}
```

## Complete Example

```yaml
connector:
  type: connector
  kind: http
  name: github
  namespace: community
  version: 0.1.0
  displayName: GitHub Integration
  description: Interact with GitHub repositories, issues, and pull requests
  author: OpenWorkflow Community
  homepage: https://docs.openworkflowspec.org/connectors/github
  categories: [vcs, github, git, development]

  runtime:
    timeout: 60
    environment:
      - name: GITHUB_TOKEN
        description: GitHub personal access token
        required: true

actions:
  - name: create_issue
    description: Create a new issue in a GitHub repository

    input:
      type: object
      properties:
        repo:
          type: string
          description: Repository in format "owner/repo"
        title:
          type: string
          description: Issue title
        body:
          type: string
          description: Issue description
          default: ""
        labels:
          type: array
          items:
            type: string
          description: Labels to add to the issue
          default: []
      required: [repo, title]

    output:
      type: object
      properties:
        issue_number:
          type: integer
          description: The created issue number
        url:
          type: string
          description: URL to the created issue

    handler:
      http:
        url: https://api.github.com/repos/${input.repo}/issues
        method: POST
        headers:
          Authorization: "Bearer ${GITHUB_TOKEN}"
          Accept: "application/vnd.github.v3+json"
        retry:
          max_attempts: 3
          backoff: exponential

  - name: list_repos
    description: List repositories for a user or organization

    input:
      type: object
      properties:
        owner:
          type: string
          description: GitHub username or organization
        type:
          type: string
          description: Repository type
          enum: [all, public, private]
          default: all
      required: [owner]

    output:
      type: object
      properties:
        repositories:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
              url:
                type: string
              description:
                type: string

    handler:
      http:
        url: https://api.github.com/users/${input.owner}/repos
        method: GET
        headers:
          Authorization: "Bearer ${GITHUB_TOKEN}"
          Accept: "application/vnd.github.v3+json"
```

## Validation

Connector schemas are validated against the JSON Schema specification. Use the OpenWorkflow CLI to validate your connector:

```bash
openworkflow connector validate my-connector.yaml
```

## Registry Submission

Once validated, submit your connector to the registry:

```bash
openworkflow connector publish my-connector.yaml
```

See [Registry Protocol](./registry-protocol.md) for details.

## Template Variables

Handler configurations support template variables:

- `${input.field_name}` - Access input parameters
- `${env.VAR_NAME}` - Access environment variables
- `${secrets.SECRET_NAME}` - Access secure credentials

**Security Note:** Template expressions in handler configs are trusted and can access secrets. User-provided inputs use a sandboxed context that cannot access `${secrets.*}`. See [Security](./security.md) for details.

## Best Practices

1. **Descriptive names**: Use clear action names that describe what they do
2. **Detailed descriptions**: Help users understand when to use each action
3. **Input validation**: Define specific types, patterns, and constraints in input schemas
4. **Parameterized queries**: Use prepared statements for SQL, never string interpolation
5. **Error handling**: Return structured error responses; sanitize sensitive data
6. **Idempotency**: Design actions to be safely retryable when possible
7. **Security**: Follow least privilege; validate URLs; sandbox execution
8. **Documentation**: Link to comprehensive docs in the homepage field
9. **Versioning**: Follow semantic versioning; breaking changes require major version bump

## Security Considerations

### SQL Injection Prevention

**❌ DANGEROUS - String Interpolation:**
```yaml
# VULNERABLE TO SQL INJECTION
actions:
  - name: get_user
    input:
      properties:
        user_id: {type: string}
    handler:
      http:
        url: https://db.example.com/query
        body: |
          SELECT * FROM users WHERE id = '${input.user_id}'
          # Attack: user_id = "1' OR '1'='1'; DROP TABLE users--"
```

**✅ SAFE - Parameterized Queries:**
```yaml
# Positional parameters
actions:
  - name: get_user
    input:
      properties:
        user_id: {type: string}
    handler:
      http:
        url: https://db.example.com/query
        body:
          sql: "SELECT * FROM users WHERE id = ?"
          parameters: ["${input.user_id}"]  # Automatically escaped

# Named parameters
actions:
  - name: search_users
    handler:
      http:
        body:
          sql: "SELECT * FROM users WHERE email = :email AND active = :active"
          parameters:
            email: "${input.email}"
            active: true
```

### Additional Security Guidance

See [Security Specification](./security.md) for comprehensive guidance:

- **SSRF Protection**: Validate and restrict user-provided URLs with `urlValidation`
- **Secret Management**: Never log or expose secrets in outputs or error messages
- **Input Validation**: Use JSON Schema with strict `pattern`, `format`, `maxLength` constraints
- **Resource Limits**: Set appropriate `timeout` and memory limits in `runtime` config
- **Template Sandboxing**: User inputs cannot access `${secrets.*}` namespace

## Next Steps

- [Workflow Schema](./workflow-schema.md) - Compose actions into workflows
- [SDK Contract](./sdk-contract.md) - Integrate connectors into your application
- [Registry Protocol](./registry-protocol.md) - Publish and discover connectors
