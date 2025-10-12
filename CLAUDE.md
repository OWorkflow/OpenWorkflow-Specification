# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is the **OpenWorkflow** specification repository - an open standard for building portable AI workflows and automations. This is a **specification-only repository** (no implementation code). Think of it as similar to OpenAPI/Swagger but for AI workflows and automation.

**Key distinction:**
- **OpenWorkflow** — The open specification (Apache 2.0 licensed)
- **Smartify Runtime** — Reference execution engine that runs OpenWorkflow specifications
- **Smartify Cloud** — Managed platform for scaling OpenWorkflow applications

## Core Architecture

### Resource Types

The specification defines four primary resource types with consistent naming:

```
<type>:<namespace>/<name>@<version>
```

1. **Connectors** (`connector:community/slack@1.2.0`)
   - Package capability providers (APIs, MCP servers, SDKs, Lambda functions)
   - Kinds: `mcp-server`, `http`, `sdk`, `lambda`, `custom`
   - Actions: Individual capabilities with input/output schemas
   - Handlers: Implementation (HTTP endpoint, SDK function, command, Kafka)

2. **Workflows** (`workflow:openworkflow/daily-weather-to-slack@1.0.0`)
   - Declarative DAGs that compose connectors and agents
   - Multiple workflows can be defined in a single `workflows.yaml` file (always plural key)
   - Support triggers (schedule, webhook, event, manual), conditional logic, loops, parallel execution
   - Logic nodes execute natively; agent nodes can use pluggable backends

3. **Agents** (`agent:openworkflow/customer-support@1.0.0`)
   - Reusable AI policies combining LLM capabilities, tools, memory, and guardrails
   - Backend-agnostic: supports native runtime, LangChain, and other backends via adapters (e.g., OpenAI Agents)
   - Configuration includes: model selection, personality, knowledge base (RAG), toolset, guardrails

4. **Bundles** (`bundle:openworkflow/startup-starter@1.0.0`)
   - Curated collections of related resources with pinned versions
   - Used for starter kits, company-specific collections, industry templates

### MCP Integration Pattern

- MCP servers are registered as connectors with `kind: "mcp-server"`
- MCP tools become **actions** in the connector
- Avoids naming collision: "connector" wraps the MCP server; MCP "tools" become connector "actions"

### Execution Backends

Workflows and agents support pluggable execution backends:
- **Native**: Built-in Smartify execution engine (default)
- **LangChain**: Execute through LangChain framework (Python/Node)
- **Custom Adapters**: Implement backend interface for other frameworks (e.g., OpenAI Agents API)
- Can mix backends within a single workflow at the step level

Backend resolution priority:
1. Step-level override
2. Agent/workflow default
3. Global default (native)

## File Organization

```
specs/                          # Core specification documents
├── connector-schema.md         # Connector definition format
├── workflow-schema.md          # Workflow composition and orchestration
├── workflow-logic-steps.md     # Control flow, loops, branching, error handling
├── agent-schema.md            # AI agent configuration
├── registry-taxonomy.md       # Resource types and naming conventions
├── sdk-contract.md            # Language-agnostic SDK requirements
├── security.md                # Auth, secrets, RBAC, security best practices
├── execution-backends.md      # Native and LangChain runtime support
├── execution-modes.md         # Local, self-hosted, cloud deployment
└── registry-protocol.md       # Discovery, search, publishing

examples/                      # Complete example implementations
├── weather/                   # HTTP connector + workflows
└── calculator/               # SDK function connector

README.md                     # Main specification overview
CONTRIBUTING.md              # Contribution guidelines
```

## Key Concepts

### Security Architecture

**Template Expression Sandboxing:**
- Handler configs (trusted): Can access `${secrets.*}`, `${env.*}`, `${input.*}`
- User inputs (untrusted): Sandboxed context that CANNOT access `${secrets.*}`
- Runtime detects and blocks secret exposure in outputs

**Authentication & Authorization:**
- Connectors support: `apiKey`, `oauth2`, `bearer`, HMAC signature, none
- Workflows support RBAC with roles and permissions
- Step-level authorization for sensitive operations
- Approval workflows for high-risk actions

**Input Validation:**
- Always use parameterized queries (NOT string interpolation) for SQL/commands
- URL validation with allowlists/blocklists for SSRF protection
- Strict JSON Schema validation with `pattern`, `format`, `maxLength`

### Workflow Features

**File Format:**
- Always use plural `workflows:` key (even for single workflow)
- Allows 1-N workflows per file without restructuring

**Data Flow:**
- Template expressions: `{{ inputs.field }}`, `{{ steps.step_id.output.field }}`
- Context model: `inputs`, `env`, `secrets`, `steps.<id>.output`
- Filters available: `upper`, `lower`, `json`, `length`, etc.

**Note:** Use `steps.<id>` consistently throughout workflows (not `nodes.*`). The step `id` field identifies each step for reference.

**Control Flow:**
- Conditional execution: `condition: "{{ steps.check.output.value > 90 }}"`
- Loops: `for_each: "{{ steps.get_cities.output.cities }}"` with `parallel: true` option
- Error handling: `continue_on_error`, retry with exponential backoff
- Timeouts and circuit breakers

### Versioning

**Specification Versioning:**
- Follows Semantic Versioning (SemVer)
- Version 0.x.x = pre-release (breaking changes may occur between minor versions)
- Version 1.0.0 = API stability guaranteed

**Resource Versioning:**
- All registry resources follow SemVer
- Published versions are immutable
- Distribution tags for moving targets: `@latest`, `@canary`
- Deprecation metadata with replacement recommendations

## Development Workflow

### Validating Specifications

When editing spec files:
```bash
# No CLI implementation exists yet - this is spec-only
# Validation would be done by reference implementations
```

### Creating Examples

Examples should include:
1. Complete connector definition (YAML/JSON)
2. Example workflows using the connector
3. README with usage instructions
4. Implementation notes (error handling, rate limits, etc.)

### Editing Specs

**Major changes require:**
1. Open GitHub issue describing proposed change
2. Community discussion
3. Create proposal document if needed
4. Submit PR with spec changes
5. Review and approval by maintainers

**Minor changes (no proposal needed):**
- Clarifications and typo fixes
- Additional examples
- Documentation improvements
- Non-breaking additions

## Common Patterns

### Connector Handler Types

1. **HTTP Handler** - External REST/HTTP API
2. **SDK Function** - In-process function call
3. **Command Handler** - Shell command/script execution
4. **Kafka Handler** - Pub/sub messaging

### Workflow Patterns

**Human-in-the-Loop:**
- Defined inline within workflows (not separate registry resources)
- Approval steps with timeout and escalation policies

**Subworkflows:**
- Reference other workflows: `workflow: data-etl-pipeline`
- Version constraints: `version: "1.2.0"` or `version: "~1.2"`

**Guardrails:**
- Step-level guardrails override agent defaults
- Content filtering, cost controls, behavioral constraints
- Output validation with JSON Schema

## Testing and Quality

### Specification Quality

When modifying specs:
- Maintain consistent terminology across all documents
- Provide complete examples that work end-to-end
- Reference related specs in "Next Steps" sections
- Include security considerations for relevant features
- Use clear, searchable headings and structure

### Example Quality

Examples should:
- Include complete, working configurations
- Demonstrate best practices
- Show both simple and advanced usage
- Include error handling patterns
- Link back to relevant spec documents

## Important Security Notes

**Pre-Release Security (v0.1.0):**
Production deployments should implement:
- Template expression sandboxing (prevent secret extraction)
- Input validation and sanitization (SQL injection, SSRF, command injection)
- Secret redaction in logs/outputs
- Access control (RBAC)
- Connector signature verification

See `specs/security.md` for comprehensive security guidance.

## Writing Style

Specifications should:
- Start with clear, concise overview
- Provide complete examples early
- Include both simple and advanced patterns
- Use consistent YAML/JSON formatting (2 spaces, required fields first)
- Cross-reference related specs
- Include "Best Practices" and "Security Considerations" sections

## Related Resources

- Main specification URL: `https://docs.openworkflowspec.org`
- Registry: `https://registry.openworkflowspec.org`
- Community: `https://community.openworkflowspec.org`
- Security contact: `security@openworkflowspec.org`
