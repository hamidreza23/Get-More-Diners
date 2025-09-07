"""
Pydantic schemas for campaign-related API operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class ChannelType(str, Enum):
    """Supported campaign channels."""
    EMAIL = "email"
    SMS = "sms"


class DeliveryStatus(str, Enum):
    """Campaign delivery statuses."""
    SIMULATED_SENT = "simulated_sent"
    SIMULATED_FAILED = "simulated_failed"


class CampaignBase(BaseModel):
    """Base campaign schema with common fields."""
    restaurant_id: UUID = Field(..., description="Restaurant ID that owns this campaign")
    channel: ChannelType = Field(..., description="Campaign channel (email/sms)")
    subject: Optional[str] = Field(None, max_length=255, description="Email subject line")
    body: str = Field(..., min_length=1, max_length=5000, description="Campaign content")
    audience_filter_json: Optional[Dict[str, Any]] = Field(
        None, 
        description="JSON object defining audience filtering criteria"
    )


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""
    
    def validate_subject_for_email(self):
        """Validate that email campaigns have subjects."""
        if self.channel == ChannelType.EMAIL and not self.subject:
            raise ValueError("Email campaigns must have a subject line")
        return self


class CampaignUpdate(BaseModel):
    """Schema for updating an existing campaign."""
    channel: Optional[ChannelType] = None
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = Field(None, min_length=1, max_length=5000)
    audience_filter_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")


class CampaignResponse(CampaignBase):
    """Schema for campaign API responses."""
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignListResponse(BaseModel):
    """Schema for paginated campaign list responses."""
    campaigns: List[CampaignResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class CampaignRecipientResponse(BaseModel):
    """Schema for campaign recipient responses."""
    id: UUID
    campaign_id: UUID
    diner_id: UUID
    delivery_status: DeliveryStatus
    preview_payload_json: Optional[Dict[str, Any]] = None
    
    # Diner information (joined from diners table)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CampaignStatsResponse(BaseModel):
    """Schema for campaign statistics."""
    campaign_id: UUID
    total_recipients: int
    sent_count: int
    failed_count: int
    delivery_rate: float  # Percentage

    model_config = ConfigDict(from_attributes=True)


class CampaignPreviewRequest(BaseModel):
    """Schema for campaign preview requests."""
    city: Optional[str] = Field(None, description="Preview for specific city")
    interests: Optional[List[str]] = Field(None, description="Preview for specific interests")
    limit: int = Field(10, ge=1, le=50, description="Number of preview recipients")

    model_config = ConfigDict(extra="forbid")


class CampaignSendRequest(BaseModel):
    """Schema for campaign send requests."""
    confirm_send: bool = Field(..., description="Confirmation flag for sending")
    max_recipients: Optional[int] = Field(
        None, 
        ge=1, 
        le=10000, 
        description="Maximum number of recipients"
    )
    test_mode: bool = Field(default=True, description="Send in test mode (simulated)")

    model_config = ConfigDict(extra="forbid")


class AudienceFilterCriteria(BaseModel):
    """Schema for audience filtering criteria."""
    cities: Optional[List[str]] = Field(None, description="Target cities")
    states: Optional[List[str]] = Field(None, description="Target states")
    interests: Optional[List[str]] = Field(None, description="Target interests")
    seniority_levels: Optional[List[str]] = Field(None, description="Target seniority levels")
    age_range: Optional[Dict[str, int]] = Field(
        None, 
        description="Age range filter {min: 18, max: 65}"
    )
    email_consent_required: bool = Field(
        default=True, 
        description="Require email consent for email campaigns"
    )
    sms_consent_required: bool = Field(
        default=True, 
        description="Require SMS consent for SMS campaigns"
    )
    exclude_recent_recipients: bool = Field(
        default=False, 
        description="Exclude recipients who received campaigns recently"
    )
    recent_days_threshold: int = Field(
        default=7, 
        ge=1, 
        le=365, 
        description="Days to consider for recent recipient exclusion"
    )

    model_config = ConfigDict(extra="forbid")


class CampaignTemplate(BaseModel):
    """Schema for campaign templates."""
    name: str = Field(..., description="Template name")
    category: str = Field(..., description="Template category")
    channel: ChannelType = Field(..., description="Template channel")
    subject: Optional[str] = Field(None, description="Template subject")
    body: str = Field(..., description="Template body")
    variables: List[str] = Field(
        default_factory=list, 
        description="Available template variables"
    )
    tags: List[str] = Field(default_factory=list, description="Template tags")

    model_config = ConfigDict(from_attributes=True)


class CampaignTemplateListResponse(BaseModel):
    """Schema for campaign template list responses."""
    templates: List[CampaignTemplate]
    categories: List[str]
    channels: List[str]

    model_config = ConfigDict(from_attributes=True)
