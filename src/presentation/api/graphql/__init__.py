"""
GraphQL API Module

Provides GraphQL API interface for KooAI.

Features:
- Complete GraphQL schema with types, queries, mutations, subscriptions
- Real-time updates via GraphQL subscriptions
- DataLoader for efficient batching (N+1 problem solution)
- GraphiQL IDE for interactive testing
- WebSocket support for subscriptions

Usage:
    # Import router in FastAPI main app
    from src.presentation.api.graphql.router import router as graphql_router

    app.include_router(graphql_router, prefix="/api/v1")

Access Points:
    - GraphQL endpoint: /api/v1/graphql
    - GraphiQL IDE: /api/v1/graphql (browser)
    - Playground: /api/v1/graphql/playground
    - Schema SDL: /api/v1/graphql/schema
    - Examples: /api/v1/graphql/examples
"""

from .schema import (
    User,
    Simulation,
    Analysis,
    Visualization,
    ConversationContext,
    TokenUsage,
    AuthResponse,
    SimulationResponse,
    AnalysisResponse,
    VisualizationResponse,
    PaginatedSimulations,
    SuccessResponse,
)

from .queries import schema, Query, Mutation, Subscription
from .router import router, graphql_router

__all__ = [
    # Schema
    "schema",
    "Query",
    "Mutation",
    "Subscription",
    # Types
    "User",
    "Simulation",
    "Analysis",
    "Visualization",
    "ConversationContext",
    "TokenUsage",
    # Responses
    "AuthResponse",
    "SimulationResponse",
    "AnalysisResponse",
    "VisualizationResponse",
    "PaginatedSimulations",
    "SuccessResponse",
    # Router
    "router",
    "graphql_router",
]
