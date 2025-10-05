"""API v1 router"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, models, knowledge_base, documents, query, graph, admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(knowledge_base.router, prefix="/knowledge-bases", tags=["Knowledge Bases"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(query.router, prefix="/query", tags=["Query"])
api_router.include_router(graph.router, prefix="/graph", tags=["Graph"])
api_router.include_router(admin.router, prefix="/admin", tags=["Administration"])
