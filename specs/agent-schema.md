# Agent Schema Specification

**Version:** 0.1.0
**Status:** Draft

## Overview

Agents are reusable AI policies that combine LLM capabilities with tools, memory, and guardrails. The agent schema is framework-agnostic, designed to work with multiple execution backends through adapter interfaces.

**Supported Backends:**
- **Native** — Smartify's built-in agent runtime
- **LangChain** — LangChain framework (Python/Node)
- **Custom Adapters** — Implement backend interface for other frameworks (e.g., OpenAI Agents, AutoGPT)

The schema defines the agent's behavior and capabilities; runtime adapters translate to framework-specific implementations.

## Core Concepts

- **Agent**: A configured AI assistant with personality, tools, knowledge, and constraints
- **Execution Backend**: Runtime that executes the agent (native or langchain)
- **Toolset**: Connectors the agent can invoke
- **Knowledge Base**: Vector stores and knowledge connectors for RAG
- **Guardrails**: Safety constraints and content filtering

## Naming Convention

Agents use the registry naming format:

```
agent:<namespace>/<name>@<version>
```

Examples:
- `agent:openworkflow/customer-support@1.0.0`
- `agent:acme/code-reviewer@2.1.0`
- `agent:research-labs/data-analyst@0.3.0`

## JSON Schema Definition

The formal JSON Schema for agent validation:

```json
{
  "$id": "https://spec.openworkflow.dev/v0/agent.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "OpenWorkflow Agent",
  "type": "object",
  "required": ["agent", "model", "instructions", "tools", "runtime"],
  "properties": {
    "registryMode": {
      "type": "boolean",
      "default": false,
      "description": "If true, enforces stricter validation for public registry publishing."
    },
    "agent": {
      "type": "object",
      "required": ["id"],
      "properties": { "id": { "type": "string", "minLength": 1 } }
    },
    "model": {
      "type": "object",
      "required": ["provider", "name"],
      "properties": {
        "provider": { "type": "string" },
        "name": { "type": "string" },
        "params": { "type": "object", "additionalProperties": true }
      }
    },
    "instructions": {
      "type": "object",
      "required": ["system"],
      "properties": {
        "system": { "type": "string", "minLength": 1 },
        "goals": { "type": "array", "items": { "type": "string" } }
      }
    },
    "tools": {
      "type": "array",
      "minItems": 0,
      "items": {
        "type": "object",
        "required": ["name"],
        "properties": {
          "name": { "type": "string", "minLength": 1 },
          "input_schema": { "type": "string" }
        },
        "additionalProperties": false
      }
    },
    "runtime": {
      "type": "string",
      "enum": ["smartify", "langchain", "agentkit", "vertexai", "anthropic", "any"]
    },
    "io": {
      "type": "object",
      "properties": {
        "output_schema": { "type": "string" }
      },
      "additionalProperties": false
    },
    "extensions": { "type": "object", "additionalProperties": true }
  },
  "additionalProperties": false,

  "allOf": [
    {
      "if": {
        "properties": { "registryMode": { "const": true } }
      },
      "then": {
        "description": "In registry mode, input/output schemas become mandatory.",
        "properties": {
          "tools": {
            "items": {
              "required": ["name", "input_schema"]
            }
          },
          "io": {
            "required": ["output_schema"]
          }
        }
      }
    }
  ]
}
```

**Registry Mode:**
When `registryMode: true` is set (used for public registry publishing), the following additional validations apply:
- All tools must have `input_schema` defined
- The `io.output_schema` becomes required

This ensures registry-published agents have complete API contracts for consumers.

## Agent Manifest Structure

### Complete Example

```json
{
  "schemaVersion": "0.1.0",
  "type": "agent",
  "name": "customer-support",
  "namespace": "smartify",
  "version": "1.0.0",
  "displayName": "Customer Support Agent",
  "description": "Handles customer inquiries with access to documentation and CRM",

  "execution": {
    "backend": "native",  // native | langchain | custom
    "runtimeHint": "python",  // python | node | any (optional)
    "config": {
      "maxIterations": 10,
      "timeout": 300
    }
  },

  "model": {
    "provider": "anthropic",
    "id": "claude-3-5-sonnet-20241022",
    "temperature": 0.7,
    "maxTokens": 4096,
    "topP": 1.0,
    "fallback": {
      "provider": "openai",
      "id": "gpt-4-turbo"
    }
  },

  "personality": {
    "name": "Alex",
    "role": "Customer Support Specialist",
    "traits": [
      "helpful",
      "empathetic",
      "professional",
      "patient"
    ],
    "tone": "friendly and professional",
    "systemPrompt": "You are Alex, a helpful customer support specialist. Always be empathetic and ensure customers feel heard. Provide clear, actionable solutions.",
    "examples": [
      {
        "input": "I can't log in to my account",
        "output": "I understand how frustrating login issues can be. Let me help you resolve this right away. Could you tell me what error message you're seeing?"
      }
    ]
  },

  "knowledge": {
    "vectorStores": [
      {
        "id": "product-docs",
        "provider": "pinecone",
        "index": "product-documentation",
        "topK": 5,
        "scoreThreshold": 0.7,
        "metadata": {
          "namespace": "v2-docs"
        }
      }
    ],
    "connectors": [
      "connector:community/confluence@1.0.0",
      "connector:community/notion@2.0.0"
    ],
    "staticContext": [
      {
        "name": "company-policies",
        "content": "Our refund policy allows returns within 30 days...",
        "priority": "high"
      }
    ]
  },

  "toolset": [
    "connector:community/salesforce@3.0.0",
    "connector:community/zendesk@1.5.0",
    "connector:community/slack@1.2.0"
  ],

  "memory": {
    "type": "buffer",
    "maxMessages": 20,
    "summarization": {
      "enabled": true,
      "threshold": 10,
      "strategy": "rolling"
    }
  },

  "guardrails": {
    "content": {
      "blockedTopics": ["politics", "religion"],
      "piiDetection": true,
      "toxicityThreshold": 0.8
    },
    "behavior": {
      "maxToolCalls": 15,
      "preventInfiniteLoops": true,
      "requireConfirmation": ["refund", "account_deletion"]
    },
    "output": {
      "maxLength": 2000,
      "format": "markdown",
      "languageCheck": true
    }
  },

  "policies": {
    "rateLimit": {
      "requestsPerMinute": 100,
      "tokensPerMinute": 50000
    },
    "cost": {
      "maxCostPerRequest": 0.50,
      "budgetAlert": 100.00
    },
    "privacy": {
      "logInputs": false,
      "logOutputs": true,
      "dataRetention": "30d"
    }
  },

  "io": {
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Customer inquiry or question"
        },
        "userId": {
          "type": "string",
          "description": "Customer user ID"
        },
        "context": {
          "type": "object",
          "description": "Additional context (conversation history, user profile, etc.)"
        }
      },
      "required": ["query"]
    },
    "outputSchema": {
      "type": "object",
      "properties": {
        "response": {
          "type": "string",
          "description": "Agent's response to the customer"
        },
        "actions": {
          "type": "array",
          "description": "Actions taken (e.g., created ticket, updated CRM)"
        },
        "confidence": {
          "type": "number",
          "description": "Confidence score (0-1)"
        },
        "needsEscalation": {
          "type": "boolean",
          "description": "Whether issue should be escalated to human"
        }
      }
    }
  },

  "metadata": {
    "categories": ["customer-support", "ai", "automation"],
    "tags": ["crm", "zendesk", "salesforce"],
    "license": "MIT",
    "author": "Smartify Team",
    "homepage": "https://docs.openworkflowspec.org/agents/customer-support"
  }
}
```

## Schema Fields Reference

### 1. Basic Metadata

```typescript
{
  "schemaVersion": "0.1.0",      // Required: spec version
  "type": "agent",                // Required: always "agent"
  "name": string,                 // Required: kebab-case name
  "namespace": string,            // Required: publisher namespace
  "version": string,              // Required: semantic version
  "displayName": string,          // Required: human-readable name
  "description": string           // Required: what this agent does
}
```

### 2. Execution

```typescript
{
  "execution": {
    "backend": "native" | "langchain" | "custom",  // Optional: preferred backend, default "native"
    "runtimeHint": "python" | "node" | "any",      // Optional: runtime preference for adapters
    "compatibility": {                              // Optional: version constraints
      "langchain": ">=0.1.0 <0.3.0",
      "openai-agents": ">=1.0.0"
    },
    "config": {                                     // Optional: runtime-agnostic config
      "maxIterations": number,
      "timeout": number,                            // seconds
      "streaming": boolean,
      "verbose": boolean
    }
  }
}
```

**Framework-Agnostic Design:** The `execution` section provides hints, not requirements. Runtimes select the appropriate backend based on availability and capability. Backend-specific configuration is pushed to adapter docs, not normative spec.

### 3. Model Configuration

```typescript
{
  "model": {
    "provider": "anthropic" | "openai" | "azure" | "bedrock" | "custom",
    "id": string,                    // Model identifier
    "temperature": number,           // 0.0 - 2.0, default 0.7
    "maxTokens": number,             // Max completion tokens
    "topP": number,                  // 0.0 - 1.0, default 1.0
    "topK": number,                  // Optional: for some providers
    "presencePenalty": number,       // -2.0 - 2.0, optional
    "frequencyPenalty": number,      // -2.0 - 2.0, optional
    "stopSequences": string[],       // Optional: stop sequences

    "fallback": {                    // Optional: fallback model
      "provider": string,
      "id": string
    },

    "providerConfig": {              // Optional: provider-specific config
      // Provider-specific parameters
    }
  }
}
```

**Supported Providers:**

- **Anthropic**: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, etc.
- **OpenAI**: `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo`, etc.
- **Azure**: Azure OpenAI models
- **Bedrock**: AWS Bedrock models
- **Custom**: Self-hosted or custom endpoints

### 4. Personality

```typescript
{
  "personality": {
    "name": string,                  // Optional: agent's name
    "role": string,                  // Optional: agent's role/title
    "traits": string[],              // Optional: personality traits
    "tone": string,                  // Optional: communication tone
    "systemPrompt": string,          // Required: base instruction prompt
    "examples": [                    // Optional: few-shot examples
      {
        "input": string,
        "output": string
      }
    ],
    "constraints": string[],         // Optional: behavioral constraints
    "language": string               // Optional: default "en"
  }
}
```

**Example:**
```json
{
  "personality": {
    "name": "Dr. Data",
    "role": "Data Analyst",
    "traits": ["analytical", "precise", "detail-oriented"],
    "tone": "professional and educational",
    "systemPrompt": "You are Dr. Data, an expert data analyst. Explain insights clearly and support claims with data.",
    "examples": [
      {
        "input": "What's our revenue trend?",
        "output": "Based on the data, revenue increased 15% QoQ. The main driver was our enterprise segment, which grew 23%. Here's the breakdown..."
      }
    ],
    "constraints": [
      "Always cite data sources",
      "Acknowledge uncertainty when data is incomplete",
      "Provide confidence intervals for predictions"
    ]
  }
}
```

### 5. Knowledge Base (RAG)

```typescript
{
  "knowledge": {
    "vectorStores": [                // Optional: vector databases
      {
        "id": string,                // Unique identifier
        "provider": "pinecone" | "weaviate" | "qdrant" | "chromadb" | "pgvector",
        "index": string,             // Index/collection name
        "topK": number,              // Number of results, default 5
        "scoreThreshold": number,    // Minimum similarity score, 0-1
        "metadata": object,          // Provider-specific metadata
        "config": object             // Connection config
      }
    ],
    "connectors": string[],          // Optional: knowledge connectors
    "staticContext": [               // Optional: static context documents
      {
        "name": string,
        "content": string,
        "priority": "high" | "medium" | "low"
      }
    ],
    "retrievalStrategy": {           // Optional: retrieval configuration
      "type": "similarity" | "mmr" | "hybrid",
      "diversityBias": number,       // For MMR, 0-1
      "rerank": boolean
    }
  }
}
```

**Vector Store Providers:**

**Pinecone:**
```json
{
  "provider": "pinecone",
  "index": "product-docs",
  "config": {
    "apiKey": "${PINECONE_API_KEY}",
    "environment": "us-west1-gcp"
  }
}
```

**Weaviate:**
```json
{
  "provider": "weaviate",
  "index": "Documentation",
  "config": {
    "url": "https://my-cluster.weaviate.network",
    "apiKey": "${WEAVIATE_API_KEY}"
  }
}
```

**ChromaDB:**
```json
{
  "provider": "chromadb",
  "index": "company_knowledge",
  "config": {
    "host": "localhost",
    "port": 8000
  }
}
```

### 6. Toolset

```typescript
{
  "toolset": string[]  // Array of connector references
}
```

**Example:**
```json
{
  "toolset": [
    "connector:community/web-search@1.0.0",
    "connector:community/calculator@1.0.0",
    "connector:github/mcp@0.4.1",
    "connector:acme/custom-api@2.0.0"
  ]
}
```

Tools are automatically translated for the execution backend:
- **Native**: Direct connector invocation
- **LangChain**: Auto-wrapped as LangChain tools

### 7. Memory

```typescript
{
  "memory": {
    "type": "buffer" | "summary" | "token_buffer" | "vector" | "none",
    "maxMessages": number,           // For buffer types
    "maxTokens": number,             // For token_buffer
    "summarization": {               // Optional: auto-summarization
      "enabled": boolean,
      "threshold": number,           // Trigger threshold
      "strategy": "rolling" | "periodic"
    },
    "vectorStore": {                 // For vector memory
      "provider": string,
      "index": string,
      "config": object
    }
  }
}
```

**Memory Types:**

- **buffer**: Keep last N messages
- **summary**: Summarize old messages
- **token_buffer**: Keep last N tokens
- **vector**: Store in vector database
- **none**: Stateless agent

**Example:**
```json
{
  "memory": {
    "type": "summary",
    "maxMessages": 50,
    "summarization": {
      "enabled": true,
      "threshold": 20,
      "strategy": "rolling"
    }
  }
}
```

### 8. Guardrails

```typescript
{
  "guardrails": {
    "content": {                     // Content filtering
      "blockedTopics": string[],
      "blockedPatterns": string[],   // Regex patterns
      "piiDetection": boolean,
      "toxicityThreshold": number,   // 0-1
      "languageFilter": string[]     // Allowed languages
    },
    "behavior": {                    // Behavioral constraints
      "maxToolCalls": number,
      "preventInfiniteLoops": boolean,
      "requireConfirmation": string[],  // Actions requiring confirmation
      "allowedDomains": string[],       // For web access
      "blockedDomains": string[]
    },
    "output": {                      // Output validation
      "maxLength": number,
      "minLength": number,
      "format": "text" | "markdown" | "json",
      "languageCheck": boolean,
      "schema": object               // JSON schema for structured output
    }
  }
}
```

**Example:**
```json
{
  "guardrails": {
    "content": {
      "blockedTopics": ["personal medical advice", "financial advice", "legal advice"],
      "piiDetection": true,
      "toxicityThreshold": 0.8
    },
    "behavior": {
      "maxToolCalls": 20,
      "preventInfiniteLoops": true,
      "requireConfirmation": ["delete_data", "send_email", "make_payment"]
    },
    "output": {
      "maxLength": 4000,
      "format": "markdown",
      "languageCheck": true
    }
  }
}
```

### 9. Policies

```typescript
{
  "policies": {
    "rateLimit": {
      "requestsPerMinute": number,
      "tokensPerMinute": number,
      "requestsPerDay": number
    },
    "cost": {
      "maxCostPerRequest": number,   // USD
      "budgetAlert": number,          // Daily budget alert
      "monthlyBudget": number
    },
    "privacy": {
      "logInputs": boolean,
      "logOutputs": boolean,
      "dataRetention": string,        // e.g., "30d", "1y"
      "anonymizeData": boolean
    },
    "compliance": {
      "gdpr": boolean,
      "hipaa": boolean,
      "sox": boolean
    }
  }
}
```

### 10. Input/Output Schema

```typescript
{
  "io": {
    "inputSchema": {                 // JSON Schema for input
      "type": "object",
      "properties": {...},
      "required": [...]
    },
    "outputSchema": {                // JSON Schema for output
      "type": "object",
      "properties": {...}
    }
  }
}
```

## Backend Compatibility

Agents are designed to be backend-agnostic. The schema declares capabilities; runtime adapters map to framework-specific implementations.

### Backend Selection

When used in workflows, backend resolution follows this priority:

1. **Step-level override**: Workflow step specifies `backend: "langchain"`
2. **Agent default**: Agent manifest's `execution.backend`
3. **Workflow default**: Workflow-level backend configuration
4. **Global default**: Native runtime

**Example Step-Level Override:**
```yaml
steps:
  - id: analyze_sentiment
    type: agent
    agent: agent:openworkflow/sentiment-analyzer@1.0.0
    backend: langchain  # Override agent's default backend
    input:
      text: "{{ steps.fetch_review.output.text }}"
```

### Adapter Responsibilities

Runtime adapters handle:
- Model provider integration
- Tool/connector invocation
- Memory management
- Guardrail enforcement
- Telemetry and observability

**For adapter implementation details, see:**
- [Execution Backends](./execution-backends.md) — Backend interface and resolution
- Native adapter docs — Smartify Runtime-specific features
- LangChain adapter docs — LangChain integration patterns
- Custom adapter guide — Implementing new backend adapters

## Complete Examples

### Example 1: Research Agent (Native)

```json
{
  "schemaVersion": "0.1.0",
  "type": "agent",
  "name": "research-assistant",
  "namespace": "smartify",
  "version": "1.0.0",
  "displayName": "Research Assistant",
  "description": "AI research assistant with web access and citation management",

  "execution": {
    "backend": "native"
  },

  "model": {
    "provider": "anthropic",
    "id": "claude-3-5-sonnet-20241022",
    "temperature": 0.3,
    "maxTokens": 4096
  },

  "personality": {
    "name": "Athena",
    "role": "Research Assistant",
    "traits": ["thorough", "analytical", "objective"],
    "tone": "academic and precise",
    "systemPrompt": "You are Athena, a research assistant. Always cite sources, acknowledge limitations, and provide balanced perspectives."
  },

  "knowledge": {
    "vectorStores": [
      {
        "id": "research-papers",
        "provider": "pinecone",
        "index": "arxiv-papers",
        "topK": 10,
        "scoreThreshold": 0.75
      }
    ]
  },

  "toolset": [
    "connector:community/web-search@1.0.0",
    "connector:community/wikipedia@1.0.0",
    "connector:community/arxiv@1.0.0"
  ],

  "memory": {
    "type": "summary",
    "maxMessages": 30,
    "summarization": {
      "enabled": true,
      "threshold": 15,
      "strategy": "rolling"
    }
  },

  "guardrails": {
    "content": {
      "piiDetection": true
    },
    "behavior": {
      "maxToolCalls": 25,
      "allowedDomains": ["arxiv.org", "scholar.google.com", "wikipedia.org"]
    }
  },

  "io": {
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "depth": {"type": "string", "enum": ["quick", "comprehensive"]}
      },
      "required": ["query"]
    }
  }
}
```

### Example 2: Code Review Agent (LangChain)

```json
{
  "schemaVersion": "0.1.0",
  "type": "agent",
  "name": "code-reviewer",
  "namespace": "acme",
  "version": "2.0.0",
  "displayName": "Code Review Agent",
  "description": "Automated code review with best practices enforcement",

  "execution": {
    "backend": "langchain",
    "runtime": "python",
    "config": {
      "agent_type": "react",
      "max_iterations": 15,
      "verbose": false
    }
  },

  "model": {
    "provider": "openai",
    "id": "gpt-4-turbo",
    "temperature": 0.2
  },

  "personality": {
    "role": "Senior Code Reviewer",
    "traits": ["detail-oriented", "constructive", "security-conscious"],
    "systemPrompt": "You are a senior code reviewer. Focus on code quality, security, performance, and best practices. Provide actionable feedback.",
    "constraints": [
      "Flag all security vulnerabilities",
      "Check for code smells and anti-patterns",
      "Suggest improvements with examples"
    ]
  },

  "knowledge": {
    "staticContext": [
      {
        "name": "coding-standards",
        "content": "Company coding standards: ...",
        "priority": "high"
      }
    ],
    "connectors": [
      "connector:community/github@2.0.0"
    ]
  },

  "toolset": [
    "connector:acme/lint-runner@1.0.0",
    "connector:acme/test-runner@1.0.0",
    "connector:community/github@2.0.0"
  ],

  "memory": {
    "type": "buffer",
    "maxMessages": 10
  },

  "guardrails": {
    "behavior": {
      "maxToolCalls": 10
    },
    "output": {
      "format": "markdown",
      "maxLength": 3000
    }
  }
}
```

### Example 3: Customer Support with Knowledge Base

```json
{
  "schemaVersion": "0.1.0",
  "type": "agent",
  "name": "support-bot",
  "namespace": "smartify",
  "version": "1.5.0",
  "displayName": "Support Bot",
  "description": "Customer support agent with access to documentation and ticketing system",

  "model": {
    "provider": "anthropic",
    "id": "claude-3-5-sonnet-20241022",
    "temperature": 0.7
  },

  "personality": {
    "name": "Sam",
    "role": "Support Specialist",
    "traits": ["empathetic", "patient", "solution-oriented"],
    "tone": "warm and professional",
    "systemPrompt": "You are Sam, a support specialist. Always acknowledge customer frustration, provide clear solutions, and follow up.",
    "examples": [
      {
        "input": "This product doesn't work!",
        "output": "I'm sorry you're experiencing issues. I'm here to help get this resolved for you. Let me understand what's happening - could you describe what you're seeing?"
      }
    ]
  },

  "knowledge": {
    "vectorStores": [
      {
        "id": "product-docs",
        "provider": "weaviate",
        "index": "ProductDocs",
        "topK": 5,
        "scoreThreshold": 0.7
      },
      {
        "id": "support-kb",
        "provider": "chromadb",
        "index": "support_articles",
        "topK": 3
      }
    ],
    "connectors": [
      "connector:community/confluence@1.0.0"
    ]
  },

  "toolset": [
    "connector:community/zendesk@1.5.0",
    "connector:community/salesforce@3.0.0",
    "connector:community/slack@1.2.0"
  ],

  "memory": {
    "type": "buffer",
    "maxMessages": 20
  },

  "guardrails": {
    "content": {
      "piiDetection": true,
      "toxicityThreshold": 0.9
    },
    "behavior": {
      "requireConfirmation": ["create_refund", "cancel_subscription"],
      "maxToolCalls": 15
    }
  },

  "policies": {
    "rateLimit": {
      "requestsPerMinute": 50
    },
    "privacy": {
      "logInputs": false,
      "dataRetention": "90d"
    }
  }
}
```

## Validation Rules

1. **Required fields**: `schemaVersion`, `type`, `name`, `namespace`, `version`, `model`
2. **Backend compatibility**: Validate backend-specific features
3. **Model provider**: Must be supported by chosen backend
4. **Toolset references**: All connectors must exist or be installable
5. **Vector stores**: Connection config must be valid
6. **Schema validation**: Input/output schemas must be valid JSON Schema

## CLI Usage

```bash
# Validate agent
smartify validate agent.json

# Test agent locally
smartify agent run agent:acme/support-bot@1.0.0 \
  --input '{"query": "How do I reset my password?"}'

# Test with specific backend
smartify agent run agent.json \
  --backend langchain \
  --input query="Test question"

# Publish to registry
smartify publish agent.json

# Install agent
smartify add agent:openworkflow/research-assistant@1.0.0
```

## SDK Usage

```python
from openworkflow import OpenWorkflow, Agent

# Load agent
openworkflow = OpenWorkflow()
agent = openworkflow.load_agent("agent:openworkflow/support-bot@1.5.0")

# Execute
result = agent.execute({
    "query": "How do I reset my password?",
    "userId": "user_123"
})

print(result["response"])
print(f"Confidence: {result['confidence']}")

# With streaming
for chunk in agent.stream({"query": "Tell me about your pricing"}):
    print(chunk["delta"], end="", flush=True)
```

## Best Practices

1. **System Prompts**: Be specific about behavior, tone, and constraints
2. **Examples**: Provide 3-5 diverse examples for better performance
3. **Guardrails**: Always include content filtering for user-facing agents
4. **Memory**: Choose memory type based on conversation length
5. **Knowledge**: Keep vector stores updated and indexed
6. **Tools**: Only include necessary connectors to reduce context
7. **Testing**: Test with diverse inputs before production
8. **Monitoring**: Track token usage, latency, and error rates

## Next Steps

- [Execution Backends](./execution-backends.md) - Backend configuration details
- [Connector Schema](./connector-schema.md) - Build tools for agents
- [Workflow Schema](./workflow-schema.md) - Use agents in workflows
- [Registry Taxonomy](./registry-taxonomy.md) - Publishing agents
