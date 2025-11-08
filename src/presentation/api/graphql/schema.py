"""
GraphQL Schema Definitions

Define GraphQL types, queries, mutations, and subscriptions.
"""

from typing import List, Optional, AsyncIterator
from datetime import datetime
import strawberry
from strawberry.types import Info
from strawberry.file_uploads import Upload


# ==========================================
# Types
# ==========================================

@strawberry.type
class User:
    """User type for GraphQL."""

    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    @strawberry.field
    async def simulations(self, info: Info) -> List["Simulation"]:
        """Get user's simulations."""
        from src.presentation.api.graphql.resolvers import get_user_simulations
        return await get_user_simulations(self.id, info)


@strawberry.type
class Simulation:
    """Simulation type for GraphQL."""

    id: str
    filename: str
    file_size: int
    simulation_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    @strawberry.field
    async def user(self, info: Info) -> Optional[User]:
        """Get simulation owner."""
        from src.presentation.api.graphql.resolvers import get_simulation_user
        return await get_simulation_user(self.id, info)

    @strawberry.field
    async def analyses(self, info: Info) -> List["Analysis"]:
        """Get simulation analyses."""
        from src.presentation.api.graphql.resolvers import get_simulation_analyses
        return await get_simulation_analyses(self.id, info)

    @strawberry.field
    async def visualizations(self, info: Info) -> List["Visualization"]:
        """Get simulation visualizations."""
        from src.presentation.api.graphql.resolvers import get_simulation_visualizations
        return await get_simulation_visualizations(self.id, info)


@strawberry.type
class Analysis:
    """Analysis type for GraphQL."""

    id: str
    simulation_id: str
    analysis_type: str
    result: strawberry.scalars.JSON
    status: str
    confidence: Optional[float] = None
    created_at: datetime

    @strawberry.field
    async def simulation(self, info: Info) -> Optional[Simulation]:
        """Get associated simulation."""
        from src.presentation.api.graphql.resolvers import get_analysis_simulation
        return await get_analysis_simulation(self.simulation_id, info)


@strawberry.type
class Visualization:
    """Visualization type for GraphQL."""

    id: str
    simulation_id: str
    viz_type: str
    file_path: str
    parameters: strawberry.scalars.JSON
    created_at: datetime


@strawberry.type
class ConversationContext:
    """LLM conversation context."""

    id: str
    user_id: str
    messages: strawberry.scalars.JSON
    max_turns: int
    created_at: datetime
    updated_at: datetime


@strawberry.type
class TokenUsage:
    """Token usage statistics."""

    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    model: str


# ==========================================
# Input Types
# ==========================================

@strawberry.input
class UserInput:
    """User creation input."""

    email: str
    username: str
    password: str
    role: str = "user"


@strawberry.input
class LoginInput:
    """Login input."""

    email: str
    password: str


@strawberry.input
class SimulationUploadInput:
    """Simulation upload input."""

    simulation_type: str
    auto_analyze: bool = False


@strawberry.input
class AnalysisInput:
    """Analysis request input."""

    simulation_id: str
    analysis_type: str
    parameters: Optional[strawberry.scalars.JSON] = None


@strawberry.input
class VisualizationInput:
    """Visualization request input."""

    simulation_id: str
    viz_type: str
    parameters: strawberry.scalars.JSON


@strawberry.input
class LLMAnalysisInput:
    """LLM analysis input."""

    prompt: str
    context_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


@strawberry.input
class PaginationInput:
    """Pagination input."""

    skip: int = 0
    limit: int = 10


@strawberry.input
class SimulationFilterInput:
    """Simulation filter input."""

    status: Optional[str] = None
    simulation_type: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


# ==========================================
# Response Types
# ==========================================

@strawberry.type
class AuthResponse:
    """Authentication response."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: User


@strawberry.type
class SimulationResponse:
    """Simulation response."""

    simulation: Simulation
    message: str


@strawberry.type
class AnalysisResponse:
    """Analysis response."""

    analysis: Analysis
    message: str


@strawberry.type
class VisualizationResponse:
    """Visualization response."""

    visualization: Visualization
    url: str
    message: str


@strawberry.type
class PaginatedSimulations:
    """Paginated simulations response."""

    simulations: List[Simulation]
    total: int
    skip: int
    limit: int
    has_more: bool


@strawberry.type
class SuccessResponse:
    """Generic success response."""

    success: bool
    message: str


@strawberry.type
class ErrorResponse:
    """Error response."""

    message: str
    code: str
    details: Optional[strawberry.scalars.JSON] = None


# ==========================================
# Subscription Types
# ==========================================

@strawberry.type
class UploadProgress:
    """Upload progress update."""

    simulation_id: str
    filename: str
    progress: float
    uploaded: int
    total: int
    status: str


@strawberry.type
class AnalysisProgress:
    """Analysis progress update."""

    analysis_id: str
    simulation_id: str
    progress: float
    status: str
    message: str


@strawberry.type
class LLMStreamChunk:
    """LLM streaming chunk."""

    chunk_id: int
    content: str
    is_final: bool
    total_tokens: Optional[int] = None


# ==========================================
# Union Types
# ==========================================

@strawberry.type
class SimulationResult:
    """Simulation result union."""

    result: strawberry.union("SimulationResultUnion", (SimulationResponse, ErrorResponse))


# ==========================================
# Enums
# ==========================================

@strawberry.enum
class SimulationStatus:
    """Simulation status enum."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


@strawberry.enum
class AnalysisType:
    """Analysis type enum."""

    COMPREHENSIVE = "comprehensive"
    CONVERGENCE = "convergence"
    SPATIAL = "spatial"
    FIELD = "field"


@strawberry.enum
class VizType:
    """Visualization type enum."""

    RENDER_3D = "render_3d"
    SLICE = "slice"
    MULTI_SLICE = "multi_slice"
    CHART = "chart"


@strawberry.enum
class UserRole:
    """User role enum."""

    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
