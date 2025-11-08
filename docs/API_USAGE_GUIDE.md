# API Usage Guide

Complete guide for using the KooAI API for simulation analysis and data processing.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [File Upload & Processing](#file-upload--processing)
- [LLM Integration](#llm-integration)
- [Real-time Updates](#real-time-updates)
- [Data Visualization](#data-visualization)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Code Examples](#code-examples)

---

## Getting Started

### Base URL

```
Production: https://api.kooai.com/api/v1
Development: http://localhost:8000/api/v1
```

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `{BASE_URL}/docs`
- **ReDoc**: `{BASE_URL}/redoc`
- **OpenAPI Spec**: `{BASE_URL}/openapi.json`

### Quick Start

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-08T10:30:00Z"
}
```

---

## Authentication

KooAI uses JWT (JSON Web Token) authentication with access and refresh tokens.

### Registration

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "role": "user"
  }'
```

**Response:**
```json
{
  "user_id": "usr_abc123",
  "email": "user@example.com",
  "username": "johndoe",
  "role": "user",
  "is_active": true,
  "created_at": "2025-11-08T10:30:00Z"
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Access Tokens

Include the access token in the Authorization header for all protected endpoints:

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Refreshing Tokens

When the access token expires (30 minutes), use the refresh token to get a new one:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

### User Roles

- **admin**: Full access to all resources and user management
- **user**: Standard access to upload, analyze, and visualize data
- **readonly**: Read-only access to view existing data

---

## File Upload & Processing

### Simple File Upload

```bash
curl -X POST http://localhost:8000/api/v1/simulations/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@simulation.vtk" \
  -F "simulation_type=cfd"
```

**Response:**
```json
{
  "simulation_id": "sim_xyz789",
  "filename": "simulation.vtk",
  "file_size": 1048576,
  "simulation_type": "cfd",
  "status": "uploaded",
  "created_at": "2025-11-08T10:35:00Z"
}
```

### Streaming Upload (Large Files)

For files larger than 100MB, use streaming upload:

```bash
curl -X POST http://localhost:8000/api/v1/files/upload/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@large_simulation.vtk" \
  -F "destination=uploads/large_simulation.vtk"
```

**Response:**
```json
{
  "filename": "large_simulation.vtk",
  "file_size": 524288000,
  "uploaded_size": 524288000,
  "checksum": "5d41402abc4b2a76b9719d911017c592",
  "upload_time_seconds": 45.2,
  "status": "completed"
}
```

### Resumable Upload

If an upload is interrupted, resume it:

```bash
# 1. Check uploaded size
curl -X GET http://localhost:8000/api/v1/files/checksum/large_simulation.vtk \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Resume from byte offset
curl -X POST http://localhost:8000/api/v1/files/upload/resume \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@large_simulation.vtk" \
  -F "destination=uploads/large_simulation.vtk" \
  -F "offset=104857600"  # Resume from 100MB
```

### Batch Upload

Upload multiple files at once:

```bash
curl -X POST http://localhost:8000/api/v1/files/upload/batch \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@sim1.vtk" \
  -F "files=@sim2.vtk" \
  -F "files=@sim3.vtk" \
  -F "destination_dir=uploads/batch"
```

### List Simulations

```bash
curl -X GET "http://localhost:8000/api/v1/simulations?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "simulations": [
    {
      "simulation_id": "sim_xyz789",
      "filename": "simulation.vtk",
      "simulation_type": "cfd",
      "status": "analyzed",
      "created_at": "2025-11-08T10:35:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

### Get Simulation Details

```bash
curl -X GET http://localhost:8000/api/v1/simulations/sim_xyz789 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## LLM Integration

### Analyze Simulation (Blocking)

```bash
curl -X POST http://localhost:8000/api/v1/simulations/sim_xyz789/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "comprehensive",
    "parameters": {
      "focus_areas": ["convergence", "boundary_conditions", "mesh_quality"]
    }
  }'
```

### Streaming Analysis (Server-Sent Events)

For real-time streaming responses:

```bash
curl -N -X POST http://localhost:8000/api/v1/llm/analyze/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Analyze the convergence behavior of this CFD simulation",
    "simulation_id": "sim_xyz789",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

**Response (Server-Sent Events):**
```
data: {"content": "Based", "chunk_id": 0, "is_final": false}

data: {"content": " on", "chunk_id": 1, "is_final": false}

data: {"content": " the", "chunk_id": 2, "is_final": false}

...

data: {"content": "", "chunk_id": 50, "is_final": true, "total_tokens": 450}
```

### Conversation Context

Create a conversation context for multi-turn dialogues:

```bash
# 1. Create context
curl -X POST http://localhost:8000/api/v1/llm/context/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "max_turns": 10
  }'

# Response: {"context_id": "ctx_abc123"}

# 2. Use context in streaming analysis
curl -N -X POST http://localhost:8000/api/v1/llm/analyze/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the Reynolds number?",
    "context_id": "ctx_abc123"
  }'

# 3. Continue conversation
curl -N -X POST http://localhost:8000/api/v1/llm/analyze/stream \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Is that in the laminar or turbulent regime?",
    "context_id": "ctx_abc123"
  }'

# 4. Delete context when done
curl -X DELETE http://localhost:8000/api/v1/llm/context/ctx_abc123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Token Usage Tracking

```bash
curl -X GET http://localhost:8000/api/v1/llm/usage \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "total_tokens": 15000,
  "total_cost_usd": 0.045,
  "usage_by_model": {
    "gpt-4": {
      "prompt_tokens": 8000,
      "completion_tokens": 7000,
      "total_tokens": 15000,
      "cost_usd": 0.045
    }
  }
}
```

---

## Real-time Updates

### WebSocket Connection

Connect to WebSocket for real-time updates:

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/client_123');

ws.onopen = () => {
  console.log('Connected to WebSocket');

  // Subscribe to upload progress
  ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['upload_progress', 'processing_status']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);

  switch(message.type) {
    case 'upload_progress':
      console.log(`Upload: ${message.data.progress}%`);
      break;
    case 'processing_status':
      console.log(`Processing: ${message.data.status}`);
      break;
    case 'notification':
      console.log(`Notification: ${message.data.message}`);
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from WebSocket');
};
```

**Python Example:**
```python
import asyncio
import websockets
import json

async def connect_websocket():
    uri = "ws://localhost:8000/api/v1/ws/client_123"

    async with websockets.connect(uri) as websocket:
        # Subscribe to channels
        await websocket.send(json.dumps({
            "action": "subscribe",
            "channels": ["upload_progress", "processing_status"]
        }))

        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

            if data["type"] == "upload_progress":
                progress = data["data"]["progress"]
                print(f"Upload: {progress}%")

asyncio.run(connect_websocket())
```

### Message Types

#### Upload Progress
```json
{
  "type": "upload_progress",
  "data": {
    "filename": "simulation.vtk",
    "progress": 75.5,
    "uploaded": 78643200,
    "total": 104857600
  },
  "timestamp": "2025-11-08T10:40:00Z"
}
```

#### Processing Status
```json
{
  "type": "processing_status",
  "data": {
    "task_id": "task_xyz",
    "status": "running",
    "progress": 50.0,
    "message": "Analyzing mesh quality..."
  },
  "timestamp": "2025-11-08T10:41:00Z"
}
```

#### Notification
```json
{
  "type": "notification",
  "data": {
    "level": "info",
    "title": "Analysis Complete",
    "message": "Simulation analysis completed successfully"
  },
  "timestamp": "2025-11-08T10:42:00Z"
}
```

---

## Data Visualization

### 3D Rendering

Render 3D visualization from VTK files:

```bash
curl -X POST http://localhost:8000/api/v1/visualizations/render/3d \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "uploads/simulation.vtk",
    "scalar_field": "temperature",
    "resolution_width": 1920,
    "resolution_height": 1080,
    "camera_position": [1, 1, 1],
    "show_axes": true,
    "background_color": "white"
  }' \
  --output render.png
```

### Slice Visualization

Generate 2D slice through 3D data:

```bash
curl -X POST http://localhost:8000/api/v1/visualizations/render/slice \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "uploads/simulation.vtk",
    "scalar_field": "velocity",
    "normal_x": 0,
    "normal_y": 0,
    "normal_z": 1,
    "resolution_width": 1920,
    "resolution_height": 1080
  }' \
  --output slice.png
```

### Multiple Slices

```bash
curl "http://localhost:8000/api/v1/visualizations/render/multi-slice?file_path=uploads/simulation.vtk&scalar_field=pressure&n_slices=10&normal_z=1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output multi_slice.png
```

### Chart Generation

Generate charts from data:

```bash
# Line chart
curl -X POST http://localhost:8000/api/v1/visualizations/charts/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chart_type": "line",
    "data": [
      [0, 1, 2, 3, 4, 5],
      [0, 1, 4, 9, 16, 25]
    ],
    "title": "Convergence History",
    "xlabel": "Iteration",
    "ylabel": "Residual",
    "output_format": "png"
  }' \
  --output chart.png
```

### Interactive Charts

Generate interactive HTML charts:

```bash
curl -X POST http://localhost:8000/api/v1/visualizations/charts/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "chart_type": "line",
    "data": [[0, 1, 2, 3], [0, 1, 4, 9]],
    "title": "Interactive Chart",
    "output_format": "html"
  }' \
  --output chart.html
```

### Chart from File

Generate chart directly from CSV:

```bash
# Create CSV file
echo -e "0,0\n1,1\n2,4\n3,9\n4,16" > data.csv

# Generate chart
curl -X POST "http://localhost:8000/api/v1/visualizations/charts/from-file?chart_type=line&title=Data" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@data.csv" \
  --output chart.png
```

### Available Fields

List scalar fields in VTK file:

```bash
curl "http://localhost:8000/api/v1/visualizations/fields/uploads/simulation.vtk" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "fields": ["temperature", "pressure", "velocity", "density"],
  "file_path": "uploads/simulation.vtk"
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2025-11-08T10:45:00Z"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Handling Authentication Errors

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/simulations/upload",
    headers={"Authorization": f"Bearer {access_token}"},
    files={"file": open("simulation.vtk", "rb")}
)

if response.status_code == 401:
    # Token expired, refresh it
    refresh_response = requests.post(
        "http://localhost:8000/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    if refresh_response.status_code == 200:
        new_tokens = refresh_response.json()
        access_token = new_tokens["access_token"]

        # Retry original request
        response = requests.post(
            "http://localhost:8000/api/v1/simulations/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": open("simulation.vtk", "rb")}
        )
```

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

---

## Rate Limiting

### Rate Limit Headers

Every response includes rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699459200
```

### Default Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| Authentication | 10 requests | 1 minute |
| File Upload | 20 requests | 1 hour |
| Analysis | 50 requests | 1 hour |
| Visualization | 100 requests | 1 hour |
| General API | 1000 requests | 1 hour |

### Handling Rate Limits

```python
import time

response = requests.get(url, headers=headers)

if response.status_code == 429:
    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
    wait_seconds = reset_time - int(time.time())

    if wait_seconds > 0:
        print(f"Rate limited. Waiting {wait_seconds} seconds...")
        time.sleep(wait_seconds)

        # Retry request
        response = requests.get(url, headers=headers)
```

---

## Code Examples

### Python Client

```python
import requests
from pathlib import Path

class KooAIClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    def login(self, email, password):
        """Login and store tokens."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()

        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

        return data

    def _headers(self):
        """Get authorization headers."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def upload_simulation(self, file_path, simulation_type="cfd"):
        """Upload simulation file."""
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.base_url}/simulations/upload",
                headers=self._headers(),
                files={"file": f},
                data={"simulation_type": simulation_type}
            )
        response.raise_for_status()
        return response.json()

    def analyze_simulation(self, simulation_id):
        """Analyze simulation."""
        response = requests.post(
            f"{self.base_url}/simulations/{simulation_id}/analyze",
            headers=self._headers(),
            json={"analysis_type": "comprehensive"}
        )
        response.raise_for_status()
        return response.json()

    def render_3d(self, file_path, output_path, scalar_field=None):
        """Render 3D visualization."""
        response = requests.post(
            f"{self.base_url}/visualizations/render/3d",
            headers=self._headers(),
            json={
                "file_path": file_path,
                "scalar_field": scalar_field,
                "resolution_width": 1920,
                "resolution_height": 1080
            }
        )
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

# Usage
client = KooAIClient()
client.login("user@example.com", "password")

sim = client.upload_simulation("simulation.vtk")
analysis = client.analyze_simulation(sim["simulation_id"])
client.render_3d("uploads/simulation.vtk", "render.png", "temperature")
```

### JavaScript/TypeScript Client

```typescript
class KooAIClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000/api/v1') {
    this.baseUrl = baseUrl;
  }

  async login(email: string, password: string) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) throw new Error('Login failed');

    const data = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;

    return data;
  }

  private headers() {
    return {
      'Authorization': `Bearer ${this.accessToken}`
    };
  }

  async uploadSimulation(file: File, simulationType: string = 'cfd') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('simulation_type', simulationType);

    const response = await fetch(`${this.baseUrl}/simulations/upload`, {
      method: 'POST',
      headers: this.headers(),
      body: formData
    });

    if (!response.ok) throw new Error('Upload failed');
    return await response.json();
  }

  async analyzeSimulation(simulationId: string) {
    const response = await fetch(
      `${this.baseUrl}/simulations/${simulationId}/analyze`,
      {
        method: 'POST',
        headers: {
          ...this.headers(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ analysis_type: 'comprehensive' })
      }
    );

    if (!response.ok) throw new Error('Analysis failed');
    return await response.json();
  }

  connectWebSocket(clientId: string) {
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${clientId}`);

    ws.onopen = () => {
      ws.send(JSON.stringify({
        action: 'subscribe',
        channels: ['upload_progress', 'processing_status']
      }));
    };

    return ws;
  }
}

// Usage
const client = new KooAIClient();
await client.login('user@example.com', 'password');

const file = document.getElementById('fileInput').files[0];
const sim = await client.uploadSimulation(file);
const analysis = await client.analyzeSimulation(sim.simulation_id);
```

---

## Best Practices

### 1. Token Management
- Store tokens securely (never in localStorage for web apps)
- Implement automatic token refresh
- Handle token expiration gracefully

### 2. File Uploads
- Use streaming upload for files > 100MB
- Implement retry logic for failed uploads
- Show upload progress to users
- Validate file types before upload

### 3. Error Handling
- Always check response status codes
- Implement exponential backoff for retries
- Log errors for debugging
- Show user-friendly error messages

### 4. Performance
- Reuse HTTP connections
- Implement request caching where appropriate
- Use WebSocket for real-time updates
- Compress large payloads

### 5. Security
- Always use HTTPS in production
- Never log sensitive data (tokens, passwords)
- Validate all user inputs
- Implement CSRF protection for web apps

---

## Support

For questions or issues:
- Documentation: https://docs.kooai.com
- API Status: https://status.kooai.com
- Support Email: support@kooai.com
- GitHub Issues: https://github.com/kooai/kooai/issues

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for API version history and changes.
