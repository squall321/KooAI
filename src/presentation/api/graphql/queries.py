"""
GraphQL Queries, Mutations, and Subscriptions

Main GraphQL API definition.
"""

from typing import List, Optional, AsyncIterator
import strawberry
from strawberry.file_uploads import Upload
from strawberry.types import Info

from src.presentation.api.graphql.schema import (
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
    UploadProgress,
    AnalysisProgress,
    LLMStreamChunk,
    UserInput,
    LoginInput,
    SimulationUploadInput,
    AnalysisInput,
    VisualizationInput,
    LLMAnalysisInput,
    PaginationInput,
    SimulationFilterInput,
)

from src.presentation.api.graphql import resolvers


# ==========================================
# Queries
# ==========================================

@strawberry.type
class Query:
    """
    GraphQL Query Root.

    All read operations.
    """

    @strawberry.field(description="Get current authenticated user")
    async def me(self, info: Info) -> Optional[User]:
        """
        Get current user information.

        Returns:
            Current authenticated user

        Example:
            ```graphql
            query {
              me {
                id
                email
                username
                role
                simulations {
                  id
                  filename
                  status
                }
              }
            }
            ```
        """
        return await resolvers.resolve_me(info)

    @strawberry.field(description="Get user by ID")
    async def user(self, user_id: str, info: Info) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Example:
            ```graphql
            query {
              user(userId: "usr_123") {
                id
                email
                username
              }
            }
            ```
        """
        return await resolvers.resolve_user(user_id, info)

    @strawberry.field(description="Get all users with pagination")
    async def users(
        self, pagination: Optional[PaginationInput] = None, info: Info = None
    ) -> List[User]:
        """
        Get all users with pagination.

        Args:
            pagination: Pagination parameters

        Returns:
            List of users

        Example:
            ```graphql
            query {
              users(pagination: { skip: 0, limit: 10 }) {
                id
                email
                username
              }
            }
            ```
        """
        return await resolvers.resolve_users(pagination, info)

    @strawberry.field(description="Get simulation by ID")
    async def simulation(
        self, simulation_id: str, info: Info
    ) -> Optional[Simulation]:
        """
        Get simulation by ID.

        Args:
            simulation_id: Simulation ID

        Returns:
            Simulation object

        Example:
            ```graphql
            query {
              simulation(simulationId: "sim_123") {
                id
                filename
                status
                analyses {
                  id
                  status
                  result
                }
              }
            }
            ```
        """
        return await resolvers.resolve_simulation(simulation_id, info)

    @strawberry.field(description="Get simulations with filtering and pagination")
    async def simulations(
        self,
        pagination: Optional[PaginationInput] = None,
        filter: Optional[SimulationFilterInput] = None,
        info: Info = None,
    ) -> PaginatedSimulations:
        """
        Get simulations with filtering and pagination.

        Args:
            pagination: Pagination parameters
            filter: Filter parameters

        Returns:
            Paginated simulations

        Example:
            ```graphql
            query {
              simulations(
                pagination: { skip: 0, limit: 20 }
                filter: { status: "uploaded", simulationType: "cfd" }
              ) {
                simulations {
                  id
                  filename
                  status
                }
                total
                hasMore
              }
            }
            ```
        """
        return await resolvers.resolve_simulations(pagination, filter, info)

    @strawberry.field(description="Get analysis by ID")
    async def analysis(self, analysis_id: str, info: Info) -> Optional[Analysis]:
        """
        Get analysis by ID.

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis object

        Example:
            ```graphql
            query {
              analysis(analysisId: "ana_123") {
                id
                analysisType
                result
                confidence
                simulation {
                  id
                  filename
                }
              }
            }
            ```
        """
        return await resolvers.resolve_analysis(analysis_id, info)

    @strawberry.field(description="Get current user's token usage")
    async def tokenUsage(self, info: Info) -> TokenUsage:
        """
        Get token usage statistics for current user.

        Returns:
            Token usage statistics

        Example:
            ```graphql
            query {
              tokenUsage {
                totalTokens
                promptTokens
                completionTokens
                costUsd
                model
              }
            }
            ```
        """
        return await resolvers.resolve_token_usage(info)


# ==========================================
# Mutations
# ==========================================

@strawberry.type
class Mutation:
    """
    GraphQL Mutation Root.

    All write operations.
    """

    @strawberry.mutation(description="Register new user")
    async def register(self, user_input: UserInput, info: Info) -> AuthResponse:
        """
        Register a new user account.

        Args:
            user_input: User registration data

        Returns:
            Authentication response with tokens

        Example:
            ```graphql
            mutation {
              register(userInput: {
                email: "user@example.com"
                username: "johndoe"
                password: "SecurePass123!"
                role: "user"
              }) {
                accessToken
                refreshToken
                user {
                  id
                  email
                  username
                }
              }
            }
            ```
        """
        return await resolvers.resolve_register(user_input, info)

    @strawberry.mutation(description="Login user")
    async def login(self, login_input: LoginInput, info: Info) -> AuthResponse:
        """
        Login with email and password.

        Args:
            login_input: Login credentials

        Returns:
            Authentication response with tokens

        Example:
            ```graphql
            mutation {
              login(loginInput: {
                email: "user@example.com"
                password: "SecurePass123!"
              }) {
                accessToken
                refreshToken
                expiresIn
                user {
                  id
                  email
                }
              }
            }
            ```
        """
        return await resolvers.resolve_login(login_input, info)

    @strawberry.mutation(description="Upload simulation file")
    async def uploadSimulation(
        self, file: Upload, upload_input: SimulationUploadInput, info: Info
    ) -> SimulationResponse:
        """
        Upload simulation file.

        Args:
            file: File upload
            upload_input: Upload parameters

        Returns:
            Simulation response

        Example:
            ```graphql
            mutation($file: Upload!) {
              uploadSimulation(
                file: $file
                uploadInput: {
                  simulationType: "cfd"
                  autoAnalyze: true
                }
              ) {
                simulation {
                  id
                  filename
                  status
                }
                message
              }
            }
            ```
        """
        return await resolvers.resolve_upload_simulation(file, upload_input, info)

    @strawberry.mutation(description="Delete simulation")
    async def deleteSimulation(
        self, simulation_id: str, info: Info
    ) -> SuccessResponse:
        """
        Delete simulation and all associated data.

        Args:
            simulation_id: Simulation ID

        Returns:
            Success response

        Example:
            ```graphql
            mutation {
              deleteSimulation(simulationId: "sim_123") {
                success
                message
              }
            }
            ```
        """
        return await resolvers.resolve_delete_simulation(simulation_id, info)

    @strawberry.mutation(description="Analyze simulation")
    async def analyzeSimulation(
        self, analysis_input: AnalysisInput, info: Info
    ) -> AnalysisResponse:
        """
        Start simulation analysis.

        Args:
            analysis_input: Analysis parameters

        Returns:
            Analysis response

        Example:
            ```graphql
            mutation {
              analyzeSimulation(analysisInput: {
                simulationId: "sim_123"
                analysisType: "comprehensive"
                parameters: { includeVisualization: true }
              }) {
                analysis {
                  id
                  status
                }
                message
              }
            }
            ```
        """
        return await resolvers.resolve_analyze_simulation(analysis_input, info)

    @strawberry.mutation(description="Create visualization")
    async def createVisualization(
        self, viz_input: VisualizationInput, info: Info
    ) -> VisualizationResponse:
        """
        Generate visualization.

        Args:
            viz_input: Visualization parameters

        Returns:
            Visualization response

        Example:
            ```graphql
            mutation {
              createVisualization(vizInput: {
                simulationId: "sim_123"
                vizType: "render_3d"
                parameters: {
                  resolution: [1920, 1080]
                  cameraPosition: [1, 1, 1]
                }
              }) {
                visualization {
                  id
                  vizType
                  filePath
                }
                url
                message
              }
            }
            ```
        """
        return await resolvers.resolve_create_visualization(viz_input, info)

    @strawberry.mutation(description="Create conversation context")
    async def createConversationContext(
        self, max_turns: int = 10, info: Info = None
    ) -> ConversationContext:
        """
        Create LLM conversation context.

        Args:
            max_turns: Maximum conversation turns

        Returns:
            Conversation context

        Example:
            ```graphql
            mutation {
              createConversationContext(maxTurns: 10) {
                id
                maxTurns
                createdAt
              }
            }
            ```
        """
        return await resolvers.resolve_create_conversation_context(max_turns, info)

    @strawberry.mutation(description="Delete conversation context")
    async def deleteConversationContext(
        self, context_id: str, info: Info
    ) -> SuccessResponse:
        """
        Delete conversation context.

        Args:
            context_id: Context ID

        Returns:
            Success response

        Example:
            ```graphql
            mutation {
              deleteConversationContext(contextId: "ctx_123") {
                success
                message
              }
            }
            ```
        """
        return await resolvers.resolve_delete_conversation_context(context_id, info)


# ==========================================
# Subscriptions
# ==========================================

@strawberry.type
class Subscription:
    """
    GraphQL Subscription Root.

    Real-time updates.
    """

    @strawberry.subscription(description="Subscribe to upload progress")
    async def uploadProgress(
        self, simulation_id: str, info: Info
    ) -> AsyncIterator[UploadProgress]:
        """
        Subscribe to file upload progress.

        Args:
            simulation_id: Simulation ID

        Yields:
            Upload progress updates

        Example:
            ```graphql
            subscription {
              uploadProgress(simulationId: "sim_123") {
                simulationId
                filename
                progress
                uploaded
                total
                status
              }
            }
            ```
        """
        async for progress in resolvers.subscribe_upload_progress(simulation_id, info):
            yield progress

    @strawberry.subscription(description="Subscribe to analysis progress")
    async def analysisProgress(
        self, analysis_id: str, info: Info
    ) -> AsyncIterator[AnalysisProgress]:
        """
        Subscribe to analysis progress.

        Args:
            analysis_id: Analysis ID

        Yields:
            Analysis progress updates

        Example:
            ```graphql
            subscription {
              analysisProgress(analysisId: "ana_123") {
                analysisId
                progress
                status
                message
              }
            }
            ```
        """
        async for progress in resolvers.subscribe_analysis_progress(analysis_id, info):
            yield progress

    @strawberry.subscription(description="Subscribe to LLM streaming")
    async def llmStream(
        self, llm_input: LLMAnalysisInput, info: Info
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Subscribe to streaming LLM responses.

        Args:
            llm_input: LLM analysis parameters

        Yields:
            LLM response chunks

        Example:
            ```graphql
            subscription {
              llmStream(llmInput: {
                prompt: "Analyze this simulation"
                temperature: 0.7
                maxTokens: 1000
              }) {
                chunkId
                content
                isFinal
                totalTokens
              }
            }
            ```
        """
        async for chunk in resolvers.subscribe_llm_stream(llm_input, info):
            yield chunk


# ==========================================
# Create GraphQL Schema
# ==========================================

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)
