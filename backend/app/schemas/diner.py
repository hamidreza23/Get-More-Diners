"""
Pydantic schemas for diner-related API operations.
"""

from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class DinerBase(BaseModel):
    """Base diner schema with common fields."""
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    seniority: Optional[str] = Field(
        None, 
        description="Seniority level: 'director', 'vp', 'head', 'c_suite', or custom value"
    )
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State")
    address_text: Optional[str] = Field(None, max_length=500, description="Full address")
    interests: Optional[List[str]] = Field(
        default_factory=list,
        description="List of interests: 'fine_dining', 'pubs', 'coffee_shops', etc."
    )
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    consent_email: bool = Field(default=True, description="Email marketing consent")
    consent_sms: bool = Field(default=True, description="SMS marketing consent")


class DinerCreate(DinerBase):
    """Schema for creating a new diner."""
    
    @classmethod
    def validate_interests(cls, v):
        """Validate interest values."""
        valid_interests = {
            'fine_dining', 'casual_dining', 'fast_food', 'coffee_shops', 
            'bars', 'pubs', 'food_trucks', 'ethnic_cuisine', 'vegan', 
            'vegetarian', 'healthy_eating', 'desserts', 'breakfast'
        }
        if v:
            for interest in v:
                if interest not in valid_interests:
                    # Allow custom interests but log them
                    pass
        return v


class DinerUpdate(BaseModel):
    """Schema for updating an existing diner."""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    seniority: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    address_text: Optional[str] = Field(None, max_length=500)
    interests: Optional[List[str]] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    consent_email: Optional[bool] = None
    consent_sms: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class DinerResponse(DinerBase):
    """Schema for diner API responses."""
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class DinerListResponse(BaseModel):
    """Schema for paginated diner list responses."""
    diners: List[DinerResponse]
    total: int
    skip: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class DinerSearchParams(BaseModel):
    """Schema for advanced diner search parameters."""
    cities: Optional[List[str]] = Field(None, description="Filter by cities")
    states: Optional[List[str]] = Field(None, description="Filter by states")
    interests: Optional[List[str]] = Field(None, description="Filter by interests")
    seniority_levels: Optional[List[str]] = Field(None, description="Filter by seniority levels")
    email_consent: Optional[bool] = Field(None, description="Filter by email consent")
    sms_consent: Optional[bool] = Field(None, description="Filter by SMS consent")
    fuzzy_city: Optional[str] = Field(None, description="Fuzzy city search using trigrams")
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum records to return")

    model_config = ConfigDict(extra="forbid")


class DinerImportRequest(BaseModel):
    """Schema for bulk diner import requests."""
    file_format: str = Field("csv", description="Import file format")
    has_header: bool = Field(True, description="Whether CSV has header row")
    column_mapping: dict = Field(
        default_factory=lambda: {
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "phone": "phone",
            "city": "city",
            "state": "state"
        },
        description="Mapping of CSV columns to diner fields"
    )
    batch_size: int = Field(100, ge=1, le=1000, description="Import batch size")

    model_config = ConfigDict(extra="forbid")


class DinerImportResponse(BaseModel):
    """Schema for diner import results."""
    total_processed: int
    successful_imports: int
    failed_imports: int
    errors: List[str]
    import_id: str

    model_config = ConfigDict(from_attributes=True)
