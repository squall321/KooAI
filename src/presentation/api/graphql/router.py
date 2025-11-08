"""
GraphQL Router Integration

Integrate GraphQL with FastAPI.
"""

from fastapi import APIRouter, Depends
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from src.presentation.api.graphql.queries import schema


# Create GraphQL router
graphql_router = GraphQLRouter(
    schema,
    path="/graphql",
    graphiql=True,  # Enable GraphiQL IDE
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
    ],
)


# FastAPI router
router = APIRouter(prefix="/graphql", tags=["GraphQL"])

# Include GraphQL router
router.include_router(graphql_router)


# Additional REST endpoint for schema introspection
@router.get("/schema")
async def get_schema():
    """
    Get GraphQL schema as SDL (Schema Definition Language).

    Returns:
        GraphQL schema in SDL format

    Example:
        ```bash
        curl http://localhost:8000/api/v1/graphql/schema
        ```
    """
    from strawberry.printer import print_schema

    return {"schema": print_schema(schema)}


@router.get("/playground")
async def graphql_playground():
    """
    GraphQL Playground HTML page.

    Returns:
        HTML page for GraphQL Playground
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>GraphQL Playground</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
        <link rel="shortcut icon" href="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />
        <script src="https://cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
    </head>
    <body>
        <div id="root"></div>
        <script>
            window.addEventListener('load', function (event) {
                GraphQLPlayground.init(document.getElementById('root'), {
                    endpoint: '/api/v1/graphql',
                    subscriptionEndpoint: 'ws://localhost:8000/api/v1/graphql',
                    settings: {
                        'request.credentials': 'include'
                    }
                })
            })
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse

    return HTMLResponse(content=html)


# Example queries for documentation
EXAMPLE_QUERIES = {
    "get_current_user": """
query GetCurrentUser {
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
""",
    "list_simulations": """
query ListSimulations {
  simulations(
    pagination: { skip: 0, limit: 10 }
    filter: { status: "uploaded" }
  ) {
    simulations {
      id
      filename
      status
      createdAt
      analyses {
        id
        status
      }
    }
    total
    hasMore
  }
}
""",
    "upload_simulation": """
mutation UploadSimulation($file: Upload!) {
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
""",
    "analyze_simulation": """
mutation AnalyzeSimulation {
  analyzeSimulation(analysisInput: {
    simulationId: "sim_123"
    analysisType: "comprehensive"
  }) {
    analysis {
      id
      status
    }
    message
  }
}
""",
    "subscribe_upload_progress": """
subscription UploadProgress {
  uploadProgress(simulationId: "sim_123") {
    simulationId
    filename
    progress
    uploaded
    total
    status
  }
}
""",
    "subscribe_llm_stream": """
subscription LLMStream {
  llmStream(llmInput: {
    prompt: "Analyze the convergence of this simulation"
    temperature: 0.7
    maxTokens: 1000
  }) {
    chunkId
    content
    isFinal
    totalTokens
  }
}
""",
}


@router.get("/examples")
async def get_example_queries():
    """
    Get example GraphQL queries.

    Returns:
        Dictionary of example queries

    Example:
        ```bash
        curl http://localhost:8000/api/v1/graphql/examples
        ```
    """
    return {
        "examples": EXAMPLE_QUERIES,
        "description": "Example GraphQL queries, mutations, and subscriptions",
    }
