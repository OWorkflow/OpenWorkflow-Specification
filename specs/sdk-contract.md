# SDK Contract Specification

**Version:** 0.1.0
**Status:** Draft

## Overview

The OpenWorkflow SDK contract defines language-agnostic interfaces and behaviors that all SDK implementations must provide. This specification focuses on the contract, not implementation details.

**What this defines:**
- Core interfaces (connector registration, workflow execution, backend registration)
- Error taxonomy and handling requirements
- Context shape and data access patterns
- Cancellation and timeout semantics
- Tracing hooks and telemetry requirements

**What this does NOT define:**
- Language-specific API design (defer to idiomatic patterns)
- Implementation algorithms (e.g., retry logic internals)
- Framework integrations (FastAPI, Express, etc. are optional)

## Design Principles

1. **Minimal dependencies**: SDKs should be lightweight
2. **Idiomatic code**: Follow language-specific conventions
3. **Framework agnostic**: Work with any web framework or runtime
4. **Progressive enhancement**: Start simple, add features as needed

## Core SDK Components

### 1. Connector Registration

SDKs must provide a way to register connectors from files or objects:

**Python:**
```python
from openworkflow import OpenWorkflow

# From file
openworkflow = OpenWorkflow()
openworkflow.register_connector("./connectors/weather.yaml")

# From object
connector_config = {
    "connector": {
        "type": "connector",
        "kind": "http",
        "name": "weather",
        "namespace": "smartify",
        "version": "1.0.0"
    },
    "actions": [...]
}
openworkflow.register_connector(connector_config)
```

**JavaScript:**
```javascript
import { OpenWorkflow } from '@openworkflow/sdk';

const openworkflow = new OpenWorkflow();
await openworkflow.registerConnector('./connectors/weather.yaml');

// Or from object
await openworkflow.registerConnector(connectorConfig);
```

**Go:**
```go
import "github.com/Open-Workflow/sdk-go"

s := openworkflow.New()
err := s.RegisterConnector("./connectors/weather.yaml")
```

### 2. Action Handler Registration

For SDK function handlers, provide a decorator/annotation pattern:

**Python:**
```python
from openworkflow import action

@action("weather.get_current_weather")
def get_weather(location: str) -> dict:
    """Handler implementation"""
    return {"temperature": 72, "conditions": "sunny"}

# Or register manually
openworkflow.register_handler("weather.get_current_weather", get_weather)
```

**JavaScript:**
```javascript
import { action } from '@openworkflow/sdk';

@action('weather.get_current_weather')
async function getWeather({ location }) {
    return { temperature: 72, conditions: 'sunny' };
}

// Or register manually
openworkflow.registerHandler('weather.get_current_weather', getWeather);
```

**Go:**
```go
func GetWeather(input map[string]interface{}) (map[string]interface{}, error) {
    location := input["location"].(string)
    return map[string]interface{}{
        "temperature": 72,
        "conditions": "sunny",
    }, nil
}

s.RegisterHandler("weather.get_current_weather", GetWeather)
```

### 3. Workflow Execution

Execute workflows locally:

**Python:**
```python
from openworkflow import Workflows

# Load workflows
workflows = Workflows.from_file("./workflows.yaml")

# Execute specific workflow
result = workflows.execute("Daily Weather Report")

# Execute with custom inputs
result = workflows.execute("Daily Weather Report", inputs={"location": "New York"})

# Execute all workflows
results = workflows.execute_all()

# Async execution
result = await workflows.execute_async("Daily Weather Report")
```

**JavaScript:**
```javascript
import { Workflows } from '@openworkflow/sdk';

const workflows = await Workflows.fromFile('./workflows.yaml');

// Execute specific workflow
const result = await workflows.execute('Daily Weather Report');

// With inputs
const result = await workflows.execute('Daily Weather Report', { location: 'New York' });

// Execute all
const results = await workflows.executeAll();
```

### 4. Cloud Integration

Register with OpenWorkflow Cloud for managed execution:

**Python:**
```python
openworkflow = OpenWorkflow(api_key="sk_...")

# Auto-register all loaded plugins
openworkflow.sync_to_cloud()

# Or register individual connector
openworkflow.register_connector("weather.yaml", cloud=True)

# Execute in cloud
workflow = Workflow.from_file("workflow.yaml")
result = workflow.execute(mode="cloud")
```

**JavaScript:**
```javascript
const openworkflow = new OpenWorkflow({ apiKey: 'sk_...' });

await openworkflow.syncToCloud();

// Execute in cloud
const workflow = await Workflow.fromFile('workflow.yaml');
const result = await workflow.execute({ mode: 'cloud' });
```

## SDK Configuration

### Initialization Options

```python
openworkflow = OpenWorkflow(
    api_key="sk_...",              # Optional: OpenWorkflow Cloud API key
    router_url="http://...",       # Optional: Custom MCP Router URL
    execution_mode="local",        # "local", "cloud", or "hybrid"
    timeout=300,                   # Default timeout for actions
    retry_config={                 # Default retry behavior
        "max_attempts": 3,
        "backoff": "exponential"
    },
    environment={                  # Environment variables for plugins
        "API_KEY": "...",
    },
    secrets_manager=None,          # Optional: custom secrets provider
    observability={                # Optional: monitoring config
        "enabled": True,
        "endpoint": "http://...",
        "sample_rate": 1.0
    }
)
```

## Execution Modes

### Local Execution

Actions execute in the same process:

```python
# All actions run locally
openworkflow = OpenWorkflow(execution_mode="local")
result = workflow.execute()  # Runs in-process
```

**Requirements:**
- All action handlers must be registered or accessible via HTTP
- No network calls to OpenWorkflow infrastructure

### Cloud Execution

Actions execute in OpenWorkflow Cloud:

```python
openworkflow = OpenWorkflow(api_key="sk_...", execution_mode="cloud")
result = workflow.execute()  # Runs in OpenWorkflow Cloud
```

**Requirements:**
- Valid API key
- Plugin must be published to registry or uploaded

### Hybrid Execution

Mix local and cloud execution:

```python
openworkflow = OpenWorkflow(execution_mode="hybrid")

# Per-workflow override
result = workflow.execute(mode="cloud")

# Per-action override in workflow definition
# actions:
#   - name: local_action
#     connector: connector:community/my-connector@1.0.0
#     execution: local
#   - name: cloud_action
#     connector: connector:external/connector@1.0.0
#     execution: cloud
```

## Handler Contract

Action handlers must follow this signature:

### Input

Handlers receive a dictionary/object with action input parameters:

```python
def handler(input: dict) -> dict:
    location = input.get("location")
    # ...
```

Or use typed parameters (Python/TypeScript):

```python
from pydantic import BaseModel

class WeatherInput(BaseModel):
    location: str

@action("weather.get_current_weather")
def handler(input: WeatherInput) -> dict:
    # input is validated automatically
    return {"temperature": 72}
```

### Output

Handlers must return:
- **Success**: Dictionary matching the action's output schema
- **Error**: Raise an exception

```python
def handler(input: dict) -> dict:
    if not input.get("location"):
        raise ValueError("Location is required")

    return {"temperature": 72, "conditions": "sunny"}
```

### Error Handling

SDKs automatically catch exceptions and format errors using the standard error taxonomy.

## Error Taxonomy

All SDK implementations must use this standardized error code taxonomy:

### Error Codes

**VALIDATION** — Input validation failure
```json
{
  "status": "error",
  "code": "VALIDATION",
  "message": "Input validation failed: location is required",
  "details": {
    "field": "location",
    "constraint": "required"
  }
}
```

**UNAVAILABLE** — Backend or connector not available
```json
{
  "status": "error",
  "code": "UNAVAILABLE",
  "message": "Backend 'langchain' is not installed",
  "details": {
    "backend": "langchain",
    "suggestion": "Install: pip install openworkflow-backend-langchain"
  }
}
```

**BACKEND_ERROR** — Backend execution failure
```json
{
  "status": "error",
  "code": "BACKEND_ERROR",
  "message": "LangChain agent execution failed",
  "details": {
    "backend": "langchain",
    "original_error": "OutputParserException: Could not parse LLM output"
  }
}
```

**TIMEOUT** — Execution exceeded deadline
```json
{
  "status": "error",
  "code": "TIMEOUT",
  "message": "Step execution exceeded timeout of 30s",
  "details": {
    "timeout_ms": 30000,
    "elapsed_ms": 31200
  }
}
```

**CANCELED** — Execution canceled by user
```json
{
  "status": "error",
  "code": "CANCELED",
  "message": "Execution canceled by user",
  "details": {
    "canceled_at": "2025-10-11T12:00:00Z"
  }
}
```

**INTERNAL_ERROR** — SDK or runtime internal error
```json
{
  "status": "error",
  "code": "INTERNAL_ERROR",
  "message": "Unexpected runtime error",
  "details": {
    "error_type": "NullPointerException",
    "stack_trace": "..."
  }
}
```

## Secrets Management

SDKs support pluggable secrets providers:

**Python:**
```python
from openworkflow.secrets import AWSSecretsManager, EnvSecretsProvider

# Use AWS Secrets Manager
openworkflow = OpenWorkflow(
    secrets_manager=AWSSecretsManager(region="us-east-1")
)

# Use environment variables (default)
openworkflow = OpenWorkflow(
    secrets_manager=EnvSecretsProvider()
)

# Custom provider
class CustomSecrets:
    def get(self, key: str) -> str:
        # Fetch from your secrets backend
        return "secret_value"

openworkflow = OpenWorkflow(secrets_manager=CustomSecrets())
```

In handlers, access secrets via context:

```python
@action("github.create_issue")
def create_issue(input: dict, context: dict) -> dict:
    token = context["secrets"]["GITHUB_TOKEN"]
    # Use token
```

## Observability

SDKs emit telemetry for monitoring:

### Logging

```python
import logging

openworkflow = OpenWorkflow(
    log_level=logging.INFO,
    log_format="json"  # or "text"
)

# SDK logs action execution, errors, timing
```

### Metrics

SDKs expose metrics for:
- Action execution count
- Action duration
- Error rate
- Queue depth (for async execution)

**Python (Prometheus):**
```python
from openworkflow.observability import PrometheusExporter

exporter = PrometheusExporter(port=9090)
openworkflow = OpenWorkflow(observability_exporter=exporter)

# Metrics available at http://localhost:9090/metrics
```

### Tracing

OpenTelemetry integration:

```python
from opentelemetry import trace
from openworkflow.observability import OpenTelemetryExporter

tracer = trace.get_tracer(__name__)
openworkflow = OpenWorkflow(
    observability_exporter=OpenTelemetryExporter(
        endpoint="http://jaeger:4318"
    )
)

# Automatic span creation for each action
```

## Workflow Context

Workflows have access to execution context:

```python
@action("my_plugin.my_action")
def handler(input: dict, context: dict) -> dict:
    # Context includes:
    # - workflow_id: unique workflow execution ID
    # - step_name: current step name
    # - inputs: workflow-level inputs
    # - secrets: secret values
    # - environment: environment variables
    # - previous_steps: outputs from previous steps

    prev_result = context["previous_steps"]["fetch_data"]["output"]
    return {"processed": prev_result}
```

## HTTP Server Integration

For HTTP-based handlers, SDKs can create API endpoints:

**Python (FastAPI):**
```python
from fastapi import FastAPI
from openworkflow.integrations.fastapi import SmartifyRouter

app = FastAPI()
openworkflow = OpenWorkflow()

# Auto-create /execute endpoints for all plugins
app.include_router(SmartifyRouter(smartify))

# Now available:
# POST /weather/execute
# POST /github/execute
```

**JavaScript (Express):**
```javascript
import express from 'express';
import { createSmartifyRouter } from '@openworkflow/sdk';

const app = express();
const openworkflow = new OpenWorkflow();

app.use('/plugins', createSmartifyRouter(smartify));

// Available:
// POST /plugins/weather/execute
// POST /plugins/github/execute
```

## Testing

SDKs provide testing utilities:

```python
from openworkflow.testing import MockSmartify, mock_action

# Mock OpenWorkflow instance
smartify = MockSmartify()

# Mock action responses
openworkflow.mock_action("weather.get_current_weather", {
    "temperature": 72,
    "conditions": "sunny"
})

# Test workflows
workflow = Workflow.from_file("workflow.yaml")
result = workflow.execute(smartify=smartify)

# Assert results
assert result["steps"]["fetch_weather"]["output"]["temperature"] == 72
```

## SDK Requirements Checklist

All language implementations must support:

- [ ] Plugin registration from YAML/JSON files
- [ ] Plugin registration from in-memory objects
- [ ] Action handler registration (decorator pattern)
- [ ] Local workflow execution
- [ ] Cloud workflow execution (with API key)
- [ ] HTTP handler invocation
- [ ] SDK function handler invocation
- [ ] Command handler invocation (shell scripts)
- [ ] Environment variable interpolation
- [ ] Secrets management (pluggable)
- [ ] Structured logging
- [ ] Error handling and formatting
- [ ] Input/output schema validation
- [ ] Retry logic with backoff
- [ ] Timeout handling
- [ ] Basic observability (metrics/tracing)
- [ ] Testing utilities

## Reference Implementations

- **Python**: [smartify-sdk-python](https://github.com/Open-Workflow/sdk-python)
- **JavaScript**: [@openworkflow/sdk](https://github.com/Open-Workflow/sdk-js)
- **Go**: [openworkflow/sdk-go](https://github.com/Open-Workflow/sdk-go)

## Next Steps

- [Connector Schema](./connector-schema.md) - Define your connectors
- [Workflow Schema](./workflow-schema.md) - Compose actions into workflows
- [Execution Modes](./execution-modes.md) - Deep dive on execution patterns
