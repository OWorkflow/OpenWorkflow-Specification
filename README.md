# OpenWorkflow

**Version:** 0.1.0
**Status:** Draft
**Last Updated:** October 2025

> **Note:** This specification follows [Semantic Versioning](https://semver.org/). Version 0.x.x indicates pre-release status where breaking changes may occur between minor versions. Version 1.0.0 will signify API stability.

## Status: Draft v0.1.0

This is an early draft of the OpenWorkflow specification. Feedback and contributions are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md) for how to participate.

## ⚠️ Security Notice (v0.1.0 Pre-Release)

This is a pre-release specification. Production deployments should implement additional security controls:

- **Template expression sandboxing** - Prevent secret extraction via user inputs
- **Input validation and sanitization** - SQL injection, command injection, SSRF protection
- **Secret redaction** - Prevent accidental secret exposure in logs/outputs
- **Access control (RBAC)** - Workflow and connector permissions
- **Connector signature verification** - Supply chain security

See [SECURITY-REVIEW.md](./SECURITY-REVIEW.md) for comprehensive security analysis and recommendations.

## Vision

**OpenWorkflow** is an open specification for building portable AI workflows and automations.

- **OpenWorkflow** — The open specification defining declarative schemas for connectors, workflows, and agents
- **Smartify Runtime** — The reference execution engine that runs OpenWorkflow specifications locally or self-hosted
- **Smartify Cloud** — The managed platform that scales OpenWorkflow applications globally

This specification defines how developers can **build once, deploy anywhere** — creating connectors and workflows using OpenWorkflow that run seamlessly across Smartify Runtime (local/self-hosted) or Smartify Cloud using identical APIs.

### Reference Implementation

The official reference implementation of OpenWorkflow is **Smartify Runtime**, which provides:
- Native execution of connectors, workflows, and agents
- Pluggable backend support (LangChain, custom adapters)
- Local and cloud deployment modes
- SDK libraries for Python, JavaScript, and Go

For the Smartify Runtime implementation, see: *(link to be added when repository is public)*

### Core Principles

- **Open Standard**: OpenWorkflow is a free, open specification — anyone can implement it
- **Declarative over imperative**: Define what your connector does, not how to integrate it
- **Zero lock-in**: Work with your existing code and infrastructure
- **SDK-first**: Lightweight integration without enforcing endpoints or frameworks
- **Community-driven**: Open-source registry and workflow schemas

## Scope

### In Scope

This specification defines:

- **Schemas** for connectors, agents, workflows, and bundles
- **Logic node catalog** with portable semantics (conditionals, loops, error handling, transforms)
- **Naming and versioning** conventions for registry resources
- **Security primitives** (authentication, authorization, secrets management, template sandboxing)
- **Registry protocol** for discovery, publishing, and dependency resolution
- **SDK contract** defining language-agnostic integration interfaces

### Not in Scope

This specification intentionally does NOT define:

- **Execution engine internals** — Runtime implementation details are left to Smartify Runtime and other implementations
- **UI/editor** — Visual workflow builders and editors are application-level concerns
- **Secret storage backends** — Specific vault implementations (runtime-dependent)
- **Billing and quotas** — Commercial platform features (Smartify Cloud-specific)
- **Deployment topologies** — Infrastructure patterns (Kubernetes, serverless, etc.) are implementation choices

### Why OpenWorkflow + Smartify?

Think of OpenWorkflow like OpenAPI/Swagger for workflows:
- **OpenWorkflow** = The specification (open standard, Apache 2.0 licensed)
- **Smartify Runtime** = The reference implementation (like Swagger Codegen)
- **Smartify Cloud** = The managed platform (like AWS API Gateway for APIs)

You write OpenWorkflow specs, run them with Smartify Runtime anywhere, and optionally scale with Smartify Cloud.

## What This Spec Covers

1. **Connector Schema** - Declarative format for capability providers (APIs, MCP servers, SDKs)
2. **Workflow Definition** - Composable DAGs orchestrating connectors and agents
3. **Agent Schema** - AI agent configuration with model selection and toolsets
4. **Registry Taxonomy** - Resource types, naming conventions, and discovery
5. **SDK Contract** - Language-agnostic integration patterns
6. **Execution Modes** - Local, self-hosted, and cloud runtime options

## Quick Start

### Define a Connector

```yaml
# weather-connector.yaml
connector:
  type: connector
  kind: http
  name: weather
  namespace: community
  version: 1.0.0
  displayName: Weather API
  description: Get current weather for any location
  categories: [weather, api]

actions:
  - name: getCurrentWeather
    description: Fetch current weather conditions
    input:
      type: object
      properties:
        location:
          type: string
          description: City name or coordinates
      required: [location]

    handler:
      # Option 1: HTTP API
      http:
        url: https://api.weather.com/current
        method: POST

      # Option 2: SDK function
      # function: weather.getCurrentWeather

      # Option 3: MCP server
      # mcp:
      #   endpoint: wss://mcp.weather.com
      #   tool: get_weather
```

### Use in a Workflow

```yaml
# workflows.yaml
workflows:
  - name: Daily Weather Report
    triggers:
      - schedule: "0 8 * * *"  # Every day at 8am

    steps:
      - id: fetch_weather
        type: action
        connector: connector:community/weather@1.0.0
        action: getCurrentWeather
        with:
          location: "San Francisco"

      - id: send_notification
        type: action
        connector: connector:community/slack@1.2.0
        action: sendMessage
        with:
          channel: "#general"
          text: "Today's weather: {{ steps.fetch_weather.output.temperature }}°"
```

### Execute Anywhere

```python
# Local execution with Smartify Runtime
from smartify import Workflows

workflows = Workflows.from_file("workflows.yaml")
result = workflows.execute("Daily Weather Report")

# Or deploy to Smartify Cloud
workflows.register(cloud_api_key="sk_smartify_...")
```

## Architecture

```
┌─────────────────────────────────────┐
│       Smartify Cloud (Optional)     │
│   - Managed OpenWorkflow runtime    │
│   - Connector registry              │
│   - Monitoring & observability      │
│   - Auto-scaling & SLA guarantees   │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────────┐
        │  Smartify SDK   │
        │   (Any Lang)    │
        └──────┬──────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼────┐ ┌──▼──────┐ ┌─▼──────┐
│ Native │ │LangChain│ │  HTTP  │
│Backend │ │ Backend │ │  API   │
└────────┘ └─────────┘ └────────┘
```

### Execution Backends

Smartify Runtime supports pluggable execution backends for maximum flexibility:

- **Native**: Built-in Smartify execution engine (default)
- **LangChain**: Execute through LangChain framework (Python/Node)
- **HTTP**: Connect to any HTTP-based workflow service
- Mix backends within a single workflow for optimal performance

## Deployment Models

| Model | Description | Use Case |
|-------|-------------|----------|
| **Local** | Run Smartify Runtime in-process via SDK | Development, testing, embedded apps |
| **Self-Hosted** | Deploy Smartify Runtime + connector services on your infrastructure | Enterprise, compliance, data residency |
| **Smartify Cloud** | Fully managed OpenWorkflow runtime with auto-scaling | SaaS apps, production workloads, quick deployment |
| **Hybrid** | Smartify Runtime locally + Smartify Cloud registry | Enterprise with centralized governance |

## Specification Documents

### Core Specs
- [Registry Taxonomy](./specs/registry-taxonomy.md) - Resource types, naming, and manifest formats
- [Connector Schema](./specs/connector-schema.md) - Capability provider definition
- [Workflow Schema](./specs/workflow-schema.md) - DAG composition and orchestration
- [Workflow Logic Steps](./specs/workflow-logic-steps.md) - Control flow, loops, branching, error handling
- [Agent Schema](./specs/agent-schema.md) - AI agent configuration
- [SDK Contract](./specs/sdk-contract.md) - Language-agnostic integration
- [**Security**](./specs/security.md) - Authentication, secrets, RBAC, and security best practices

### Integration Patterns
- [Registry Protocol](./specs/registry-protocol.md) - Discovery, search, and publishing
- [Execution Backends](./specs/execution-backends.md) - Native and LangChain runtime support
- [Execution Modes](./specs/execution-modes.md) - Local, self-hosted, and cloud deployment
- [MCP Integration](./specs/mcp-integration.md) - Model Context Protocol connectors

### Advanced Topics
- [Security Model](./specs/security.md) - Authentication, secrets management
- [Observability](./specs/observability.md) - Logging, metrics, tracing
- [Error Handling](./specs/error-handling.md) - Retries, timeouts, circuit breakers

## Example Implementations

See [examples/](./examples/) for complete implementations:
- [Weather](./examples/weather/) - HTTP connector + workflows
- [Calculator](./examples/calculator/) - SDK function connector

## Registry

Browse and contribute at [registry.openworkflowspec.org](https://registry.openworkflowspec.org)

**Resource Types:**
- **Connectors**: Slack, GitHub (MCP), Stripe, AWS, OpenAI
- **Workflows**: Automation templates, incident response, CI/CD (with inline human-in-the-loop steps)
- **Agents**: Triage bots, customer support, code review
- **Bundles**: Starter kits, industry templates

## Contributing

We welcome contributions to:
- Connector implementations
- SDK improvements
- Documentation
- Specification enhancements

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

This specification is released under the MIT License. See [LICENSE](./LICENSE) for details.

---

**Questions?** Join our community at [community.openworkflowspec.org](https://community.openworkflowspec.org)
