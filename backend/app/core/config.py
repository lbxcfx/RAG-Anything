"""Application configuration"""
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "RAG-Anything Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Database
    DATABASE_URL: str = "sqlite:///./rag_anything_dev.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Neo4j
    NEO4J_URL: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4jpassword"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"

    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Alibaba Cloud DashScope (通义千问)
    DASHSCOPE_API_KEY: Optional[str] = None
    # 北京地域: https://dashscope.aliyuncs.com/compatible-mode/v1
    # 新加坡地域: https://dashscope-intl.aliyuncs.com/compatible-mode/v1
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # File Storage
    UPLOAD_DIR: str = "./storage/uploads"
    PARSED_DIR: str = "./storage/parsed"
    VECTOR_DIR: str = "./storage/vectors"

    # RAG Configuration
    DEFAULT_LLM_MODEL: str = "qwen-turbo"
    DEFAULT_VLM_MODEL: str = "qwen-vl-max"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-v3"
    DEFAULT_EMBEDDING_DIM: int = 1024

    # Parser Configuration
    DEFAULT_PARSER: str = "mineru"
    DEFAULT_PARSE_METHOD: str = "auto"

    # MinerU API Configuration
    MINERU_API_URL: str = "https://mineru.net/api/v4/extract/task"  # MinerU云端API地址
    MINERU_API_KEY: str = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc1OTU4NDM5OCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiODM2N2M5NDMtMjliZC00ZGQxLTg0MGYtODcwOTI4YzM2MjU3IiwiZW1haWwiOiIiLCJleHAiOjE3NjA3OTM5OTh9.mW1e-4WLd6gUJRl3q4FDDwpBOadWcPZv80Rmum-mntNccGSh1G5-24rodVFFhXauVI2IyFeMXVoSNQlrRoEstw"
    MINERU_USE_API: bool = True  # 使用API方式调用MinerU

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:4173", "http://localhost:4174"]

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = "../.env"
        case_sensitive = True
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略额外的环境变量


settings = Settings()
