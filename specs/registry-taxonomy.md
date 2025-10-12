# Registry Taxonomy & Naming

**Version:** 0.1.0

> This specification follows [Semantic Versioning](https://semver.org/).

## Overview

The OpenWorkflow Registry uses a consistent, future-proof naming system that maps cleanly to MCP and provides intuitive discovery. This document defines the canonical resource types, naming conventions, and manifest formats.

## Resource Types

The registry supports four top-level resource types:

### 1. Connector

A **connector** packages a capability provider (Slack API, GitHub MCP server, Stripe HTTP, AWS Lambda, etc.).

**Why "connector"?**
- Neutral and widely understood term
- Avoids collision with MCP's "tool" terminology (MCP servers expose tools; we register the server as a connector)
- Clear purpose: connects OpenWorkflow to external capabilities

**Sub-kinds:**
- `mcp-server` - MCP protocol server
- `http` - REST/HTTP API
- `sdk` - SDK function integration
- `lambda` - AWS Lambda or serverless function
- `custom` - Custom integration type

### 2. Workflow

A shareable, versioned DAG (directed acyclic graph) using connectors and agents.

Workflows are portable orchestrations that reference other registry resources by ID. Human-in-the-loop steps (approvals, forms, assignments) are defined inline within workflows rather than as separate registry resources.

### 3. Agent

A reusable agent policy defining:
- Model selection (provider + model ID)
- Planning/decoding configuration
- Allowed toolset (by reference to connectors)
- Safety policies and rate limits

Agents are invocable nodes in workflows, enabling agentic reasoning within orchestrations.

### 4. Bundle

A curated set of related resources (1–N workflows + connectors + agents) with pinned versions.

**Use cases:**
- Starter kits (e.g., "Customer Support Suite")
- Company-specific workflow collections
- Industry templates (e.g., "HIPAA Compliance Pack")

## Naming Convention

All registry resources use a consistent ID format:

```
<type>:<namespace>/<name>@<version>
```

### Components

- **type**: `connector` | `workflow` | `agent` | `bundle`
- **namespace**: Publisher identifier
  - `smartify` - Official OpenWorkflow resources
  - `org/user` - Community publishers (e.g., `acme`, `dylan`, `github`)
- **name**: Resource name in kebab-case
- **version**: Semantic version (SemVer)

### Examples

```
connector:community/slack@1.2.0
connector:github/mcp@0.4.1
workflow:openworkflow/daily-weather-to-slack@1.0.0
agent:openworkflow/triage-bot@0.2.0
bundle:openworkflow/startup-starter@1.0.0
```

## CLI Integration

### Install/Add Resources

```bash
# Add connector
smartify add connector:github/mcp

# Add with version constraint
smartify add connector:github/mcp@~0.4

# Add workflow
smartify add workflow:openworkflow/daily-weather-to-slack

# Add agent
smartify add agent:openworkflow/triage-bot

# Add bundle (installs all included resources)
smartify add bundle:openworkflow/startup-starter
```

### Search Registry

```bash
# Search by type
smartify search --type connector github

# Search MCP connectors
smartify search --type connector --kind mcp-server github

# Search workflows
smartify search --type workflow --category automation

# Search agents
smartify search --type agent
```

## MCP Integration

### How This Maps to MCP

In the MCP ecosystem:
- An **MCP server** exposes one or more **tools**
- Each tool has inputs, outputs, and a handler

In Smartify:
- Register the MCP server as a **connector** with `kind: "mcp-server"`
- The tools inside become **actions** surfaced by that connector
- Actions are discovered at install/import time via MCP protocol introspection

**Why not call them "tools"?**
If we called registry entries "tools," we'd collide with MCP's specific meaning. "Connector" cleanly avoids confusion.

### Example Flow

1. Developer publishes MCP server to OpenWorkflow Registry as a connector
2. User installs: `smartify add connector:github/mcp@0.4.1`
3. OpenWorkflow SDK connects to MCP server and discovers available tools
4. Tools become available as actions: `connector:github/mcp.create_issue`
5. Workflows reference actions using the connector ID

## Manifest Formats

### Schema Version

All manifests include a `schemaVersion` field for evolution:

```json
{
  "schemaVersion": "0.1.0",
  "type": "connector",
  ...
}
```

### A) Connector Manifest

#### MCP Server Connector

```json
{
  "schemaVersion": "0.1.0",
  "type": "connector",
  "kind": "mcp-server",
  "name": "github-mcp",
  "namespace": "github",
  "version": "0.4.1",
  "displayName": "GitHub (MCP)",
  "description": "Expose GitHub MCP tools as OpenWorkflow actions",

  "auth": {
    "type": "apiKey",
    "in": "header",
    "name": "Authorization",
    "prefix": "Bearer "
  },

  "mcp": {
    "transport": "websocket",
    "endpoint": "wss://mcp.github.dev",
    "protocolVersion": "2024-11-05",
    "expose": "all"
  },

  "categories": ["developer-tools", "vcs"],
  "homepage": "https://github.com/mcp/servers/github",
  "license": "MIT"
}
```

#### HTTP Connector

```json
{
  "schemaVersion": "0.1.0",
  "type": "connector",
  "kind": "http",
  "name": "slack",
  "namespace": "smartify",
  "version": "1.2.0",
  "displayName": "Slack",
  "description": "Send messages, manage channels, and interact with Slack workspaces",

  "security": {
    "trustLevel": "official",
    "publisher": {
      "name": "Smartify",
      "email": "security@openworkflow.ai",
      "gpgKey": "0xABCD1234"
    },
    "permissions": {
      "network": true,
      "filesystem": false
    }
  },

  "actions": [
    {
      "name": "sendMessage",
      "description": "Send a message to a channel",
      "input": {
        "type": "object",
        "properties": {
          "channel": {"type": "string"},
          "text": {"type": "string"}
        },
        "required": ["channel", "text"]
      },
      "handler": {
        "http": {
          "url": "https://slack.com/api/chat.postMessage",
          "method": "POST",
          "headers": {
            "Authorization": "Bearer ${SLACK_TOKEN}"
          }
        }
      }
    }
  ],

  "auth": {
    "type": "oauth2",
    "scopes": ["chat:write", "channels:read"]
  },

  "categories": ["communication"],
  "homepage": "https://docs.openworkflowspec.org/connectors/slack"
}
```

#### SDK Function Connector

```json
{
  "schemaVersion": "0.1.0",
  "type": "connector",
  "kind": "sdk",
  "name": "calculator",
  "namespace": "smartify",
  "version": "1.0.0",
  "displayName": "Calculator",
  "description": "Basic mathematical operations",

  "actions": [
    {
      "name": "add",
      "description": "Add two numbers",
      "input": {
        "type": "object",
        "properties": {
          "a": {"type": "number"},
          "b": {"type": "number"}
        },
        "required": ["a", "b"]
      },
      "handler": {
        "function": "calculator.add"
      }
    }
  ],

  "runtime": {
    "timeout": 5
  },

  "categories": ["utility"],
  "license": "MIT"
}
```

### B) Workflow Manifest

```json
{
  "schemaVersion": "0.1.0",
  "type": "workflow",
  "name": "daily-weather-to-slack",
  "namespace": "smartify",
  "version": "1.0.0",
  "displayName": "Daily Weather to Slack",
  "description": "Fetch weather and post to Slack channel daily",

  "triggers": [
    {
      "type": "schedule",
      "cron": "0 9 * * *",
      "timezone": "America/Los_Angeles"
    }
  ],

  "inputs": {
    "city": {
      "type": "string",
      "default": "San Francisco"
    },
    "channel": {
      "type": "string",
      "default": "#weather"
    }
  },

  "steps": [
    {
      "id": "get_weather",
      "type": "action",
      "connector": "connector:community/weather@0.3.2",
      "action": "getWeather",
      "input": {
        "city": "{{ inputs.city }}"
      }
    },
    {
      "id": "post_slack",
      "type": "action",
      "connector": "connector:community/slack@1.2.0",
      "action": "sendMessage",
      "input": {
        "channel": "{{ inputs.channel }}",
        "text": "Today in {{ inputs.city }}: {{ steps.get_weather.output.temp }}°F, {{ steps.get_weather.output.conditions }}"
      }
    }
  ],

  "outputs": {
    "message_id": {
      "value": "{{ steps.post_slack.output.ts }}"
    }
  },

  "categories": ["automation", "notifications"],
  "requires": {
    "spec": ">=0.1.0 <0.3.0"
  }
}
```

### C) Agent Manifest

```json
{
  "schemaVersion": "0.1.0",
  "type": "agent",
  "name": "triage-bot",
  "namespace": "smartify",
  "version": "0.2.0",
  "displayName": "Issue Triage Bot",
  "description": "Automatically triage and categorize GitHub issues",

  "execution": {
    "backend": "native",
    "config": {
      "maxIterations": 8
    }
  },

  "model": {
    "provider": "anthropic",
    "id": "claude-3-5-sonnet-20241022"
  },

  "planner": {
    "strategy": "react",
    "maxTurns": 8
  },

  "toolset": [
    "connector:github/mcp@0.4.1",
    "connector:community/slack@1.2.0"
  ],

  "systemPrompt": "You are a helpful GitHub issue triage assistant. Analyze issues, assign labels, and notify relevant teams.",

  "policies": {
    "safety": "medium",
    "rateLimit": {
      "rpm": 200
    }
  },

  "io": {
    "inputSchema": {
      "type": "object",
      "properties": {
        "issueUrl": {"type": "string"}
      },
      "required": ["issueUrl"]
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "category": {"type": "string"},
        "priority": {"type": "string"},
        "assignee": {"type": "string"}
      }
    }
  },

  "categories": ["automation", "ai"],
  "license": "MIT"
}
```

### D) Bundle Manifest

```json
{
  "schemaVersion": "0.1.0",
  "type": "bundle",
  "name": "startup-starter",
  "namespace": "smartify",
  "version": "1.0.0",
  "displayName": "Startup Starter Pack",
  "description": "Essential workflows and connectors for startups",

  "includes": [
    "workflow:openworkflow/daily-weather-to-slack@1.0.0",
    "workflow:openworkflow/github-to-slack-notifications@2.1.0",
    "connector:community/slack@1.2.0",
    "connector:github/mcp@0.4.1",
    "agent:openworkflow/triage-bot@0.2.0"
  ],

  "categories": ["starter-kit"],
  "homepage": "https://docs.openworkflowspec.org/bundles/startup-starter"
}
```

## Registry Discovery

### Facets & Filters

The registry supports filtering by:

- **Type**: `connector`, `workflow`, `agent`, `bundle`
- **Namespace**: Publisher/organization
- **Categories**: `automation`, `communication`, `developer-tools`, `ai`, etc.
- **Kind** (connectors only): `mcp-server`, `http`, `sdk`, `lambda`, `custom`
- **Auth Type**: `apiKey`, `oauth2`, `bearer`, `none`
- **Runtime**: `http`, `mcp-server`, `lambda`, `sdk`

### Trust Levels & Badges

Connectors are classified by security trust level:

**🟢 Official** (`official`)
- Published and maintained by OpenWorkflow team
- Full security audit and code review
- Signed with Smartify's GPG key
- Guaranteed support and SLA
- Automatic security updates

**🟡 Verified** (`verified`)
- Publisher identity confirmed
- Community code review completed
- Signed with publisher's verified GPG key
- Listed in verified publishers registry
- Security audit summary available

**🟠 Community** (`community`)
- Public community submissions
- Basic malware scan passed
- SHA256 checksum verified
- Use with caution
- No security guarantees

**🔴 Unverified** (`unverified`)
- No verification performed
- Blocked by default in production
- Requires explicit opt-in
- High risk - not recommended

**Additional Badges:**
- **MCP Compatible** (`mcp`) - Works with MCP protocol
- **Agentic** (`agent`) - Uses AI agents
- **Audited** (`audited`) - Third-party security audit

## Versioning & Evolution

### Semantic Versioning

All resources follow SemVer:

- **Major (x.0.0)**: Breaking changes
- **Minor (1.x.0)**: New features, backward compatible
- **Patch (1.0.x)**: Bug fixes

### Immutability

Published versions are **immutable**. Once `connector:community/slack@1.2.0` is published, it cannot be modified.

### Distribution Tags

Use dist-tags for moving targets:

```bash
# Install latest version
smartify add connector:community/slack@latest

# Install from specific tag
smartify add connector:community/slack@canary
```

### Deprecation

Mark versions as deprecated:

```json
{
  "deprecated": true,
  "deprecationReason": "Security vulnerability fixed in 1.3.0",
  "replacement": "connector:community/slack@1.3.0"
}
```

### Compatibility

Specify compatibility requirements:

```json
{
  "requires": {
    "spec": ">=0.1.0 <0.3.0",
    "sdk-python": ">=0.6.0",
    "sdk-js": ">=0.5.0"
  }
}
```

## Publishing Workflow

```bash
# 1. Validate manifest
smartify validate connector.json

# 2. Test locally
smartify test connector.json

# 3. Publish to registry
smartify publish connector.json

# 4. Tag as latest
smartify tag connector:myorg/myconnector@1.0.0 latest
```

## Best Practices

1. **Descriptive Names**: Use clear, searchable names
2. **Complete Metadata**: Fill all optional fields for discoverability
3. **Semantic Versioning**: Follow SemVer strictly
4. **Documentation**: Link to comprehensive docs in `homepage`
5. **Categories**: Use standard categories for better search
6. **Testing**: Include test workflows/examples
7. **Security**: Sign packages with Sigstore for verification
8. **Dependencies**: Pin versions in workflows and bundles

## Next Steps

- [Connector Schema](./connector-schema.md) - Detailed connector specification
- [Workflow Schema](./workflow-schema.md) - Workflow composition
- [Agent Schema](./agent-schema.md) - Agent configuration
- [Registry Protocol](./registry-protocol.md) - API endpoints and operations
