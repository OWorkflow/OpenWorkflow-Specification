# Calculator Connector Example

This example demonstrates the **SDK function handler** pattern - the simplest way to create a OpenWorkflow connector. No HTTP service required, just pure Python functions.

## Key Features

- **Zero infrastructure**: No web server, no containers
- **Pure functions**: Simple Python functions decorated with `@action`
- **Local execution**: Runs in the same process as your application
- **Fast**: No network overhead

## Usage

### Basic Setup

```python
from openworkflow import OpenWorkflow, Workflow
import handlers  # Imports register all actions

openworkflow = OpenWorkflow(execution_mode="local")
openworkflow.register_connector("connector.yaml")

workflow = Workflow.from_file("workflow.yaml")
result = workflow.execute()
```

### Direct Action Calls

```python
from handlers import add, multiply, percentage

# Call actions directly
result = add(10, 5)
print(result)  # {"result": 15}

# Chain operations
sum_result = add(10, 5)["result"]
product = multiply(sum_result, 2)["result"]
final = percentage(product, 15)["result"]

print(f"15% of (10 + 5) * 2 = {final}")
```

### In a Workflow

```yaml
workflow:
  name: Compound Interest Calculator

  inputs:
    principal:
      type: number
      description: Initial investment amount
      default: 1000
    rate:
      type: number
      description: Annual interest rate (percentage)
      default: 5
    years:
      type: number
      description: Investment period in years
      default: 10

  steps:
    # Convert rate to decimal
    - name: rate_to_decimal
      plugin: calculator
      action: divide
      input:
        a: "{{ inputs.rate }}"
        b: 100

    # Calculate (1 + rate)^years
    - name: calculate_power
      plugin: calculator
      action: power
      input:
        base: "{{ 1 + steps.rate_to_decimal.output.result }}"
        exponent: "{{ inputs.years }}"

    # Calculate final amount
    - name: final_amount
      plugin: calculator
      action: multiply
      input:
        a: "{{ inputs.principal }}"
        b: "{{ steps.calculate_power.output.result }}"

    # Calculate total interest earned
    - name: interest_earned
      plugin: calculator
      action: subtract
      input:
        a: "{{ steps.final_amount.output.result }}"
        b: "{{ inputs.principal }}"

  outputs:
    final_amount:
      value: "{{ steps.final_amount.output.result }}"
      description: Total value after compound interest
    interest_earned:
      value: "{{ steps.interest_earned.output.result }}"
      description: Total interest earned
```

Execute:
```python
workflow = Workflow.from_file("compound_interest.yaml")
result = workflow.execute(inputs={
    "principal": 1000,
    "rate": 5,
    "years": 10
})

print(f"Final amount: ${result.outputs['final_amount']:.2f}")
print(f"Interest earned: ${result.outputs['interest_earned']:.2f}")
```

## Handler Implementation

Each action is a simple Python function:

```python
from openworkflow import action

@action("calculator.add")
def add(a: float, b: float) -> dict:
    """Add two numbers."""
    return {"result": a + b}
```

The `@action` decorator:
1. Registers the function with the SDK
2. Maps it to the action name in `connector.yaml`
3. Handles input validation against the schema
4. Wraps errors in standard format

## Error Handling

```python
@action("calculator.divide")
def divide(a: float, b: float) -> dict:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return {"result": a / b}
```

Errors are automatically caught and formatted:
```json
{
  "status": "error",
  "message": "Cannot divide by zero",
  "code": "VALUE_ERROR"
}
```

## Testing

```python
import pytest
from handlers import add, divide, sqrt

def test_add():
    result = add(2, 3)
    assert result["result"] == 5

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)

def test_sqrt_negative():
    with pytest.raises(ValueError, match="Cannot calculate square root"):
        sqrt(-4)
```

## When to Use This Pattern

✅ **Good for:**
- Simple computational connectors
- Local-only execution
- Embedded in applications
- Quick prototyping
- No external dependencies

❌ **Not ideal for:**
- Connectors with external API calls (use HTTP handler)
- Multi-language support needed
- Independent scaling requirements
- Network-isolated execution

## Converting to HTTP Service

If you later need to deploy as a service:

```python
from fastapi import FastAPI
from handlers import add, subtract, multiply, divide

app = FastAPI()

@app.post("/execute")
def execute(request: dict):
    action = request["action"]
    input_data = request["input"]

    # Route to appropriate handler
    handlers = {
        "calculator.add": add,
        "calculator.subtract": subtract,
        "calculator.multiply": multiply,
        "calculator.divide": divide,
    }

    handler = handlers.get(action)
    if not handler:
        return {"status": "error", "message": f"Unknown action: {action}"}

    try:
        result = handler(**input_data)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

Update `connector.yaml` handler:
```yaml
handler:
  http:
    url: http://calculator-service:8000/execute
    method: POST
```

## Advantages

1. **Simplicity**: No web framework needed
2. **Performance**: In-process execution is fastest
3. **Debugging**: Use standard Python debugger
4. **Testing**: Test functions directly, no HTTP mocking
5. **Dependencies**: Minimal requirements

## Next Steps

- See [Weather Example](../weather/) for HTTP-based connector
- Read [SDK Contract](../../specs/sdk-contract.md) for full SDK API
- Explore [Workflow Schema](../../specs/workflow-schema.md) for advanced patterns
