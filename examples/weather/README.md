# Weather Connector Example

This example demonstrates a complete weather connector that fetches current conditions and forecasts using the Open-Meteo API.

## Structure

- `connector.yaml` - Connector definition with two actions
- `workflows.yaml` - Multiple workflows example (daily report, alerts, health check)
- `service.py` - HTTP service implementation (Python/FastAPI)

## Actions

### get_current_weather

Fetches current weather conditions for a location.

**Input:**
```json
{
  "location": "San Francisco"
}
```

**Output:**
```json
{
  "location": "San Francisco",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "temperature": 18.5,
  "windspeed": 12.3,
  "wind_direction": 280,
  "weather_code": 2,
  "time": "2025-10-07T12:00:00Z",
  "status": "success"
}
```

### get_forecast

Gets 7-day weather forecast.

**Input:**
```json
{
  "location": "New York",
  "days": 7
}
```

## Running Locally

### Install Connector

```bash
# Load connector into SDK
smartify add connector:community/weather

# Or install from local file
smartify add ./connector.yaml
```

### Execute Workflows

**Python SDK:**
```python
from openworkflow import OpenWorkflow, Workflows

openworkflow = OpenWorkflow(execution_mode="local")
openworkflow.register_connector("connector.yaml")

# Load all workflows
workflows = Workflows.from_file("workflows.yaml")

# Execute specific workflow
report_result = workflows.execute("Daily Weather Report", inputs={
    "locations": ["San Francisco", "Seattle"]
})

# Execute health check
health_result = workflows.execute("Service Health Check")

# Or execute all workflows
results = workflows.execute_all()
```

**CLI:**
```bash
# Execute specific workflow
smartify workflow run workflows.yaml --workflow "Daily Weather Report" --input locations='["Boston","NYC"]'

# List available workflows
smartify workflow list workflows.yaml

# Execute all workflows
smartify workflow run workflows.yaml --all
```

### Run as HTTP Service

```bash
# Install dependencies
pip install fastapi uvicorn requests

# Start service
uvicorn service:app --host 0.0.0.0 --port 8000

# Test endpoint
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{"location": "San Francisco"}'
```

## Deploying

### Docker

```bash
# Build image
docker build -t weather-plugin .

# Run container
docker run -d -p 8000:8000 \
  -e MCP_ROUTER_URL=http://mcp-router:8000 \
  weather-plugin
```

### Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
```

### OpenWorkflow Cloud

```bash
# Publish to registry
smartify publish connector.yaml

# Deploy workflow
smartify workflow deploy workflows.yaml
```

## Testing

```bash
# Validate connector schema
smartify validate connector.yaml

# Test workflow
smartify workflow test workflow.yaml --input locations='["Boston","Seattle"]'
```

## Implementation Notes

### Error Handling

The connector implements retry logic with exponential backoff for external API calls:
- Geocoding API (Nominatim)
- Weather API (Open-Meteo)

### Rate Limiting

Open-Meteo API limits:
- 10,000 requests/day for free tier
- Consider caching results for same location within time window

### Weather Codes

WMO weather codes:
- 0: Clear sky
- 1-3: Partly cloudy
- 45, 48: Fog
- 51-67: Rain
- 71-77: Snow
- 80-99: Thunderstorm

See: https://open-meteo.com/en/docs

## Extending

### Add New Actions

Add to `connector.yaml`:
```yaml
actions:
  - name: get_air_quality
    description: Get air quality index for a location
    # ... action definition
```

### Custom Handler

Use SDK function instead of HTTP:
```python
from openworkflow import action

@action("weather.get_current_weather")
def get_weather(location: str) -> dict:
    # Custom implementation
    return {"temperature": 20, "location": location}
```

## References

- [Connector Schema Spec](../../specs/connector-schema.md)
- [Workflow Schema Spec](../../specs/workflow-schema.md)
- [Open-Meteo API Docs](https://open-meteo.com/en/docs)
