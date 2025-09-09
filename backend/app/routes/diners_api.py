"""
Diners API routes with filtering and pagination.
Updated to match the corrected challenge data structure.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
import logging

from ..db import get_db
from ..middleware import get_current_user_id_from_state

logger = logging.getLogger(__name__)

router = APIRouter()


class DinerItem(BaseModel):
    """Individual diner in the response - matches challenge data structure."""
    phone: str  # Primary key
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    seniority: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    dining_interests: Optional[str] = None  # Comma-separated string from challenge
    interests: List[str] = []  # Parsed for frontend compatibility
    email: Optional[str] = None
    consent_email: bool = True
    consent_sms: bool = True


class DinersResponse(BaseModel):
    """Response for diners endpoint."""
    total: int
    items: List[DinerItem]


class FilterOptionsResponse(BaseModel):
    """Response for filter options endpoint."""
    interests: List[str]
    seniority_levels: List[str]
    states: List[str]
    cities: List[str]










@router.get("/filter-options", response_model=FilterOptionsResponse)
async def get_filter_options(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> FilterOptionsResponse:
    """
    Get unique filter options from the diners table.
    Returns all unique values for interests, seniority levels, states, and cities.
    """
    try:
        current_user_id = get_current_user_id_from_state(request)
        
        # Get unique interests
        interests_query = text("""
            SELECT DISTINCT unnest(interests) as interest
            FROM diners
            WHERE interests IS NOT NULL AND array_length(interests, 1) > 0
            ORDER BY interest
        """).execution_options(postgresql_prepare=False)
        interests_result = await db.execute(interests_query)
        interests = [row[0] for row in interests_result.fetchall()]
        
        # Get unique seniority levels
        seniority_query = text("""
            SELECT DISTINCT seniority
            FROM diners
            WHERE seniority IS NOT NULL AND seniority != ''
            ORDER BY seniority
        """).execution_options(postgresql_prepare=False)
        seniority_result = await db.execute(seniority_query)
        seniority_levels = [row[0] for row in seniority_result.fetchall()]
        
        # Get unique states
        states_query = text("""
            SELECT DISTINCT state
            FROM diners
            WHERE state IS NOT NULL AND state != ''
            ORDER BY state
        """).execution_options(postgresql_prepare=False)
        states_result = await db.execute(states_query)
        states = [row[0] for row in states_result.fetchall()]
        
        # Get unique cities
        cities_query = text("""
            SELECT DISTINCT city
            FROM diners
            WHERE city IS NOT NULL AND city != ''
            ORDER BY city
        """).execution_options(postgresql_prepare=False)
        cities_result = await db.execute(cities_query)
        cities = [row[0] for row in cities_result.fetchall()]
        
        return FilterOptionsResponse(
            interests=interests,
            seniority_levels=seniority_levels,
            states=states,
            cities=cities
        )
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get filter options"
        )


@router.get("/test", response_model=DinersResponse)
async def test_diners(
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=1000, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
) -> DinersResponse:
    """
    Test endpoint for diners - no authentication required.
    """
    try:
        # Calculate offset
        offset = (page - 1) * pageSize
        
        # Simple count query
        count_query = text("SELECT COUNT(*) as total FROM diners")
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Simple data query
        data_query = text("""
            SELECT 
                phone,
                first_name,
                last_name,
                seniority,
                city,
                state,
                address_text as address,
                CASE 
                    WHEN interests IS NOT NULL AND array_length(interests, 1) > 0 
                    THEN array_to_string(interests, ', ')
                    ELSE NULL
                END as dining_interests,
                email,
                COALESCE(consent_email, true) as consent_email,
                COALESCE(consent_sms, true) as consent_sms
            FROM diners
            ORDER BY first_name, last_name, phone
            LIMIT :limit OFFSET :offset
        """)
        
        data_result = await db.execute(data_query, {"limit": pageSize, "offset": offset})
        rows = data_result.fetchall()
        
        # Convert rows to DinerItem objects
        items = []
        for row in rows:
            item = DinerItem(
                phone=row.phone or "",
                first_name=row.first_name,
                last_name=row.last_name,
                seniority=row.seniority,
                city=row.city,
                state=row.state,
                address=row.address,
                dining_interests=row.dining_interests,
                interests=row.dining_interests.split(', ') if row.dining_interests else [],
                email=row.email,
                consent_email=row.consent_email,
                consent_sms=row.consent_sms
            )
            items.append(item)
        
        return DinersResponse(total=total, items=items)
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.get("/", response_model=DinersResponse)
@router.get("", response_model=DinersResponse)
async def get_diners(
    request: Request,
    city: Optional[str] = Query(None, description="Filter by city (case-insensitive)"),
    state: Optional[str] = Query(None, description="Filter by state (case-insensitive)"),
    interests: Optional[str] = Query(None, description="Comma-separated interests"),
    seniority: Optional[str] = Query(None, description="Comma-separated seniority levels"),
    match: str = Query("any", pattern="^(any|all)$", description="Interest match type: any or all"),
    channel: Optional[str] = Query(None, description="Filter by communication channel (email/sms)"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=1000, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
) -> DinersResponse:
    """
    Get filtered list of diners with pagination.
    
    Filters:
    - city: Case-insensitive partial match
    - state: Case-insensitive partial match (full names or abbreviations)
    - interests: Comma-separated list with any/all matching
    - seniority: Comma-separated seniority levels (any match)
    
    Only returns diners who have given consent for email OR SMS.
    """
    try:
        current_user_id = get_current_user_id_from_state(request)
        
        # Calculate offset
        offset = (page - 1) * pageSize
        
        # Build WHERE conditions based on channel
        if channel == "email":
            where_conditions = ["consent_email = true AND email IS NOT NULL"]
        elif channel == "sms":
            where_conditions = ["consent_sms = true AND phone IS NOT NULL"]
        else:
            # Default: show diners with consent for either channel
            where_conditions = ["(consent_email = true OR consent_sms = true)"]
        params = {}
        
        # City filter: case-insensitive ILIKE
        if city:
            where_conditions.append("city ILIKE :city")
            params["city"] = f"%{city}%"
        
        # State filter: case-insensitive partial match
        if state:
            where_conditions.append("state ILIKE :state")
            params["state"] = f"%{state}%"
        
        # Interests filter: search in the interests array field  
        if interests:
            interest_list = [interest.strip() for interest in interests.split(",") if interest.strip()]
            if interest_list:
                if match == "all":
                    # ALL: interests array contains all specified interests
                    where_conditions.append("interests @> :interests")
                    params["interests"] = interest_list
                else:
                    # ANY: interests array overlaps with specified interests
                    where_conditions.append("interests && :interests")
                    params["interests"] = interest_list
        
        # Seniority filter: search in seniority field
        if seniority:
            seniority_list = [s.strip() for s in seniority.split(",") if s.strip()]
            if seniority_list:
                # Use ANY match for seniority (OR logic)
                seniority_conditions = []
                for i, s in enumerate(seniority_list):
                    seniority_conditions.append(f"seniority ILIKE :seniority_{i}")
                    params[f"seniority_{i}"] = f"%{s}%"
                where_conditions.append(f"({' OR '.join(seniority_conditions)})")
        
        # Build WHERE clause
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Count query - using diners table which has the correct structure  
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM diners
            {where_clause}
        """).execution_options(postgresql_prepare=False)
        
        count_result = await db.execute(count_query, params)
        total = count_result.scalar()
        
        # Data query with pagination - using diners table which has the correct structure
        data_query = text(f"""
            SELECT 
                phone,
                first_name,
                last_name,
                seniority,
                city,
                state,
                address_text as address,
                CASE 
                    WHEN interests IS NOT NULL AND array_length(interests, 1) > 0 
                    THEN array_to_string(interests, ', ')
                    ELSE NULL
                END as dining_interests,
                email,
                COALESCE(consent_email, true) as consent_email,
                COALESCE(consent_sms, true) as consent_sms
            FROM diners
            {where_clause}
            ORDER BY first_name, last_name, phone
            LIMIT :limit OFFSET :offset
        """).execution_options(postgresql_prepare=False)
        
        # Add pagination params
        params.update({
            "limit": pageSize,
            "offset": offset
        })
        
        data_result = await db.execute(data_query, params)
        rows = data_result.fetchall()
        
        # Convert to response format
        items = []
        for row in rows:
            # Parse dining_interests into interests array
            interests_array = []
            if row.dining_interests:
                interests_array = [interest.strip() for interest in row.dining_interests.split(",") if interest.strip()]
            
            diner = DinerItem(
                phone=row.phone,
                first_name=row.first_name,
                last_name=row.last_name,
                seniority=row.seniority,
                city=row.city,
                state=row.state,
                address=row.address,
                dining_interests=row.dining_interests,
                interests=interests_array,  # For frontend compatibility
                email=row.email,
                consent_email=row.consent_email,
                consent_sms=row.consent_sms
            )
            items.append(diner)
        
        logger.info(f"Retrieved {len(items)} diners (total: {total}) for user {current_user_id}")
        
        return DinersResponse(
            total=total,
            items=items
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions (like 401 Unauthorized) as-is
        raise
    except Exception as e:
        logger.error(f"Error fetching diners: {type(e).__name__}: {str(e)}")
        logger.error(f"Exception details: {repr(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch diners: {type(e).__name__}: {str(e)}"
        )
