# KooAI API 사용 가이드

## 📖 목차
- [인증](#인증)
- [엔드포인트 목록](#엔드포인트-목록)
- [에러 코드](#에러-코드)
- [Rate Limiting](#rate-limiting)
- [예제 코드](#예제-코드)

---

## 🔐 인증

KooAI API는 JWT (JSON Web Token) 기반 인증을 사용합니다.

### 토큰 발급

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "your_password"
  }'
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 인증 헤더 사용

모든 보호된 엔드포인트는 Authorization 헤더가 필요합니다:

```bash
Authorization: Bearer <access_token>
```

---

## 📋 엔드포인트 목록

### Health & Status

#### GET /health
시스템 헬스 체크 (인증 불필요)

```bash
curl "http://localhost:8000/health"
```

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-07T12:00:00Z"
}
```

#### GET /health/ready
상세 준비 상태 확인 (DB, Redis, Storage)

```bash
curl "http://localhost:8000/health/ready"
```

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-07T12:00:00Z",
  "dependencies": {
    "database": {"status": "healthy", "response_time_ms": 5},
    "cache": {"status": "healthy", "response_time_ms": 2},
    "storage": {"status": "healthy", "response_time_ms": 10}
  }
}
```

---

### Simulations

#### POST /api/simulations
새로운 시뮬레이션 생성

```bash
curl -X POST "http://localhost:8000/api/simulations" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Simulation",
    "description": "Test simulation",
    "metadata": {
      "solver": "OpenFOAM",
      "version": "v2312"
    }
  }'
```

**응답:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My Simulation",
  "status": "created",
  "created_at": "2024-11-07T12:00:00Z"
}
```

#### GET /api/simulations
시뮬레이션 목록 조회

**쿼리 파라미터:**
- `skip`: 오프셋 (기본값: 0)
- `limit`: 페이지 크기 (기본값: 50, 최대: 100)
- `status`: 필터 (`pending`, `processing`, `completed`, `failed`)
- `sort_by`: 정렬 기준 (`created_at`, `updated_at`, `name`)
- `order`: 정렬 순서 (`asc`, `desc`)

```bash
curl "http://localhost:8000/api/simulations?limit=10&status=completed" \
  -H "Authorization: Bearer <token>"
```

**응답:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "My Simulation",
      "status": "completed",
      "created_at": "2024-11-07T12:00:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 10
}
```

#### GET /api/simulations/{id}
특정 시뮬레이션 상세 조회

```bash
curl "http://localhost:8000/api/simulations/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer <token>"
```

#### DELETE /api/simulations/{id}
시뮬레이션 삭제

```bash
curl -X DELETE "http://localhost:8000/api/simulations/123e4567-e89b-12d3-a456-426614174000" \
  -H "Authorization: Bearer <token>"
```

---

### Files

#### POST /api/simulations/{id}/files
파일 업로드

```bash
curl -X POST "http://localhost:8000/api/simulations/123e4567-e89b-12d3-a456-426614174000/files" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/simulation.vtk"
```

**응답:**
```json
{
  "file_id": "file_abc123",
  "filename": "simulation.vtk",
  "size": 1024000,
  "format": "vtk",
  "status": "uploaded"
}
```

#### GET /api/simulations/{id}/files
시뮬레이션의 파일 목록

```bash
curl "http://localhost:8000/api/simulations/123e4567-e89b-12d3-a456-426614174000/files" \
  -H "Authorization: Bearer <token>"
```

#### GET /api/files/{file_id}/download
파일 다운로드

```bash
curl "http://localhost:8000/api/files/file_abc123/download" \
  -H "Authorization: Bearer <token>" \
  -o downloaded_file.vtk
```

---

### Analysis

#### POST /api/simulations/{id}/analyze
AI 분석 요청

```bash
curl -X POST "http://localhost:8000/api/simulations/123e4567-e89b-12d3-a456-426614174000/analyze" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "llm",
    "prompt": "Summarize the simulation results",
    "options": {
      "model": "gpt-4",
      "temperature": 0.7
    }
  }'
```

**응답:**
```json
{
  "analysis_id": "analysis_xyz789",
  "status": "processing",
  "estimated_time_seconds": 30
}
```

#### GET /api/analysis/{analysis_id}
분석 결과 조회

```bash
curl "http://localhost:8000/api/analysis/analysis_xyz789" \
  -H "Authorization: Bearer <token>"
```

**응답:**
```json
{
  "analysis_id": "analysis_xyz789",
  "status": "completed",
  "result": {
    "summary": "The simulation shows...",
    "insights": ["Key finding 1", "Key finding 2"],
    "metrics": {
      "max_velocity": 15.2,
      "avg_pressure": 101325
    }
  }
}
```

---

## ❌ 에러 코드

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 204 | No Content | 성공 (응답 본문 없음) |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 리소스 충돌 |
| 422 | Unprocessable Entity | 검증 실패 |
| 429 | Too Many Requests | Rate limit 초과 |
| 500 | Internal Server Error | 서버 오류 |
| 503 | Service Unavailable | 서비스 이용 불가 |

### 에러 응답 형식

```json
{
  "detail": "Error message",
  "error_code": "SIMULATION_NOT_FOUND",
  "timestamp": "2024-11-07T12:00:00Z"
}
```

### 공통 에러 코드

| 코드 | HTTP | 설명 |
|------|------|------|
| `INVALID_TOKEN` | 401 | JWT 토큰이 유효하지 않음 |
| `TOKEN_EXPIRED` | 401 | JWT 토큰 만료 |
| `INSUFFICIENT_PERMISSIONS` | 403 | 권한 부족 |
| `SIMULATION_NOT_FOUND` | 404 | 시뮬레이션을 찾을 수 없음 |
| `FILE_NOT_FOUND` | 404 | 파일을 찾을 수 없음 |
| `FILE_TOO_LARGE` | 413 | 파일 크기 초과 (최대 5GB) |
| `UNSUPPORTED_FILE_FORMAT` | 422 | 지원하지 않는 파일 형식 |
| `VALIDATION_ERROR` | 422 | 입력 검증 실패 |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit 초과 |

---

## 🚦 Rate Limiting

### 기본 제한

- **익명 사용자:** 10 요청/분
- **인증 사용자:** 100 요청/분
- **프리미엄 사용자:** 1000 요청/분

### Rate Limit 헤더

응답에 다음 헤더가 포함됩니다:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699358400
```

### Rate Limit 초과 시

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 45
}
```

---

## 💻 예제 코드

### Python

```python
import requests
import json

class KooAIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = None
        self.login(username, password)
    
    def login(self, username, password):
        """로그인하여 토큰 발급"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
    
    def headers(self):
        """인증 헤더 반환"""
        return {"Authorization": f"Bearer {self.token}"}
    
    def create_simulation(self, name, description=None, metadata=None):
        """새 시뮬레이션 생성"""
        data = {"name": name}
        if description:
            data["description"] = description
        if metadata:
            data["metadata"] = metadata
        
        response = requests.post(
            f"{self.base_url}/api/simulations",
            headers=self.headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def upload_file(self, simulation_id, file_path):
        """파일 업로드"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/simulations/{simulation_id}/files",
                headers=self.headers(),
                files=files
            )
        response.raise_for_status()
        return response.json()
    
    def analyze(self, simulation_id, prompt, model="gpt-4"):
        """AI 분석 요청"""
        data = {
            "analysis_type": "llm",
            "prompt": prompt,
            "options": {"model": model}
        }
        response = requests.post(
            f"{self.base_url}/api/simulations/{simulation_id}/analyze",
            headers=self.headers(),
            json=data
        )
        response.raise_for_status()
        return response.json()

# 사용 예제
if __name__ == "__main__":
    client = KooAIClient(
        "http://localhost:8000",
        "user@example.com",
        "password123"
    )
    
    # 시뮬레이션 생성
    sim = client.create_simulation(
        name="My Simulation",
        description="Test simulation",
        metadata={"solver": "OpenFOAM"}
    )
    print(f"Created simulation: {sim['id']}")
    
    # 파일 업로드
    file_info = client.upload_file(sim['id'], "data/simulation.vtk")
    print(f"Uploaded file: {file_info['file_id']}")
    
    # 분석 요청
    analysis = client.analyze(
        sim['id'],
        "Summarize the key findings from this simulation"
    )
    print(f"Analysis started: {analysis['analysis_id']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

class KooAIClient {
  constructor(baseURL, username, password) {
    this.baseURL = baseURL;
    this.token = null;
    this.login(username, password);
  }

  async login(username, password) {
    const response = await axios.post(`${this.baseURL}/api/auth/login`, {
      username,
      password
    });
    this.token = response.data.access_token;
  }

  headers() {
    return {
      'Authorization': `Bearer ${this.token}`
    };
  }

  async createSimulation(name, description = null, metadata = null) {
    const data = { name };
    if (description) data.description = description;
    if (metadata) data.metadata = metadata;

    const response = await axios.post(
      `${this.baseURL}/api/simulations`,
      data,
      { headers: this.headers() }
    );
    return response.data;
  }

  async uploadFile(simulationId, filePath) {
    const FormData = require('form-data');
    const fs = require('fs');
    
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));

    const response = await axios.post(
      `${this.baseURL}/api/simulations/${simulationId}/files`,
      form,
      {
        headers: {
          ...this.headers(),
          ...form.getHeaders()
        }
      }
    );
    return response.data;
  }

  async analyze(simulationId, prompt, model = 'gpt-4') {
    const response = await axios.post(
      `${this.baseURL}/api/simulations/${simulationId}/analyze`,
      {
        analysis_type: 'llm',
        prompt,
        options: { model }
      },
      { headers: this.headers() }
    );
    return response.data;
  }
}

// 사용 예제
(async () => {
  const client = new KooAIClient(
    'http://localhost:8000',
    'user@example.com',
    'password123'
  );

  await client.login('user@example.com', 'password123');

  const sim = await client.createSimulation('My Simulation');
  console.log(`Created simulation: ${sim.id}`);

  const fileInfo = await client.uploadFile(sim.id, 'data/simulation.vtk');
  console.log(`Uploaded file: ${fileInfo.file_id}`);

  const analysis = await client.analyze(
    sim.id,
    'Summarize the key findings'
  );
  console.log(`Analysis started: ${analysis.analysis_id}`);
})();
```

### cURL 스크립트

```bash
#!/bin/bash
# complete_workflow.sh

BASE_URL="http://localhost:8000"
USERNAME="user@example.com"
PASSWORD="password123"

# 1. 로그인
echo "Logging in..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. 시뮬레이션 생성
echo "Creating simulation..."
SIM_ID=$(curl -s -X POST "$BASE_URL/api/simulations" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Simulation","description":"Test"}' \
  | jq -r '.id')

echo "Simulation ID: $SIM_ID"

# 3. 파일 업로드
echo "Uploading file..."
FILE_ID=$(curl -s -X POST "$BASE_URL/api/simulations/$SIM_ID/files" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data/simulation.vtk" \
  | jq -r '.file_id')

echo "File ID: $FILE_ID"

# 4. 분석 요청
echo "Requesting analysis..."
ANALYSIS_ID=$(curl -s -X POST "$BASE_URL/api/simulations/$SIM_ID/analyze" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"analysis_type":"llm","prompt":"Summarize results"}' \
  | jq -r '.analysis_id')

echo "Analysis ID: $ANALYSIS_ID"

# 5. 분석 결과 대기
echo "Waiting for analysis..."
sleep 30

# 6. 결과 조회
echo "Fetching results..."
curl -s "$BASE_URL/api/analysis/$ANALYSIS_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

---

## 📚 추가 리소스

- **Interactive API Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

## 🆘 지원

문제가 있으신가요?

- [GitHub Issues](https://github.com/your-org/kooai/issues)
- [Documentation](https://kooai.readthedocs.io)
- Email: support@kooai.example.com
