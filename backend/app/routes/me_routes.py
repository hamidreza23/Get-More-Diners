"""
User-specific routes for /me endpoints.
Handles user's own restaurant and profile data.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, text
from pydantic import BaseModel, Field
import logging

from ..db import get_db
from ..middleware import get_current_user_id_from_state

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_user_deleted(user_id: str, db: AsyncSession) -> bool:
    """Check if a user has been deleted."""
    try:
        check_deleted_query = text("""
            SELECT user_id FROM public.deleted_users WHERE user_id = :user_id
        """)
        result = await db.execute(check_deleted_query, {"user_id": user_id})
        deleted_user = result.fetchone()
        return deleted_user is not None
    except Exception as e:
        logger.error(f"Error checking deleted user status: {e}")
        return False


class RestaurantUpsert(BaseModel):
    """Schema for restaurant upsert operations."""
    name: str = Field(..., min_length=1, max_length=255)
    cuisine: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    caption: Optional[str] = Field(None, max_length=500)


class RestaurantResponse(BaseModel):
    """Response schema for restaurant data."""
    id: str
    owner_user_id: str
    name: str
    cuisine: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    caption: Optional[str] = None
    created_at: str


@router.get("/restaurant")
async def get_my_restaurant(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[RestaurantResponse]:
    """
    Get the single restaurant owned by the authenticated user.
    
    Args:
        request: HTTP request with user context
        db: Database session
        
    Returns:
        Optional[RestaurantResponse]: Restaurant data if exists, None otherwise
    """
    try:
        current_user_id = get_current_user_id_from_state(request)
        
        # Query for user's restaurant
        query = text("""
            SELECT id, owner_user_id, name, cuisine, city, state,
                   contact_email, contact_phone, website_url, logo_url, caption, created_at
            FROM public.restaurants
            WHERE owner_user_id = :user_id
            LIMIT 1
        """)
        
        result = await db.execute(query, {"user_id": current_user_id})
        restaurant = result.fetchone()
        
        if not restaurant:
            return None
        
        # Convert to response format
        return RestaurantResponse(
            id=str(restaurant.id),
            owner_user_id=str(restaurant.owner_user_id),
            name=restaurant.name,
            cuisine=restaurant.cuisine,
            city=restaurant.city,
            state=restaurant.state,
            contact_email=restaurant.contact_email,
            contact_phone=restaurant.contact_phone,
            website_url=restaurant.website_url,
            logo_url=restaurant.logo_url,
            caption=restaurant.caption,
            created_at=restaurant.created_at.isoformat() if restaurant.created_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user restaurant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve restaurant"
        )


@router.put("/restaurant")
async def upsert_my_restaurant(
    restaurant_data: RestaurantUpsert,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> RestaurantResponse:
    """
    Upsert (create or update) restaurant for the authenticated user.
    
    Args:
        restaurant_data: Restaurant data to upsert
        request: HTTP request with user context
        db: Database session
        
    Returns:
        RestaurantResponse: Updated/created restaurant data
    """
    try:
        current_user_id = get_current_user_id_from_state(request)
        
        # Use PostgreSQL UPSERT with ON CONFLICT
        upsert_query = text("""
            INSERT INTO public.restaurants (
                id, owner_user_id, name, cuisine, city, state, contact_email, contact_phone, website_url, logo_url, caption
            ) VALUES (
                gen_random_uuid(), :user_id, :name, :cuisine, :city, :state, :contact_email, :contact_phone, :website_url, :logo_url, :caption
            )
            ON CONFLICT (owner_user_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                cuisine = EXCLUDED.cuisine,
                city = EXCLUDED.city,
                state = EXCLUDED.state,
                contact_email = EXCLUDED.contact_email,
                contact_phone = EXCLUDED.contact_phone,
                website_url = EXCLUDED.website_url,
                logo_url = EXCLUDED.logo_url,
                caption = EXCLUDED.caption
            RETURNING id, owner_user_id, name, cuisine, city, state,
                      contact_email, contact_phone, website_url, logo_url, caption, created_at
        """)
        
        # Note: This assumes a unique constraint on owner_user_id
        # If not in schema, we'll need to check for existing first
        try:
            result = await db.execute(upsert_query, {
                "user_id": current_user_id,
                "name": restaurant_data.name,
                "cuisine": restaurant_data.cuisine,
                "city": restaurant_data.city,
                "state": restaurant_data.state,
                "contact_email": restaurant_data.contact_email,
                "contact_phone": restaurant_data.contact_phone,
                "website_url": restaurant_data.website_url,
                "logo_url": restaurant_data.logo_url,
                "caption": restaurant_data.caption
            })
            await db.commit()
            
            restaurant = result.fetchone()
            
        except Exception as upsert_error:
            # If upsert fails (no unique constraint), do manual check and update
            await db.rollback()
            logger.info("UPSERT failed, trying manual check-and-update")
            
            # Check if restaurant exists
            check_query = text("""
                SELECT id FROM public.restaurants WHERE owner_user_id = :user_id
            """)
            check_result = await db.execute(check_query, {"user_id": current_user_id})
            existing = check_result.fetchone()
            
            if existing:
                # Update existing
                update_query = text("""
                    UPDATE public.restaurants 
                    SET name = :name, cuisine = :cuisine, city = :city, state = :state,
                        contact_email = :contact_email, contact_phone = :contact_phone, website_url = :website_url, logo_url = :logo_url, caption = :caption
                    WHERE owner_user_id = :user_id
                    RETURNING id, owner_user_id, name, cuisine, city, state, 
                              contact_email, contact_phone, website_url, logo_url, caption, created_at
                """)
            else:
                # Insert new
                update_query = text("""
                    INSERT INTO public.restaurants (
                        id, owner_user_id, name, cuisine, city, state, contact_email, contact_phone, website_url, logo_url, caption
                    ) VALUES (
                        gen_random_uuid(), :user_id, :name, :cuisine, :city, :state, :contact_email, :contact_phone, :website_url, :logo_url, :caption
                    )
                    RETURNING id, owner_user_id, name, cuisine, city, state, 
                              contact_email, contact_phone, website_url, logo_url, caption, created_at
                """)
            
            result = await db.execute(update_query, {
                "user_id": current_user_id,
                "name": restaurant_data.name,
                "cuisine": restaurant_data.cuisine,
                "city": restaurant_data.city,
                "state": restaurant_data.state,
                "contact_email": restaurant_data.contact_email,
                "contact_phone": restaurant_data.contact_phone,
                "website_url": restaurant_data.website_url,
                "logo_url": restaurant_data.logo_url,
                "caption": restaurant_data.caption
            })
            await db.commit()
            
            restaurant = result.fetchone()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upsert restaurant"
            )
        
        return RestaurantResponse(
            id=str(restaurant.id),
            owner_user_id=str(restaurant.owner_user_id),
            name=restaurant.name,
            cuisine=restaurant.cuisine,
            city=restaurant.city,
            state=restaurant.state,
            contact_email=restaurant.contact_email,
            contact_phone=restaurant.contact_phone,
            website_url=restaurant.website_url,
            logo_url=restaurant.logo_url,
            caption=restaurant.caption,
            created_at=restaurant.created_at.isoformat() if restaurant.created_at else ""
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error upserting restaurant: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save restaurant"
        )


@router.delete("/delete-account")
async def delete_my_account(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete the authenticated user's account and all associated data.
    
    This will delete:
    - All campaign recipients
    - All campaigns
    - All restaurants
    - The user from auth.users (handled by Supabase)
    
    Args:
        request: HTTP request with user context
        db: Database session
        
    Returns:
        Dict[str, str]: Deletion confirmation message
    """
    try:
        logger.info(f"Delete account request received from {request.client.host if request.client else 'unknown'}")
        
        # Check authentication state
        logger.info(f"Request state: authenticated={getattr(request.state, 'authenticated', False)}, user_id={getattr(request.state, 'user_id', None)}")
        
        current_user_id = get_current_user_id_from_state(request)
        
        # Create a simple deleted_users table to track deleted users
        try:
            create_deleted_users_table = text("""
                CREATE TABLE IF NOT EXISTS public.deleted_users (
                    user_id UUID PRIMARY KEY,
                    deleted_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            await db.execute(create_deleted_users_table)
            
            # Mark user as deleted
            mark_user_deleted = text("""
                INSERT INTO public.deleted_users (user_id, deleted_at)
                VALUES (:user_id, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    deleted_at = NOW()
            """)
            await db.execute(mark_user_deleted, {"user_id": current_user_id})
            logger.info(f"Marked user {current_user_id} as deleted")
        except Exception as e:
            logger.error(f"Error creating/marking deleted user: {e}")
            # Continue with deletion even if marking fails
        
        # Delete campaign recipients first (due to foreign key constraints)
        delete_recipients_query = text("""
            DELETE FROM public.campaign_recipients 
            WHERE campaign_id IN (
                SELECT c.id 
                FROM public.campaigns c
                JOIN public.restaurants r ON c.restaurant_id = r.id
                WHERE r.owner_user_id = :user_id
            )
        """)
        result1 = await db.execute(delete_recipients_query, {"user_id": current_user_id})
        logger.info(f"Deleted {result1.rowcount} campaign recipients")
        
        # Delete campaigns
        delete_campaigns_query = text("""
            DELETE FROM public.campaigns 
            WHERE restaurant_id IN (
                SELECT id 
                FROM public.restaurants 
                WHERE owner_user_id = :user_id
            )
        """)
        result2 = await db.execute(delete_campaigns_query, {"user_id": current_user_id})
        logger.info(f"Deleted {result2.rowcount} campaigns")
        
        # Delete restaurants
        delete_restaurants_query = text("""
            DELETE FROM public.restaurants 
            WHERE owner_user_id = :user_id
        """)
        result3 = await db.execute(delete_restaurants_query, {"user_id": current_user_id})
        logger.info(f"Deleted {result3.rowcount} restaurants")
        
        await db.commit()
        
        logger.info(f"Successfully deleted all data for user {current_user_id}")
        
        return {
            "message": "Account and all associated data deleted successfully. You will not be able to sign in again with this account."
        }
        
    except HTTPException as e:
        await db.rollback()
        logger.error(f"HTTP error deleting user account: {e.detail}")
        raise e
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user account: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )
