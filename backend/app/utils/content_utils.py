"""
Content processing utilities for AI-generated marketing content.
Handles length enforcement, text cleaning, and formatting.
"""

import re
from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Length limits
SMS_MAX_LENGTH = 160
EMAIL_SUBJECT_MAX_LENGTH = 78
EMAIL_BODY_MAX_LENGTH = 400  # Increased limit to accommodate restaurant details


def enforce_sms_length(text: str) -> str:
    """
    Enforce SMS length limit (≤160 characters) with smart truncation.
    
    Args:
        text: Input SMS text
        
    Returns:
        str: SMS text within length limit
    """
    if len(text) <= SMS_MAX_LENGTH:
        return text
    
    # Smart truncation at word boundary
    truncated = text[:SMS_MAX_LENGTH - 3]  # Leave room for "..."
    
    # Find last space for word boundary
    last_space = truncated.rfind(' ')
    if last_space > SMS_MAX_LENGTH * 0.7:  # Only if we don't lose too much
        truncated = truncated[:last_space]
    
    return truncated + "..."


def enforce_email_subject_length(subject: str) -> str:
    """
    Enforce email subject length limit with smart truncation.
    
    Args:
        subject: Email subject line
        
    Returns:
        str: Subject within length limit
    """
    if len(subject) <= EMAIL_SUBJECT_MAX_LENGTH:
        return subject
    
    # For subjects, truncate more aggressively
    truncated = subject[:EMAIL_SUBJECT_MAX_LENGTH - 3]
    
    # Find last space
    last_space = truncated.rfind(' ')
    if last_space > EMAIL_SUBJECT_MAX_LENGTH * 0.6:
        truncated = truncated[:last_space]
    
    return truncated + "..."


def enforce_email_body_length(body: str) -> str:
    """
    Enforce email body length limit (≤400 characters) with smart truncation.
    
    Args:
        body: Email body text
        
    Returns:
        str: Body text within length limit
    """
    if len(body) <= EMAIL_BODY_MAX_LENGTH:
        return body
    
    # Smart truncation at sentence or word boundary
    truncated = body[:EMAIL_BODY_MAX_LENGTH - 3]
    
    # Try to find sentence boundary first
    sentence_end = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if sentence_end > EMAIL_BODY_MAX_LENGTH * 0.6:
        return truncated[:sentence_end + 1]
    
    # Fall back to word boundary
    last_space = truncated.rfind(' ')
    if last_space > EMAIL_BODY_MAX_LENGTH * 0.7:
        truncated = truncated[:last_space]
    
    return truncated + "..."


def clean_generated_text(text: str) -> str:
    """
    Clean AI-generated text by removing unwanted formatting and caps.
    
    Args:
        text: Raw AI-generated text
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return text
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Fix all-caps words (convert to title case, but preserve acronyms)
    def fix_caps(match):
        word = match.group(0)
        # Keep short words (likely acronyms) as-is
        if len(word) <= 3:
            return word
        # Convert long all-caps words to title case
        return word.capitalize()
    
    text = re.sub(r'\b[A-Z]{4,}\b', fix_caps, text)
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    
    # Remove excessive punctuation
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    text = re.sub(r'\.{3,}', '...', text)
    
    # Clean up quotes
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r'['']', "'", text)
    
    return text.strip()


def inject_personalization(text: str, preserve_existing: bool = True) -> str:
    """
    Inject {FirstName} personalization token into text.
    
    Args:
        text: Input text
        preserve_existing: If True, don't add if personalization already exists
        
    Returns:
        str: Text with personalization token
    """
    if preserve_existing and ('{FirstName}' in text or '{firstname}' in text.lower()):
        return text
    
    # Common greeting patterns to replace
    greeting_patterns = [
        (r'\bHi there\b', 'Hi {FirstName}'),
        (r'\bHello there\b', 'Hello {FirstName}'),
        (r'\bHey there\b', 'Hey {FirstName}'),
        (r'\bGreetings\b', 'Hi {FirstName}'),
        (r'^Hi[,!]?\s+', 'Hi {FirstName}, '),
        (r'^Hello[,!]?\s+', 'Hello {FirstName}, '),
        (r'^Hey[,!]?\s+', 'Hey {FirstName}, '),
    ]
    
    for pattern, replacement in greeting_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)
    
    # If no greeting found, add at the beginning
    if text and not text.lower().startswith(('hi', 'hello', 'hey')):
        return f"Hi {{FirstName}}, {text}"
    
    return text


def parse_email_content(content: str) -> Tuple[str, str]:
    """
    Parse AI-generated content into subject and body for emails.
    
    Args:
        content: Raw AI-generated content
        
    Returns:
        Tuple[str, str]: (subject, body)
    """
    content = content.strip()
    
    # Look for explicit SUBJECT: and BODY: markers
    if "SUBJECT:" in content and "BODY:" in content:
        parts = content.split("BODY:", 1)
        subject = parts[0].replace("SUBJECT:", "").strip()
        body = parts[1].strip()
        return subject, body
    
    # Look for Subject: and Body: markers (case variations)
    subject_match = re.search(r'(?:subject|SUBJECT):\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
    body_match = re.search(r'(?:body|BODY):\s*(.+)', content, re.IGNORECASE | re.DOTALL)
    
    if subject_match and body_match:
        return subject_match.group(1).strip(), body_match.group(1).strip()
    
    # Fallback: use first line as subject, rest as body
    lines = content.split('\n', 1)
    if len(lines) >= 2:
        subject = lines[0].strip()
        body = lines[1].strip()
        
        # Remove common prefixes
        subject = re.sub(r'^(subject|SUBJECT):\s*', '', subject, flags=re.IGNORECASE)
        body = re.sub(r'^(body|BODY):\s*', '', body, flags=re.IGNORECASE)
        
        return subject, body
    
    # Single line content - generate subject from content
    if len(content) > EMAIL_SUBJECT_MAX_LENGTH:
        # Use first part as subject
        subject = content[:EMAIL_SUBJECT_MAX_LENGTH - 3] + "..."
        body = content
    else:
        subject = content
        body = content
    
    return subject, body


def validate_content_length(content_type: str, text: str) -> Dict[str, Any]:
    """
    Validate content length and provide feedback.
    
    Args:
        content_type: 'sms', 'email_subject', or 'email_body'
        text: Text to validate
        
    Returns:
        Dict with validation results
    """
    limits = {
        'sms': SMS_MAX_LENGTH,
        'email_subject': EMAIL_SUBJECT_MAX_LENGTH,
        'email_body': EMAIL_BODY_MAX_LENGTH
    }
    
    if content_type not in limits:
        return {"valid": False, "error": f"Unknown content type: {content_type}"}
    
    max_length = limits[content_type]
    current_length = len(text)
    
    return {
        "valid": current_length <= max_length,
        "current_length": current_length,
        "max_length": max_length,
        "remaining": max_length - current_length,
        "truncated": current_length > max_length
    }


def create_content_preview(channel: str, subject: str = None, body: str = None) -> Dict[str, Any]:
    """
    Create a preview of the content with length information.
    
    Args:
        channel: 'email' or 'sms'
        subject: Email subject (for email channel)
        body: Content body
        
    Returns:
        Dict with preview and length info
    """
    preview = {"channel": channel}
    
    if channel == "email":
        if subject:
            subject_validation = validate_content_length("email_subject", subject)
            preview["subject"] = {
                "text": subject,
                "validation": subject_validation
            }
        
        if body:
            body_validation = validate_content_length("email_body", body)
            preview["body"] = {
                "text": body,
                "validation": body_validation
            }
    
    elif channel == "sms":
        if body:
            sms_validation = validate_content_length("sms", body)
            preview["body"] = {
                "text": body,
                "validation": sms_validation
            }
    
    return preview
