"""
Agentic AI functions for restaurant marketing automation.
Refactored for clean structure, reliable newline handling, and strict length control.
- Guaranteed multi-line EMAIL bodies (real newlines), single-line SMS.
- Robust SUBJECT/BODY parsing with defensive fallbacks.
- Clear prompt builder with explicit formatting constraints.
- Minimal, readable utilities.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# -----------------------
# Enums & Data Models
# -----------------------

class Channel(Enum):
    EMAIL = "email"
    SMS = "sms"


class Tone(Enum):
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    URGENT = "urgent"
    PLAYFUL = "playful"
    FORMAL = "formal"


@dataclass
class OfferRequest:
    cuisine: str
    tone: str
    channel: Channel
    goal: str
    constraints: Optional[str] = None
    restaurant_details: Optional[Dict[str, Any]] = None


@dataclass
class OfferContent:
    subject: Optional[str]
    body: str
    channel: Channel
    metadata: Dict[str, Any]
    html_formatted: Optional[str] = None  # New field for HTML-formatted content
    json_structured: Optional[Dict[str, Any]] = None  # New field for JSON-structured content


@dataclass
class AudienceAdvice:
    suggested_interests: List[str]
    rationale: str
    confidence_score: float


# -----------------------
# Utilities
# -----------------------

class TextUtils:
    EMAIL_SUBJECT_LIMIT = 60
    EMAIL_BODY_LIMIT = 500
    SMS_LIMIT = 160

    @staticmethod
    def normalize_newlines(text: str, keep_linebreaks: bool) -> str:
        """Convert a variety of newline markers to actual newlines.
        Handles: "\\n", raw backslash-n, "/n", "<br>", "<br/>", CRLF.
        Optionally flattens to one line for SMS.
        """
        if not text:
            return ""
        t = text
        # common web-ish markers → \n
        # Replace HTML breaks first
        t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
        # Literal sequences
        t = t.replace("\\r\\n", "\n")
        t = t.replace("\r\n", "\n")
        t = t.replace("\\n", "\n")      # the two-char sequence backslash+n
        t = t.replace("/n", "\n")         # sometimes users type /n
        
        # Collapse spaces per line
        lines = [re.sub(r"[ \t]+", " ", ln.strip()) for ln in t.split("\n")]
        lines = [ln for ln in lines if ln]
        if keep_linebreaks:
            return "\n".join(lines)
        return " ".join(lines)

    @staticmethod
    def cap_length(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        cut = text[: max_len - 3]
        cut = cut.rsplit(" ", 1)[0] if " " in cut else cut
        return cut + "..."

    @staticmethod
    def fix_all_caps(text: str) -> str:
        allowed = {"NEW", "SALE", "FREE", "NOW", "TODAY", "URGENT", "EXCLUSIVE", "LIMITED"}
        if not text:
            return text
        lines = text.split("\n")
        fixed_lines: List[str] = []
        for line in lines:
            words = line.split(" ")
            out_words: List[str] = []
            for w in words:
                clean = re.sub(r"[^\w]", "", w)
                if clean.isupper() and len(clean) > 1 and clean not in allowed:
                    out_words.append(w.capitalize())
                else:
                    out_words.append(w)
            fixed_lines.append(" ".join(out_words))
        return "\n".join(fixed_lines)

    @staticmethod
    def ensure_firstname_once(text: str, limit: int) -> str:
        count = text.count("{FirstName}")
        if count == 1:
            return text
        if count > 1:
            first = text.find("{FirstName}")
            before = text[: first + len("{FirstName}")]
            after = text[first + len("{FirstName}") :].replace("{FirstName}", "")
            return (before + after).strip()
        # Absent → try prefix if it fits
        cand = f"{{FirstName}}, {text}"
        return cand if len(cand) <= limit else text

    @staticmethod
    def smart_truncate_with_cta(text: str, max_len: int, multiline: bool) -> str:
        if len(text) <= max_len:
            return text
        # Try to preserve the last sentence (CTA-ish)
        sentences = re.split(r"(?<=[.!?])\s+", text) if multiline else text.split(". ")
        if len(sentences) > 1:
            last = sentences[-1]
            space_left = max_len - len(last) - (2 if multiline else 2)
            if space_left > 40:  # room for a meaningful intro
                start = text[:space_left]
                start = start.rsplit(" ", 1)[0]
                joiner = "\n\n" if multiline else ". "
                candidate = f"{start}{joiner}{last}"
                if len(candidate) <= max_len:
                    return candidate
        return TextUtils.cap_length(text, max_len)

    @staticmethod
    def tidy_subject(subject: str) -> str:
        subject = re.sub(r"\s+", " ", (subject or "").strip())
        return TextUtils.cap_length(subject, TextUtils.EMAIL_SUBJECT_LIMIT)


# -----------------------
# Prompt Builder
# -----------------------

class PromptBuilder:
    @staticmethod
    def system(channel: Channel, output_format: str = "text") -> str:
        if channel == Channel.EMAIL:
            if output_format == "json":
                return (
                    "You are a professional restaurant marketing copywriter.\n"
                    "Create compelling EMAIL campaigns that drive orders and bookings.\n\n"
                    "OUTPUT RULES (MANDATORY):\n"
                    "- Subject: 40-60 characters, engaging and clear\n"
                    "- Body: Array of paragraphs with proper structure\n"
                    "- Each paragraph should be 1-2 sentences maximum\n"
                    "- Include exactly ONE clear call-to-action in the final paragraph\n"
                    "- Use warm, appetizing language that creates urgency\n"
                    "- Include {FirstName} token exactly once in the greeting\n"
                    "- DO NOT include signature elements (Best regards, contact info) in paragraphs\n"
                    "- Keep paragraphs focused on content, not contact information\n\n"
                    "STRICT JSON FORMAT (NO DEVIATIONS):\n"
                    '{\n'
                    '  "subject": "<subject text>",\n'
                    '  "paragraphs": [\n'
                    '    "<greeting paragraph with {FirstName}>",\n'
                    '    "<main content paragraph>",\n'
                    '    "<call-to-action paragraph>"\n'
                    '  ],\n'
                    '  "tone": "<detected emotional tone>",\n'
                    '  "call_to_action": "<main CTA verb/action>"\n'
                    '}\n\n'
                    "CRITICAL: Each paragraph should be clean content only. No signatures, contact info, or 'Best regards' in the paragraphs array."
                )
            else:
                return (
                    "You are a professional restaurant marketing copywriter.\n"
                    "Create compelling EMAIL campaigns that drive orders and bookings.\n\n"
                    "OUTPUT RULES (MANDATORY):\n"
                    "- Subject: 40-60 characters, engaging and clear\n"
                    "- Body: 2-3 short paragraphs with REAL line breaks between them\n"
                    "- Each paragraph should be 1-2 sentences maximum\n"
                    "- Include exactly ONE clear call-to-action in the final paragraph\n"
                    "- Use warm, appetizing language that creates urgency\n"
                    "- Include {FirstName} token exactly once in the greeting\n"
                    "- NEVER include instruction text in your output\n\n"
                    "STRICT FORMAT (NO DEVIATIONS):\n"
                    "SUBJECT: <subject text>\n"
                    "BODY: <paragraph 1>\n\n<paragraph 2>\n\n<call-to-action paragraph>\n"
                )
        # SMS
        if output_format == "json":
            return (
                "Create a restaurant SMS. Max 160 chars TOTAL.\n"
                "Include ONE clear call-to-action and {FirstName} token.\n"
                "Use warm, urgent language. Be concise and compelling.\n\n"
                "STRICT JSON FORMAT:\n"
                '{\n'
                '  "message": "<SMS text with {FirstName}>",\n'
                '  "character_count": <number>,\n'
                '  "call_to_action": "<main CTA verb>"\n'
                '}'
            )
        else:
            return (
                "Create a restaurant SMS. Max 160 chars TOTAL.\n"
                "Include ONE clear call-to-action and {FirstName} token.\n"
                "Use warm, urgent language. Be concise and compelling.\n"
                "Output ONLY the SMS text - no labels or formatting.\n"
            )

    @staticmethod
    def user(request: OfferRequest, output_format: str = "text") -> str:
        # Resolve restaurant details first for downstream use
        rd = request.restaurant_details or {}

        # Process constraints intelligently to extract actionable requirements
        constraints_text = ""
        cta_instruction = ""
        if request.constraints:
            constraints = request.constraints.lower()

            # Time-sensitive urgency
            if any(word in constraints for word in ["time limit", "today", "urgent", "limited time", "this week", "ends soon", "hurry"]):
                constraints_text += "\nUrgency: Use time-sensitive language (today only, limited-time, ends soon)."

            # Call-to-action handling with website integration
            if any(phrase in constraints for phrase in ["call-to-action", "cta", "reserve", "book", "visit", "order"]):
                if rd.get("website_url"):
                    cta_instruction = f"\nCall-to-Action: Use strong action verbs and include the reservation/order link: {rd['website_url']}"
                else:
                    cta_instruction = "\nCall-to-Action: Use strong action verbs (Reserve, Book, Visit, Call, Order) with clear next steps."
                constraints_text += cta_instruction

            # Promotional content
            if any(word in constraints for word in ["promote", "new", "special", "offer", "discount", "deal", "seasonal"]):
                constraints_text += "\nPromotion: Highlight special offers, new items, or exclusive deals prominently."

            # Special events or holidays
            if any(word in constraints for word in ["holiday", "celebration", "event", "special occasion", "anniversary", "brunch", "happy hour"]):
                constraints_text += "\nEvent: Incorporate celebratory language and specific occasion messaging."

        # Build concise restaurant context
        bits = []
        if rd.get("name"):
            bits.append(rd.get("name"))
        if rd.get("city"):
            bits.append(rd.get("city"))
        if rd.get("phone"):
            bits.append(rd.get("phone"))
        ctx = ("\nRestaurant context: " + ", ".join(bits)) if bits else ""
        if rd.get("website_url"):
            ctx += f"\nReservation/Order URL: {rd['website_url']}"

        # Add comprehensive context about all parameters
        comprehensive_context = f"""

COMPREHENSIVE CONTEXT:
• CUISINE TYPE: {request.cuisine} — Use authentic {request.cuisine.lower()} dishes and language
• TONE: {request.tone} — Maintain this tone consistently
• CHANNEL: {request.channel.value.upper()} — Optimize for this channel
• GOAL: {request.goal} — Focus copy to achieve this goal
• CONSTRAINTS: {request.constraints or 'None specified'} — Follow the requirements
• RESTAURANT: {rd.get('name', 'Restaurant')} — Personalize for this establishment"""

        head = (
            f"Create a {request.channel.value.upper()} for a {request.cuisine} restaurant.\n"
            f"Goal: {request.goal}\n"
            f"Tone: {request.tone}{constraints_text}{comprehensive_context}{ctx}"
        )
        if request.channel == Channel.EMAIL:
            website_example = ""
            if rd.get("website_url"):
                website_example = f"\n\nReserve at {rd['website_url']}"

            if output_format == "json":
                return head + (
                    f"\n\nOUTPUT FORMAT (STRICT JSON):\n"  # structured for internal parsing
                    "{\n"
                    "  \"subject\": \"<engaging subject 40-60 chars>\",\n"
                    "  \"paragraphs\": [\n"
                    "    \"<greeting with {FirstName}>\",\n"
                    f"    \"<main content about {request.cuisine} and {request.goal}>\",\n"
                    f"    \"<call-to-action paragraph>{website_example}\"\n"
                    "  ],\n"
                    "  \"tone\": \"<detected tone>\",\n"
                    "  \"call_to_action\": \"<main action verb>\"\n"
                    "}\n\n"
                    "Rules: No signatures in paragraphs; use real newlines inside paragraphs only if needed."
                )
            else:
                return head + (
                    f"\n\nOUTPUT FORMAT (STRICT TEXT):\n"
                    "SUBJECT: <subject text>\n"
                    "BODY: <greeting with {FirstName}>\n\n"
                    f"<main content about {request.cuisine} and {request.goal}>\n\n"
                    f"<call-to-action paragraph>{website_example}\n"
                )
        return head


# -----------------------
# Parsing
# -----------------------

class Parser:
    @staticmethod
    def parse_email(generated: str) -> Tuple[Optional[str], str]:
        if not generated:
            return None, ""
        raw = (generated or "").replace("\r\n", "\n").strip()
        # Strict SUBJECT/BODY capture
        m = re.search(r"^\s*SUBJECT:\s*(.+?)\s*$", raw, re.IGNORECASE | re.MULTILINE)
        n = re.search(r"^\s*BODY:\s*(.+)\Z", raw, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        subject = m.group(1).strip() if m else None
        body = n.group(1).strip() if n else raw
        # Normalize subject & body newlines
        subject = TextUtils.tidy_subject(subject) if subject else None
        body = TextUtils.normalize_newlines(body, keep_linebreaks=True)
        # Ensure proper email formatting with multiple paragraphs
        if body.count("\n") < 1 and len(body) > 80:
            # Split into paragraphs at logical points
            sentences = re.split(r'(?<=[.!?])\s+', body)
            if len(sentences) >= 3:
                # First paragraph: greeting + main message
                first_para = sentences[0]
                # Second paragraph: details/benefits
                second_para = ' '.join(sentences[1:-1])
                # Third paragraph: call to action
                third_para = sentences[-1]
                body = f"{first_para}\n\n{second_para}\n\n{third_para}"
            elif len(sentences) >= 2:
                # Two paragraphs: main message + call to action
                first_para = sentences[0]
                second_para = ' '.join(sentences[1:])
                body = f"{first_para}\n\n{second_para}"
        return subject, body


# -----------------------
# Offer Writer
# -----------------------

class OfferWriter:
    EMAIL_SUBJECT_LIMIT = TextUtils.EMAIL_SUBJECT_LIMIT
    EMAIL_BODY_LIMIT = TextUtils.EMAIL_BODY_LIMIT
    SMS_LIMIT = TextUtils.SMS_LIMIT

    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.client = None
        self.html_formatter = None
        if openai_api_key:
            try:
                from openai import AsyncOpenAI  # type: ignore
                self.client = AsyncOpenAI(api_key=openai_api_key)
                self.html_formatter = HTMLFormatter(openai_api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"OpenAI client unavailable; falling back to templates. Error: {e}")
        else:
            logger.warning("No OpenAI API key provided; using templates only")

    async def generate_offer(self, request: OfferRequest, output_format: str = "text") -> OfferContent:
        self._validate_request(request)
        try:
            if self.client:
                logger.info(f"Using AI generation path with {output_format} format")
                content = await self._generate_with_ai(request, output_format)
            else:
                logger.info("Using AI fallback path")
                content = await self._generate_with_template(request)
        except Exception as e:
            logger.error(f"AI generation error; using AI fallback. Details: {e}")
            content = await self._generate_with_template(request)
        
        # Add HTML formatting if available/requested
        content = await self._add_formatting(content, output_format)
        
        return self._finalize(content, request)

    # ----- AI path -----
    async def _generate_with_ai(self, request: OfferRequest, output_format: str = "text") -> OfferContent:
        system_prompt = PromptBuilder.system(request.channel, output_format)
        user_prompt = PromptBuilder.user(request, output_format)
        logger.info(f"Starting AI generation for {request.channel.value} campaign")
        logger.info(f"System prompt length: {len(system_prompt)}")
        logger.info(f"User prompt length: {len(user_prompt)}")
        subject: Optional[str] = None
        body: str = ""
        try:
            resp = await self.client.chat.completions.create(  # type: ignore[attr-defined]
                model="gpt-4o",  # Use better model for more intelligent content
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=200,
                temperature=0.7,
                timeout=30,
            )
            out = (resp.choices[0].message.content or "").strip()
            logger.info(f"AI response received, length: {len(out)}")
            
            # Clean up any instruction text that might be included
            out = self._clean_instruction_text(out)
            
            # Parse based on output format
            json_metadata = None
            if output_format == "json":
                if request.channel == Channel.EMAIL:
                    subject, body, json_metadata = JSONStructureParser.parse_json_email(out)
                    # For JSON format, don't add signature here - it should be handled separately
                else:
                    body, json_metadata = JSONStructureParser.parse_json_sms(out)
                    subject = None
            else:
                if request.channel == Channel.EMAIL:
                    subject, body = Parser.parse_email(out)
                else:
                    # SMS must be single line
                    subject = None
                    body = TextUtils.normalize_newlines(out, keep_linebreaks=False)
            
            # Safety check: ensure body is not raw JSON
            if body and body.strip().startswith('{') and ('paragraphs' in body or 'message' in body):
                logger.warning("Raw JSON detected in body, falling back to text parsing")
                if request.channel == Channel.EMAIL:
                    subject, body = Parser.parse_email(out)
                else:
                    body = TextUtils.normalize_newlines(out, keep_linebreaks=False)
                    subject = None
                json_metadata = None
            
            # Additional safety check: if body still contains JSON structure, force text parsing
            if body and ('{"' in body or '"paragraphs"' in body or '"subject"' in body):
                logger.warning("JSON structure still present in body, forcing text parsing")
                if request.channel == Channel.EMAIL:
                    subject, body = Parser.parse_email(out)
                else:
                    body = TextUtils.normalize_newlines(out, keep_linebreaks=False)
                    subject = None
                json_metadata = None
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            logger.error(f"Request details: channel={request.channel}, cuisine={request.cuisine}")
            return self._generate_with_template(request)
        # Only add signature for non-JSON formats or when JSON doesn't include it
        if output_format != "json" or not json_metadata:
            body = self._append_signature(body, request.restaurant_details, request.channel)
        
        # Final cleanup to remove any instruction text and ensure proper formatting
        body = self._final_cleanup(body)
        
        # Validate that constraints were followed
        body = self._validate_constraints_fulfillment(body, request)
        
        # Combine metadata
        metadata = {
            "ai_generated": True,
            "model": "gpt-4o",
            "tone": request.tone,
            "goal": request.goal,
            "output_format": output_format,
        }
        
        # Add JSON metadata if available
        if json_metadata:
            metadata.update(json_metadata)
        
        return OfferContent(
            subject=subject,
            body=body,
            channel=request.channel,
            metadata=metadata,
        )

    # ----- AI Fallback path -----
    async def _generate_with_template(self, request: OfferRequest) -> OfferContent:
        """
        Generate AI-powered fallback content when main AI generation fails.
        This replaces the old hardcoded template system.
        """
        try:
            if self.client:
                logger.info("Using AI fallback generation")
                return await self._generate_ai_fallback(request)
            else:
                logger.warning("No AI client available for fallback generation")
                return self._generate_emergency_fallback(request)
        except Exception as e:
            logger.error(f"AI fallback generation failed: {e}")
            return self._generate_emergency_fallback(request)
    
    async def _generate_ai_fallback(self, request: OfferRequest) -> OfferContent:
        """Generate AI-powered fallback content when main AI fails."""
        try:
            # Create a simplified prompt for fallback generation
            fallback_prompt = f"""
            Create a {request.channel.value} for a {request.cuisine} restaurant.
            Goal: {request.goal}
            Tone: {request.tone}
            Constraints: {request.constraints or 'None'}
            
            Make it engaging and authentic. Include {{FirstName}} token.
            
            {"Format as JSON with subject and paragraphs array" if request.channel == Channel.EMAIL else "Keep under 160 characters"}
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a restaurant marketing expert. Create compelling content."},
                    {"role": "user", "content": fallback_prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            content = response.choices[0].message.content or ""
            
            if request.channel == Channel.EMAIL:
                if "{" in content and "}" in content:  # JSON format
                    subject, body, _ = JSONStructureParser.parse_json_email(content)
                else:
                    subject, body = Parser.parse_email(content)
            else:
                body = TextUtils.normalize_newlines(content, keep_linebreaks=False)
                subject = None
            
            # Apply signature and cleanup (fallback always gets signature)
            body = self._append_signature(body, request.restaurant_details, request.channel)
            body = self._final_cleanup(body)
            body = self._validate_constraints_fulfillment(body, request)
            
            return OfferContent(
                subject=subject,
                body=body,
                channel=request.channel,
                metadata={"ai_generated": True, "fallback_used": True, "model": "gpt-4o"}
            )
            
        except Exception as e:
            logger.error(f"AI fallback generation failed: {e}")
            return self._generate_emergency_fallback(request)
    
    def _generate_emergency_fallback(self, request: OfferRequest) -> OfferContent:
        """Ultimate fallback when all AI generation fails."""
        logger.warning("Using emergency fallback - minimal content")
        
        if request.channel == Channel.EMAIL:
            body = f"Hello {{FirstName}}! Enjoy our {request.cuisine} cuisine today. Visit us soon!"
            # Add a simple CTA if website is available
            rd = request.restaurant_details or {}
            if rd.get('website_url'):
                body += f"\n\nReserve your table: {rd['website_url']}"
            body = self._append_signature(body, request.restaurant_details, request.channel)
            body = self._final_cleanup(body)
            return OfferContent(
                subject=f"Special {request.cuisine} Offer",
                body=body,
                channel=request.channel,
                metadata={"ai_generated": False, "emergency_fallback": True}
            )
        else:
            return OfferContent(
                subject=None,
                body=f"Hi {{FirstName}}! Try our {request.cuisine} today!",
                channel=request.channel,
                metadata={"ai_generated": False, "emergency_fallback": True}
            )

    # ----- Finalization -----
    def _finalize(self, content: OfferContent, request: OfferRequest) -> OfferContent:
        subject = content.subject
        body = content.body
        if request.channel == Channel.EMAIL:
            subject = TextUtils.tidy_subject(subject or "") if subject else None
            body = TextUtils.fix_all_caps(body)
            body = TextUtils.smart_truncate_with_cta(body, TextUtils.EMAIL_BODY_LIMIT, multiline=True)
            body = TextUtils.ensure_firstname_once(body, limit=TextUtils.EMAIL_BODY_LIMIT)
        else:
            body = TextUtils.normalize_newlines(body, keep_linebreaks=False)
            body = TextUtils.fix_all_caps(body)
            body = TextUtils.smart_truncate_with_cta(body, TextUtils.SMS_LIMIT, multiline=False)
            body = TextUtils.ensure_firstname_once(body, limit=TextUtils.SMS_LIMIT)
        md = dict(content.metadata or {})
        md.update({
            "processed": True,
            "length_email_subject": len(subject) if (request.channel == Channel.EMAIL and subject) else 0,
            "length_email_body": len(body) if request.channel == Channel.EMAIL else 0,
            "length_sms": len(body) if request.channel == Channel.SMS else 0,
            "has_firstname_token": ("{FirstName}" in (subject or "")) or ("{FirstName}" in body),
            "has_html_formatting": content.html_formatted is not None,
            "has_json_structure": content.json_structured is not None,
        })
        return OfferContent(
            subject=subject, 
            body=body, 
            channel=request.channel, 
            metadata=md,
            html_formatted=content.html_formatted,
            json_structured=content.json_structured
        )

    # ----- Helpers -----
    def _append_signature(self, message: str, details: Optional[Dict[str, Any]], channel: Channel) -> str:
        if not details:
            return message
        name = details.get("name")
        phone = details.get("phone")
        email = details.get("email")
        url = details.get("website_url")
        if channel == Channel.SMS:
            # keep SMS single-line; add compact signature if room
            sig_parts = [p for p in [name, phone] if p]
            sig = " • ".join(sig_parts)
            if not sig:
                return message
            compact = f"{message} — {sig}"
            return compact if len(compact) <= TextUtils.SMS_LIMIT else message
        # EMAIL: multi-line signature with proper formatting
        # First, clean the message of any instruction text
        cleaned_message = self._remove_instruction_text(message)
        # Then ensure the main message has proper line breaks
        formatted_message = self._ensure_line_breaks(cleaned_message)
        lines = [formatted_message.strip()]
        
        # Build signature section (professional tone)
        sig: List[str] = []
        if name:
            sig.append("Best regards,")
            sig.append(f"The {name} Team")
        else:
            sig.append("Best regards,")
        # Contact details
        contact_lines: List[str] = []
        if phone:
            contact_lines.append(f"Phone: {phone}")
        if email:
            contact_lines.append(f"Email: {email}")
        if contact_lines:
            sig.extend(contact_lines)
        # Add website if not already included in message body
        if url and url not in formatted_message:
            sig.append(f"Website: {url}")
        
        if sig:
            lines.append("")
            lines.append("\n".join(sig))
        return "\n".join(lines).rstrip()
    
    async def _add_formatting(self, content: OfferContent, output_format: str) -> OfferContent:
        """Add additional formatting like HTML if requested."""
        try:
            # Add HTML formatting if we have the formatter
            if self.html_formatter:
                html_formatted = await self.html_formatter.format_to_html(content)
                # Create new content with HTML formatting
                return OfferContent(
                    subject=content.subject,
                    body=content.body,
                    channel=content.channel,
                    metadata=content.metadata,
                    html_formatted=html_formatted,
                    json_structured=content.metadata.get('json_structured')
                )
        except Exception as e:
            logger.error(f"HTML formatting failed: {e}")
        
        return content

    def _ensure_line_breaks(self, message: str) -> str:
        """
        Ensure the message has proper line breaks for email formatting.
        Creates 2-3 paragraphs with proper spacing.
        """
        if not message:
            return message
            
        # If it already has proper line breaks, clean up spacing
        if message.count('\n') >= 2:
            # Clean up existing line breaks and ensure double spacing
            lines = [line.strip() for line in message.split('\n') if line.strip()]
            return '\n\n'.join(lines)
            
        # Split into sentences for paragraph creation
        sentences = re.split(r'(?<=[.!?])\s+', message)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= 1:
            return message
            
        # Create 2-3 paragraphs based on content length
        if len(sentences) >= 4:
            # Three paragraphs: greeting, details, CTA
            para1 = sentences[0]
            para2 = ' '.join(sentences[1:-1])
            para3 = sentences[-1]
            return f"{para1}\n\n{para2}\n\n{para3}"
        elif len(sentences) >= 2:
            # Two paragraphs: main message and CTA
            para1 = sentences[0]
            para2 = ' '.join(sentences[1:])
            return f"{para1}\n\n{para2}"
        
        return message

    def _remove_instruction_text(self, text: str) -> str:
        """
        Remove instruction text from the message content.
        """
        if not text:
            return text
            
        # Remove specific instruction phrases
        instruction_phrases = [
            "add time limit",
            "include call-to-action",
            "call-to-action today",
            "time limit",
            "include call-to-action today",
            "add time limit, include call-to-action today"
        ]
        
        cleaned_text = text
        for phrase in instruction_phrases:
            # Remove the phrase (case insensitive)
            cleaned_text = re.sub(re.escape(phrase), '', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\s*[.!?]+\s*[.!?]+', '.', cleaned_text)
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text

    def _clean_instruction_text(self, text: str) -> str:
        """
        Remove any instruction text that the AI might have included in the response.
        """
        if not text:
            return text
            
        # Common instruction phrases to remove
        instruction_phrases = [
            "add time limit",
            "include call-to-action",
            "call-to-action today",
            "time limit",
            "include",
            "add",
            "today",
            "instruction",
            "requirement",
            "constraint"
        ]
        
        # Split into lines and remove lines that contain instruction text
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_lower = line.lower().strip()
            # Skip lines that are just instruction text
            if any(phrase in line_lower for phrase in instruction_phrases) and len(line_lower) < 50:
                continue
            # Skip lines that are just punctuation or very short
            if len(line_lower) < 3 or line_lower in ['.', '!', '?', '-', '—']:
                continue
            cleaned_lines.append(line)
        
        # Join back together
        cleaned_text = '\n'.join(cleaned_lines).strip()
        
        # If we removed too much, return original
        if len(cleaned_text) < 20:
            return text
            
        return cleaned_text

    def _final_cleanup(self, text: str) -> str:
        """
        Final cleanup to remove instruction text and ensure proper formatting.
        Enhanced to create compelling, well-formatted content.
        """
        if not text:
            return text
            
        # Remove instruction text patterns more aggressively
        instruction_patterns = [
            r'\badd time limit\b[.!?]*',
            r'\binclude call[- ]?to[- ]?action\b[.!?]*',
            r'\bcall[- ]?to[- ]?action today\b[.!?]*',
            r'\btime limit\b[.!?]*',
            r'\binclude\b.*?\btoday\b[.!?]*',
            r'\badd\b.*?\btoday\b[.!?]*',
            r'\bIMPORTANT:\s*',
            r'\bCALL[- ]?TO[- ]?ACTION:\s*'
        ]
        
        cleaned_text = text
        for pattern in instruction_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Normalize whitespace while preserving line breaks and paragraphs
        lines = cleaned_text.split('\n')
        normalized_lines: List[str] = []
        for ln in lines:
            stripped = re.sub(r'[ \t]+', ' ', ln.strip())
            normalized_lines.append(stripped)
        # Limit consecutive blank lines to max two
        out_lines: List[str] = []
        blank_run = 0
        for ln in normalized_lines:
            if ln == '':
                blank_run += 1
                if blank_run <= 2:
                    out_lines.append('')
            else:
                blank_run = 0
                out_lines.append(ln)
        cleaned_text = '\n'.join(out_lines).strip()
        # Clean repeated punctuation (within lines)
        cleaned_text = re.sub(r'([.!?,])\s*\1+', r'\1', cleaned_text)
        
        # Ensure proper email formatting with engaging structure
        if cleaned_text.count('\n') < 1 and len(cleaned_text) > 80:
            # Split into engaging paragraphs
            sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if len(sentences) >= 3:
                # Three paragraphs: hook, details, urgency/CTA
                para1 = sentences[0]  # Hook/greeting
                para2 = ' '.join(sentences[1:-1])  # Details/benefits
                para3 = sentences[-1]  # Call to action
                cleaned_text = f"{para1}\n\n{para2}\n\n{para3}"
            elif len(sentences) >= 2:
                # Two paragraphs: main message + CTA
                para1 = sentences[0]
                para2 = ' '.join(sentences[1:])
                cleaned_text = f"{para1}\n\n{para2}"
        
        return cleaned_text

    def _constraints_hint(self, constraints: str) -> str:
        text = constraints.strip()
        if not text:
            return ""
        parts = [p.strip(" .") for p in re.split(r"[;•\n]+", text) if p.strip()]
        hint = " — ".join(parts[:2])
        if not re.search(r"(today|now|book|reserve|try|order|visit)", hint, re.IGNORECASE):
            hint += " today."
        return hint

    def _templates(self) -> Dict[str, Dict[str, str]]:
        """
        DEPRECATED: Templates are no longer used.
        All content is now AI-generated for better quality and customization.
        This method is kept for backward compatibility only.
        """
        return {}

    def _select_template(self, cuisine: str, goal: str, channel: Channel) -> str:
        """
        DEPRECATED: Template selection is no longer used.
        All content is now AI-generated.
        """
        return "ai_generated"

    def _validate_request(self, request: OfferRequest) -> None:
        if not isinstance(request.channel, Channel):
            raise ValueError("request.channel must be a Channel enum")
        for f in ("cuisine", "tone", "goal"):
            if not getattr(request, f):
                raise ValueError(f"request.{f} is required")
    
    def _validate_constraints_fulfillment(self, body: str, request: OfferRequest) -> str:
        """
        Validate that the generated content actually follows the specified constraints.
        Add missing elements if constraints were not properly followed.
        """
        if not request.constraints:
            return body
            
        constraints = request.constraints.lower()
        body_lower = body.lower()
        modifications = []
        
        # Check for time urgency constraints
        if any(word in constraints for word in ["today", "urgent", "time limit", "limited time"]):
            if not any(word in body_lower for word in ["today", "urgent", "limited", "hurry", "now", "quick"]):
                modifications.append("Added urgency: Please note this is a limited-time offer!")
        
        # Check for call-to-action constraints
        if any(phrase in constraints for phrase in ["call-to-action", "cta", "reserve", "book"]):
            if not any(word in body_lower for word in ["reserve", "book", "visit", "call", "order", "try"]):
                # Get website URL if available
                rd = request.restaurant_details or {}
                if rd.get("website_url"):
                    modifications.append(f"Reserve your table: {rd['website_url']}")
                else:
                    modifications.append("Reserve your table today!")
        
        # Check for promotional constraints
        if any(word in constraints for word in ["new", "special", "promotion", "discount", "offer"]):
            if not any(word in body_lower for word in ["new", "special", "exclusive", "discount", "offer", "deal"]):
                modifications.append("Don't miss this special offer!")
        
        # If modifications are needed, add them appropriately
        if modifications:
            logger.info(f"Adding missing constraint elements: {modifications}")
            # Add to the end of the content before signature
            if request.channel == Channel.EMAIL:
                # Find signature start
                lines = body.split('\n')
                signature_start = -1
                for i, line in enumerate(lines):
                    if any(word in line.lower() for word in ['regards', 'sincerely', 'best']):
                        signature_start = i
                        break
                
                if signature_start > 0:
                    # Insert before signature
                    lines.insert(signature_start, "")
                    lines.insert(signature_start + 1, " ".join(modifications))
                    body = "\n".join(lines)
                else:
                    # Append to end
                    body += "\n\n" + " ".join(modifications)
            else:
                # SMS - check if we have room
                addition = " " + modifications[0] if modifications else ""
                if len(body + addition) <= 160:
                    body += addition
        
        return body


# -----------------------
# Conciseness Checker
# -----------------------

class ConcisenessChecker:
    """Post-processes content to enforce constraints and improve quality."""
    
    def process_content(self, content: OfferContent, enforce_firstname: bool = True) -> OfferContent:
        """
        Process content to enforce constraints and improve quality.
        
        Args:
            content: Content to process
            enforce_firstname: Whether to ensure {FirstName} token is present
            
        Returns:
            Processed content with enforced constraints
        """
        subject = content.subject
        body = content.body
        
        # Apply text processing
        if content.channel == Channel.EMAIL:
            if subject:
                subject = TextUtils.tidy_subject(subject)
            body = TextUtils.fix_all_caps(body)
            body = TextUtils.smart_truncate_with_cta(body, TextUtils.EMAIL_BODY_LIMIT, multiline=True)
            if enforce_firstname:
                body = TextUtils.ensure_firstname_once(body, limit=TextUtils.EMAIL_BODY_LIMIT)
        else:
            body = TextUtils.normalize_newlines(body, keep_linebreaks=False)
            body = TextUtils.fix_all_caps(body)
            body = TextUtils.smart_truncate_with_cta(body, TextUtils.SMS_LIMIT, multiline=False)
            if enforce_firstname:
                body = TextUtils.ensure_firstname_once(body, limit=TextUtils.SMS_LIMIT)
        
        # Update metadata
        metadata = content.metadata.copy()
        metadata.update({
            "processed": True,
            "length_email_subject": len(subject) if (content.channel == Channel.EMAIL and subject) else 0,
            "length_email_body": len(body) if content.channel == Channel.EMAIL else 0,
            "length_sms": len(body) if content.channel == Channel.SMS else 0,
            "has_firstname_token": ("{FirstName}" in (subject or "")) or ("{FirstName}" in body),
        })
        
        return OfferContent(
            subject=subject,
            body=body,
            channel=content.channel,
            metadata=metadata
        )


# -----------------------
# HTML Formatter Agent
# -----------------------

class HTMLFormatter:
    """Agent that converts content to properly formatted HTML."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.client = None
        if openai_api_key:
            try:
                from openai import AsyncOpenAI  # type: ignore
                self.client = AsyncOpenAI(api_key=openai_api_key)
                logger.info("HTML Formatter OpenAI client initialized")
            except Exception as e:
                logger.warning(f"HTML Formatter OpenAI client unavailable; using templates. Error: {e}")
        else:
            logger.warning("No OpenAI API key provided for HTML Formatter; using templates only")
    
    async def format_to_html(self, content: OfferContent) -> str:
        """Convert content to properly formatted HTML."""
        try:
            if self.client and content.channel == Channel.EMAIL:
                return await self._ai_format_email_html(content)
            else:
                return self._template_format_html(content)
        except Exception as e:
            logger.error(f"HTML formatting error; using template fallback. Details: {e}")
            return self._template_format_html(content)
    
    async def _ai_format_email_html(self, content: OfferContent) -> str:
        """Use AI to convert email content to properly formatted HTML."""
        system_prompt = (
            "You are an expert HTML email formatter. Convert plain text email content "
            "into well-structured, responsive HTML email format.\n\n"
            "REQUIREMENTS:\n"
            "- Use semantic HTML structure with proper paragraphs\n"
            "- Apply inline CSS styles for email compatibility\n"
            "- Preserve {FirstName} tokens exactly\n"
            "- Make call-to-action buttons prominent\n"
            "- Ensure mobile-responsive design\n"
            "- Use restaurant-appropriate color scheme\n\n"
            "Output only clean HTML code without explanations."
        )
        
        user_prompt = f"""
        Convert this email content to HTML:
        
        Subject: {content.subject or 'Special Offer'}
        
        Body:
        {content.body}
        
        Create a professional email template with:
        - Proper paragraph spacing
        - Emphasized call-to-action
        - Restaurant-friendly styling
        - Mobile compatibility
        """
        
        try:
            resp = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            html_content = (resp.choices[0].message.content or "").strip()
            # Clean up any markdown artifacts
            html_content = html_content.replace('```html', '').replace('```', '').strip()
            return html_content
            
        except Exception as e:
            logger.error(f"AI HTML formatting failed: {e}")
            return self._template_format_html(content)
    
    def _template_format_html(self, content: OfferContent) -> str:
        """Template-based HTML formatting."""
        if content.channel == Channel.EMAIL:
            # Split body into paragraphs
            paragraphs = [p.strip() for p in content.body.split('\n\n') if p.strip()]
            
            # Build HTML paragraphs
            html_paragraphs = []
            for i, para in enumerate(paragraphs):
                if i == 0:  # First paragraph (greeting)
                    html_paragraphs.append(f'<p style="margin: 0 0 16px 0; font-size: 16px; line-height: 1.5; color: #333;">{para}</p>')
                elif i == len(paragraphs) - 1:  # Last paragraph (CTA)
                    # Check if it contains URL or action words
                    if any(word in para.lower() for word in ['reserve', 'book', 'visit', 'order', 'call']):
                        html_paragraphs.append(f'<p style="margin: 16px 0; font-size: 16px; line-height: 1.5; font-weight: bold; color: #d4482b;">{para}</p>')
                    else:
                        html_paragraphs.append(f'<p style="margin: 16px 0 0 0; font-size: 16px; line-height: 1.5; color: #333;">{para}</p>')
                else:  # Middle paragraphs
                    html_paragraphs.append(f'<p style="margin: 16px 0; font-size: 16px; line-height: 1.5; color: #333;">{para}</p>')
            
            return f"""
<div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; background-color: #ffffff; padding: 20px;">
    <div style="background-color: #f8f9fa; padding: 24px; border-radius: 8px; border-left: 4px solid #d4482b;">
        {''.join(html_paragraphs)}
    </div>
</div>
"""
        else:
            # SMS - simple HTML wrapper
            return f'<div style="font-family: Arial, sans-serif; font-size: 14px; color: #333; padding: 12px; background-color: #f8f9fa; border-radius: 8px; max-width: 300px;">{content.body}</div>'


# -----------------------
# JSON Structure Parser
# -----------------------

class JSONStructureParser:
    """Parser for JSON-structured AI responses."""
    
    @staticmethod
    def parse_json_email(generated: str) -> Tuple[Optional[str], str, Optional[Dict[str, Any]]]:
        """Parse JSON-structured email response with proper separation."""
        if not generated:
            return None, "", None
            
        try:
            import json
            # Clean up the response
            cleaned = generated.strip()
            # Remove any markdown code blocks
            cleaned = re.sub(r'```json\s*|\s*```', '', cleaned)
            
            # Try to find JSON object in the text
            json_start = cleaned.find('{')
            json_end = cleaned.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found")
            
            json_str = cleaned[json_start:json_end]
            data = json.loads(json_str)
            
            subject = data.get('subject', '')
            
            # Handle paragraph array with proper separation
            if 'paragraphs' in data and isinstance(data['paragraphs'], list):
                paragraphs = data['paragraphs']
                # Filter out empty paragraphs and clean them
                clean_paragraphs = []
                for para in paragraphs:
                    if para and para.strip():
                        clean_paragraphs.append(para.strip())
                
                # Separate main content from signature
                main_paragraphs = []
                signature_parts = []
                
                for para in clean_paragraphs:
                    # Check if this paragraph contains signature elements
                    if any(word in para.lower() for word in ['best regards', 'sincerely', 'contact', 'phone', 'email', 'website', 'reserve online']):
                        signature_parts.append(para)
                    else:
                        main_paragraphs.append(para)
                
                # Join main content with proper spacing
                body = '\n\n'.join(main_paragraphs)
                
                # Add signature separately if found
                if signature_parts:
                    body += '\n\n' + '\n'.join(signature_parts)
            else:
                body = data.get('body', '')
            
            # Validate that we got meaningful content
            if not body or len(body.strip()) < 10:
                raise ValueError("No meaningful content in JSON")
            
            # Extract metadata
            metadata = {
                'tone': data.get('tone'),
                'call_to_action': data.get('call_to_action'),
                'json_structured': True,
                'has_signature': any(word in body.lower() for word in ['best regards', 'sincerely', 'contact'])
            }
            
            return subject, body, metadata
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Generated content: {generated[:200]}...")
            # Fallback to regular parsing
            subject, body = Parser.parse_email(generated)
            return subject, body, None
    
    @staticmethod
    def parse_json_sms(generated: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Parse JSON-structured SMS response."""
        if not generated:
            return "", None
            
        try:
            import json
            # Clean up the response
            cleaned = generated.strip()
            cleaned = re.sub(r'```json\s*|\s*```', '', cleaned)
            
            data = json.loads(cleaned)
            
            message = data.get('message', '')
            
            # Extract metadata
            metadata = {
                'character_count': data.get('character_count'),
                'call_to_action': data.get('call_to_action'),
                'json_structured': True
            }
            
            return message, metadata
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"JSON SMS parsing failed: {e}")
            # Fallback to regular parsing
            return generated, None


# -----------------------
# Audience Advisor (unchanged interface, cleaner fallback)
# -----------------------

class AudienceAdvisor:
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.client = None
        if openai_api_key:
            try:
                from openai import AsyncOpenAI  # type: ignore
                self.client = AsyncOpenAI(api_key=openai_api_key)
            except Exception:
                logger.warning("OpenAI client unavailable; using fallback heuristics")

    async def suggest_interests(self, city: str, state: str, cuisine: str, daypart: Optional[str] = None) -> AudienceAdvice:
        try:
            if self.client:
                return await self._with_ai(city, state, cuisine, daypart)
        except Exception as e:
            logger.error(f"AI suggestion failed: {e}")
        return self._heuristics(city, state, cuisine, daypart)

    async def _with_ai(self, city: str, state: str, cuisine: str, daypart: Optional[str]) -> AudienceAdvice:
        prompt = (
            f"As a restaurant marketing expert, suggest the most effective customer interest categories for {city}, {state}.\n\n"
            f"Cuisine: {cuisine}\nTarget time: {daypart or 'all day'}\n\n"
            "Provide 3–5 specific categories.\n\n"
            "INTERESTS: a, b, c\n"
            "RATIONALE: brief explanation"
        )
        resp = await self.client.chat.completions.create(  # type: ignore[attr-defined]
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a restaurant marketing expert."}, {"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3,
            timeout=20,
        )
        text = (resp.choices[0].message.content or "").strip()
        interests, rationale = self._parse(text)
        return AudienceAdvice(suggested_interests=interests, rationale=rationale, confidence_score=0.85 if interests else 0.5)

    def _heuristics(self, city: str, state: str, cuisine: str, daypart: Optional[str]) -> AudienceAdvice:
        base_map = {
            "italian": ["fine_dining", "wine_lovers", "family_dining"],
            "mexican": ["casual_dining", "groups", "happy_hour"],
            "chinese": ["takeout", "family_dining", "lunch_crowd"],
            "american": ["sports_bars", "family_dining", "comfort_food"],
            "japanese": ["sushi_lovers", "fine_dining", "date_night"],
            "thai": ["spicy_food", "healthy_eating", "lunch_crowd"],
            "indian": ["spicy_food", "vegetarian", "ethnic_cuisine"],
            "french": ["fine_dining", "wine_lovers", "romantic_dining"],
            "seafood": ["fresh_seafood", "coastal_dining", "fine_dining"],
            "steakhouse": ["meat_lovers", "business_dining", "special_occasions"],
        }
        c = (cuisine or "").lower()
        interests = next((v for k, v in base_map.items() if k in c), ["local_dining", "good_food", "restaurants"])
        if daypart:
            dp = daypart.lower()
            add = {
                "breakfast": ["coffee_lovers", "early_birds", "business_breakfast"],
                "lunch": ["lunch_crowd", "business_lunch", "quick_service"],
                "dinner": ["dinner_out", "date_night", "family_dining"],
                "late_night": ["nightlife", "late_night_dining", "bar_food"],
            }.get(dp, [])
            interests += add
        # dedupe keep order
        seen = set()
        uniq: List[str] = []
        for i in interests:
            if i not in seen:
                uniq.append(i)
                seen.add(i)
        uniq = uniq[:5]
        rationale = (
            f"Selected interests for {cuisine} in {city}, {state}. "
            + (f"Optimized for {daypart}. " if daypart else "")
            + "These categories typically drive engagement for similar restaurants."
        )
        return AudienceAdvice(uniq, rationale, 0.65)

    def _parse(self, response: str) -> Tuple[List[str], str]:
        if not response:
            return [], ""
        parts = re.split(r"RATIONALE:\s*", response, flags=re.IGNORECASE)
        interests_part = re.sub(r"INTERESTS:\s*", "", parts[0], flags=re.IGNORECASE).strip()
        rationale = (parts[1] if len(parts) > 1 else "").strip()
        interests = [i.strip() for i in interests_part.split(",") if i.strip()]
        return interests[:5], rationale


# -----------------------
# Quick usage example (pseudo)
# -----------------------
# async def demo():
#     writer = OfferWriter(openai_api_key="...")
#     req = OfferRequest(
#         cuisine="Italian",
#         tone=Tone.FRIENDLY.value,
#         channel=Channel.EMAIL,
#         goal="Promote new menu items",
#         restaurant_details={"name": "Your Restaurant", "phone": "(555) 123-4567", "email": "info@restaurant.com"},
#     )
#     content = await writer.generate_offer(req)
#     print(content.subject)
#     print("---")
#     print(content.body)
