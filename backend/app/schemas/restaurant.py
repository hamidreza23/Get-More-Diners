"""
Pydantic schemas for restaurant-related API operations.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RestaurantBase(BaseModel):
    """Base restaurant schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Restaurant name")
    cuisine: Optional[str] = Field(None, max_length=100, description="Type of cuisine")
    city: Optional[str] = Field(None, max_length=100, description="Restaurant city")
    state: Optional[str] = Field(None, max_length=50, description="Restaurant state")
    contact_email: Optional[str] = Field(None, description="Contact email address")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    website_url: Optional[str] = Field(None, description="Restaurant website or reservation URL")
    logo_url: Optional[str] = Field(None, description="Restaurant logo image URL")
    caption: Optional[str] = Field(None, max_length=500, description="Restaurant description or caption")


class RestaurantCreate(RestaurantBase):
    """Schema for creating a new restaurant."""
    pass


class RestaurantUpdate(BaseModel):
    """Schema for updating an existing restaurant."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cuisine: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website_url: Optional[str] = None
    logo_url: Optional[str] = None
    caption: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class RestaurantResponse(RestaurantBase):
    """Schema for restaurant API responses."""
    id: UUID
    owner_user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RestaurantListResponse(BaseModel):
    """Schema for paginated restaurant list responses."""
    restaurants: List[RestaurantResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)
