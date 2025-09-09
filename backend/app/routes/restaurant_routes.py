"""
Restaurant management routes.
Handles CRUD operations for restaurants with proper ownership validation.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete
from ..dependencies import get_current_user_id
import logging

from ..db import get_db
from ..middleware import get_current_user_id_from_state
from ..models import restaurants_table
from ..schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    RestaurantListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=RestaurantResponse)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> RestaurantResponse:
    """
    Create a new restaurant.
    
    Args:
        restaurant_data: Restaurant creation data
        request: HTTP request with user context
        db: Database session
        
    Returns:
        RestaurantResponse: Created restaurant data
    """
    try:
        # Use hardcoded user ID for testing
        current_user_id = get_current_user_id_from_state(request)
        
        # Create restaurant with current user as owner
        query = insert(restaurants_table).values(
            owner_user_id=current_user_id,
            **restaurant_data.model_dump()
        ).returning(restaurants_table)
        
        result = await db.execute(query)
        await db.commit()
        
        restaurant = result.fetchone()
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create restaurant"
            )
        
        return RestaurantResponse.model_validate(restaurant)
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating restaurant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create restaurant"
        )


@router.get("/", response_model=RestaurantListResponse)
async def list_restaurants(
    skip: int = 0,
    limit: int = 100,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> RestaurantListResponse:
    """
    List restaurants owned by the current user.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        RestaurantListResponse: List of restaurants
    """
    try:
        # Query restaurants owned by current user
        query = select(restaurants_table).where(
            restaurants_table.c.owner_user_id == current_user_id
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        restaurants = result.fetchall()
        
        # Count total restaurants
        count_query = select(func.count()).select_from(restaurants_table).where(
            restaurants_table.c.owner_user_id == current_user_id
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return RestaurantListResponse(
            restaurants=[RestaurantResponse.model_validate(r) for r in restaurants],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing restaurants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restaurants"
        )


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> RestaurantResponse:
    """
    Get a specific restaurant by ID.
    
    Args:
        restaurant_id: Restaurant UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        RestaurantResponse: Restaurant data
    """
    try:
        query = select(restaurants_table).where(
            restaurants_table.c.id == restaurant_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        result = await db.execute(query)
        restaurant = result.fetchone()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        return RestaurantResponse.model_validate(restaurant)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting restaurant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restaurant"
        )


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: UUID,
    restaurant_data: RestaurantUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> RestaurantResponse:
    """
    Update a restaurant.
    
    Args:
        restaurant_id: Restaurant UUID
        restaurant_data: Restaurant update data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        RestaurantResponse: Updated restaurant data
    """
    try:
        # Update only fields that are provided
        update_data = restaurant_data.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        query = update(restaurants_table).where(
            restaurants_table.c.id == restaurant_id,
            restaurants_table.c.owner_user_id == current_user_id
        ).values(**update_data).returning(restaurants_table)
        
        result = await db.execute(query)
        await db.commit()
        
        restaurant = result.fetchone()
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        return RestaurantResponse.model_validate(restaurant)
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating restaurant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update restaurant"
        )


@router.delete("/{restaurant_id}")
async def delete_restaurant(
    restaurant_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete a restaurant.
    
    Args:
        restaurant_id: Restaurant UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        dict: Deletion confirmation
    """
    try:
        query = delete(restaurants_table).where(
            restaurants_table.c.id == restaurant_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        result = await db.execute(query)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found"
            )
        
        return {"message": "Restaurant deleted successfully"}
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting restaurant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete restaurant"
        )


# Note: This would need to import the actual table definitions
# Import table definition from models
from ..models import restaurants_table
