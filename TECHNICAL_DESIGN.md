# 기술 설계 문서

## 1. 시스템 아키텍처

### 1.1 전체 아키텍처 (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   REST API   │  │   GraphQL    │  │     CLI      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────────────────────────────────────┐       │
│  │              Use Cases / Services                 │       │
│  │  - UploadSimulationUseCase                       │       │
│  │  - AnalyzeSimulationUseCase                      │       │
│  │  - TrainModelUseCase                             │       │
│  │  - CompareSimulationsUseCase                     │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Entities  │  │   Value    │  │  Domain    │            │
│  │            │  │  Objects   │  │  Services  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                               │
│  ┌─────────────────────────────────────────────────┐        │
│  │         Repository Interfaces                    │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │  Redis   │  │ Vector DB│  │ File Sys │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │  Celery  │  │   LLM    │  │AI Models │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 데이터 흐름

```
[Client]
   ↓ HTTP/REST
[API Gateway / Load Balancer]
   ↓
[FastAPI Application]
   ↓
[Use Case Layer]
   ↓
[Domain Services] ← [Repositories]
   ↓                      ↓
[Entities]           [PostgreSQL / Vector DB / File System]
   ↓
[AI/ML Pipeline]
   ↓
[Result Aggregation]
   ↓
[Response]
```

---

## 2. 핵심 컴포넌트 상세 설계

### 2.1 데이터 타입 시스템

#### 인터페이스 설계

```python
from typing import Protocol, Self, Any, Dict
from abc import abstractmethod
import numpy as np

class IDataType(Protocol):
    """모든 데이터 타입의 기본 인터페이스"""

    @abstractmethod
    def validate(self) -> bool:
        """데이터 유효성 검증"""
        pass

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        """직렬화"""
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Dict[str, Any]) -> Self:
        """역직렬화"""
        pass

    @abstractmethod
    def compress(self, method: str = "default") -> bytes:
        """압축"""
        pass

    @classmethod
    @abstractmethod
    def decompress(cls, data: bytes, method: str = "default") -> Self:
        """압축 해제"""
        pass

    @abstractmethod
    def transform(self, transformation: "ITransformation") -> Self:
        """데이터 변환"""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """메타데이터 추출"""
        pass
```

#### 구체적 구현: ContourData

```python
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from shapely.geometry import Polygon, LineString

@dataclass
class ContourData:
    """컨투어 데이터 클래스"""
    points: np.ndarray  # Shape: (N, 2) or (N, 3)
    is_closed: bool = True
    attributes: Dict[str, Any] = None

    def validate(self) -> bool:
        """검증 로직"""
        if self.points.shape[0] < 3:
            return False
        if self.points.ndim != 2:
            return False
        if self.points.shape[1] not in [2, 3]:
            return False
        return True

    def serialize(self) -> Dict[str, Any]:
        return {
            "type": "contour",
            "points": self.points.tolist(),
            "is_closed": self.is_closed,
            "attributes": self.attributes or {}
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "ContourData":
        return cls(
            points=np.array(data["points"]),
            is_closed=data.get("is_closed", True),
            attributes=data.get("attributes")
        )

    def compress(self, method: str = "default") -> bytes:
        """컨투어 압축 (Douglas-Peucker 또는 VAE)"""
        if method == "douglas-peucker":
            return self._compress_douglas_peucker()
        elif method == "vae":
            return self._compress_vae()
        else:
            return self._compress_default()

    def _compress_douglas_peucker(self, epsilon: float = 1.0) -> bytes:
        """Douglas-Peucker 알고리즘"""
        from shapely.geometry import LineString
        line = LineString(self.points)
        simplified = line.simplify(epsilon, preserve_topology=True)
        return np.array(simplified.coords).tobytes()

    def _compress_vae(self) -> bytes:
        """VAE 기반 압축 (Phase 6에서 구현)"""
        # VAE 모델을 통한 압축
        pass

    def get_area(self) -> float:
        """면적 계산"""
        if not self.is_closed:
            return 0.0
        polygon = Polygon(self.points)
        return polygon.area

    def get_perimeter(self) -> float:
        """둘레 계산"""
        if self.is_closed:
            geom = Polygon(self.points)
        else:
            geom = LineString(self.points)
        return geom.length
```

#### MeshData (3D)

```python
@dataclass
class MeshData:
    """3D 메시 데이터"""
    vertices: np.ndarray  # Shape: (N, 3)
    faces: np.ndarray     # Shape: (M, 3) or (M, 4)
    normals: np.ndarray = None
    attributes: Dict[str, np.ndarray] = None  # 노드별 속성

    def validate(self) -> bool:
        if self.vertices.shape[1] != 3:
            return False
        if self.faces.ndim != 2:
            return False
        if np.any(self.faces >= len(self.vertices)):
            return False
        return True

    def compute_normals(self) -> np.ndarray:
        """법선 벡터 계산"""
        if self.faces.shape[1] == 3:
            # 삼각형 메시
            v0 = self.vertices[self.faces[:, 0]]
            v1 = self.vertices[self.faces[:, 1]]
            v2 = self.vertices[self.faces[:, 2]]

            normals = np.cross(v1 - v0, v2 - v0)
            normals /= np.linalg.norm(normals, axis=1, keepdims=True)
            return normals

    def simplify(self, target_reduction: float = 0.5) -> "MeshData":
        """메시 단순화"""
        import pyvista as pv
        mesh = pv.PolyData(self.vertices,
                          np.hstack([np.full((len(self.faces), 1), 3), self.faces]))
        simplified = mesh.decimate(target_reduction)

        return MeshData(
            vertices=simplified.points,
            faces=simplified.faces.reshape(-1, 4)[:, 1:],
            attributes=self.attributes
        )

    def compute_volume(self) -> float:
        """볼륨 계산 (닫힌 메시)"""
        # 부호있는 볼륨 계산
        v0 = self.vertices[self.faces[:, 0]]
        v1 = self.vertices[self.faces[:, 1]]
        v2 = self.vertices[self.faces[:, 2]]

        return np.sum(np.cross(v0, v1) @ v2.T) / 6.0
```

### 2.2 VAE 모델 아키텍처

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class ContourVAE(nn.Module):
    """컨투어 데이터 압축을 위한 VAE"""

    def __init__(self,
                 input_dim: int = 100,  # 컨투어 포인트 수
                 latent_dim: int = 16,
                 hidden_dims: List[int] = [128, 64, 32]):
        super().__init__()

        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # Encoder
        encoder_layers = []
        prev_dim = input_dim * 2  # x, y 좌표
        for h_dim in hidden_dims:
            encoder_layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_dim = h_dim

        self.encoder = nn.Sequential(*encoder_layers)
        self.fc_mu = nn.Linear(hidden_dims[-1], latent_dim)
        self.fc_logvar = nn.Linear(hidden_dims[-1], latent_dim)

        # Decoder
        decoder_layers = []
        prev_dim = latent_dim
        for h_dim in reversed(hidden_dims):
            decoder_layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_dim = h_dim

        decoder_layers.append(nn.Linear(prev_dim, input_dim * 2))
        self.decoder = nn.Sequential(*decoder_layers)

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """인코딩: 입력 -> 잠재 공간"""
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """재매개변수화 트릭"""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """디코딩: 잠재 공간 -> 재구성"""
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        recon = self.decode(z)
        return recon, mu, logvar

    def loss_function(self,
                     recon: torch.Tensor,
                     x: torch.Tensor,
                     mu: torch.Tensor,
                     logvar: torch.Tensor,
                     beta: float = 1.0) -> Dict[str, torch.Tensor]:
        """손실 함수: Reconstruction + KL Divergence"""

        # Reconstruction loss (MSE)
        recon_loss = F.mse_loss(recon, x, reduction='sum')

        # KL divergence
        kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())

        # Total loss
        total_loss = recon_loss + beta * kl_loss

        return {
            'loss': total_loss,
            'recon_loss': recon_loss,
            'kl_loss': kl_loss
        }


class ContourVAETrainer:
    """VAE 학습 클래스"""

    def __init__(self,
                 model: ContourVAE,
                 device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
                 learning_rate: float = 1e-3,
                 beta_schedule: str = 'constant'):

        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.beta_schedule = beta_schedule

    def train_epoch(self,
                   dataloader: torch.utils.data.DataLoader,
                   epoch: int) -> Dict[str, float]:
        """1 에폭 학습"""
        self.model.train()
        total_loss = 0
        total_recon = 0
        total_kl = 0

        for batch_idx, data in enumerate(dataloader):
            data = data.to(self.device)

            self.optimizer.zero_grad()
            recon, mu, logvar = self.model(data)

            # Beta annealing
            beta = self._get_beta(epoch)
            losses = self.model.loss_function(recon, data, mu, logvar, beta)

            losses['loss'].backward()
            self.optimizer.step()

            total_loss += losses['loss'].item()
            total_recon += losses['recon_loss'].item()
            total_kl += losses['kl_loss'].item()

        n_batches = len(dataloader)
        return {
            'loss': total_loss / n_batches,
            'recon_loss': total_recon / n_batches,
            'kl_loss': total_kl / n_batches
        }

    def _get_beta(self, epoch: int) -> float:
        """Beta annealing schedule"""
        if self.beta_schedule == 'constant':
            return 1.0
        elif self.beta_schedule == 'linear':
            return min(1.0, epoch / 100)
        elif self.beta_schedule == 'cyclical':
            return 0.5 * (1 + np.cos(np.pi * (epoch % 10) / 10))
        else:
            return 1.0
```

### 2.3 LLM 통합 시스템

```python
from typing import Protocol, List, Dict, Any
from abc import abstractmethod

class ILLMClient(Protocol):
    """LLM 클라이언트 인터페이스"""

    @abstractmethod
    async def generate(self,
                      prompt: str,
                      context: Dict[str, Any],
                      max_tokens: int = 1000,
                      temperature: float = 0.7) -> str:
        """텍스트 생성"""
        pass

    @abstractmethod
    async def embed(self, text: str) -> np.ndarray:
        """텍스트 임베딩"""
        pass

    @abstractmethod
    async def chat(self,
                  messages: List[Dict[str, str]],
                  **kwargs) -> str:
        """채팅 인터페이스"""
        pass


class OpenAIClient:
    """OpenAI API 클라이언트"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        import openai
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def generate(self,
                      prompt: str,
                      context: Dict[str, Any],
                      max_tokens: int = 1000,
                      temperature: float = 0.7) -> str:

        # 컨텍스트를 프롬프트에 주입
        full_prompt = self._inject_context(prompt, context)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

    async def embed(self, text: str) -> np.ndarray:
        response = await self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return np.array(response.data[0].embedding)

    def _inject_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """프롬프트에 컨텍스트 주입"""
        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
        return f"{context_str}\n\n{prompt}"


class LLMPromptTemplate:
    """프롬프트 템플릿 관리"""

    SIMULATION_ANALYSIS = """
다음은 시뮬레이션 결과 데이터입니다:

시뮬레이션 ID: {simulation_id}
시뮬레이션 유형: {simulation_type}
주요 파라미터:
{parameters}

결과 요약:
{results_summary}

위 데이터를 분석하여 다음 질문에 답변해주세요:
{question}

분석 시 다음 사항을 고려해주세요:
1. 물리적 타당성
2. 통계적 유의성
3. 이전 시뮬레이션과의 차이점
4. 잠재적 문제점 또는 이상치
"""

    COMPARISON_ANALYSIS = """
다음은 두 시뮬레이션 결과의 비교입니다:

시뮬레이션 A:
{simulation_a}

시뮬레이션 B:
{simulation_b}

주요 차이점:
{differences}

두 시뮬레이션을 비교 분석하고 다음을 설명해주세요:
1. 주요 차이점의 원인
2. 어느 결과가 더 신뢰할 수 있는지
3. 개선을 위한 제안사항
"""

    @classmethod
    def render(cls, template_name: str, **kwargs) -> str:
        """템플릿 렌더링"""
        template = getattr(cls, template_name)
        return template.format(**kwargs)


class LLMAnalysisChain:
    """LLM 기반 분석 체인"""

    def __init__(self, llm_client: ILLMClient):
        self.llm = llm_client

    async def analyze_simulation(self,
                                simulation_data: Dict[str, Any],
                                question: str) -> str:
        """시뮬레이션 분석"""

        # 1. 데이터 요약
        summary = await self._summarize_data(simulation_data)

        # 2. 프롬프트 생성
        prompt = LLMPromptTemplate.render(
            'SIMULATION_ANALYSIS',
            simulation_id=simulation_data['id'],
            simulation_type=simulation_data['type'],
            parameters=self._format_parameters(simulation_data['parameters']),
            results_summary=summary,
            question=question
        )

        # 3. LLM 호출
        analysis = await self.llm.generate(prompt, context={})

        return analysis

    async def compare_simulations(self,
                                 sim_a: Dict[str, Any],
                                 sim_b: Dict[str, Any]) -> str:
        """시뮬레이션 비교 분석"""

        # 1. 차이점 계산
        differences = self._compute_differences(sim_a, sim_b)

        # 2. 프롬프트 생성
        prompt = LLMPromptTemplate.render(
            'COMPARISON_ANALYSIS',
            simulation_a=self._format_simulation(sim_a),
            simulation_b=self._format_simulation(sim_b),
            differences=differences
        )

        # 3. LLM 호출
        comparison = await self.llm.generate(prompt, context={})

        return comparison

    async def _summarize_data(self, data: Dict[str, Any]) -> str:
        """데이터 요약"""
        # 통계적 요약
        stats = self._compute_statistics(data)
        return f"평균: {stats['mean']}, 표준편차: {stats['std']}, 최소/최대: {stats['min']}/{stats['max']}"

    def _compute_statistics(self, data: Dict[str, Any]) -> Dict[str, float]:
        """통계 계산"""
        # 실제 구현
        pass

    def _compute_differences(self, sim_a: Dict, sim_b: Dict) -> str:
        """차이점 계산"""
        # 실제 구현
        pass
```

### 2.4 Repository 패턴 구현

```python
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

class ISimulationRepository(ABC):
    """시뮬레이션 리포지토리 인터페이스"""

    @abstractmethod
    async def save(self, simulation: "SimulationResult") -> str:
        pass

    @abstractmethod
    async def find_by_id(self, simulation_id: str) -> Optional["SimulationResult"]:
        pass

    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List["SimulationResult"]:
        pass

    @abstractmethod
    async def update(self, simulation: "SimulationResult") -> None:
        pass

    @abstractmethod
    async def delete(self, simulation_id: str) -> None:
        pass


class PostgreSQLSimulationRepository:
    """PostgreSQL 기반 구현"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, simulation: "SimulationResult") -> str:
        """시뮬레이션 저장"""
        db_simulation = SimulationModel(
            id=simulation.id,
            name=simulation.name,
            type=simulation.type,
            parameters=simulation.parameters,
            metadata=simulation.metadata,
            created_at=simulation.created_at
        )

        self._session.add(db_simulation)
        await self._session.commit()
        await self._session.refresh(db_simulation)

        return db_simulation.id

    async def find_by_id(self, simulation_id: str) -> Optional["SimulationResult"]:
        """ID로 조회"""
        stmt = select(SimulationModel).where(SimulationModel.id == simulation_id)
        result = await self._session.execute(stmt)
        db_simulation = result.scalar_one_or_none()

        if db_simulation is None:
            return None

        return self._to_domain(db_simulation)

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List["SimulationResult"]:
        """조건으로 조회"""
        stmt = select(SimulationModel)

        # 동적 필터 구성
        filters = []
        if 'type' in criteria:
            filters.append(SimulationModel.type == criteria['type'])
        if 'date_from' in criteria:
            filters.append(SimulationModel.created_at >= criteria['date_from'])
        if 'date_to' in criteria:
            filters.append(SimulationModel.created_at <= criteria['date_to'])

        if filters:
            stmt = stmt.where(and_(*filters))

        result = await self._session.execute(stmt)
        db_simulations = result.scalars().all()

        return [self._to_domain(db_sim) for db_sim in db_simulations]

    def _to_domain(self, db_model: "SimulationModel") -> "SimulationResult":
        """DB 모델 -> 도메인 엔티티 변환"""
        return SimulationResult(
            id=db_model.id,
            name=db_model.name,
            type=db_model.type,
            parameters=db_model.parameters,
            metadata=db_model.metadata,
            created_at=db_model.created_at
        )
```

---

## 3. 데이터베이스 스키마 설계

### 3.1 PostgreSQL 스키마

```sql
-- 시뮬레이션 결과
CREATE TABLE simulations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    parameters JSONB,
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_simulations_type ON simulations(type);
CREATE INDEX idx_simulations_status ON simulations(status);
CREATE INDEX idx_simulations_created_at ON simulations(created_at DESC);
CREATE INDEX idx_simulations_parameters ON simulations USING GIN(parameters);

-- 데이터셋
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID REFERENCES simulations(id) ON DELETE CASCADE,
    data_type VARCHAR(100) NOT NULL,  -- 'mesh', 'contour', 'curve', etc.
    data_format VARCHAR(50),  -- 'json', 'binary', 'vtk', etc.
    storage_path TEXT,  -- 파일 시스템 경로 또는 S3 키
    size_bytes BIGINT,
    checksum VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_datasets_simulation_id ON datasets(simulation_id);
CREATE INDEX idx_datasets_data_type ON datasets(data_type);

-- AI 모델
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100),  -- 'vae', 'transformer', 'cnn', etc.
    architecture JSONB,
    storage_path TEXT,
    performance_metrics JSONB,
    training_config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, version)
);

-- 분석 작업
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID REFERENCES simulations(id),
    analysis_type VARCHAR(100) NOT NULL,
    model_id UUID REFERENCES ai_models(id),
    input_parameters JSONB,
    results JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_analyses_simulation_id ON analyses(simulation_id);
CREATE INDEX idx_analyses_status ON analyses(status);

-- 벡터 임베딩 (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE simulation_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    simulation_id UUID REFERENCES simulations(id) ON DELETE CASCADE,
    embedding vector(1536),  -- OpenAI ada-002 차원
    embedding_model VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_embeddings_vector ON simulation_embeddings
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 3.2 Redis 캐싱 전략

```python
from typing import Optional, Any
import redis.asyncio as redis
import json
import pickle
from functools import wraps

class CacheManager:
    """Redis 캐시 매니저"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 가져오기"""
        value = await self.redis.get(key)
        if value is None:
            return None
        return pickle.loads(value)

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 저장"""
        serialized = pickle.dumps(value)
        await self.redis.setex(key, ttl, serialized)

    async def delete(self, key: str):
        """캐시 삭제"""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str):
        """패턴 매칭으로 삭제"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)


def cache(ttl: int = 3600, key_prefix: str = ""):
    """캐시 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # 캐시에서 조회
            cache_manager = kwargs.get('cache_manager')
            if cache_manager:
                cached = await cache_manager.get(cache_key)
                if cached is not None:
                    return cached

            # 함수 실행
            result = await func(*args, **kwargs)

            # 캐시에 저장
            if cache_manager:
                await cache_manager.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


# 사용 예시
@cache(ttl=1800, key_prefix="simulation")
async def get_simulation_by_id(simulation_id: str, cache_manager: CacheManager):
    # DB에서 조회
    pass
```

---

## 4. API 설계

### 4.1 REST API 엔드포인트

```python
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Simulation Post-Processing API", version="1.0.0")

# DTO 모델
class SimulationCreateRequest(BaseModel):
    name: str
    type: str
    parameters: dict
    metadata: Optional[dict] = None

class SimulationResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    created_at: datetime

class AnalysisRequest(BaseModel):
    simulation_ids: List[str]
    analysis_type: str
    parameters: Optional[dict] = None

# 엔드포인트
@app.post("/api/v1/simulations", response_model=SimulationResponse)
async def create_simulation(
    request: SimulationCreateRequest,
    use_case: "UploadSimulationUseCase" = Depends()
):
    """시뮬레이션 생성"""
    result = await use_case.execute(request)
    return result

@app.post("/api/v1/simulations/upload")
async def upload_simulation_file(
    file: UploadFile = File(...),
    simulation_id: Optional[str] = None,
    use_case: "UploadSimulationUseCase" = Depends()
):
    """시뮬레이션 파일 업로드"""
    content = await file.read()
    result = await use_case.process_file(content, file.filename, simulation_id)
    return {"simulation_id": result}

@app.get("/api/v1/simulations/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: str,
    repository: "ISimulationRepository" = Depends()
):
    """시뮬레이션 조회"""
    simulation = await repository.find_by_id(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return simulation

@app.get("/api/v1/simulations")
async def list_simulations(
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    repository: "ISimulationRepository" = Depends()
):
    """시뮬레이션 목록 조회"""
    criteria = {}
    if type:
        criteria['type'] = type
    if status:
        criteria['status'] = status

    simulations = await repository.find_by_criteria(criteria)
    return simulations[offset:offset+limit]

@app.post("/api/v1/analyses")
async def create_analysis(
    request: AnalysisRequest,
    use_case: "AnalyzeSimulationUseCase" = Depends()
):
    """분석 작업 생성"""
    result = await use_case.execute(request)
    return {"analysis_id": result.id, "status": result.status}

@app.get("/api/v1/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    repository: "IAnalysisRepository" = Depends()
):
    """분석 결과 조회"""
    analysis = await repository.find_by_id(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@app.post("/api/v1/models/train")
async def train_model(
    model_type: str,
    training_data_ids: List[str],
    config: dict,
    use_case: "TrainModelUseCase" = Depends()
):
    """모델 학습 시작"""
    result = await use_case.execute(model_type, training_data_ids, config)
    return {"job_id": result.job_id, "status": "started"}

@app.get("/api/v1/models")
async def list_models(
    model_type: Optional[str] = None,
    registry: "AIModelRegistry" = Depends()
):
    """모델 목록 조회"""
    models = await registry.list_models(model_type)
    return models

@app.post("/api/v1/search/semantic")
async def semantic_search(
    query: str,
    top_k: int = 10,
    search_service: "SemanticSearchService" = Depends()
):
    """시맨틱 검색"""
    results = await search_service.search(query, top_k)
    return results
```

---

## 5. 플러그인 시스템

```python
from typing import Protocol, Dict, Any, List
import importlib
import inspect
from pathlib import Path

class IPlugin(Protocol):
    """플러그인 인터페이스"""

    name: str
    version: str
    description: str

    def initialize(self, config: Dict[str, Any]) -> None:
        """플러그인 초기화"""
        pass

    def get_capabilities(self) -> List[str]:
        """제공하는 기능 목록"""
        pass

    def execute(self, operation: str, data: Any, **kwargs) -> Any:
        """작업 실행"""
        pass

    def cleanup(self) -> None:
        """정리"""
        pass


class PluginManager:
    """플러그인 매니저"""

    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, IPlugin] = {}

    def discover_plugins(self) -> List[str]:
        """플러그인 자동 발견"""
        plugin_files = self.plugin_dir.glob("*_plugin.py")
        plugin_names = []

        for file in plugin_files:
            module_name = file.stem
            try:
                module = importlib.import_module(f"plugins.{module_name}")

                # Plugin 클래스 찾기
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and hasattr(obj, 'name'):
                        plugin = obj()
                        self._plugins[plugin.name] = plugin
                        plugin_names.append(plugin.name)
            except Exception as e:
                print(f"Failed to load plugin {module_name}: {e}")

        return plugin_names

    def get_plugin(self, name: str) -> Optional[IPlugin]:
        """플러그인 가져오기"""
        return self._plugins.get(name)

    def execute_plugin(self, plugin_name: str, operation: str, data: Any, **kwargs) -> Any:
        """플러그인 실행"""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not found")

        return plugin.execute(operation, data, **kwargs)


# 플러그인 예시: 커스텀 분석
class CustomAnalysisPlugin:
    """커스텀 분석 플러그인"""

    name = "custom_analysis"
    version = "1.0.0"
    description = "사용자 정의 분석 플러그인"

    def initialize(self, config: Dict[str, Any]) -> None:
        self.config = config
        # 초기화 로직

    def get_capabilities(self) -> List[str]:
        return ["statistical_analysis", "trend_analysis", "comparison"]

    def execute(self, operation: str, data: Any, **kwargs) -> Any:
        if operation == "statistical_analysis":
            return self._statistical_analysis(data, **kwargs)
        elif operation == "trend_analysis":
            return self._trend_analysis(data, **kwargs)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def _statistical_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        # 통계 분석 로직
        import numpy as np
        return {
            "mean": np.mean(data),
            "std": np.std(data),
            "min": np.min(data),
            "max": np.max(data)
        }

    def _trend_analysis(self, data: Any, **kwargs) -> Dict[str, Any]:
        # 트렌드 분석 로직
        pass

    def cleanup(self) -> None:
        # 정리 로직
        pass
```

---

## 6. 성능 최적화 전략

### 6.1 데이터베이스 최적화

```python
# 1. 연결 풀링
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,  # 연결 풀 크기
    max_overflow=10,  # 최대 오버플로우
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_recycle=3600,  # 1시간마다 연결 재활용
    echo=False
)

# 2. 쿼리 최적화
async def get_simulations_with_datasets(simulation_ids: List[str]):
    """N+1 쿼리 문제 해결: Eager Loading"""
    stmt = (
        select(SimulationModel)
        .options(selectinload(SimulationModel.datasets))  # Eager loading
        .where(SimulationModel.id.in_(simulation_ids))
    )
    result = await session.execute(stmt)
    return result.scalars().all()

# 3. 배치 삽입
async def bulk_insert_simulations(simulations: List[Dict]):
    """대량 삽입 최적화"""
    async with AsyncSession(engine) as session:
        session.add_all([
            SimulationModel(**sim) for sim in simulations
        ])
        await session.commit()
```

### 6.2 비동기 처리

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncProcessor:
    """비동기 처리 매니저"""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_in_background(self, func, *args, **kwargs):
        """CPU 집약적 작업을 백그라운드에서 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)

    async def process_multiple(self, tasks: List):
        """여러 작업 병렬 처리"""
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

# 사용 예시
async def analyze_simulations(simulation_ids: List[str]):
    processor = AsyncProcessor()

    # 모든 시뮬레이션 병렬 분석
    tasks = [
        processor.process_in_background(heavy_analysis, sim_id)
        for sim_id in simulation_ids
    ]

    results = await processor.process_multiple(tasks)
    return results
```

---

## 7. 보안 설계

```python
from fastapi import Security, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

# JWT 설정
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class SecurityManager:
    """보안 매니저"""

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """액세스 토큰 생성"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
        """토큰 검증"""
        token = credentials.credentials
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    @staticmethod
    def check_permission(user_payload: dict, required_role: str):
        """권한 검사"""
        user_roles = user_payload.get("roles", [])
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

# RBAC 데코레이터
def require_role(role: str):
    async def role_checker(credentials: HTTPAuthorizationCredentials = Security(security)):
        payload = SecurityManager.verify_token(credentials)
        SecurityManager.check_permission(payload, role)
        return payload
    return role_checker

# 사용 예시
@app.post("/api/v1/simulations")
async def create_simulation(
    request: SimulationCreateRequest,
    user: dict = Depends(require_role("analyst"))
):
    # 분석가 역할이 있는 사용자만 시뮬레이션 생성 가능
    pass
```

---

이 기술 설계 문서는 프로젝트 계획서와 함께 사용되며, 각 Phase에서 구체적인 구현 시 참고할 수 있습니다.
