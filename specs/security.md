# Security Specification

**Version:** 0.1.0

> This specification defines security controls, best practices, and requirements for the OpenWorkflow platform.

## Overview

Security is fundamental to Smartify's design. This specification covers:

1. **Authentication & Authorization** - Who can access what
2. **Secrets Management** - Protecting sensitive credentials
3. **Input Validation** - Preventing injection attacks
4. **Execution Isolation** - Sandboxing and resource limits
5. **Supply Chain Security** - Trust and verification
6. **Audit & Compliance** - Logging and monitoring

## Threat Model

### Assets to Protect

- **Secrets**: API keys, tokens, passwords, certificates
- **User Data**: PII, business data, workflow inputs/outputs
- **Infrastructure**: Compute resources, databases, APIs
- **Intellectual Property**: Workflow definitions, agent configurations

### Threat Actors

- **External Attackers**: Unauthorized access, data theft
- **Malicious Connectors**: Supply chain attacks, backdoors
- **Compromised Credentials**: Stolen API keys, leaked secrets
- **Insider Threats**: Unauthorized actions by legitimate users

### Attack Vectors

- Template injection → Secret extraction
- SQL/Command injection → Data breach, system compromise
- SSRF → Internal network access
- Supply chain attacks → Malicious connector execution
- DoS/Resource exhaustion → Service disruption

---

## 1. Authentication & Authorization

### 1.1 Connector Authentication

Connectors support multiple authentication methods:

```yaml
connector:
  auth:
    type: oauth2 | apiKey | bearer | basic | mtls | custom

    # OAuth2
    oauth2:
      authorizationUrl: https://provider.com/oauth/authorize
      tokenUrl: https://provider.com/oauth/token
      scopes: [read, write]

    # API Key
    apiKey:
      in: header | query | cookie
      name: X-API-Key

    # Bearer Token
    bearer:
      scheme: Bearer

    # Mutual TLS
    mtls:
      clientCert: ${secrets.CLIENT_CERT}
      clientKey: ${secrets.CLIENT_KEY}
      caCert: ${secrets.CA_CERT}
```

### 1.2 Workflow Authorization (RBAC)

**Role-Based Access Control** for workflow execution:

```yaml
workflows:
  - name: Delete User Data
    version: 1.0.0

    # Access control
    authorization:
      enabled: true

      # Required roles (OR logic)
      roles: [admin, data-team-lead]

      # Required permissions (AND logic)
      permissions:
        - workflows:execute
        - users:delete

      # Approval workflow
      approval:
        required: true
        approvers: [manager, security-team]
        timeout: 3600  # 1 hour

    steps:
      - name: delete_user
        connector: connector:community/database@1.0.0
        action: delete

        # Step-level authorization
        authorization:
          permissions: [database:write]
```

### 1.3 Connector Permissions

Restrict connector access in agent toolsets:

```json
{
  "toolset": [
    {
      "connector": "connector:community/database@1.0.0",
      "actions": ["query", "insert"],  // Allowlist
      "deny": ["delete", "drop"],       // Denylist
      "rateLimit": {
        "rpm": 10
      }
    }
  ]
}
```

### 1.4 Webhook Authentication

Secure webhook triggers:

```yaml
triggers:
  - type: webhook
    path: /workflows/ingest-data
    method: POST

    auth:
      # HMAC signature verification (recommended)
      type: hmac-sha256
      secret_name: WEBHOOK_SECRET
      header: X-Hub-Signature-256

      # Alternative: Bearer token
      # type: bearer
      # secret_name: WEBHOOK_TOKEN

    security:
      # IP allowlist
      ipAllowlist:
        - 192.168.1.0/24
        - 10.0.0.5

      # Replay protection
      replayWindow: 300  # 5 minutes
      timestampHeader: X-Request-Timestamp

      # Request limits
      maxPayloadSize: 1048576  # 1MB

      rateLimit:
        rpm: 60
        burst: 10
```

**HMAC Verification Example:**
```python
import hmac
import hashlib

def verify_webhook(request):
    signature = request.headers.get('X-Hub-Signature-256')
    secret = get_secret('WEBHOOK_SECRET')

    expected = 'sha256=' + hmac.new(
        secret.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

---

## 2. Secrets Management

### 2.1 Secret Storage

**Principles:**
- Secrets never appear in plaintext in workflow definitions
- Secrets are stored encrypted at rest
- Access is logged and audited

**Template Syntax:**
```yaml
steps:
  - connector: connector:community/api@1.0.0
    input:
      headers:
        Authorization: "Bearer {{ secrets.API_TOKEN }}"
      # ✅ Secrets only in connector configs
      # ❌ NEVER in user-controlled inputs
```

### 2.2 Secret Scoping

Limit secret access to specific connectors:

```yaml
secrets:
  DATABASE_PASSWORD:
    value: ${env.DB_PASSWORD}  # From environment
    scope:
      connectors:
        - connector:community/database@1.0.0
      workflows:
        - workflow:openworkflow/data-pipeline

    rotation:
      interval: 90  # Days
      notifyBefore: 7  # Days warning
```

### 2.3 Secret Redaction

**Runtime Protection:**

```yaml
execution:
  security:
    secretRedaction:
      enabled: true  # Default: true in production

      # Patterns to detect and redact
      patterns:
        - "password"
        - "token"
        - "key"
        - "secret"
        - "credential"

      # Redaction strategy
      redactedValue: "***REDACTED***"

      # Block execution if secrets detected in outputs
      blockOnExposure: true

      # Fields to scan
      scanFields:
        - workflow.outputs
        - step.outputs
        - error.messages
        - logs
```

**Example - Blocked Execution:**
```yaml
# This will FAIL at runtime
steps:
  - name: leak_secret
    connector: connector:community/slack@1.2.0
    action: post_message
    input:
      text: "API Key: {{ secrets.API_KEY }}"  # ❌ BLOCKED

# Error: Secret exposure detected in step 'leak_secret' output field 'text'
```

### 2.4 Secret Injection Prevention

**Sandboxed Template Context:**

User inputs cannot access secrets:

```yaml
# ✅ SAFE - Connector config
handler:
  http:
    headers:
      Authorization: "Bearer {{ secrets.API_KEY }}"

# ❌ BLOCKED - User input
steps:
  - input:
      message: "{{ inputs.user_message }}"

# If inputs.user_message = "{{ secrets.API_KEY }}"
# Result: Literal string "{{ secrets.API_KEY }}" (not interpolated)
```

---

## 3. Input Validation & Injection Prevention

### 3.1 Template Expression Sandboxing

**Allowed Operations:**
- Variable access: `{{ inputs.field }}`, `{{ steps.previous.output }}`
- Filters: `{{ value | upper }}`, `{{ array | length }}`
- Arithmetic: `{{ 1 + 2 }}`, `{{ price * quantity }}`
- Comparisons: `{{ value > 10 }}`, `{{ status == 'active' }}`
- Logic: `{{ condition and other_condition }}`

**Blocked Operations:**
- System calls: `{{ system() }}`, `{{ exec() }}`
- File access: `{{ read_file() }}`, `{{ open() }}`
- Code execution: `{{ eval() }}`, `{{ import() }}`
- Secret access from user context: `{{ secrets.* }}`
- Dangerous filters: `{{ value | eval }}`

**Implementation Note:**
SDKs must implement sandboxed template engines (e.g., Jinja2 with `SandboxedEnvironment`, Liquid restricted mode).

### 3.2 SQL Injection Prevention

**❌ DANGEROUS - String Interpolation:**
```yaml
steps:
  - connector: connector:community/database@1.0.0
    action: query
    input:
      sql: "SELECT * FROM users WHERE id = {{ inputs.user_id }}"
      # Vulnerable to: user_id = "1 OR 1=1; DROP TABLE users--"
```

**✅ SAFE - Parameterized Queries:**
```yaml
steps:
  - connector: connector:community/database@1.0.0
    action: query
    input:
      sql: "SELECT * FROM users WHERE id = ?"
      parameters: ["{{ inputs.user_id }}"]
      # Parameters are automatically escaped
```

**Named Parameters:**
```yaml
input:
  sql: "SELECT * FROM users WHERE email = :email AND active = :active"
  parameters:
    email: "{{ inputs.email }}"
    active: true
```

### 3.3 Command Injection Prevention

**Restricted Command Execution:**

```yaml
handler:
  command: "./scripts/process.sh"

  security:
    # Sandbox execution
    sandbox: true

    # Allowlist of executable commands
    allowedCommands:
      - /usr/bin/python3
      - ./scripts/*.sh

    # Filesystem restrictions
    filesystem:
      mode: readonly  # readonly | writeonly | readwrite
      allowedPaths:
        - /app/data
        - /tmp/smartify
      deniedPaths:
        - /etc
        - /root

    # Network restrictions
    network:
      enabled: false  # Default: disabled
      allowedHosts:
        - api.example.com
      blockedPorts: [22, 23, 3389]
```

### 3.4 SSRF Prevention

**URL Validation:**

```yaml
handler:
  http:
    url: "{{ input.callback_url }}"

    urlValidation:
      # Domain allowlist
      allowedDomains:
        - "*.example.com"
        - "api.partner.com"

      # Block internal/metadata endpoints
      blockedDomains:
        - "169.254.169.254"  # AWS metadata
        - "metadata.google.internal"  # GCP metadata
        - "localhost"
        - "127.0.0.1"
        - "*.internal"

      # Port restrictions
      allowedPorts: [80, 443]
      blockedPorts: [22, 23, 3306, 5432, 6379]

      # Protocol restrictions
      allowedSchemes: [https]  # Force HTTPS

      # IP range blocks
      blockedIpRanges:
        - "10.0.0.0/8"      # Private
        - "172.16.0.0/12"   # Private
        - "192.168.0.0/16"  # Private
```

### 3.5 Input Schema Validation

**Enhanced JSON Schema:**

```yaml
actions:
  - name: create_user
    input:
      type: object
      properties:
        email:
          type: string
          format: email
          maxLength: 255
          sanitize: true  # Auto-escape HTML entities

        user_id:
          type: string
          pattern: "^[a-zA-Z0-9_-]{1,50}$"  # Alphanumeric only

        age:
          type: integer
          minimum: 0
          maximum: 150

        callback_url:
          type: string
          format: uri
          pattern: "^https://.*\\.example\\.com/.*$"

      required: [email, user_id]
      additionalProperties: false  # Reject unknown fields
```

---

## 4. Execution Isolation

### 4.1 Resource Limits

**Default Limits:**

| Resource | Default | Max |
|----------|---------|-----|
| CPU | 0.5 cores | 4 cores |
| Memory | 512MB | 4GB |
| Timeout | 120s | 600s |
| Disk I/O | 10MB/s | 100MB/s |
| Network bandwidth | 10MB/s | 100MB/s |
| Concurrent executions | 10 | 100 |

**Configuration:**

```yaml
connector:
  runtime:
    resources:
      cpu: "1.0"           # CPU cores
      memory: "1GB"        # Memory limit
      timeout: 300         # Seconds

      storage:
        maxSize: "1GB"     # Scratch disk space
        ephemeral: true    # Delete after execution

      network:
        bandwidth: "10MB/s"

      limits:
        maxFileDescriptors: 1024
        maxProcesses: 10
```

### 4.2 Container Isolation

**Self-Hosted Deployment Security:**

```yaml
# docker-compose.yml
services:
  connector-weather:
    image: openworkflow/connector-weather:1.0.0

    # Security options
    read_only: true  # Read-only filesystem

    security_opt:
      - no-new-privileges:true
      - seccomp=unconfined

    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

    # Resource limits
    mem_limit: 512m
    cpus: 0.5

    # Network isolation
    networks:
      - connector-network

    # Temporary filesystem
    tmpfs:
      - /tmp:size=100m,mode=1777
```

### 4.3 SDK Function Sandboxing

**Recommended Pattern:**

```python
from openworkflow import register_action, sandbox

@register_action("process_data")
@sandbox(
    allow_network=False,
    allow_filesystem=False,
    max_memory_mb=256,
    timeout_seconds=30,
    allowed_modules=["json", "datetime"]  # Import restrictions
)
def process_data(input_data):
    # Runs in restricted environment
    return {"result": "processed"}
```

---

## 5. Supply Chain Security

### 5.1 Connector Trust Levels

**Classification:**

🟢 **Official** (`official`)
- Published by OpenWorkflow team
- Full security audit
- Signed with OpenWorkflow GPG key
- SLA and support guaranteed

🟡 **Verified** (`verified`)
- Publisher identity confirmed
- Community code review
- Signed with publisher GPG key
- Listed in verified publisher registry

🟠 **Community** (`community`)
- Public submissions
- Basic malware scan passed
- Checksum verified
- Use with caution

🔴 **Unverified** (`unverified`)
- No verification performed
- Blocked by default
- Explicit opt-in required

### 5.2 Trust Policy

**Configuration:**

```yaml
# .openworkflow/config.yaml

registry:
  trustPolicy:
    # Allowed trust levels
    allowedLevels: [official, verified]

    # Require signature verification
    requireSignatures: true

    # Publisher allowlist
    allowedPublishers:
      - smartify
      - github
      - acme-corp

    # Block specific connectors
    blockedConnectors:
      - connector:malicious/backdoor@*

    # Security scanning
    scanning:
      enabled: true
      scanForSecrets: true
      scanForMalware: true
```

### 5.3 Connector Security Manifest

**Required Fields:**

```yaml
connector:
  name: example-api
  namespace: acme
  version: 1.0.0

  security:
    trustLevel: verified

    publisher:
      name: Acme Corp
      email: security@acme.com
      website: https://acme.com
      gpgKey: 0x1234ABCD

    # Required permissions
    permissions:
      network: true
      filesystem: false
      environmentVariables: [API_KEY, API_SECRET]

    # Declared dependencies
    dependencies:
      - connector:community/http@1.0.0

    # Security audit trail
    audit:
      lastReview: "2025-09-15"
      reviewedBy: security-team@openworkflow.ai
      findings: https://docs.openworkflowspec.org/audits/acme-v1.pdf

    # Vulnerability disclosure
    vulnerabilityReporting:
      email: security@acme.com
      url: https://acme.com/security
```

### 5.4 Signature Verification

**Publishing:**

```bash
# Sign connector manifest
gpg --armor --detach-sign connector.yaml

# Publish with signature
openworkflow connector publish \
  connector.yaml \
  --signature connector.yaml.asc \
  --key-id 0x1234ABCD
```

**Verification:**

```bash
# Verify signature
openworkflow connector verify connector:acme/example@1.0.0 \
  --check-signature \
  --require-verified

# Output:
# ✓ Checksum verified
# ✓ Signature valid (key: 0x1234ABCD)
# ✓ Publisher verified: Acme Corp
# ✓ Trust level: verified
```

---

## 6. Audit & Compliance

### 6.1 Audit Logging

**What to Log:**

```yaml
execution:
  audit:
    enabled: true

    # Log level
    level: info  # debug | info | warn | error

    # Retention
    retention: 90  # Days

    # PII handling
    piiRedaction: true
    piiFields: [email, phone, ssn, credit_card]

    # Logged fields
    fields:
      - timestamp
      - user_id
      - workflow_id
      - workflow_name
      - workflow_version
      - connector
      - action
      - status
      - duration_ms
      - error_code
      - ip_address
      - user_agent

    # Exclude sensitive data
    excludeFields:
      - input  # May contain PII
      - output # May contain secrets

    # Destinations
    destinations:
      - type: elasticsearch
        endpoint: https://logs.example.com
      - type: s3
        bucket: audit-logs
```

**Log Format:**

```json
{
  "timestamp": "2025-10-07T12:34:56Z",
  "event_type": "workflow.execution",
  "user_id": "user_abc123",
  "workflow_id": "workflow_xyz789",
  "workflow_name": "Data Export",
  "workflow_version": "1.2.0",
  "status": "success",
  "duration_ms": 1234,
  "connectors_used": [
    "connector:community/database@1.0.0",
    "connector:community/s3@2.1.0"
  ],
  "ip_address": "203.0.113.1",
  "geo": "US-CA",
  "metadata": {
    "trigger": "webhook",
    "environment": "production"
  }
}
```

### 6.2 Security Monitoring

**Anomaly Detection:**

```yaml
monitoring:
  security:
    # Failed authentication attempts
    failedAuthThreshold: 5
    failedAuthWindow: 300  # 5 minutes

    # Unusual execution patterns
    anomalyDetection:
      enabled: true
      baselineWindow: 7  # Days
      thresholds:
        executionCount: 200%  # 2x baseline
        errorRate: 150%
        duration: 300%

    # Suspicious activity
    alerts:
      - type: secret_exposure_attempt
        severity: critical
        action: block_and_notify

      - type: multiple_failed_executions
        threshold: 10
        window: 600  # 10 minutes
        severity: high

      - type: privilege_escalation_attempt
        severity: critical
        action: block_and_notify
```

### 6.3 Compliance Features

**GDPR:**

```yaml
compliance:
  gdpr:
    # Right to erasure
    dataRetention:
      workflowHistory: 90  # Days
      auditLogs: 365

    # Data subject requests
    dataExport:
      enabled: true
      format: json
      includeWorkflows: true
      includeLogs: true

    # Consent management
    consentRequired: true
    consentWorkflows: [data-processing, email-campaign]
```

**SOC 2:**

```yaml
compliance:
  soc2:
    # Change management
    approvalRequired: true
    approvalWorkflows: [production-deploy]

    # Access reviews
    accessReviewInterval: 90  # Days

    # Encryption
    encryptionAtRest: true
    encryptionInTransit: true
```

---

## 7. Incident Response

### 7.1 Security Incident Workflow

```yaml
workflows:
  - name: Security Incident Response

    triggers:
      - type: event
        source: security-monitoring
        filter:
          severity: [critical, high]

    steps:
      - name: assess_threat
        connector: connector:community/security-scanner@1.0.0
        action: analyze_incident

      - name: notify_security_team
        connector: connector:community/pagerduty@1.0.0
        action: create_incident

      - name: block_malicious_connector
        condition: "{{ steps.assess_threat.output.threat_level == 'critical' }}"
        connector: connector:community/registry@1.0.0
        action: blocklist_connector

      - name: revoke_credentials
        condition: "{{ steps.assess_threat.output.credentials_compromised }}"
        connector: connector:community/secrets@1.0.0
        action: rotate_secrets
```

### 7.2 Breach Notification

```yaml
incidentResponse:
  breach:
    # Automatic detection
    detection:
      dataExfiltration: true
      unauthorizedAccess: true
      secretLeakage: true

    # Notification timeline
    notificationWindow: 72  # Hours (GDPR requirement)

    # Stakeholders
    notifyList:
      - security-team@openworkflow.ai
      - legal@openworkflow.ai
      - affected-users  # If PII involved
```

---

## Best Practices Summary

### Checklist for Secure Workflows

- [ ] Use parameterized queries (never string interpolation)
- [ ] Validate all user inputs with JSON Schema
- [ ] Enable secret redaction
- [ ] Implement RBAC for sensitive workflows
- [ ] Use HMAC authentication for webhooks
- [ ] Only use official/verified connectors
- [ ] Enable audit logging
- [ ] Set resource limits
- [ ] Test with security scanning tools
- [ ] Review and rotate secrets regularly

### Secure Development

1. **Principle of Least Privilege** - Grant minimum necessary permissions
2. **Defense in Depth** - Multiple layers of security
3. **Fail Securely** - Errors should not expose sensitive data
4. **Secure by Default** - Security features enabled automatically
5. **Zero Trust** - Verify everything, trust nothing

---

## Next Steps

- [Connector Schema](./connector-schema.md) - Secure connector development
- [Workflow Schema](./workflow-schema.md) - Authorization and secrets
- [Registry Protocol](./registry-protocol.md) - Trust and verification
- [Execution Modes](./execution-modes.md) - Isolation and sandboxing
