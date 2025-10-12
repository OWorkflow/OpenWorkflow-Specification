# Execution Backends Specification

**Version:** 0.1.0
**Status:** Draft

## Overview

OpenWorkflow supports a pluggable backend model for agent and workflow execution. This architecture enables interoperability with multiple frameworks through adapter interfaces while maintaining Smartify's native runtime as the default execution engine.

**Backend Types:**
- **Native** — Smartify's built-in runtime (default)
- **LangChain** — LangChain framework adapter
- **Custom** — Implement adapter interface for other frameworks (OpenAI Agents, AutoGPT, etc.)

This specification defines the backend resolution order, adapter interface, and telemetry requirements. Framework-specific implementation details are deferred to adapter documentation.

## Backend Resolution Order

When executing a workflow step, the backend is resolved using this priority:

1. **Step-level override** (highest priority) — Workflow step specifies `backend: "langchain"`
2. **Agent default** — Referenced agent's `execution.backend` field
3. **Workflow default** — Workflow-level backend configuration (if supported by runtime)
4. **Global default** — Native runtime (lowest priority)

**Example:**
```yaml
workflows:
  - name: Hybrid Workflow
    steps:
      - id: analyze
        type: agent
        agent: agent:acme/analyzer@1.0.0  # Agent specifies backend: native
        backend: langchain  # Step override wins → uses langchain

      - id: process
        type: agent
        agent: agent:acme/processor@1.0.0  # Agent specifies backend: langchain
        # No step override → uses agent's backend (langchain)

      - id: store
        type: action
        connector: connector:community/db@1.0.0
        # No agent, no override → uses global default (native)
```

## Conceptual Backend Types

The specification defines backend capabilities at a conceptual level:

### Native Backend

Default execution engine optimized for OpenWorkflow workflows. Features:
- Direct connector execution
- Full specification compliance
- Deterministic execution semantics
- Minimal runtime overhead

### LangChain Backend

Adapter for LangChain framework. Features:
- Connector-to-tool translation
- LangChain ecosystem integration
- Framework-specific memory and callbacks
- Python and Node.js runtimes

### Custom Backends

Implement the backend adapter interface for other frameworks:
- OpenAI Agents API
- AutoGPT
- Semantic Kernel
- Custom orchestration engines

**Note:** Backend implementation details (installation, configuration, feature parity) are documented in adapter-specific guides, not this normative specification.

## Backend Declaration

### Agent Manifest

Agents declare their execution backend in the manifest:

```json
{
  "schemaVersion": "0.1.0",
  "type": "agent",
  "name": "research-assistant",
  "namespace": "smartify",
  "version": "1.0.0",

  "execution": {
    "backend": "langchain",
    "runtime": "python",
    "compatibility": {
      "langchain": ">=0.1.0 <0.3.0"
    },
    "config": {
      "agent_type": "react",
      "verbose": true
    }
  },

  "model": {
    "provider": "anthropic",
    "id": "claude-3-5-sonnet-20241022"
  },

  "toolset": [
    "connector:community/web-search@1.0.0",
    "connector:community/wikipedia@1.0.0"
  ]
}
```

#### Execution Block Fields

```typescript
{
  "execution": {
    "backend": "native" | "langchain" | "assistants" | "custom",  // Required
    "runtime": "python" | "node",                                   // Optional (required for langchain)
    "compatibility": {                                              // Optional
      "framework_name": "version_range"
    },
    "config": {                                                     // Optional: backend-specific config
      // Backend-specific configuration
    }
  }
}
```

**Default behavior:** If `execution` is omitted, defaults to `native` backend.

### Workflow Step Override

Workflows can override execution backend per-step:

```json
{
  "schemaVersion": "0.1.0",
  "type": "workflow",
  "name": "hybrid-workflow",

  "workflows": [
    {
      "name": "Mixed Backend Example",
      "steps": [
        {
          "id": "fetch_data",
          "type": "action",
          "connector": "connector:community/database@1.0.0",
          "action": "query",
          "execution": {
            "backend": "native"
          }
        },
        {
          "id": "analyze_with_ai",
          "type": "agent",
          "agent": "agent:openworkflow/data-analyst@1.0.0",
          "execution": {
            "backend": "langchain",
            "runtime": "python"
          },
          "with": {
            "data": "{{ steps.fetch_data.output }}"
          }
        },
        {
          "id": "store_results",
          "type": "action",
          "connector": "connector:community/database@1.0.0",
          "action": "insert",
          "execution": {
            "backend": "native"
          }
        }
      ]
    }
  ]
}
```

## Backend Resolution Priority

When executing a step, backend is resolved in this order:

1. **Step-level `execution` field** (highest priority)
2. **Referenced agent's `execution` field**
3. **Global default** (`native`)

### Resolution Examples

```json
// Example 1: Step overrides agent
{
  "id": "analyze",
  "type": "agent",
  "agent": "agent:acme/analyzer@1.0.0",  // Agent specifies "native"
  "execution": {
    "backend": "langchain"  // Step override wins → uses langchain
  }
}

// Example 2: Agent default
{
  "id": "process",
  "type": "agent",
  "agent": "agent:acme/processor@1.0.0"  // Agent specifies "langchain"
  // No step override → uses langchain
}

// Example 3: Global default
{
  "id": "transform",
  "type": "action",
  "connector": "connector:community/transform@1.0.0"
  // No agent, no step override → uses native
}
```

## Connector Capabilities

Connectors may declare capabilities to help backend adapters:

```json
{
  "schemaVersion": "0.1.0",
  "type": "connector",
  "name": "web-search",
  "namespace": "smartify",
  "version": "1.0.0",

  "capabilities": {
    "runtime": "http",
    "frameworks": {
      "langchain": {
        "tool_prefix": "search_",
        "supports_streaming": false,
        "schema_format": "json_schema"
      }
    }
  },

  "actions": [
    {
      "name": "search",
      "description": "Search the web"
    }
  ]
}
```

**Capabilities fields:**

```typescript
{
  "capabilities": {
    "runtime": "http" | "mcp-server" | "sdk" | "lambda",  // Connector type
    "frameworks": {                                         // Optional framework hints
      "langchain": {
        "tool_prefix": string,           // Prefix for tool names
        "supports_streaming": boolean,   // Stream support
        "schema_format": string          // Schema format
      }
    }
  }
}
```

**Note:** Capabilities are **descriptive only** and don't affect validation.

## SDK Contract

### Backend Registration

SDKs must provide a backend registration interface:

```python
from openworkflow import OpenWorkflow, Backend

# Register LangChain backend
langchain_backend = LangChainBackend(
    runtime="python",
    version="0.2.0"
)
openworkflow.register_backend("langchain", langchain_backend)

# Use in workflow
workflow = Workflows.from_file("workflow.yaml")
result = workflow.execute()  # Automatically routes to correct backend
```

### Backend Interface

All backends must implement this interface:

```python
class Backend(ABC):
    @abstractmethod
    def invoke(
        self,
        manifest: dict,
        input: dict,
        context: ExecutionContext
    ) -> dict:
        """
        Execute an agent or action.

        Args:
            manifest: Agent or connector manifest
            input: Input parameters
            context: Execution context (run_id, secrets, etc.)

        Returns:
            Structured result dictionary
        """
        pass

    @abstractmethod
    def get_info(self) -> BackendInfo:
        """Return backend metadata (name, version, capabilities)"""
        pass
```

### Execution Context

Standardized context passed to all backends:

```python
@dataclass
class ExecutionContext:
    run_id: str              # Unique execution ID
    workflow_id: str         # Workflow ID (if applicable)
    node_id: str             # Node ID (if applicable)
    secrets: dict            # Secret values
    environment: dict        # Environment variables
    trace_id: str            # Distributed trace ID
    deadline: datetime       # Execution deadline
    metadata: dict           # Additional metadata
```

## LangChain Integration

### Connector to Tool Translation

OpenWorkflow connectors are automatically translated to LangChain tools:

**Smartify Connector:**
```yaml
connector:
  name: web-search
  actions:
    - name: search
      description: Search the web
      input:
        type: object
        properties:
          query:
            type: string
```

**Generated LangChain Tool:**
```python
from langchain.tools import Tool

search_tool = Tool(
    name="web_search_search",
    description="Search the web",
    func=lambda query: connector.execute("search", {"query": query})
)
```

### Agent Configuration

LangChain-specific configuration in agent manifest:

```json
{
  "execution": {
    "backend": "langchain",
    "runtime": "python",
    "config": {
      "agent_type": "react",           // AgentType
      "max_iterations": 10,
      "handle_parsing_errors": true,
      "verbose": true,
      "memory_type": "buffer"          // Optional: conversation memory
    }
  }
}
```

### Python SDK Example

```python
from openworkflow import OpenWorkflow, Workflows
from openworkflow.backends import LangChainBackend

# Initialize with LangChain backend
openworkflow = OpenWorkflow()
openworkflow.register_backend("langchain", LangChainBackend())

# Load agent that uses LangChain
agent = openworkflow.load_agent("agent:acme/researcher@1.0.0")

# Execute
result = agent.execute({
    "task": "Research the latest AI developments"
})

print(result["output"])
```

### Node.js SDK Example

```javascript
import { OpenWorkflow } from '@openworkflow/sdk';
import { LangChainBackend } from '@openworkflow/backend-langchain';

const openworkflow = new OpenWorkflow();
openworkflow.registerBackend('langchain', new LangChainBackend());

const agent = await openworkflow.loadAgent('agent:acme/researcher@1.0.0');
const result = await agent.execute({
  task: 'Research the latest AI developments'
});
```

## Telemetry Requirements

All backend adapters MUST emit standardized telemetry for observability:

### Required Telemetry Fields

Execution events must include:

```json
{
  "event_id": "evt_123",
  "type": "step.execution.completed",
  "timestamp": "2025-10-07T12:00:00Z",

  "execution": {
    "backend": "langchain",            // Required: backend name
    "runtime": "python",                // Optional: runtime environment
    "adapter_version": "0.2.0",        // Required: adapter version
    "duration_ms": 3420,                // Required: execution duration
    "token_usage": {                    // Optional: if LLM execution
      "prompt_tokens": 150,
      "completion_tokens": 80,
      "total_tokens": 230
    }
  },

  "result": {
    "status": "success",
    "output": {...}
  }
}
```

### Trace Attributes

Backends should emit OpenTelemetry span attributes:
- `backend.name` — Backend identifier ("native", "langchain", "custom")
- `backend.version` — Adapter version
- `backend.runtime` — Runtime environment (if applicable)
- `step.id` — Step identifier
- `step.type` — Step type ("action", "agent", "logic")
- `agent.id` — Agent identifier (if agent step)
- `connector.id` — Connector identifier (if action step)

## Error Handling

### New Error Codes

**UNAVAILABLE**
```json
{
  "status": "error",
  "code": "UNAVAILABLE",
  "message": "Backend 'langchain' is not installed or configured",
  "details": {
    "backend": "langchain",
    "suggestion": "Install: pip install smartify-backend-langchain"
  }
}
```

**BACKEND_ERROR**
```json
{
  "status": "error",
  "code": "BACKEND_ERROR",
  "message": "LangChain agent execution failed",
  "details": {
    "backend": "langchain",
    "original_error": "OutputParserException: Could not parse LLM output",
    "trace": "..."
  }
}
```

## CLI Integration

### Backend Management

```bash
# List available backends
smartify backends list

# Output:
# native      1.0.0    [installed]  OpenWorkflow native runtime
# langchain   0.2.0    [installed]  LangChain integration
# assistants  -        [not installed]

# Install backend
pip install smartify-backend-langchain

# Test backend
smartify backend test langchain
```

### Execution with Backend Override

```bash
# Run agent with specific backend
smartify agent run agent:acme/researcher@1.0.0 \
  --backend langchain \
  --input task="Research AI"

# Run workflow with backend preference
smartify workflow run workflow.yaml \
  --prefer-backend langchain

# Validate backend compatibility
smartify agent validate agent.json --check-backends
```

## Validation Rules

Validators must enforce:

1. **Backend field validation**
   - Must be one of: `native`, `langchain`, `assistants`, `custom`
   - If omitted, defaults to `native`

2. **Runtime compatibility**
   - LangChain requires `runtime` field (`python` or `node`)
   - Native backend ignores `runtime` field

3. **Version compatibility**
   - Compatibility ranges must be valid semver
   - SDK warns on version mismatches

4. **Step override safety**
   - Step can override agent backend
   - Step can specify backend for actions (defaults to native)

5. **Capabilities are descriptive**
   - Connector capabilities don't affect execution
   - Used for documentation and tooling only

## Registry Badges

Backends are reflected in registry badges:

- **LangChain Compatible** (`langchain`) - Works with LangChain backend
- **Native Optimized** (`native`) - Optimized for OpenWorkflow native runtime
- **Multi-Backend** (`multi-backend`) - Supports multiple backends

## Best Practices

### When to Use Native

✅ Direct API integrations
✅ Simple action orchestration
✅ Performance-critical workflows
✅ Deterministic behavior required

### When to Use LangChain

✅ Complex LLM reasoning
✅ Access to LangChain ecosystem
✅ Migrating existing LangChain code
✅ Research and experimentation
✅ Advanced memory/callback features

### Mixing Backends

```json
{
  "steps": [
    {
      "id": "fast_lookup",
      "execution": {"backend": "native"}  // Fast, deterministic
    },
    {
      "id": "ai_reasoning",
      "execution": {"backend": "langchain"}  // Complex reasoning
    },
    {
      "id": "store_result",
      "execution": {"backend": "native"}  // Fast write
    }
  ]
}
```

## Migration Guide

### From LangChain to Smartify

1. Define connectors for your LangChain tools
2. Create agent manifest with `backend: langchain`
3. Use existing LangChain code with minimal changes
4. Optionally migrate to native for better performance

### Testing Parity

Conformance tests ensure output parity between backends:

```python
# Test agent on both backends
agent_manifest = {...}

native_result = execute_agent(agent_manifest, backend="native")
langchain_result = execute_agent(agent_manifest, backend="langchain")

assert_similar_outputs(native_result, langchain_result)
```

## Conformance Testing

Required conformance tests:

1. ✅ Backend resolution priority (step > agent > default)
2. ✅ Output parity between native and LangChain
3. ✅ Connector to tool translation accuracy
4. ✅ Timeout and cancellation handling
5. ✅ Backend metadata in telemetry events
6. ✅ Error code standardization (UNAVAILABLE, BACKEND_ERROR)
7. ✅ Version compatibility warnings

## Examples

See [examples/backends/](../examples/backends/) for:
- Native agent execution
- LangChain agent execution
- Mixed backend workflow
- Connector with LangChain capabilities

## Next Steps

- [Agent Schema](./agent-schema.md) - Define agents with backends
- [Workflow Schema](./workflow-schema.md) - Mix backends in workflows
- [SDK Contract](./sdk-contract.md) - Implement backend support
- [Connector Schema](./connector-schema.md) - Add framework capabilities
