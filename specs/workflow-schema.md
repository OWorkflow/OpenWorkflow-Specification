# Workflow Schema Specification

**Version:** 0.1.0
**Status:** Draft

## Overview

Workflows compose multiple actions, agents, and logic nodes into orchestrated sequences. They support conditional logic, loops, parallel execution, error handling, data transformation, and various trigger types.

Workflows are backend-agnostic: logic nodes execute natively in the orchestrator, while agent steps may delegate to pluggable backends (native, LangChain, custom adapters). Execution backend can be overridden at the step level. See [Execution Backends](./execution-backends.md) for backend resolution order and adapter interfaces.

## Step Types

Workflows support three primary step categories:

1. **Action Steps**: Execute connector actions
2. **Agent Steps**: Invoke AI agents (with optional backend override)
3. **Logic Steps**: Control flow, branching, loops, transforms

For detailed logic step semantics and the portable node catalog, see [Workflow Logic Steps](./workflow-logic-steps.md).

### Backend Overrides

Agent and connector steps can override the execution backend:

```yaml
steps:
  - id: analyze_data
    type: agent
    agent: agent:openworkflow/data-analyst@1.0.0
    backend: langchain  # Override agent's default backend
    input:
      query: "Analyze sales trends"
```

See [Execution Backends](./execution-backends.md) for resolution priority and adapter configuration.

## Template Context Model

Workflows use a consistent template expression context for all data references:

- `{{ inputs.<field> }}` — Workflow-level input parameters
- `{{ env.<VAR> }}` — Environment variables
- `{{ secrets.<NAME> }}` — Secure credentials (trusted context only)
- `{{ steps.<id>.output.<field> }}` — Output from a previous step (by step `id`)

**Note:** Always use `steps.<id>` to reference step outputs (the `id` field uniquely identifies each step).

## File Format

Workflow files always use the plural `workflows:` key and contain an array of workflow definitions. This allows for single or multiple workflows in one file:

```yaml
workflows:
  - name: string          # Required: workflow name
    version: string       # Optional: semantic version (default: "1.0.0")
    description: string   # Optional: what this workflow does
    # ... workflow definition
```

**Single workflow example:**
```yaml
workflows:
  - name: Daily Weather Report
    version: 1.0.0
    # ... steps, triggers, etc.
```

**Multiple workflows example:**
```yaml
workflows:
  - name: Daily Weather Report
    version: 1.0.0
    # ... workflow definition

  - name: Weather Alerts
    version: 1.0.0
    # ... workflow definition
```

This consistent format simplifies parsing and allows workflows to grow from one to many without restructuring.

## Basic Structure

Each workflow in the array follows this structure:

```yaml
workflows:
  - name: string            # Required: human-readable workflow name
    version: string         # Optional: semantic version (default: "1.0.0")
    description: string     # Optional: what this workflow does

    # Inputs available to all steps
    inputs:
      param_name:
        type: string|number|boolean|object
        description: string
        default: any        # Optional default value
        required: boolean   # Default: false

    # How this workflow is triggered
    triggers:
      - type: schedule|webhook|event|manual
        # ... trigger-specific config

    # Execution steps
    steps:
      - name: string        # Required: unique step identifier
        connector: string   # Required: connector ID (e.g., connector:community/slack@1.0.0)
        action: string      # Required: action name
        input:              # Action input (can reference context)
          param: value
        # ... step-specific config

    # Output values
    outputs:
      output_name:
        value: "{{ steps.step_name.output.field }}"
        description: string
```

## Workflow Inputs

Define parameters that can be provided at execution time:

```yaml
workflows:
  - name: Weather Report Generator

    inputs:
      location:
        type: string
        description: City name to get weather for
        default: "San Francisco"
        required: true

      units:
        type: string
        description: Temperature units
        enum: [celsius, fahrenheit]
        default: celsius

      include_forecast:
        type: boolean
        description: Whether to include 7-day forecast
        default: false
```

## Authorization (RBAC)

Control who can execute workflows:

```yaml
workflows:
  - name: Delete User Data
    version: 0.1.0

    # Access control
    authorization:
      enabled: true

      # Required roles (OR logic - user needs at least one)
      roles: [admin, data-team-lead]

      # Required permissions (AND logic - user needs all)
      permissions:
        - workflows:execute
        - users:delete

      # Approval workflow (optional)
      approval:
        required: true
        approvers: [manager, security-team]
        timeout: 3600  # 1 hour to approve

    steps:
      - name: delete_records
        connector: connector:community/database@1.0.0
        action: delete

        # Step-level authorization (additional check)
        authorization:
          permissions: [database:write:users]
```

**Authorization Model:**
- Users authenticate with identity provider (OAuth2, SAML, etc.)
- Roles and permissions assigned via IAM system
- Workflow execution checks authorization before running
- Failed authorization logged for audit

See [Security Specification](./security.md) for complete RBAC details.

Execute with inputs:

```python
workflows = Workflows.from_file("workflows.yaml")
workflows.execute("Weather Report Generator", inputs={
    "location": "New York",
    "include_forecast": True
})
```

## Triggers

### Manual Trigger

Workflow runs on-demand only:

```yaml
triggers:
  - type: manual
```

### Schedule Trigger

Run on a cron schedule:

```yaml
triggers:
  - type: schedule
    cron: "0 8 * * *"           # Every day at 8am
    timezone: "America/New_York"
```

### Webhook Trigger

Run when HTTP request received:

```yaml
triggers:
  - type: webhook
    path: /workflows/my-workflow
    method: POST

    # Authentication
    auth:
      # HMAC signature (recommended)
      type: hmac-sha256
      secret_name: WEBHOOK_SECRET
      header: X-Hub-Signature-256

      # Alternative: Bearer token
      # type: bearer
      # secret_name: WEBHOOK_TOKEN

    # Security options
    security:
      # IP allowlist
      ipAllowlist:
        - 192.168.1.0/24
        - 10.0.0.5

      # Replay attack protection
      replayWindow: 300  # 5 minutes
      timestampHeader: X-Request-Timestamp

      # Rate limiting
      rateLimit:
        rpm: 60  # Requests per minute
        burst: 10

      # Payload limits
      maxPayloadSize: 1048576  # 1MB
```

Webhook payload is available as `trigger.payload`:

```yaml
steps:
  - name: process_webhook
    connector: connector:community/my-connector@1.0.0
    action: process
    input:
      data: "{{ trigger.payload }}"
```

### Event Trigger

Run when event received from configured event bus (Kafka, SNS/SQS, webhooks, etc.):

```yaml
triggers:
  - type: event
    source: kafka                   # Event bus type: kafka | sns | sqs | webhook | custom
    topic: user.signup              # Topic/queue name
    filter:                         # Optional: filter events
      event_type: new_user
```

Event data available as `trigger.event`:

```yaml
steps:
  - name: welcome_user
    connector: connector:community/email@1.0.0
    action: send
    input:
      to: "{{ trigger.event.user_email }}"
      template: welcome
```

## Steps

### Basic Step

```yaml
steps:
  - name: fetch_weather
    connector: connector:community/weather@1.0.0
    action: get_current_weather
    input:
      location: "{{ inputs.location }}"
```

### Conditional Execution

Run step only if condition is true:

```yaml
steps:
  - name: check_temperature
    connector: connector:community/weather@1.0.0
    action: get_current_weather
    input:
      location: "San Francisco"

  - name: send_heat_alert
    connector: connector:community/slack@1.2.0
    action: post_message
    condition: "{{ steps.check_temperature.output.temperature > 90 }}"
    input:
      channel: "#alerts"
      text: "Heat alert! Temperature is {{ steps.check_temperature.output.temperature }}°F"
```

### Loops

Iterate over arrays:

```yaml
steps:
  - name: get_cities
    connector: connector:community/database@1.0.0
    action: query
    input:
      sql: "SELECT city FROM locations"

  - name: fetch_weather_for_city
    connector: connector:community/weather@1.0.0
    action: get_current_weather
    for_each: "{{ steps.get_cities.output.cities }}"
    input:
      location: "{{ item.city }}"
```

Each iteration's output is collected in an array. Use `parallel: true` for unbounded concurrency (default is sequential):

```json
{
  "fetch_weather_for_city": {
    "output": [
      {"temperature": 72, "city": "San Francisco"},
      {"temperature": 85, "city": "Los Angeles"}
    ]
  }
}
```

### Parallel Execution

Run multiple steps concurrently:

```yaml
steps:
  - name: parallel_tasks
    parallel:
      - name: fetch_weather
        connector: connector:community/weather@1.0.0
        action: get_current_weather
        input:
          location: "San Francisco"

      - name: fetch_news
        connector: connector:community/news@1.0.0
        action: get_headlines
        input:
          topic: weather

      - name: fetch_traffic
        connector: connector:community/traffic@1.0.0
        action: get_conditions
        input:
          city: "San Francisco"

  - name: generate_report
    connector: connector:community/reporting@1.0.0
    action: create
    input:
      weather: "{{ steps.parallel_tasks.fetch_weather.output }}"
      news: "{{ steps.parallel_tasks.fetch_news.output }}"
      traffic: "{{ steps.parallel_tasks.fetch_traffic.output }}"
```

### Error Handling

Handle step failures gracefully:

```yaml
steps:
  - name: risky_operation
    connector: connector:community/external-api@1.0.0
    action: call
    input:
      endpoint: "https://api.example.com/data"

    # Retry configuration
    retry:
      max_attempts: 3
      backoff: exponential
      backoff_factor: 2

    # Continue workflow even if this fails (sets status to 'failed' but doesn't halt workflow)
    continue_on_error: true

  - name: handle_failure
    connector: connector:community/logging@1.0.0
    action: log_error
    condition: "{{ steps.risky_operation.status == 'failed' }}"
    input:
      message: "Operation failed: {{ steps.risky_operation.error }}"
```

### Timeout

Limit step execution time:

```yaml
steps:
  - name: slow_operation
    connector: connector:community/data-processing@1.0.0
    action: process_large_dataset
    timeout: 300  # 5 minutes
    input:
      dataset_id: "12345"
```

## Data Transformation

Use template expressions to transform data:

```yaml
steps:
  - name: fetch_user
    connector: connector:community/database@1.0.0
    action: query
    input:
      sql: "SELECT * FROM users WHERE id = {{ inputs.user_id }}"

  - name: send_email
    connector: connector:community/email@1.0.0
    action: send
    input:
      to: "{{ steps.fetch_user.output.email }}"
      subject: "Hello {{ steps.fetch_user.output.first_name }}!"
      body: |
        Hi {{ steps.fetch_user.output.first_name }} {{ steps.fetch_user.output.last_name }},

        Your account status: {{ steps.fetch_user.output.status | upper }}

# Template filters available:
# - upper, lower, title: string case
# - default: default value if null
# - length: array/string length
# - json: serialize to JSON
# - round: round number
```

## Workflow Outputs

Define values to return from workflow execution:

```yaml
workflows:
  - name: Data Pipeline

    steps:
      - name: fetch_data
        connector: connector:community/database@1.0.0
        action: query
        # ...

      - name: process_data
        connector: connector:community/transform@1.0.0
        action: process
        # ...

    outputs:
      record_count:
        value: "{{ steps.fetch_data.output.count }}"
        description: Number of records processed

      result_url:
        value: "{{ steps.process_data.output.url }}"
        description: URL to processed data

      success:
        value: "{{ steps.process_data.status == 'success' }}"
        description: Whether pipeline completed successfully
```

Outputs are returned from execution:

```python
result = workflow.execute()
print(result.outputs["record_count"])  # 1000
print(result.outputs["result_url"])    # https://...
```

## Subworkflows

Call other workflows as steps:

```yaml
steps:
  - name: run_etl
    workflow: data-etl-pipeline
    version: "1.2.0"              # Optional: specific version
    input:
      source: "{{ inputs.data_source }}"
      destination: "{{ inputs.data_dest }}"

  - name: notify_completion
    plugin: slack
    action: post_message
    input:
      channel: "#data-team"
      text: "ETL completed: {{ steps.run_etl.outputs.record_count }} records"
```

## Environment Variables

Reference environment variables:

```yaml
steps:
  - name: deploy
    connector: connector:community/kubernetes@1.0.0
    action: deploy
    input:
      cluster: "{{ env.K8S_CLUSTER }}"
      namespace: "{{ env.K8S_NAMESPACE }}"
      image: "myapp:{{ env.VERSION }}"
```

## Secrets

Access secure credentials:

```yaml
steps:
  - name: call_api
    connector: connector:community/http@1.0.0
    action: request
    input:
      url: "https://api.example.com/data"
      headers:
        Authorization: "Bearer {{ secrets.API_TOKEN }}"
```

**Security:**
- Secrets are not logged or exposed in workflow history
- User inputs cannot access `{{ secrets.* }}` (sandboxed context)
- Runtime detects and blocks secret exposure in outputs
- See [Security](./security.md) for secret redaction policies

**❌ DANGEROUS - Secret Leakage:**
```yaml
# This will be BLOCKED at runtime
steps:
  - name: debug_output
    connector: connector:community/slack@1.2.0
    input:
      text: "Debug: {{ secrets.DATABASE_URL }}"  # ❌ Blocked
```

## Complete Examples

### Example Workflow

```yaml
workflows:
  - name: Daily Sales Report
    version: 0.1.0
    description: Generate and distribute daily sales report

    inputs:
      report_date:
        type: string
        description: Date for report (YYYY-MM-DD)
        default: "{{ today }}"

      recipients:
        type: array
        description: Email addresses to send report to
        required: true

    triggers:
      - type: schedule
        cron: "0 9 * * *"  # Every day at 9am
        timezone: "America/New_York"

    steps:
      # Fetch sales data
      - name: fetch_sales
        connector: connector:community/database@1.0.0
        action: query
        input:
          sql: |
            SELECT product, SUM(amount) as total
            FROM sales
            WHERE date = '{{ inputs.report_date }}'
            GROUP BY product
        timeout: 60

      # Calculate metrics
      - name: calculate_metrics
        connector: connector:community/analytics@1.0.0
        action: compute
        input:
          data: "{{ steps.fetch_sales.output.rows }}"
          metrics: [total, average, top_products]

      # Generate chart
      - name: create_chart
        connector: connector:community/visualization@1.0.0
        action: create_chart
        input:
          type: bar
          data: "{{ steps.calculate_metrics.output }}"
          title: "Sales by Product - {{ inputs.report_date }}"

      # Upload to storage
      - name: upload_chart
        connector: connector:community/s3@1.0.0
        action: upload
        input:
          bucket: "company-reports"
          key: "sales/{{ inputs.report_date }}.png"
          file: "{{ steps.create_chart.output.image_data }}"

      # Send emails in parallel
      - name: send_reports
        connector: connector:community/email@1.0.0
        action: send
        for_each: "{{ inputs.recipients }}"
        parallel: true
        input:
          to: "{{ item }}"
          subject: "Daily Sales Report - {{ inputs.report_date }}"
          body: |
            Hi there,

            Here's your daily sales report for {{ inputs.report_date }}:

            Total Sales: ${{ steps.calculate_metrics.output.total }}
            Average: ${{ steps.calculate_metrics.output.average }}
            Top Product: {{ steps.calculate_metrics.output.top_products[0] }}

            Chart: {{ steps.upload_chart.output.url }}
          attachments:
            - url: "{{ steps.upload_chart.output.url }}"
              filename: "sales_chart.png"

      # Log completion
      - name: log_success
        connector: connector:community/logging@1.0.0
        action: info
        input:
          message: "Sales report generated and sent to {{ inputs.recipients | length }} recipients"

    outputs:
      total_sales:
        value: "{{ steps.calculate_metrics.output.total }}"
        description: Total sales amount

      report_url:
        value: "{{ steps.upload_chart.output.url }}"
        description: URL to chart image

      recipients_count:
        value: "{{ inputs.recipients | length }}"
        description: Number of recipients
```

### Multiple Workflows in One File

Example showing multiple workflows bundled together:

```yaml
workflows:
  # Development workflow
  - name: Run Tests
    version: 0.1.0
    description: Execute test suite for the connector

    triggers:
      - type: webhook
        path: /test
        method: POST

    steps:
      - name: run_unit_tests
        connector: connector:community/testing@1.0.0
        action: run_tests
        input:
          suite: unit
          coverage: true

      - name: run_integration_tests
        connector: connector:community/testing@1.0.0
        action: run_tests
        input:
          suite: integration

      - name: publish_results
        connector: connector:community/slack@1.2.0
        action: post_message
        input:
          channel: "#ci-cd"
          text: "Tests completed: {{ steps.run_unit_tests.output.passed }}/{{ steps.run_unit_tests.output.total }} passed"

  # Deployment workflow
  - name: Deploy Connector
    version: 0.1.0
    description: Deploy connector to production

    inputs:
      environment:
        type: string
        enum: [staging, production]
        default: staging

    triggers:
      - type: webhook
        path: /deploy
        method: POST

    steps:
      - name: build_image
        connector: connector:community/docker@1.0.0
        action: build
        input:
          dockerfile: ./Dockerfile
          tags: ["connector:{{ inputs.environment }}"]

      - name: push_image
        connector: connector:community/docker@1.0.0
        action: push
        input:
          image: "{{ steps.build_image.output.image_id }}"

      - name: deploy_to_k8s
        connector: connector:community/kubernetes@1.0.0
        action: apply
        input:
          manifest: ./k8s/{{ inputs.environment }}.yaml
          namespace: smartify-connectors

      - name: verify_health
        connector: connector:community/http@1.0.0
        action: get
        input:
          url: "https://{{ inputs.environment }}.openworkflow.ai/healthz"
        retry:
          max_attempts: 5
          backoff: exponential

  # Monitoring workflow
  - name: Health Check
    version: 0.1.0
    description: Periodic health monitoring

    triggers:
      - type: schedule
        cron: "*/5 * * * *"  # Every 5 minutes

    steps:
      - name: check_endpoint
        connector: connector:community/http@1.0.0
        action: get
        input:
          url: "https://api.openworkflow.ai/connectors/weather/healthz"
        timeout: 10

      - name: alert_on_failure
        connector: connector:community/pagerduty@1.0.0
        action: create_incident
        condition: "{{ steps.check_endpoint.status != 'success' }}"
        input:
          severity: high
          title: "Weather connector health check failed"
          description: "{{ steps.check_endpoint.error }}"
```

## Validation

Validate workflows using the OpenWorkflow CLI:

```bash
# Validate single workflow
smartify workflow validate my-workflow.yaml

# Validate file with multiple workflows
smartify workflow validate workflows.yaml
```

## Execution

### Single Workflow

```bash
# Execute with default inputs
smartify workflow run my-workflow.yaml

# Execute with custom inputs
smartify workflow run my-workflow.yaml --input location="New York" --input units=fahrenheit

# Execute in cloud
smartify workflow run my-workflow.yaml --cloud

# Dry run (validate without executing)
smartify workflow run my-workflow.yaml --dry-run
```

### Multiple Workflows

```bash
# Execute specific workflow by name
smartify workflow run workflows.yaml --workflow "Run Tests"

# List all workflows in file
smartify workflow list workflows.yaml

# Execute all workflows
smartify workflow run workflows.yaml --all
```

### SDK Usage

**Single workflow:**
```python
from openworkflow import Workflow

workflow = Workflow.from_file("my-workflow.yaml")
result = workflow.execute()
```

**Multiple workflows:**
```python
from openworkflow import Workflows

# Load all workflows
workflows = Workflows.from_file("workflows.yaml")

# Execute specific workflow
result = workflows.execute("Run Tests")

# Execute all workflows
results = workflows.execute_all()

# Iterate workflows
for workflow in workflows:
    print(f"Workflow: {workflow.name}")
    result = workflow.execute()
```

## Dry Run & Testing

Test workflows before deployment:

```yaml
workflows:
  - name: Data Pipeline
    version: 0.1.0

    # Testing configuration
    testing:
      # Dry run mode
      dryRun:
        enabled: true
        mockConnectors: true  # Use mocked responses
        mockData:
          connector:community/database@1.0.0:
            query: {rows: [{id: 1, name: "test"}]}

      # Test fixtures
      fixtures:
        - name: sample_user
          inputs:
            user_id: "test_123"
          expectedOutputs:
            status: "success"
            user_name: "Test User"

        - name: edge_case_empty
          inputs:
            user_id: "nonexistent"
          expectedOutputs:
            status: "error"
            error_code: "USER_NOT_FOUND"
```

**CLI Usage:**
```bash
# Dry run without executing connectors
smartify workflow run workflow.yaml --dry-run

# Test with specific fixture
smartify workflow test workflow.yaml --fixture sample_user

# Validate workflow structure
smartify workflow validate workflow.yaml
```

## Per-Step Guardrails

Add guardrails to individual steps:

```yaml
steps:
  - name: process_customer_data
    connector: connector:community/ai-processor@1.0.0
    action: analyze

    # Step-level guardrails (overrides agent defaults)
    guardrails:
      # Content filtering
      piiDetection: true  # Block if PII detected in output
      toxicityThreshold: 0.7
      blockedTopics: [violence, hate-speech, medical-advice]

      # Cost controls
      maxCost: 0.10  # USD per execution
      maxTokens: 1000

      # Behavioral constraints
      maxToolCalls: 5
      timeLimit: 30  # Seconds

      # Output validation
      outputSchema:
        type: object
        required: [sentiment, summary]
```

## Best Practices

1. **Descriptive names**: Use clear step names that describe their purpose
2. **Error handling**: Add retry logic and error handling for external services
3. **Timeouts**: Set appropriate timeouts for long-running operations
4. **Idempotency**: Design workflows to be safely re-runnable
5. **Testing**: Use dry-run and fixtures before production deployment
6. **Logging**: Add logging steps for debugging and audit trails
7. **Guardrails**: Apply step-level guardrails for sensitive operations
8. **Documentation**: Add descriptions to inputs, outputs, and complex steps

## Next Steps

- [Connector Schema](./connector-schema.md) - Define reusable connectors
- [SDK Contract](./sdk-contract.md) - Execute workflows programmatically
- [Execution Modes](./execution-modes.md) - Local vs. cloud execution
