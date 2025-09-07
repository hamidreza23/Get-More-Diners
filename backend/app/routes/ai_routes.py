"""
AI-powered features routes.
Provides AI assistance for campaign content generation and audience analysis.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import logging

from ..auth import get_current_user_id
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# AI feature schemas
class CampaignContentRequest(BaseModel):
    restaurant_name: str
    cuisine_type: Optional[str] = None
    campaign_type: str  # 'promotion', 'event', 'announcement', 'seasonal'
    target_audience: Optional[str] = None
    key_message: Optional[str] = None
    channel: str  # 'email' or 'sms'
    tone: Optional[str] = "friendly"  # 'friendly', 'professional', 'casual', 'urgent'


class CampaignContentResponse(BaseModel):
    subject: Optional[str] = None
    body: str
    suggestions: List[str]
    tone_analysis: Dict[str, Any]


class AudienceAnalysisRequest(BaseModel):
    restaurant_id: str
    analysis_type: str  # 'demographic', 'interest', 'location', 'behavior'
    filters: Optional[Dict[str, Any]] = None


class AudienceAnalysisResponse(BaseModel):
    analysis_type: str
    insights: List[Dict[str, Any]]
    recommendations: List[str]
    target_segments: List[Dict[str, Any]]


@router.post("/generate-content", response_model=CampaignContentResponse)
async def generate_campaign_content(
    request: CampaignContentRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> CampaignContentResponse:
    """
    Generate AI-powered campaign content.
    
    Args:
        request: Campaign content generation request
        current_user_id: Current authenticated user ID
        
    Returns:
        CampaignContentResponse: Generated content and suggestions
    """
    try:
        # Check if OpenAI is configured
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="AI features require OpenAI API key configuration"
            )
        
        # Import OpenAI client
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI package not installed"
            )
        
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Create prompt based on request parameters
        prompt = _create_content_generation_prompt(request)
        
        # Generate content using OpenAI
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional marketing copywriter specializing in restaurant marketing campaigns. Create engaging, persuasive content that drives customer action."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        generated_content = response.choices[0].message.content
        
        # Parse the generated content
        content_parts = _parse_generated_content(generated_content, request.channel)
        
        # Generate additional suggestions
        suggestions = await _generate_content_suggestions(client, request, generated_content)
        
        return CampaignContentResponse(
            subject=content_parts.get("subject"),
            body=content_parts.get("body", generated_content),
            suggestions=suggestions,
            tone_analysis={
                "detected_tone": request.tone,
                "readability_score": "Good",
                "engagement_potential": "High"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating campaign content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate campaign content"
        )


@router.post("/analyze-audience", response_model=AudienceAnalysisResponse)
async def analyze_audience(
    request: AudienceAnalysisRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> AudienceAnalysisResponse:
    """
    Perform AI-powered audience analysis.
    
    Args:
        request: Audience analysis request
        current_user_id: Current authenticated user ID
        
    Returns:
        AudienceAnalysisResponse: Analysis insights and recommendations
    """
    try:
        # Mock implementation - in production, this would analyze actual data
        if request.analysis_type == "demographic":
            insights = [
                {"metric": "Age Range", "value": "25-45", "percentage": 65},
                {"metric": "Gender", "value": "Mixed", "female": 55, "male": 45},
                {"metric": "Income Level", "value": "Middle to High", "percentage": 70}
            ]
            recommendations = [
                "Target campaigns during lunch hours for working professionals",
                "Create family-friendly promotions for evening dining",
                "Focus on quality and experience messaging"
            ]
            target_segments = [
                {"name": "Young Professionals", "size": 35, "characteristics": ["convenience", "quality", "time-sensitive"]},
                {"name": "Families", "size": 30, "characteristics": ["value", "variety", "child-friendly"]},
                {"name": "Food Enthusiasts", "size": 25, "characteristics": ["quality", "experience", "novelty"]}
            ]
        
        elif request.analysis_type == "interest":
            insights = [
                {"category": "Fine Dining", "interest_level": 85},
                {"category": "Casual Dining", "interest_level": 70},
                {"category": "Quick Service", "interest_level": 45}
            ]
            recommendations = [
                "Emphasize culinary expertise and premium ingredients",
                "Highlight unique dishes and chef specialties",
                "Create exclusive dining experiences"
            ]
            target_segments = [
                {"name": "Culinary Adventurers", "size": 40, "characteristics": ["novelty", "quality", "experience"]},
                {"name": "Regular Diners", "size": 35, "characteristics": ["consistency", "value", "convenience"]},
                {"name": "Special Occasion", "size": 25, "characteristics": ["ambiance", "service", "memorable"]}
            ]
        
        elif request.analysis_type == "location":
            insights = [
                {"area": "Downtown", "customer_density": 40},
                {"area": "Suburbs", "customer_density": 35},
                {"area": "Business District", "customer_density": 25}
            ]
            recommendations = [
                "Target lunch promotions for business district customers",
                "Create delivery campaigns for suburban areas",
                "Focus on evening dining for downtown residents"
            ]
            target_segments = [
                {"name": "Urban Professionals", "size": 45, "characteristics": ["convenience", "quality", "time-conscious"]},
                {"name": "Suburban Families", "size": 35, "characteristics": ["value", "parking", "family-size portions"]},
                {"name": "Tourists", "size": 20, "characteristics": ["experience", "local cuisine", "recommendations"]}
            ]
        
        else:  # behavior analysis
            insights = [
                {"behavior": "Repeat Customers", "percentage": 60},
                {"behavior": "Weekend Diners", "percentage": 45},
                {"behavior": "Event Celebrators", "percentage": 30}
            ]
            recommendations = [
                "Create loyalty programs for repeat customers",
                "Develop weekend special menus and promotions",
                "Offer private dining packages for celebrations"
            ]
            target_segments = [
                {"name": "Loyal Customers", "size": 50, "characteristics": ["consistency", "familiarity", "rewards"]},
                {"name": "Occasion Diners", "size": 30, "characteristics": ["special events", "quality", "service"]},
                {"name": "Explorers", "size": 20, "characteristics": ["variety", "new experiences", "recommendations"]}
            ]
        
        return AudienceAnalysisResponse(
            analysis_type=request.analysis_type,
            insights=insights,
            recommendations=recommendations,
            target_segments=target_segments
        )
        
    except Exception as e:
        logger.error(f"Error analyzing audience: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze audience"
        )


@router.get("/content-templates")
async def get_content_templates(
    category: Optional[str] = None,
    channel: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get pre-built content templates.
    
    Args:
        category: Template category filter
        channel: Channel filter (email/sms)
        current_user_id: Current authenticated user ID
        
    Returns:
        Dict[str, Any]: Available templates
    """
    templates = {
        "email": {
            "promotion": [
                {
                    "name": "Weekend Special",
                    "subject": "🍽️ Weekend Special: 20% Off Your Favorite Dishes!",
                    "body": "Join us this weekend for an exclusive 20% discount on all menu items. Perfect time to try our chef's specialties!"
                },
                {
                    "name": "Happy Hour",
                    "subject": "🍻 Happy Hour Extended: Save on Drinks & Appetizers",
                    "body": "We've extended our happy hour! Join us Monday-Friday, 3-6 PM for discounted drinks and appetizers."
                }
            ],
            "event": [
                {
                    "name": "Live Music Night",
                    "subject": "🎵 Live Music Night This Friday!",
                    "body": "Experience great food and live music this Friday! Reserve your table now for an unforgettable evening."
                }
            ]
        },
        "sms": {
            "promotion": [
                {
                    "name": "Flash Sale",
                    "body": "🔥 FLASH SALE: 30% off appetizers today only! Show this text to claim. Valid until 9 PM."
                },
                {
                    "name": "Lunch Deal",
                    "body": "🍽️ Lunch Special: $12.99 for any entrée + drink. Available 11 AM - 3 PM. Limited time!"
                }
            ]
        }
    }
    
    # Filter by category and channel if specified
    if channel:
        templates = {channel: templates.get(channel, {})}
    
    if category:
        filtered = {}
        for ch, cats in templates.items():
            if category in cats:
                filtered[ch] = {category: cats[category]}
        templates = filtered
    
    return {
        "templates": templates,
        "categories": ["promotion", "event", "announcement", "seasonal"],
        "channels": ["email", "sms"]
    }


def _create_content_generation_prompt(request: CampaignContentRequest) -> str:
    """Create a prompt for content generation."""
    prompt = f"""
    Create a {request.channel} marketing campaign for {request.restaurant_name}.
    
    Details:
    - Cuisine: {request.cuisine_type or 'Not specified'}
    - Campaign Type: {request.campaign_type}
    - Target Audience: {request.target_audience or 'General dining customers'}
    - Key Message: {request.key_message or 'Not specified'}
    - Tone: {request.tone}
    
    Requirements:
    - {'Include both subject line and body' if request.channel == 'email' else 'Create SMS message (160 characters or less)'}
    - Make it engaging and action-oriented
    - Include a clear call-to-action
    - Use appropriate tone and language
    - Focus on the key message if provided
    
    {'Format: SUBJECT: [subject line] BODY: [email body]' if request.channel == 'email' else 'Format: [SMS message]'}
    """
    return prompt


def _parse_generated_content(content: str, channel: str) -> Dict[str, str]:
    """Parse the generated content into components."""
    if channel == "email" and "SUBJECT:" in content and "BODY:" in content:
        parts = content.split("BODY:")
        subject_part = parts[0].replace("SUBJECT:", "").strip()
        body_part = parts[1].strip()
        return {"subject": subject_part, "body": body_part}
    else:
        return {"body": content.strip()}


async def _generate_content_suggestions(client, request: CampaignContentRequest, generated_content: str) -> List[str]:
    """Generate additional content suggestions."""
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Generate 3 alternative variations or improvements for the given marketing content. Keep them brief and actionable."
                },
                {
                    "role": "user",
                    "content": f"Original content: {generated_content}\n\nProvide 3 alternative suggestions:"
                }
            ],
            max_tokens=200,
            temperature=0.8
        )
        
        suggestions_text = response.choices[0].message.content
        # Parse suggestions (simple split by line)
        suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and not s.strip().startswith('Original')]
        return suggestions[:3]  # Return max 3 suggestions
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        return [
            "Try adding urgency with time-limited offers",
            "Include social proof or customer testimonials",
            "Consider personalizing with customer name or preferences"
        ]
