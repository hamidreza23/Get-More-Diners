"""
Campaigns API with audience building and recipient tracking.
Implements the exact campaign logic specified.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, Field
import logging
import json

from ..db import get_db
from ..middleware import get_current_user_id_from_state

logger = logging.getLogger(__name__)

router = APIRouter()


class CampaignFilters(BaseModel):
    """Filters for audience selection."""
    city: Optional[str] = None
    state: Optional[str] = None
    interests: Optional[List[str]] = None
    match: str = Field("any", pattern="^(any|all)$")


class CampaignCreate(BaseModel):
    """Request schema for creating campaigns."""
    channel: str = Field(..., pattern="^(email|sms)$")
    name: str = Field(..., min_length=1, max_length=255, description="Campaign name")
    subject: Optional[str] = Field(None, description="Required for email campaigns")
    body: str = Field(..., min_length=1)
    filters: CampaignFilters


class CampaignPreview(BaseModel):
    """Preview of a campaign recipient."""
    diner_id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    rendered_message: str


class CampaignCreateResponse(BaseModel):
    """Response for campaign creation."""
    campaignId: str
    audienceSize: int
    previews: List[CampaignPreview]


class CampaignListItem(BaseModel):
    """Campaign item in list response."""
    id: str
    created_at: str
    channel: str
    name: Optional[str]
    subject: Optional[str]
    body: str
    status: str  # 'active', 'paused', 'stopped'
    audience_size: int
    sent_count: int
    failed_count: int
    click_rate: float  # Simulated CTR for demo


class CampaignDetail(BaseModel):
    """Detailed campaign information."""
    id: str
    created_at: str
    channel: str
    subject: Optional[str]
    body: str
    filters: Dict[str, Any]
    recipients: List[Dict[str, Any]]


@router.post("/", response_model=CampaignCreateResponse)
@router.post("", response_model=CampaignCreateResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    # request: Request, # Removed for testing
    db: AsyncSession = Depends(get_db)
) -> CampaignCreateResponse:
    """
    Create a new campaign with audience building and recipient tracking.
    
    Steps:
    1. Find user's restaurant (must exist)
    2. Build audience query respecting consent
    3. Insert campaign row
    4. Insert recipients with simulated delivery
    5. Return campaign info with previews
    """
    try:
        # Use hardcoded user ID for testing
        current_user_id = "235009c5-e2c6-4236-bb26-7c3640718a3f"
        
        # Validate email campaigns have subjects
        if campaign_data.channel == "email" and not campaign_data.subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email campaigns must have a subject"
            )
        
        # Step 1: Find user's restaurant (must exist)
        restaurant_query = text("""
            SELECT id FROM public.restaurants 
            WHERE owner_user_id = :user_id
            LIMIT 1
        """)
        
        restaurant_result = await db.execute(restaurant_query, {"user_id": current_user_id})
        restaurant = restaurant_result.fetchone()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must create a restaurant before creating campaigns"
            )
        
        restaurant_id = restaurant.id
        
        # Step 2: Build audience query that respects consent
        audience_query, audience_params = build_audience_query(campaign_data)
        
        # Get audience count and sample
        audience_result = await db.execute(audience_query, audience_params)
        audience_members = audience_result.fetchall()
        
        audience_size = len(audience_members)
        
        if audience_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No audience members match the specified filters"
            )
        
        # Step 3: Insert campaign row
        campaign_id = str(uuid4())
        
        insert_campaign_query = text("""
            INSERT INTO public.campaigns (
                id, restaurant_id, channel, name, subject, body, audience_filter_json, created_at
            ) VALUES (
                :id, :restaurant_id, :channel, :name, :subject, :body, :filters, NOW()
            )
        """)
        
        await db.execute(insert_campaign_query, {
            "id": campaign_id,
            "restaurant_id": str(restaurant_id),
            "channel": campaign_data.channel,
            "name": campaign_data.name,
            "subject": campaign_data.subject,
            "body": campaign_data.body,
            "filters": json.dumps(campaign_data.filters.dict())
        })
        
        # Step 4: Insert recipients with simulated delivery
        previews = []
        
        for i, diner in enumerate(audience_members):
            recipient_id = str(uuid4())
            
            # Render message with fake {FirstName}
            rendered_message = render_message(
                campaign_data, 
                diner.first_name or "Friend"
            )
            
            # Create preview payload
            preview_payload = {
                "channel": campaign_data.channel,
                "subject": campaign_data.subject,
                "body": rendered_message,
                "recipient_name": f"{diner.first_name or ''} {diner.last_name or ''}".strip(),
                "sent_at": "2024-01-01T12:00:00Z"  # Simulated timestamp
            }
            
            # Insert recipient record (using proper diner_id)
            insert_recipient_query = text("""
                INSERT INTO public.campaign_recipients (
                    id, campaign_id, diner_id, delivery_status, preview_payload_json
                ) VALUES (
                    :id, :campaign_id, :diner_id, :status, :payload
                )
            """)
            
            await db.execute(insert_recipient_query, {
                "id": recipient_id,
                "campaign_id": campaign_id,
                "diner_id": diner.id,  # Use diner.id instead of diner.phone
                "status": "simulated_sent",  # All simulated as sent for demo
                "payload": json.dumps(preview_payload)
            })
            
            # Add to previews (first 5 only)
            if i < 5:
                previews.append(CampaignPreview(
                    diner_id=diner.phone,  # Use phone as identifier
                    first_name=diner.first_name,
                    last_name=diner.last_name,
                    email=diner.email,
                    phone=diner.phone,
                    rendered_message=rendered_message
                ))
        
        # Commit transaction
        await db.commit()
        
        return CampaignCreateResponse(
            campaignId=campaign_id,
            audienceSize=audience_size,
            previews=previews
        )
        
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


@router.get("/", response_model=List[CampaignListItem])
@router.get("", response_model=List[CampaignListItem])
async def list_campaigns(
    # request: Request, # Removed for testing
    db: AsyncSession = Depends(get_db)
) -> List[CampaignListItem]:
    """
    List campaigns for the authenticated user's restaurant.
    
    Returns array with campaign info and audience size.
    """
    try:
        # Use hardcoded user ID for testing
        current_user_id = "235009c5-e2c6-4236-bb26-7c3640718a3f"
        
        # Get campaigns with detailed metrics
        query = text("""
            SELECT 
                c.id,
                c.created_at,
                c.channel,
                c.name,
                c.subject,
                c.body,
                COALESCE(c.status, 'active') as status,
                COUNT(cr.id) as audience_size,
                COUNT(CASE WHEN cr.delivery_status = 'simulated_sent' THEN 1 END) as sent_count,
                COUNT(CASE WHEN cr.delivery_status = 'simulated_failed' THEN 1 END) as failed_count
            FROM public.campaigns c
            JOIN public.restaurants r ON r.id = c.restaurant_id
            LEFT JOIN public.campaign_recipients cr ON cr.campaign_id = c.id
            WHERE r.owner_user_id = :user_id
            GROUP BY c.id, c.created_at, c.channel, c.name, c.subject, c.body, c.status
            ORDER BY c.created_at DESC
        """)
        
        result = await db.execute(query, {"user_id": current_user_id})
        campaigns = result.fetchall()
        
        return [
            CampaignListItem(
                id=str(campaign.id),
                created_at=campaign.created_at.isoformat() if campaign.created_at else "",
                channel=campaign.channel,
                name=campaign.name or (campaign.subject or f"{campaign.channel.title()} Campaign"),
                subject=campaign.subject,
                body=campaign.body,
                status=campaign.status or 'active',
                audience_size=campaign.audience_size or 0,
                sent_count=campaign.sent_count or 0,
                failed_count=campaign.failed_count or 0,
                click_rate=round((campaign.sent_count or 0) * 0.15, 1)  # Simulate 15% CTR for demo
            )
            for campaign in campaigns
        ]
        
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaigns"
        )


@router.patch("/{campaign_id}/status")
async def update_campaign_status(
    campaign_id: str,
    status_data: dict,
    # request: Request, # Removed for testing
    db: AsyncSession = Depends(get_db)
):
    """
    Update campaign status (active, paused, stopped).
    """
    try:
        # Use hardcoded user ID for testing
        current_user_id = "235009c5-e2c6-4236-bb26-7c3640718a3f"
        
        new_status = status_data.get("status")
        if new_status not in ["active", "paused", "stopped"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be 'active', 'paused', or 'stopped'"
            )
        
        # Verify campaign ownership
        verify_query = text("""
            SELECT c.id FROM public.campaigns c
            JOIN public.restaurants r ON r.id = c.restaurant_id
            WHERE c.id = :campaign_id AND r.owner_user_id = :user_id
        """)
        
        verify_result = await db.execute(verify_query, {
            "campaign_id": campaign_id,
            "user_id": current_user_id
        })
        
        if not verify_result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Update campaign status
        update_query = text("""
            UPDATE public.campaigns 
            SET status = :status
            WHERE id = :campaign_id
        """)
        
        await db.execute(update_query, {
            "campaign_id": campaign_id,
            "status": new_status
        })
        
        await db.commit()
        
        return {"message": f"Campaign status updated to {new_status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating campaign status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update campaign status"
        )


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> CampaignDetail:
    """
    Get campaign details with filters and first 25 recipients.
    """
    try:
        current_user_id = get_current_user_id_from_state(request)
        
        # Get campaign info
        campaign_query = text("""
            SELECT 
                c.id,
                c.created_at,
                c.channel,
                c.subject,
                c.body,
                c.audience_filter_json
            FROM public.campaigns c
            JOIN public.restaurants r ON r.id = c.restaurant_id
            WHERE c.id = :campaign_id AND r.owner_user_id = :user_id
        """)
        
        campaign_result = await db.execute(campaign_query, {
            "campaign_id": campaign_id,
            "user_id": current_user_id
        })
        campaign = campaign_result.fetchone()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Get first 25 recipients with preview payloads
        recipients_query = text("""
            SELECT 
                cr.diner_id,
                cr.delivery_status,
                cr.preview_payload_json,
                d.first_name,
                d.last_name,
                d.email,
                d.phone
            FROM public.campaign_recipients cr
            JOIN public.diners d ON d.id = cr.diner_id
            WHERE cr.campaign_id = :campaign_id
            ORDER BY cr.id
            LIMIT 25
        """)
        
        recipients_result = await db.execute(recipients_query, {"campaign_id": campaign_id})
        recipients = recipients_result.fetchall()
        
        # Format recipients
        recipient_list = []
        for recipient in recipients:
            preview_payload = json.loads(recipient.preview_payload_json) if recipient.preview_payload_json else {}
            
            recipient_list.append({
                "diner_id": recipient.diner_id,  # Use proper diner_id
                "first_name": recipient.first_name,
                "last_name": recipient.last_name,
                "email": recipient.email,
                "phone": recipient.phone,
                "delivery_status": recipient.delivery_status,
                "preview_payload": preview_payload
            })
        
        # Parse filters
        filters = json.loads(campaign.audience_filter_json) if campaign.audience_filter_json else {}
        
        return CampaignDetail(
            id=str(campaign.id),
            created_at=campaign.created_at.isoformat() if campaign.created_at else "",
            channel=campaign.channel,
            subject=campaign.subject,
            body=campaign.body,
            filters=filters,
            recipients=recipient_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve campaign"
        )


def build_audience_query(campaign_data: CampaignCreate) -> tuple:
    """
    Build audience query based on channel consent and filters.
    
    Args:
        campaign_data: Campaign creation data
        
    Returns:
        tuple: (query, params)
    """
    # Base consent conditions
    if campaign_data.channel == "email":
        consent_condition = "consent_email = true AND email IS NOT NULL"
    else:  # sms
        consent_condition = "consent_sms = true AND phone IS NOT NULL"
    
    # Build filter conditions
    where_conditions = [consent_condition]
    params = {}
    
    filters = campaign_data.filters
    
    # City filter
    if filters.city:
        where_conditions.append("city ILIKE :city")
        params["city"] = f"%{filters.city}%"
    
    # State filter
    if filters.state:
        where_conditions.append("state = :state")
        params["state"] = filters.state.upper()
    
    # Interests filter
    if filters.interests:
        if filters.match == "all":
            # ALL: interests @> array (contains all specified interests)
            where_conditions.append("interests @> :interests")
        else:
            # ANY: interests && array (has any of the specified interests)
            where_conditions.append("interests && :interests")
        params["interests"] = filters.interests
    
            # Build final query
    where_clause = " AND ".join(where_conditions)
    
    query = text(f"""
        SELECT id, phone, first_name, last_name, email
        FROM public.diners
        WHERE {where_clause}
        ORDER BY phone
    """)
    
    return query, params


@router.delete("/{campaign_id}", response_model=dict)
async def delete_campaign(
    campaign_id: str,
    # request: Request, # Removed for testing
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Delete a campaign and all its recipients.
    """
    try:
        # Use hardcoded user ID for testing
        current_user_id = "235009c5-e2c6-4236-bb26-7c3640718a3f"
        
        # Verify campaign belongs to user
        campaign_query = text("""
            SELECT c.id
            FROM public.campaigns c
            JOIN public.restaurants r ON r.id = c.restaurant_id
            WHERE c.id = :campaign_id AND r.owner_user_id = :user_id
        """)
        
        result = await db.execute(campaign_query, {
            "campaign_id": campaign_id,
            "user_id": current_user_id
        })
        
        campaign = result.fetchone()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        # Delete campaign recipients first (foreign key constraint)
        delete_recipients_query = text("""
            DELETE FROM public.campaign_recipients
            WHERE campaign_id = :campaign_id
        """)
        
        await db.execute(delete_recipients_query, {
            "campaign_id": campaign_id
        })
        
        # Delete campaign
        delete_campaign_query = text("""
            DELETE FROM public.campaigns
            WHERE id = :campaign_id
        """)
        
        await db.execute(delete_campaign_query, {
            "campaign_id": campaign_id
        })
        
        await db.commit()
        
        return {"message": "Campaign deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete campaign"
        )


def render_message(campaign_data: CampaignCreate, first_name: str) -> str:
    """
    Render message with personalization.
    
    Args:
        campaign_data: Campaign data
        first_name: Recipient's first name
        
    Returns:
        str: Rendered message
    """
    message = campaign_data.body
    
    # Replace personalization tokens
    message = message.replace("{FirstName}", first_name)
    message = message.replace("{firstname}", first_name)
    message = message.replace("{FIRSTNAME}", first_name.upper())
    
    return message
