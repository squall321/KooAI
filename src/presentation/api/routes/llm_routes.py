"""
LLM Integration API Routes

Endpoints for AI-powered analysis with streaming support.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.infrastructure.llm.streaming import (
    StreamingLLMService,
    ConversationContext,
    TokenUsageTracker,
)

router = APIRouter(prefix="/llm", tags=["analysis"])


# Request/Response models
class AnalysisRequest(BaseModel):
    """LLM analysis request."""

    prompt: str
    context_id: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000


class UsageResponse(BaseModel):
    """Token usage response."""

    total_tokens: int
    total_cost_usd: float
    usage_by_model: dict


# In-memory storage (replace with database)
_contexts: dict[str, ConversationContext] = {}
_usage_tracker = TokenUsageTracker()


@router.post(
    "/analyze/stream",
    summary="Streaming LLM Analysis",
    description="Get AI analysis with Server-Sent Events streaming",
)
async def analyze_with_llm_stream(request: AnalysisRequest):
    """
    ## Streaming LLM Analysis

    Stream AI-generated analysis using Server-Sent Events (SSE).

    ### Features
    - Real-time streaming responses
    - Conversation context support
    - Token usage tracking
    - Multiple LLM provider support

    ### Request Body
    - **prompt**: Analysis prompt
    - **context_id**: Optional conversation context ID
    - **temperature**: Sampling temperature (0.0-1.0)
    - **max_tokens**: Maximum tokens to generate

    ### Returns
    Server-Sent Events stream with analysis chunks

    ### Example
    ```python
    import httpx

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/api/v1/llm/analyze/stream",
            json={"prompt": "Analyze this simulation..."}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(data["content"], end="", flush=True)
    ```

    ### JavaScript Example
    ```javascript
    const eventSource = new EventSource('/api/v1/llm/analyze/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.content);
    };
    ```
    """
    service = StreamingLLMService()

    # Get or create context
    context = None
    if request.context_id:
        if request.context_id not in _contexts:
            _contexts[request.context_id] = ConversationContext()
        context = _contexts[request.context_id]

    # Stream response
    async def generate():
        async for chunk in service.stream_analysis(
            prompt=request.prompt,
            context=context,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        ):
            yield chunk.to_sse()

            # Track usage on final chunk
            if chunk.finish_reason:
                _usage_tracker.record_usage(
                    model="mock-model",
                    prompt_tokens=len(request.prompt.split()),
                    completion_tokens=chunk.metadata.get("token_count", 0),
                    cost_usd=0.001,  # Mock cost
                )

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post(
    "/context/create",
    summary="Create Conversation Context",
    description="Create a new conversation context for multi-turn dialogue",
)
async def create_context():
    """
    ## Create Conversation Context

    Create a new conversation context for maintaining multi-turn dialogues.

    ### Returns
    - **context_id**: New context ID

    ### Example
    ```bash
    curl -X POST "http://localhost:8000/api/v1/llm/context/create"
    ```

    Response:
    ```json
    {
        "context_id": "ctx_abc123",
        "max_turns": 10
    }
    ```
    """
    import uuid

    context_id = f"ctx_{uuid.uuid4().hex[:8]}"
    _contexts[context_id] = ConversationContext()

    return {"context_id": context_id, "max_turns": 10}


@router.delete(
    "/context/{context_id}",
    summary="Delete Conversation Context",
    description="Delete a conversation context",
)
async def delete_context(context_id: str):
    """
    ## Delete Conversation Context

    Clear and delete a conversation context.

    ### Parameters
    - **context_id**: Context ID to delete

    ### Example
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/llm/context/ctx_abc123"
    ```
    """
    if context_id in _contexts:
        del _contexts[context_id]
        return {"message": f"Context {context_id} deleted"}
    return {"message": "Context not found"}


@router.get(
    "/usage",
    response_model=UsageResponse,
    summary="Get Token Usage Stats",
    description="Get LLM token usage and cost statistics",
)
async def get_usage_stats():
    """
    ## Get Token Usage Statistics

    Retrieve aggregate token usage and cost information.

    ### Returns
    - **total_tokens**: Total tokens used
    - **total_cost_usd**: Total cost in USD
    - **usage_by_model**: Usage breakdown by model

    ### Example
    ```bash
    curl "http://localhost:8000/api/v1/llm/usage"
    ```

    Response:
    ```json
    {
        "total_tokens": 15420,
        "total_cost_usd": 0.523,
        "usage_by_model": {
            "gpt-4": {
                "requests": 10,
                "total_tokens": 8500,
                "prompt_tokens": 5200,
                "completion_tokens": 3300
            }
        }
    }
    ```
    """
    return UsageResponse(
        total_tokens=_usage_tracker.get_total_tokens(),
        total_cost_usd=_usage_tracker.get_total_cost(),
        usage_by_model=_usage_tracker.get_usage_by_model(),
    )
