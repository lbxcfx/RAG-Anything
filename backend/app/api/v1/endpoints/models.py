"""Model configuration endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.models.user import User
from app.models.model_config import ModelConfig
from app.schemas.model_config import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
)

router = APIRouter()


@router.post("/", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_model_config(
    config_in: ModelConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create new model configuration"""
    # If setting as default, unset other defaults of same type
    if config_in.is_default:
        result = await db.execute(
            select(ModelConfig).where(
                ModelConfig.user_id == current_user.id,
                ModelConfig.model_type == config_in.model_type,
                ModelConfig.is_default == True,
            )
        )
        existing_defaults = result.scalars().all()
        for existing in existing_defaults:
            existing.is_default = False

    # Create new config
    config = ModelConfig(
        **config_in.model_dump(), user_id=current_user.id
    )

    db.add(config)
    await db.commit()
    await db.refresh(config)

    return ModelConfigResponse.from_orm(config)


@router.get("/", response_model=List[ModelConfigResponse])
async def list_model_configs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    model_type: str = None,
):
    """List user's model configurations"""
    query = select(ModelConfig).where(ModelConfig.user_id == current_user.id)

    if model_type:
        query = query.where(ModelConfig.model_type == model_type)

    result = await db.execute(query)
    configs = result.scalars().all()

    return [ModelConfigResponse.from_orm(c) for c in configs]


@router.get("/{config_id}", response_model=ModelConfigResponse)
async def get_model_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get model configuration"""
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.id == config_id,
            ModelConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found",
        )

    return ModelConfigResponse.from_orm(config)


@router.put("/{config_id}", response_model=ModelConfigResponse)
async def update_model_config(
    config_id: int,
    config_update: ModelConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update model configuration"""
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.id == config_id,
            ModelConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found",
        )

    # Update fields
    update_data = config_update.model_dump(exclude_unset=True)

    # Don't update API key if it's the masked value
    if update_data.get("api_key") == "***":
        update_data.pop("api_key", None)

    # Handle default setting
    if update_data.get("is_default") and not config.is_default:
        result = await db.execute(
            select(ModelConfig).where(
                ModelConfig.user_id == current_user.id,
                ModelConfig.model_type == config.model_type,
                ModelConfig.is_default == True,
            )
        )
        existing_defaults = result.scalars().all()
        for existing in existing_defaults:
            existing.is_default = False

    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return ModelConfigResponse.from_orm(config)


@router.post("/{config_id}/default/", response_model=ModelConfigResponse)
async def set_default_model_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Set model configuration as default"""
    # Get the config to set as default
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.id == config_id,
            ModelConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found",
        )

    # Unset other defaults of the same type
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.user_id == current_user.id,
            ModelConfig.model_type == config.model_type,
            ModelConfig.is_default == True,
        )
    )
    existing_defaults = result.scalars().all()
    for existing in existing_defaults:
        existing.is_default = False

    # Set this config as default
    config.is_default = True

    await db.commit()
    await db.refresh(config)

    return ModelConfigResponse.from_orm(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_config(
    config_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete model configuration"""
    result = await db.execute(
        select(ModelConfig).where(
            ModelConfig.id == config_id,
            ModelConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model configuration not found",
        )

    await db.delete(config)
    await db.commit()
