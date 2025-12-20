"""
DateTime utility functions for consistent datetime handling across the application
"""

from datetime import datetime, timezone
from typing import Union, Optional


def parse_datetime(value: Union[str, datetime, None]) -> Optional[datetime]:
    """
    Parse a datetime value that could be:
    - A datetime object (returned as-is)
    - An ISO format string (parsed to datetime)
    - None (returned as None)
    
    Handles various ISO formats including:
    - 2025-12-20T10:30:00+00:00
    - 2025-12-20T10:30:00Z
    - 2025-12-20T10:30:00.123456+00:00
    
    Args:
        value: The datetime value to parse
        
    Returns:
        A timezone-aware datetime object or None
    """
    if value is None:
        return None
    
    # Already a datetime object
    if isinstance(value, datetime):
        # Ensure it's timezone-aware
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    
    # String - parse it
    if isinstance(value, str):
        try:
            # Handle 'Z' suffix (common in JavaScript/JSON)
            normalized = value.replace('Z', '+00:00')
            return datetime.fromisoformat(normalized)
        except ValueError:
            # Try alternative parsing if standard fails
            try:
                # Handle potential milliseconds without timezone
                if '.' in value and '+' not in value and 'Z' not in value:
                    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
            return None
    
    # Unknown type
    return None


def ensure_datetime(value: Union[str, datetime, None], default: Optional[datetime] = None) -> Optional[datetime]:
    """
    Ensure a value is a datetime object, with an optional default.
    
    Args:
        value: The value to convert
        default: Default value if parsing fails or value is None
        
    Returns:
        A datetime object or the default value
    """
    result = parse_datetime(value)
    return result if result is not None else default
