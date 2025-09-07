"""
Campaign management routes.
Handles marketing campaign creation, management, and recipient tracking.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func, join
import logging

from ..db import get_db
from ..auth import get_current_user_id
from ..schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignRecipientResponse,
    CampaignStatsResponse,
    CampaignPreviewRequest,
    CampaignSendRequest
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> CampaignResponse:
    """
    Create a new campaign.
    
    Args:
        campaign_data: Campaign creation data
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        CampaignResponse: Created campaign data
    """
    try:
        # Verify restaurant ownership
        restaurant_query = select(restaurants_table).where(
            restaurants_table.c.id == campaign_data.restaurant_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        restaurant_result = await db.execute(restaurant_query)
        restaurant = restaurant_result.fetchone()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found or access denied"
            )
        
        # Create campaign
        query = insert(campaigns_table).values(
            **campaign_data.model_dump()
        ).returning(campaigns_table)
        
        result = await db.execute(query)
        await db.commit()
        
        campaign = result.fetchone()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create campaign"
            )
        
        return CampaignResponse.model_validate(campaign)
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create campaign"
        )


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    restaurant_id: Optional[UUID] = Query(None),
    channel: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> CampaignListResponse:
    """
    List campaigns for the current user's restaurants.
    
    Args:
        restaurant_id: Filter by specific restaurant ID
        channel: Filter by channel (email/sms)
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        CampaignListResponse: List of campaigns
    """
    try:
        # Base query with restaurant ownership check
        query = select(campaigns_table).select_from(
            join(campaigns_table, restaurants_table,
                 campaigns_table.c.restaurant_id == restaurants_table.c.id)
        ).where(restaurants_table.c.owner_user_id == current_user_id)
        
        count_query = select(func.count()).select_from(
            join(campaigns_table, restaurants_table,
                 campaigns_table.c.restaurant_id == restaurants_table.c.id)
        ).where(restaurants_table.c.owner_user_id == current_user_id)
        
        # Apply filters
        conditions = []
        
        if restaurant_id:
            conditions.append(campaigns_table.c.restaurant_id == restaurant_id)
        
        if channel:
            conditions.append(campaigns_table.c.channel == channel)
        
        if conditions:
            from sqlalchemy import and_
            filter_condition = and_(*conditions)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        # Add pagination and ordering
        query = query.order_by(campaigns_table.c.created_at.desc()).offset(skip).limit(limit)
        
        # Execute queries
        result = await db.execute(query)
        campaigns = result.fetchall()
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return CampaignListResponse(
            campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaigns"
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> CampaignResponse:
    """
    Get a specific campaign by ID.
    
    Args:
        campaign_id: Campaign UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        CampaignResponse: Campaign data
    """
    try:
        query = select(campaigns_table).select_from(
            join(campaigns_table, restaurants_table,
                 campaigns_table.c.restaurant_id == restaurants_table.c.id)
        ).where(
            campaigns_table.c.id == campaign_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        result = await db.execute(query)
        campaign = result.fetchone()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return CampaignResponse.model_validate(campaign)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign"
        )


@router.get("/{campaign_id}/recipients", response_model=List[CampaignRecipientResponse])
async def get_campaign_recipients(
    campaign_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> List[CampaignRecipientResponse]:
    """
    Get recipients for a specific campaign.
    
    Args:
        campaign_id: Campaign UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        List[CampaignRecipientResponse]: Campaign recipients
    """
    try:
        # Verify campaign ownership
        campaign_query = select(campaigns_table).select_from(
            join(campaigns_table, restaurants_table,
                 campaigns_table.c.restaurant_id == restaurants_table.c.id)
        ).where(
            campaigns_table.c.id == campaign_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        campaign_result = await db.execute(campaign_query)
        if not campaign_result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get recipients with diner information
        query = select(
            campaign_recipients_table,
            diners_table.c.first_name,
            diners_table.c.last_name,
            diners_table.c.email,
            diners_table.c.phone
        ).select_from(
            join(campaign_recipients_table, diners_table,
                 campaign_recipients_table.c.diner_id == diners_table.c.id)
        ).where(
            campaign_recipients_table.c.campaign_id == campaign_id
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        recipients = result.fetchall()
        
        return [CampaignRecipientResponse.model_validate(r) for r in recipients]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign recipients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign recipients"
        )


@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(
    campaign_id: UUID,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> CampaignStatsResponse:
    """
    Get campaign statistics.
    
    Args:
        campaign_id: Campaign UUID
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        CampaignStatsResponse: Campaign statistics
    """
    try:
        # Verify campaign ownership
        campaign_query = select(campaigns_table).select_from(
            join(campaigns_table, restaurants_table,
                 campaigns_table.c.restaurant_id == restaurants_table.c.id)
        ).where(
            campaigns_table.c.id == campaign_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.fetchone()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get recipient statistics
        stats_query = select([
            func.count().label('total_recipients'),
            func.sum(func.case([(campaign_recipients_table.c.delivery_status == 'simulated_sent', 1)], else_=0)).label('sent_count'),
            func.sum(func.case([(campaign_recipients_table.c.delivery_status == 'simulated_failed', 1)], else_=0)).label('failed_count')
        ]).where(campaign_recipients_table.c.campaign_id == campaign_id)
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.fetchone()
        
        return CampaignStatsResponse(
            campaign_id=campaign_id,
            total_recipients=stats.total_recipients or 0,
            sent_count=stats.sent_count or 0,
            failed_count=stats.failed_count or 0,
            delivery_rate=(stats.sent_count or 0) / (stats.total_recipients or 1) * 100
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign statistics"
        )


@router.post("/{campaign_id}/preview")
async def preview_campaign(
    campaign_id: UUID,
    preview_request: CampaignPreviewRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Preview campaign with audience filtering.
    
    Args:
        campaign_id: Campaign UUID
        preview_request: Preview request parameters
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        Dict[str, Any]: Preview results
    """
    try:
        # Verify campaign ownership
        campaign_query = select(campaigns_table).select_from(
            join(campaigns_table, restaurants_table,
                 campaigns_table.c.restaurant_id == restaurants_table.c.id)
        ).where(
            campaigns_table.c.id == campaign_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.fetchone()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Apply audience filters from campaign and preview request
        query = select(diners_table)
        conditions = []
        
        # Apply filters based on audience_filter_json from campaign
        if campaign.audience_filter_json:
            # This would implement the JSON filter logic
            # For now, a placeholder implementation
            pass
        
        # Apply additional filters from preview request
        if preview_request.city:
            conditions.append(diners_table.c.city.ilike(f"%{preview_request.city}%"))
        
        if preview_request.interests:
            for interest in preview_request.interests:
                conditions.append(diners_table.c.interests.contains([interest]))
        
        if conditions:
            from sqlalchemy import and_
            query = query.where(and_(*conditions))
        
        # Limit preview results
        query = query.limit(preview_request.limit or 10)
        
        result = await db.execute(query)
        preview_recipients = result.fetchall()
        
        return {
            "campaign_id": campaign_id,
            "estimated_recipients": len(preview_recipients),
            "preview_recipients": [
                {
                    "id": str(r.id),
                    "first_name": r.first_name,
                    "last_name": r.last_name,
                    "email": r.email,
                    "city": r.city,
                    "interests": r.interests
                }
                for r in preview_recipients
            ],
            "channel": campaign.channel,
            "subject": campaign.subject,
            "body_preview": campaign.body[:200] + "..." if len(campaign.body) > 200 else campaign.body
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview campaign"
        )


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: UUID,
    send_request: CampaignSendRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Send campaign to recipients (simulated).
    
    Args:
        campaign_id: Campaign UUID
        send_request: Send request parameters
        current_user_id: Current authenticated user ID
        db: Database session
        
    Returns:
        Dict[str, Any]: Send results
    """
    try:
        # Verify campaign ownership
        campaign_query = select(campaigns_table).select_from(
            join(campaigns_table, restaurants_table,
                 campaigns_table.c.restaurant_id == restaurants_table.c.id)
        ).where(
            campaigns_table.c.id == campaign_id,
            restaurants_table.c.owner_user_id == current_user_id
        )
        
        campaign_result = await db.execute(campaign_query)
        campaign = campaign_result.fetchone()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get target audience (simplified implementation)
        # In a real implementation, this would apply complex filtering logic
        audience_query = select(diners_table).limit(send_request.max_recipients or 1000)
        audience_result = await db.execute(audience_query)
        recipients = audience_result.fetchall()
        
        # Create campaign recipients (simulated delivery)
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            # Simulate delivery success/failure (90% success rate)
            import random
            delivery_status = "simulated_sent" if random.random() > 0.1 else "simulated_failed"
            
            recipient_data = {
                "campaign_id": campaign_id,
                "diner_id": recipient.id,
                "delivery_status": delivery_status,
                "preview_payload_json": {
                    "channel": campaign.channel,
                    "subject": campaign.subject,
                    "body": campaign.body,
                    "recipient_name": f"{recipient.first_name} {recipient.last_name}",
                    "sent_at": "2024-01-01T12:00:00Z"  # Placeholder timestamp
                }
            }
            
            insert_query = insert(campaign_recipients_table).values(**recipient_data)
            await db.execute(insert_query)
            
            if delivery_status == "simulated_sent":
                sent_count += 1
            else:
                failed_count += 1
        
        await db.commit()
        
        return {
            "campaign_id": campaign_id,
            "total_recipients": len(recipients),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "delivery_rate": (sent_count / len(recipients)) * 100 if recipients else 0,
            "status": "completed"
        }
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error sending campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send campaign"
        )


# Import table definitions from models
from ..models import campaigns_table, campaign_recipients_table, restaurants_table
