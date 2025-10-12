# Contributing to OpenWorkflow Open Specification

Thank you for your interest in contributing to the OpenWorkflow Open Specification! This document provides guidelines for contributing to the specification and ecosystem.

## Ways to Contribute

### 1. Specification Improvements

- Clarify existing specifications
- Propose new features or patterns
- Fix typos or errors
- Add examples and use cases
- Improve documentation

### 2. Connector Contributions

- Submit community connectors to the registry
- Improve existing connectors
- Add tests and documentation
- Fix bugs

### 3. SDK Development

- Implement SDKs for new languages
- Improve existing SDK implementations
- Add features and bug fixes
- Write tests

### 4. Example Projects

- Create example connectors and workflows
- Share real-world use cases
- Write tutorials and guides

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/Open-Workflow/OpenWorkflow-Specification.git
   cd OpenWorkflow-Specification
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/my-contribution
   ```

3. **Make your changes**
   - Follow existing patterns and style
   - Add tests if applicable
   - Update documentation

4. **Submit a pull request**
   - Provide clear description
   - Reference related issues
   - Ensure tests pass

## Specification Changes

### Proposal Process

Major changes to the specification follow this process:

1. **Open an issue** describing the proposed change
2. **Discuss** with the community and maintainers
3. **Create a proposal** document if needed
4. **Submit PR** with specification changes
5. **Review and iterate** based on feedback
6. **Approval** by maintainers
7. **Merge** and version bump

### What Requires a Proposal

- New schema fields or structures
- Breaking changes to existing specs
- New execution modes or patterns
- Changes to core concepts

### What Doesn't Require a Proposal

- Clarifications and typo fixes
- Additional examples
- Documentation improvements
- Non-breaking additions

## Connector Submissions

### Connector Quality Guidelines

Connectors submitted to the public registry should:

1. **Be well-documented**
   - Clear description of functionality
   - Usage examples
   - API documentation for all actions

2. **Have proper error handling**
   - Graceful failure modes
   - Helpful error messages
   - Retry logic for transient failures

3. **Include tests**
   - Unit tests for handlers
   - Integration tests with real services
   - Example workflows

4. **Follow security best practices**
   - Secure credential handling
   - Input validation
   - No hardcoded secrets

5. **Be maintained**
   - Responsive to issues
   - Regular updates
   - Clear deprecation policy

### Submission Process

```bash
# 1. Validate your connector
smartify validate connector.yaml

# 2. Test locally
smartify test connector.yaml

# 3. Submit to registry
smartify publish connector.yaml

# 4. Create PR to add to community index
# Edit: registry/community-connectors.yaml
```

## Code Style

### YAML/JSON

- Use 2 spaces for indentation
- Quote string values consistently
- Add comments for complex configurations
- Order fields logically (required fields first)

**Example:**
```yaml
connector:
  type: connector
  kind: http
  name: my-connector
  namespace: myorg
  version: 1.0.0
  displayName: My Connector
  description: Clear description here

actions:
  - name: action_name
    description: What this action does
    input:
      type: object
      properties:
        required_field:
          type: string
          description: Field description
        optional_field:
          type: string
          default: "default value"
```

### Python

- Follow PEP 8
- Type hints for all functions
- Docstrings for public APIs
- Descriptive variable names

### JavaScript/TypeScript

- Use ESLint with recommended config
- Async/await over callbacks
- Type definitions for TypeScript
- JSDoc for documentation

### Go

- Follow standard Go conventions
- Run gofmt before committing
- Use meaningful variable names
- Write tests

## Documentation

### Writing Style

- **Clear and concise**: Get to the point quickly
- **Examples first**: Show before explaining
- **Complete**: Don't assume knowledge
- **Searchable**: Use clear headings and keywords

### Documentation Structure

```
specs/
  ├── plugin-schema.md      # Technical specification
  ├── sdk-contract.md       # SDK requirements
  └── ...

examples/
  ├── weather/              # Complete example
  │   ├── README.md         # Usage guide
  │   ├── connector.yaml    # Connector definition
  │   └── ...
  └── ...
```

## Testing

### Connector Tests

```python
# tests/test_weather.py
from openworkflow.testing import MockSmartify, mock_action
from weather import get_current_weather

def test_get_weather_success():
    result = get_current_weather({"location": "San Francisco"})
    assert result["status"] == "success"
    assert "temperature" in result

def test_get_weather_invalid_location():
    with pytest.raises(ValueError):
        get_current_weather({"location": ""})
```

### Workflow Tests

```bash
# Test workflow with mock inputs
smartify workflow test workflow.yaml \
  --input location="Test City" \
  --mock weather.get_current_weather='{"temperature": 72}'
```

## Versioning

The specification follows semantic versioning:

- **Major (2.0.0)**: Breaking changes
- **Minor (1.1.0)**: New features, backward compatible
- **Patch (1.0.1)**: Bug fixes, clarifications

## Communication

- **GitHub Issues**: Bug reports, feature requests
- **Discussions**: Questions, brainstorming
- **Discord**: Real-time chat (community.openworkflowspec.org)
- **Email**: security@openworkflow.ai (security issues only)

## Code of Conduct

### Our Standards

- **Respectful**: Treat everyone with respect
- **Inclusive**: Welcome diverse perspectives
- **Constructive**: Provide helpful feedback
- **Professional**: Keep discussions on-topic

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in the project

## Questions?

- Read the [FAQ](./FAQ.md)
- Ask in [Discussions](https://github.com/Open-Workflow/OpenWorkflow-Specification/discussions)
- Join our [Discord](https://community.openworkflowspec.org)

Thank you for contributing to Smartify! 🚀
