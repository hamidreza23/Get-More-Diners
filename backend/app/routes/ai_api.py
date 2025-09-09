"""
AI-powered content generation API with agentic AI capabilities.
Implements Offer Writer, Conciseness Checker, and Audience Advisor agents.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
import asyncio
from pydantic import BaseModel, Field, validator
import logging

from ..dependencies import get_current_user_id
from ..config import get_settings
from ..db import get_db
from ..ai_agents import (
    OfferWriter,
    ConcisenessChecker,
    AudienceAdvisor,
    OfferRequest as AgentOfferRequest,
    Channel,
    OfferContent
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Initialize AI agents
offer_writer = OfferWriter(openai_api_key=settings.openai_api_key)
conciseness_checker = ConcisenessChecker()
audience_advisor = AudienceAdvisor(openai_api_key=settings.openai_api_key)


class OfferRequest(BaseModel):
    """Request schema for AI offer generation."""
    cuisine: str = Field(..., min_length=1, max_length=100, description="Type of cuisine")
    tone: str = Field(..., description="Tone of the message")
    channel: str = Field(..., pattern="^(email|sms)$", description="Channel: email or sms")
    goal: str = Field(..., min_length=1, max_length=200, description="Goal of the campaign")
    constraints: Optional[str] = Field(None, max_length=500, description="Additional constraints")
    output_format: Optional[str] = Field("text", pattern="^(text|json|html)$", description="Output format: text, json, or html")
    include_html: Optional[bool] = Field(False, description="Whether to include HTML-formatted version")
    
    @validator('tone')
    def validate_tone(cls, v):
        """Validate tone values."""
        valid_tones = {'friendly', 'professional', 'urgent', 'casual', 'formal', 'playful'}
        if v.lower() not in valid_tones:
            # Allow custom tones but normalize common ones
            tone_mapping = {
                'fun': 'playful',
                'serious': 'professional',
                'business': 'professional',
                'relaxed': 'casual'
            }
            v = tone_mapping.get(v.lower(), v)
        return v.lower()


class EmailOfferResponse(BaseModel):
    """Response schema for email offers."""
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body")


class SMSOfferResponse(BaseModel):
    """Response schema for SMS offers."""
    body: str = Field(..., description="SMS body")


class OfferResponse(BaseModel):
    """Unified response schema for offers."""
    channel: str
    content: Dict[str, str]
    html_content: Optional[str] = Field(None, description="HTML-formatted version of the content")
    json_structure: Optional[Dict[str, Any]] = Field(None, description="JSON-structured content data")
    preview: Dict[str, Any]
    metadata: Dict[str, Any]


class AudienceAdviceRequest(BaseModel):
    """Request schema for audience advice."""
    city: str = Field(..., min_length=1, max_length=100, description="Restaurant city")
    state: str = Field(..., min_length=2, max_length=50, description="Restaurant state")
    cuisine: str = Field(..., min_length=1, max_length=100, description="Restaurant cuisine type")
    daypart: Optional[str] = Field(None, description="Target time period (breakfast, lunch, dinner, late_night)")
    
    @validator('daypart')
    def validate_daypart(cls, v):
        """Validate daypart values."""
        if v is None:
            return v
        valid_dayparts = {'breakfast', 'lunch', 'dinner', 'late_night', 'brunch', 'happy_hour'}
        if v.lower() not in valid_dayparts:
            # Normalize common variations
            daypart_mapping = {
                'morning': 'breakfast',
                'noon': 'lunch',
                'evening': 'dinner',
                'night': 'late_night',
                'afternoon': 'lunch'
            }
            v = daypart_mapping.get(v.lower(), v)
        return v.lower()


class AudienceAdviceResponse(BaseModel):
    """Response schema for audience advice."""
    suggested_interests: List[str]
    rationale: str
    confidence_score: float
    metadata: Dict[str, Any]


# -------- Food Image (Demo) --------
class FoodImageRequest(BaseModel):
    dish_name: str = Field(..., min_length=2, max_length=100, description="Name of the dish")
    ingredients: List[str] | str = Field(..., description="List of ingredients or a comma-separated string")
    style: Optional[str] = Field("natural", description="Rendering style: natural, vivid, rustic, gourmet")
    size: Optional[str] = Field("768x768", pattern=r"^(512x512|768x768|1024x1024)$", description="Image size")
    variations: Optional[int] = Field(1, ge=1, le=4, description="Number of images to generate")


class FoodImageResponse(BaseModel):
    images: List[str]  # data URLs or URLs
    prompt: str
    metadata: Dict[str, Any]


@router.post("/offer", response_model=OfferResponse)
async def generate_offer(
    request_data: OfferRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> OfferResponse:
    """
    Generate AI-powered marketing offer using the Offer Writer and Conciseness Checker agents.
    
    This endpoint implements a two-stage agentic AI process:
    1. Offer Writer: Generates initial content using AI or templates
    2. Conciseness Checker: Post-processes to enforce constraints and quality
    
    Args:
        request_data: Offer generation parameters
        current_user_id: Authenticated user ID from JWT
        
    Returns:
        OfferResponse: Generated and processed content with metadata
    """
    try:
        # current_user_id is provided via dependency
        logger.info(f"Generating {request_data.channel} offer for user {current_user_id}")
        
        # Get restaurant details
        restaurant_query = text("""
            SELECT name, contact_email, contact_phone, website_url
            FROM restaurants
            WHERE owner_user_id = :user_id
            LIMIT 1
        """)
        result = await db.execute(restaurant_query, {"user_id": current_user_id})
        restaurant_row = result.fetchone()
        
        restaurant_details = {
            "name": restaurant_row.name if restaurant_row else "Our Restaurant",
            "email": restaurant_row.contact_email if restaurant_row else None,
            "phone": restaurant_row.contact_phone if restaurant_row else None,
            "website_url": restaurant_row.website_url if restaurant_row else None
        }
        
        # Convert request to agent format
        agent_request = AgentOfferRequest(
            cuisine=request_data.cuisine,
            tone=request_data.tone,
            channel=Channel.EMAIL if request_data.channel == "email" else Channel.SMS,
            goal=request_data.goal,
            constraints=request_data.constraints,
            restaurant_details=restaurant_details
        )
        
        # Stage 1: Generate content with Offer Writer agent
        output_format = getattr(request_data, 'output_format', 'text')
        # Temporarily disable JSON format until parsing is fully reliable
        if output_format == 'json':
            output_format = 'text'
            logger.info("JSON format temporarily disabled, using text format")
        # AI demo mode or upstream not configured → fast mock
        if settings.ai_demo_mode or not settings.openai_api_key:
            logger.info("AI_DEMO_MODE active or OpenAI not configured; returning fallback offer")
            return create_fallback_offer(request_data, current_user_id)

        # Otherwise, call upstream with timeout
        try:
            raw_content = await asyncio.wait_for(
                offer_writer.generate_offer(agent_request, output_format),
                timeout=8.0
            )
        except Exception as e:
            logger.error(f"Offer writer failed or timed out: {e}")
            return create_fallback_offer(request_data, current_user_id)
        logger.info(f"Offer Writer generated content: {len(raw_content.body)} chars, format: {output_format}")
        
        # Stage 2: Post-process with Conciseness Checker agent
        processed_content = conciseness_checker.process_content(
            raw_content, 
            enforce_firstname=True
        )
        logger.info(f"Conciseness Checker processed content: {len(processed_content.body)} chars")
        logger.info(f"Processed content preview: {processed_content.body[:200]}...")
        
        # Create response format with filled placeholders
        if processed_content.channel == Channel.EMAIL:
            # Fill placeholders with actual restaurant data
            filled_subject = (processed_content.subject or "Special Offer")
            filled_body = processed_content.body
            
            # Ensure content is properly formatted (not raw JSON)
            if filled_body.startswith('{') and 'paragraphs' in filled_body:
                logger.warning("Raw JSON detected in body, attempting to parse")
                try:
                    import json
                    json_data = json.loads(filled_body)
                    if 'paragraphs' in json_data and isinstance(json_data['paragraphs'], list):
                        # Filter out empty paragraphs and join with proper spacing
                        clean_paragraphs = [p.strip() for p in json_data['paragraphs'] if p and p.strip()]
                        filled_body = '\n\n'.join(clean_paragraphs)
                    elif 'body' in json_data:
                        filled_body = json_data['body']
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from body")
            
            # Additional check for any remaining JSON structure
            if '{"' in filled_body or '"paragraphs"' in filled_body or '"subject"' in filled_body:
                logger.warning("JSON structure still present, using fallback content")
                filled_body = f"Hello {{FirstName}}! We have an exciting update about our {request_data.cuisine} cuisine. Visit us soon for a delightful dining experience!"
            
            if restaurant_details:
                filled_subject = filled_subject.replace("{RestaurantName}", restaurant_details.get('name', 'Restaurant'))
                filled_subject = filled_subject.replace("{Website}", restaurant_details.get('website_url', ''))
                
                filled_body = filled_body.replace("{RestaurantName}", restaurant_details.get('name', 'Restaurant'))
                filled_body = filled_body.replace("{Website}", restaurant_details.get('website_url', ''))
                filled_body = filled_body.replace("{Phone}", restaurant_details.get('phone', ''))
                filled_body = filled_body.replace("{Email}", restaurant_details.get('email', ''))
            
            content = {
                "subject": filled_subject,
                "body": filled_body
            }
            logger.info(f"Final email content - Subject: {filled_subject[:50]}..., Body: {filled_body[:100]}...")
        else:
            # Fill SMS placeholders
            filled_body = processed_content.body
            
            # Ensure SMS content is properly formatted
            if filled_body.startswith('{') and 'message' in filled_body:
                logger.warning("Raw JSON detected in SMS body, attempting to parse")
                try:
                    import json
                    json_data = json.loads(filled_body)
                    if 'message' in json_data:
                        filled_body = json_data['message']
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from SMS body")
            
            # Additional check for any remaining JSON structure in SMS
            if '{"' in filled_body or '"message"' in filled_body:
                logger.warning("JSON structure still present in SMS, using fallback content")
                filled_body = f"Hi {{FirstName}}! Try our {request_data.cuisine} today!"
            
            if restaurant_details:
                filled_body = filled_body.replace("{RestaurantName}", restaurant_details.get('name', 'Restaurant'))
                filled_body = filled_body.replace("{Website}", restaurant_details.get('website_url', ''))
                filled_body = filled_body.replace("{Phone}", restaurant_details.get('phone', ''))
            
            content = {"body": filled_body}
            logger.info(f"Final SMS content: {filled_body[:100]}...")
        
        # Create preview with validation info and restaurant data
        preview = create_content_preview(processed_content, restaurant_details)
        
        # Combine metadata
        metadata = processed_content.metadata.copy()
        metadata.update({
            "user_id": current_user_id,
            "request_cuisine": request_data.cuisine,
            "request_tone": request_data.tone,
            "request_goal": request_data.goal,
            "agent_pipeline": ["offer_writer", "conciseness_checker"],
            "openai_available": bool(settings.openai_api_key)
        })
        
        # Prepare response with optional HTML and JSON structure
        html_content = None
        json_structure = None
        
        # Include HTML content if available
        if processed_content.html_formatted:
            html_content = processed_content.html_formatted
        
        # Include JSON structure if available  
        if processed_content.json_structured:
            json_structure = processed_content.json_structured
        
        return OfferResponse(
            channel=request_data.channel,
            content=content,
            html_content=html_content,
            json_structure=json_structure,
            preview=preview,
            metadata=metadata
        )
            
    except Exception as e:
        logger.error(f"Error in agentic offer generation: {e}", exc_info=True)
        
        # Return fallback content
        fallback_content = create_fallback_offer(request_data, current_user_id)
        return fallback_content


@router.post("/audience-advice", response_model=AudienceAdviceResponse)
async def get_audience_advice(
    request_data: AudienceAdviceRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> AudienceAdviceResponse:
    """
    Get AI-powered audience targeting suggestions using the Audience Advisor agent.
    
    This endpoint provides intelligent recommendations for customer interest targeting
    based on location, cuisine type, and timing context.
    
    Args:
        request_data: Audience advice request parameters
        current_user_id: Authenticated user ID from JWT
        
    Returns:
        AudienceAdviceResponse: Suggested interests with rationale
    """
    try:
        logger.info(f"Generating audience advice for {request_data.city}, {request_data.state}")
        
        # Generate advice using Audience Advisor agent
        advice = await audience_advisor.suggest_interests(
            city=request_data.city,
            state=request_data.state,
            cuisine=request_data.cuisine,
            daypart=request_data.daypart
        )
        
        # Create metadata
        metadata = {
            "user_id": current_user_id,
            "request_location": f"{request_data.city}, {request_data.state}",
            "request_cuisine": request_data.cuisine,
            "request_daypart": request_data.daypart,
            "ai_generated": bool(settings.openai_api_key),
            "agent_used": "audience_advisor"
        }
        
        return AudienceAdviceResponse(
            suggested_interests=advice.suggested_interests,
            rationale=advice.rationale,
            confidence_score=advice.confidence_score,
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"Error generating audience advice: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate audience advice"
        )


def create_content_preview(content: OfferContent, restaurant_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create comprehensive content preview with sample data showing proper formatting.
    
    Args:
        content: Processed content from agents
        
    Returns:
        Dict with preview, validation info, and formatted samples
    """
    # Generate sample customer names dynamically
    sample_names = ["Alex", "Jordan", "Casey", "Taylor", "Morgan"]
    
    # Get restaurant details for placeholder filling
    restaurant_name = restaurant_details.get('name', 'Restaurant') if restaurant_details else 'Restaurant'
    restaurant_website = restaurant_details.get('website_url', '') if restaurant_details else ''
    restaurant_phone = restaurant_details.get('phone', '') if restaurant_details else ''
    restaurant_email = restaurant_details.get('email', '') if restaurant_details else ''
    
    preview = {
        "channel": content.channel.value,
        "length_validation": {
            "email_subject_limit": 60,
            "email_body_limit": 500,
            "sms_limit": 160
        },
        "quality_checks": {
            "has_firstname_token": content.metadata.get("has_firstname_token", False),
            "processed_by_conciseness_checker": content.metadata.get("processed", False),
            "all_caps_fixed": True,  # Conciseness checker always fixes this
            "has_multiple_paragraphs": content.body.count('\n\n') >= 1 if content.channel.value == "email" else True,
            "has_call_to_action": any(word in content.body.lower() for word in ['reserve', 'book', 'visit', 'order', 'call', 'try'])
        },
        "formatting": {
            "paragraph_count": len([p for p in content.body.split('\n\n') if p.strip()]) if content.channel.value == "email" else 1,
            "line_break_count": content.body.count('\n'),
            "has_proper_spacing": '\n\n' in content.body if content.channel.value == "email" else True
        }
    }
    
    if content.channel == Channel.EMAIL and content.subject:
        preview.update({
            "subject": content.subject,
            "subject_length": len(content.subject),
            "subject_within_limit": len(content.subject) <= 60,
            "body": content.body,
            "body_length": len(content.body),
            "body_within_limit": len(content.body) <= 400
        })
        
        # Add HTML preview with sample data and filled placeholders
        if content.html_formatted:
            # Fill placeholders with actual restaurant data
            filled_html = content.html_formatted
            filled_html = filled_html.replace("{RestaurantName}", restaurant_name)
            filled_html = filled_html.replace("{Website}", restaurant_website)
            filled_html = filled_html.replace("{Phone}", restaurant_phone)
            filled_html = filled_html.replace("{Email}", restaurant_email)
            
            preview["html_preview"] = {
                "raw_html": content.html_formatted,
                "sample_rendered": filled_html.replace("{FirstName}", "Alex"),
                "multiple_samples": [
                    {
                        "name": name,
                        "subject": content.subject.replace("{FirstName}", name).replace("{RestaurantName}", restaurant_name) if content.subject else None,
                        "html_content": filled_html.replace("{FirstName}", name)
                    }
                    for name in sample_names[:3]
                ]
            }
        
        # Add text formatting analysis with filled placeholders
        filled_body = content.body
        filled_body = filled_body.replace("{RestaurantName}", restaurant_name)
        filled_body = filled_body.replace("{Website}", restaurant_website)
        filled_body = filled_body.replace("{Phone}", restaurant_phone)
        filled_body = filled_body.replace("{Email}", restaurant_email)
        
        preview["text_formatting"] = {
            "paragraphs": [p.strip() for p in filled_body.split('\n\n') if p.strip()],
            "has_greeting": "{FirstName}" in filled_body.split('\n\n')[0] if filled_body.split('\n\n') else False,
            "has_signature": any(word in filled_body.lower() for word in ['regards', 'sincerely', 'best']),
            "cta_paragraph": filled_body.split('\n\n')[-1] if '\n\n' in filled_body else filled_body,
            "filled_with_restaurant_data": True
        }
        
    else:
        preview.update({
            "body": content.body,
            "body_length": len(content.body),
            "body_within_limit": len(content.body) <= 160
        })
        
        # SMS preview with sample data and filled placeholders
        filled_sms_body = content.body
        filled_sms_body = filled_sms_body.replace("{RestaurantName}", restaurant_name)
        filled_sms_body = filled_sms_body.replace("{Website}", restaurant_website)
        filled_sms_body = filled_sms_body.replace("{Phone}", restaurant_phone)
        
        preview["sms_samples"] = [
            {
                "name": name,
                "message": filled_sms_body.replace("{FirstName}", name)
            }
            for name in sample_names[:3]
        ]
    
    # Add comprehensive personalization preview with filled placeholders
    filled_subject = (content.subject or "").replace("{RestaurantName}", restaurant_name).replace("{Website}", restaurant_website)
    filled_body_preview = content.body.replace("{RestaurantName}", restaurant_name).replace("{Website}", restaurant_website).replace("{Phone}", restaurant_phone).replace("{Email}", restaurant_email)
    
    if "{FirstName}" in filled_subject:
        preview["subject_personalized"] = filled_subject.replace("{FirstName}", "Alex")
    if "{FirstName}" in filled_body_preview:
        preview["body_personalized"] = filled_body_preview.replace("{FirstName}", "Alex")
    
    # Add formatting demonstration with filled placeholders
    preview["format_demonstration"] = {
        "raw_with_tokens": {
            "subject": content.subject,
            "body": content.body,
            "shows_line_breaks": repr(content.body)  # Shows actual \n characters
        },
        "rendered_sample": {
            "subject": filled_subject.replace("{FirstName}", "Alex"),
            "body": filled_body_preview.replace("{FirstName}", "Alex"),
            "html_version": filled_html.replace("{FirstName}", "Alex") if content.html_formatted else None
        },
        "restaurant_data_used": {
            "name": restaurant_name,
            "website": restaurant_website,
            "phone": restaurant_phone,
            "email": restaurant_email
        }
    }
    
    # Add constraint effectiveness analysis
    if content.metadata.get('json_structured'):
        preview["constraint_analysis"] = {
            "detected_tone": content.metadata.get('tone'),
            "detected_cta": content.metadata.get('call_to_action'),
            "json_structure_available": True,
            "structured_data": content.json_structured
        }
    
    return preview


def create_fallback_offer(request_data: OfferRequest, user_id: str) -> OfferResponse:
    """
    Create fallback offer when agent processing fails.
    
    Args:
        request_data: Original request
        user_id: User ID
        
    Returns:
        OfferResponse: Safe fallback content
    """
    if request_data.channel == "email":
        content = {
            "subject": f"Special {request_data.cuisine} Offer",
            "body": f"Hi {{FirstName}}, enjoy our delicious {request_data.cuisine} cuisine today! Visit us for an amazing dining experience."
        }
        preview = {
            "channel": "email",
            "subject": content["subject"],
            "subject_length": len(content["subject"]),
            "body": content["body"],
            "body_length": len(content["body"]),
            "body_personalized": content["body"].replace("{FirstName}", "John"),
            "fallback_used": True
        }
    else:
        content = {
            "body": f"Hi {{FirstName}}! Try our amazing {request_data.cuisine[:20]} today! Special offer - visit us now!"
        }
        preview = {
            "channel": "sms",
            "body": content["body"],
            "body_length": len(content["body"]),
            "body_personalized": content["body"].replace("{FirstName}", "John"),
            "fallback_used": True
        }
    
    return OfferResponse(
        channel=request_data.channel,
        content=content,
        preview=preview,
        metadata={
            "user_id": user_id,
            "fallback_used": True,
            "reason": "Agent processing failed",
            "ai_generated": False,
            "agent_pipeline": ["fallback_only"]
        }
    )


# Backwards compatibility endpoint (optional)
@router.get("/health")
async def ai_health_check() -> Dict[str, Any]:
    """
    Check the health and availability of AI services.
    
    Returns:
        Dict with service status information
    """
    status_info = {
        "offer_writer_available": True,
        "conciseness_checker_available": True,
        "audience_advisor_available": True,
        "openai_configured": bool(settings.openai_api_key),
        "agents_operational": True
    }
    
    # Test basic agent functionality
    try:
        # Quick test of conciseness checker
        test_content = OfferContent(
            subject="Test",
            body="Test message",
            channel=Channel.SMS,
            metadata={}
        )
        conciseness_checker.process_content(test_content)
        
    except Exception as e:
        logger.warning(f"Agent health check failed: {e}")
        status_info["agents_operational"] = False
        status_info["error"] = str(e)
    
    return status_info


@router.post("/food-image", response_model=FoodImageResponse)
async def generate_food_image(
    req: FoodImageRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> FoodImageResponse:
    """
    Demo: Generate a food image from a dish name and ingredients using OpenAI images API.
    Falls back to a placeholder image when OpenAI is not configured.
    """
    # Normalize ingredients
    if isinstance(req.ingredients, str):
        ingredients_list = [i.strip() for i in req.ingredients.split(",") if i.strip()]
    else:
        ingredients_list = [i.strip() for i in req.ingredients if i and i.strip()]

    style_map = {
        "natural": "natural lighting, realistic colors",
        "vivid": "vivid colors, dramatic lighting",
        "rustic": "rustic presentation, wooden table, cozy ambiance",
        "gourmet": "gourmet plating, minimal background, studio lighting",
    }
    style_desc = style_map.get((req.style or "natural").lower(), "natural lighting, realistic colors")

    ingredients_phrase = ", ".join(ingredients_list) if ingredients_list else "fresh ingredients"
    prompt = (
        f"Professional food photography of {req.dish_name}. "
        f"Ingredients: {ingredients_phrase}. "
        f"Style: {style_desc}. Overhead or 45-degree angle, shallow depth of field, appetizing, high detail, no text, no watermark."
    )

    images: List[str] = []
    used_model = None
    try:
        if settings.openai_api_key:
            from openai import AsyncOpenAI  # type: ignore
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            used_model = "gpt-image-1"
            n = max(1, min(req.variations or 1, 4))
            size = req.size or "768x768"
            resp = await client.images.generate(
                model=used_model,
                prompt=prompt,
                n=n,
                size=size,
                response_format="b64_json",
            )
            for d in resp.data:
                b64 = d.b64_json
                if b64:
                    images.append(f"data:image/png;base64,{b64}")
        else:
            # Fallback placeholder (demo)
            placeholder = "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=1024"
            images = [placeholder]
            used_model = None
    except Exception as e:
        logger.error(f"Food image generation failed: {e}")
        placeholder = "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=1024"
        images = [placeholder]

    return FoodImageResponse(
        images=images,
        prompt=prompt,
        metadata={
            "model": used_model,
            "style": req.style or "natural",
            "size": req.size or "768x768",
            "variations": req.variations or 1,
            "ingredients": ingredients_list,
            "ai_generated": bool(settings.openai_api_key),
            "user_id": current_user_id,
        },
    )
