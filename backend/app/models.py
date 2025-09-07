"""
SQLAlchemy models placeholder.

Note: Since we're using the schema.sql from Supabase directly,
these models are primarily for reference and type hints.
The actual tables are created and managed via Supabase SQL.
"""

from sqlalchemy import Table, Column, String, Text, DateTime, Boolean, UUID, ARRAY
from sqlalchemy.sql import func
from .db import Base

# Note: These are placeholder table definitions for IDE support and type hints
# The actual tables are created via the Supabase schema.sql file

# Restaurants table
restaurants_table = Table(
    'restaurants',
    Base.metadata,
    Column('id', UUID, primary_key=True),
    Column('owner_user_id', UUID, nullable=False),
    Column('name', Text, nullable=False),
    Column('cuisine', Text),
    Column('city', Text),
    Column('state', Text),
    Column('contact_email', Text),
    Column('contact_phone', Text),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

# Diners table
diners_table = Table(
    'diners',
    Base.metadata,
    Column('id', UUID, primary_key=True),
    Column('first_name', Text),
    Column('last_name', Text),
    Column('seniority', Text),
    Column('city', Text),
    Column('state', Text),
    Column('address_text', Text),
    Column('interests', ARRAY(Text)),
    Column('email', Text),
    Column('phone', Text),
    Column('consent_email', Boolean, default=True),
    Column('consent_sms', Boolean, default=True),
)

# Campaigns table
campaigns_table = Table(
    'campaigns',
    Base.metadata,
    Column('id', UUID, primary_key=True),
    Column('restaurant_id', UUID, nullable=False),
    Column('channel', Text, nullable=False),
    Column('subject', Text),
    Column('body', Text, nullable=False),
    Column('audience_filter_json', Text),  # JSONB in PostgreSQL
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

# Campaign recipients table
campaign_recipients_table = Table(
    'campaign_recipients',
    Base.metadata,
    Column('id', UUID, primary_key=True),
    Column('campaign_id', UUID, nullable=False),
    Column('diner_id', UUID, nullable=False),
    Column('delivery_status', Text, nullable=False),
    Column('preview_payload_json', Text),  # JSONB in PostgreSQL
)
