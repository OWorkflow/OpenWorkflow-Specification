"""
Calculator connector handlers - Pure SDK function implementation.

This demonstrates the simplest OpenWorkflow connector implementation:
no HTTP service needed, just register Python functions with Smartify SDK.
"""

from smartify import action
import math


@action("calculator.add")
def add(a: float, b: float) -> dict:
    """Add two numbers."""
    return {"result": a + b}


@action("calculator.subtract")
def subtract(a: float, b: float) -> dict:
    """Subtract b from a."""
    return {"result": a - b}


@action("calculator.multiply")
def multiply(a: float, b: float) -> dict:
    """Multiply two numbers."""
    return {"result": a * b}


@action("calculator.divide")
def divide(a: float, b: float) -> dict:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return {"result": a / b}


@action("calculator.power")
def power(base: float, exponent: float) -> dict:
    """Raise base to exponent power."""
    return {"result": math.pow(base, exponent)}


@action("calculator.sqrt")
def sqrt(value: float) -> dict:
    """Calculate square root."""
    if value < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return {"result": math.sqrt(value)}


@action("calculator.percentage")
def percentage(value: float, percent: float) -> dict:
    """Calculate percentage of a value."""
    return {"result": (value * percent) / 100}


# Example usage
if __name__ == "__main__":
    from smartify import Smartify, Workflow

    # Initialize Smartify Runtime and register OpenWorkflow connector
    smartify = Smartify(execution_mode="local")
    smartify.register_connector("connector.yaml")

    # All functions are automatically registered via @action decorator

    # Create a simple workflow
    workflow_config = {
        "workflow": {
            "name": "Math Operations Demo",
            "steps": [
                {
                    "name": "add_numbers",
                    "plugin": "calculator",
                    "action": "add",
                    "input": {"a": 10, "b": 5}
                },
                {
                    "name": "multiply_result",
                    "plugin": "calculator",
                    "action": "multiply",
                    "input": {
                        "a": "{{ steps.add_numbers.output.result }}",
                        "b": 2
                    }
                },
                {
                    "name": "calculate_percentage",
                    "plugin": "calculator",
                    "action": "percentage",
                    "input": {
                        "value": "{{ steps.multiply_result.output.result }}",
                        "percent": 15
                    }
                }
            ]
        }
    }

    workflow = Workflow(workflow_config)
    result = workflow.execute()

    print(f"Add result: {result.steps['add_numbers']['output']['result']}")
    print(f"Multiply result: {result.steps['multiply_result']['output']['result']}")
    print(f"15% of result: {result.steps['calculate_percentage']['output']['result']}")
