# Execution Modes Specification

**Version:** 0.1.0

## Overview

The OpenWorkflow specification defines workflows that can run anywhere. **Smartify Runtime** is the official reference implementation that executes OpenWorkflow specs across multiple deployment modes — from local development to production cloud environments. This flexibility allows developers to "build once, deploy anywhere."

## Execution Modes

### 1. Local Execution

Actions run in the same process as the SDK.

**Use cases:**
- Local development and testing
- Embedded workflows in applications
- Single-server deployments
- Offline operation

**Example:**
```python
from smartify import Smartify, Workflow

smartify = Smartify(execution_mode="local")

# Register local handlers
@smartify.action("my_plugin.process_data")
def process_data(input):
    return {"result": "processed"}

# Execute workflow locally
workflow = Workflow.from_file("workflow.yaml")
result = workflow.execute()  # Runs in-process with Smartify Runtime
```

**Characteristics:**
- No network calls to Smartify infrastructure
- All handlers must be registered or accessible
- Lowest latency
- No usage metering
- Full control over execution environment

### 2. Self-Hosted Execution

Plugins run as independent services, orchestrated by a self-hosted MCP Router.

**Use cases:**
- Enterprise deployments
- Compliance requirements (data residency)
- Custom infrastructure integration
- Private plugin registry

**Architecture:**
```
┌─────────────────┐
│  Your App       │
│  (Smartify SDK) │
└────────┬────────┘
         │
    ┌────▼────────────┐
    │  MCP Router     │
    │  (Self-hosted)  │
    └────┬────────────┘
         │
    ┌────▼─────────────┐
    │  Plugin Services │
    │  (Containers)    │
    └──────────────────┘
```

**Setup:**
```bash
# Deploy MCP Router
docker run -d \
  -p 8000:8000 \
  -e KAFKA_BROKERS=kafka:9092 \
  -e DATABASE_URL=postgres://... \
  openworkflow/mcp-router:latest

# Deploy plugin services
docker run -d \
  -e MCP_ROUTER_URL=http://mcp-router:8000 \
  -e TOOL_URL=http://weather:8000 \
  openworkflow/plugin-weather:latest
```

**SDK Configuration:**
```python
smartify = Smartify(
    execution_mode="self_hosted",
    router_url="http://mcp-router:8000"
)

workflow = Workflow.from_file("workflow.yaml")
result = workflow.execute()  # Routes through your MCP Router
```

**Characteristics:**
- Full control over infrastructure
- Private plugin registry support
- Custom observability stack
- Your own authentication/authorization
- No data leaves your network

### 3. Smartify Cloud Execution

Plugins execute in the fully managed Smartify Cloud runtime, which implements the OpenWorkflow specification at scale.

**Use cases:**
- Quick deployment
- SaaS applications
- Auto-scaling requirements
- No infrastructure management

**Setup:**
```python
smartify = Smartify(
    execution_mode="cloud",
    api_key="sk_..."
)

# Publish plugin to cloud
smartify.install_plugin("weather")

workflow = Workflow.from_file("workflow.yaml")
result = workflow.execute()  # Runs in Smartify Cloud
```

**Characteristics:**
- Zero infrastructure management
- Automatic scaling
- Built-in monitoring and logging
- Usage-based billing
- SLA guarantees
- Global deployment

### 4. Hybrid Execution

Mix local and cloud execution in the same workflow.

**Use cases:**
- Sensitive data processing locally, external APIs via cloud
- Gradual cloud migration
- Cost optimization (run heavy workloads in cloud)
- Low-latency requirements for specific actions

**Example:**
```yaml
workflow:
  name: Hybrid Processing Pipeline

  steps:
    # Run locally - sensitive data
    - name: process_user_data
      plugin: data_processor
      action: process
      execution: local
      input:
        data: "{{ inputs.user_data }}"

    # Run in cloud - external API
    - name: enrich_data
      plugin: external_enrichment
      action: enrich
      execution: cloud
      input:
        processed_data: "{{ steps.process_user_data.output }}"

    # Run locally - store results
    - name: save_results
      plugin: database
      action: insert
      execution: local
      input:
        data: "{{ steps.enrich_data.output }}"
```

**SDK Configuration:**
```python
smartify = Smartify(
    execution_mode="hybrid",
    api_key="sk_...",  # For cloud actions
    router_url="http://localhost:8000"  # For self-hosted actions
)

# Register local handlers
@smartify.action("data_processor.process")
def process_data(input):
    # Sensitive processing
    return {"result": "processed"}

workflow.execute()  # Automatically routes to local or cloud
```

## HTTP-Based Execution

For connectors exposed as HTTP services (common with self-hosted deployments).

### Connector Service Requirements

Each connector service must implement:

### Resource Limits

**Default Limits:**

All connector executions have default resource constraints:

| Resource | Default | Maximum |
|----------|---------|---------|
| CPU | 0.5 cores | 4 cores |
| Memory | 512MB | 4GB |
| Timeout | 120s | 600s |
| Disk I/O | 10MB/s | 100MB/s |
| Network | 10MB/s | 100MB/s |
| Concurrent | 10 | 100 |

**Configuration:**

```yaml
connector:
  runtime:
    resources:
      cpu: "1.0"        # CPU cores
      memory: "1GB"     # Memory limit
      timeout: 300      # Execution timeout (seconds)

      storage:
        maxSize: "1GB"  # Scratch disk space
        ephemeral: true # Delete after execution

      network:
        bandwidth: "10MB/s"

      limits:
        maxFileDescriptors: 1024
        maxProcesses: 10
```

### Service Endpoints

Each connector service must implement:

**1. Execute Endpoint**

`POST /execute`

Request:
```json
{
  "action": "plugin_name.action_name",
  "input": {
    "param1": "value1"
  }
}
```

Response (success):
```json
{
  "status": "success",
  "data": {
    "result": "output_data"
  }
}
```

Response (error):
```json
{
  "status": "error",
  "message": "Description of error",
  "code": "ERROR_CODE"
}
```

**2. Health Check Endpoint**

`GET /healthz`

Response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "checks": {
    "external_api": "healthy",
    "database": "degraded"
  }
}
```

Status values:
- `ok`: All systems operational
- `degraded`: Partial functionality
- `unhealthy`: Service unavailable

**3. Registration (Self-Hosted)**

Plugins register with MCP Router on startup:

```python
import httpx
import asyncio

async def register_with_mcp_router():
    payload = {
        "plugin_slug": "weather",
        "version": "1.0.0",
        "url": "http://weather-service:8000",
        "actions": ["get_current_weather", "get_forecast"]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MCP_ROUTER_URL}/register",
            json=payload
        )
        print(f"Registered: {response.json()}")

# Call on startup
asyncio.create_task(register_with_mcp_router())
```

## Event-Driven Execution (Kafka)

For asynchronous, event-driven workflows.

### Producer (MCP Router)

Publishes workflow tasks to Kafka:

```python
from aiokafka import AIOKafkaProducer
import json

async def execute_workflow_async(workflow_id, plugin_slug, action, input_data):
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKERS)
    await producer.start()

    message = {
        "workflow_id": workflow_id,
        "plugin": plugin_slug,
        "action": action,
        "input": input_data,
        "timestamp": "2025-10-07T12:00:00Z"
    }

    await producer.send(
        f"smartify.workflow.{plugin_slug}",
        json.dumps(message).encode()
    )

    await producer.stop()
```

### Consumer (Plugin Service)

Listens for tasks and processes them:

```python
from aiokafka import AIOKafkaConsumer
import json

async def consume_tasks():
    consumer = AIOKafkaConsumer(
        "smartify.workflow.weather",
        bootstrap_servers=KAFKA_BROKERS,
        group_id="weather-consumer"
    )

    await consumer.start()

    try:
        async for msg in consumer:
            task = json.loads(msg.value)
            workflow_id = task["workflow_id"]
            action = task["action"]
            input_data = task["input"]

            # Execute action
            result = execute_action(action, input_data)

            # Publish result back
            await publish_result(workflow_id, result)

    finally:
        await consumer.stop()

asyncio.create_task(consume_tasks())
```

### Response Pattern

Two options for async execution:

**1. Polling**

Workflow execution returns immediately with execution ID:
```json
{
  "status": "pending",
  "execution_id": "exec_123abc",
  "poll_url": "/workflows/executions/exec_123abc"
}
```

Client polls for completion:
```python
execution_id = result["execution_id"]

while True:
    status = smartify.get_execution_status(execution_id)
    if status["status"] in ["completed", "failed"]:
        break
    await asyncio.sleep(1)

final_result = status["result"]
```

**2. Webhooks**

Workflow specifies callback URL:
```python
result = workflow.execute_async(
    callback_url="https://myapp.com/webhooks/workflow-complete"
)
```

OpenWorkflow POSTs result to callback:
```json
{
  "execution_id": "exec_123abc",
  "status": "completed",
  "result": {
    "outputs": {...}
  }
}
```

## Execution Context

All actions receive execution context:

```python
@smartify.action("my_plugin.my_action")
def my_action(input: dict, context: dict) -> dict:
    # Context includes:
    workflow_id = context["workflow_id"]
    step_name = context["step_name"]
    execution_mode = context["execution_mode"]  # local, cloud, self_hosted
    environment = context["environment"]
    secrets = context["secrets"]
    previous_steps = context["previous_steps"]

    return {"result": "processed"}
```

## Performance Considerations

| Mode | Latency | Throughput | Cost | Scaling |
|------|---------|------------|------|---------|
| **Local** | <10ms | High | None | Process-bound |
| **Self-Hosted** | 50-100ms | High | Infrastructure | Manual/K8s |
| **Cloud** | 100-300ms | Very High | Per-request | Automatic |
| **Hybrid** | Varies | High | Mixed | Mixed |

### Optimization Tips

1. **Local mode**: Use for low-latency requirements
2. **Parallel execution**: Use workflow `parallel` blocks for concurrent actions
3. **Caching**: Cache plugin results in workflows
4. **Batch operations**: Group multiple inputs in single action call
5. **Async execution**: Use Kafka for long-running workflows

## Security

### Local Execution
- Process-level isolation only
- No network boundaries
- Access to local filesystem and environment

### Self-Hosted Execution
- Network segmentation via VPC/firewall
- mTLS between SDK and router
- Service mesh (optional): Istio, Linkerd
- Custom authentication/authorization

### Cloud Execution
- Multi-tenant isolation
- API key authentication
- TLS encryption in transit
- Encrypted at rest
- SOC 2 / ISO 27001 compliance

## Monitoring & Observability

### Local Execution
```python
smartify = Smartify(
    execution_mode="local",
    observability={
        "enabled": True,
        "log_level": "INFO",
        "trace_sampling": 1.0
    }
)

# Logs written to stdout/file
# Metrics exposed via Prometheus exporter
```

### Self-Hosted Execution
Deploy observability stack:
```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports: ["9090:9090"]

  grafana:
    image: grafana/grafana
    ports: ["3000:3000"]

  loki:
    image: grafana/loki
    ports: ["3100:3100"]
```

MCP Router and plugins export metrics to Prometheus.

### Cloud Execution
Built-in monitoring via Smartify Cloud dashboard:
- Execution logs
- Metrics and traces
- Error rates
- Latency histograms
- Usage analytics

## Migration Paths

### Local → Self-Hosted
1. Deploy Smartify Router
2. Containerize connector services
3. Update SDK config to point to router
4. No code changes needed

### Local → Smartify Cloud
1. Sign up for Smartify Cloud
2. Publish connectors to registry
3. Update SDK with API key
4. Set `execution_mode="cloud"`

### Self-Hosted → Smartify Cloud
1. Publish connectors to Smartify Cloud registry
2. Migrate workflows (no changes needed — OpenWorkflow spec is portable)
3. Update SDK authentication
4. Decommission self-hosted infrastructure

### Hybrid Approach
Gradually migrate plugins:
```python
# Start hybrid
smartify = Smartify(execution_mode="hybrid")

# Mark specific plugins for cloud execution
workflow.execute(overrides={
    "weather": "cloud",  # Run in cloud
    "database": "local"  # Keep local
})
```

## Streaming Execution

For real-time workflow progress updates, Smartify Runtime supports streaming execution:

**Configuration:**
```yaml
execution:
  streaming:
    enabled: true
    protocol: sse | websocket
    events:
      - step.started
      - step.progress
      - step.completed
      - step.failed
      - workflow.completed
```

**Server-Sent Events (SSE):**
```python
smartify = Smartify(execution_mode="cloud", streaming={"protocol": "sse"})

async for event in workflow.execute_stream():
    if event["type"] == "step.started":
        print(f"Started: {event['step_name']}")
    elif event["type"] == "step.progress":
        print(f"Progress: {event['percent']}%")
    elif event["type"] == "step.completed":
        print(f"Completed: {event['step_name']}")
```

**WebSocket:**
```python
import asyncio
from smartify import Smartify

async def stream_workflow():
    smartify = Smartify(streaming={"protocol": "websocket"})

    async with smartify.stream(workflow_id="wf_123") as stream:
        async for event in stream:
            print(f"{event['type']}: {event['data']}")

asyncio.run(stream_workflow())
```

**Event Format:**
```json
{
  "type": "step.progress",
  "timestamp": "2025-10-07T12:00:00Z",
  "workflow_id": "wf_123",
  "step_name": "process_data",
  "data": {
    "percent": 45,
    "message": "Processing record 450/1000"
  }
}
```

**Use cases:**
- Real-time UI progress bars
- Long-running workflows
- Interactive debugging
- Live dashboards

## Best Practices

1. **Development**: Start with local execution
2. **Staging**: Use self-hosted with production-like setup
3. **Production**: Cloud for public-facing, self-hosted for sensitive data
4. **Testing**: Local mode for unit tests, cloud for integration tests
5. **Cost optimization**: Use hybrid mode to balance cost and performance
6. **Real-time updates**: Enable streaming for long-running workflows
7. **Resource limits**: Always configure appropriate CPU, memory, and timeout limits

## Next Steps

- [Plugin Schema](./plugin-schema.md) - Define plugins
- [SDK Contract](./sdk-contract.md) - Integrate SDK
- [Observability](./observability.md) - Monitor execution
