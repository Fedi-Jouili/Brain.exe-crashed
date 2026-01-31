"""
PriceSense API
Multi-agent AI shopping assistant with financial intelligence
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware
from app.api.v1 import auth, profile, search, trace, health

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## PriceSense API

AI-powered shopping assistant that helps users make financially responsible purchasing decisions.

### Multi-Agent Architecture

The search system uses a pipeline of specialized agents:

1. **Discovery Agent** - Semantic product search using vector embeddings
2. **Financial Analyzer** - Assesses affordability based on user's financial profile
3. **PathFinder Agent** - Suggests alternatives for expensive products
4. **Ranking Agent** - Optimizes ordering using Thompson Sampling
5. **Explainer Agent** - Generates human-readable recommendations

### Authentication

All protected endpoints require a Bearer token in the Authorization header.
Refresh tokens are managed via httpOnly cookies for security.

### Error Handling

All errors follow a consistent format:
```json
{
  "error_code": "ERROR_CODE",
  "message": "Human readable message",
  "details": {},
  "trace_id": "optional-trace-id"
}
```
    """,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Response-Time"]
)

# Custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(profile.router, prefix=settings.API_V1_PREFIX)
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
app.include_router(trace.router, prefix=settings.API_V1_PREFIX)
app.include_router(health.router, prefix=settings.API_V1_PREFIX)


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your access token"
        }
    }
    
    # Add security requirement to all protected endpoints
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                # Skip health endpoints
                tags = operation.get("tags", [])
                if "Health" not in tags:
                    operation["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/")
async def root():
    """Root endpoint - redirects to API docs"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
        "openapi": f"{settings.API_V1_PREFIX}/openapi.json"
    }
