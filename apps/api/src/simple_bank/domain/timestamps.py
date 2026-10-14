"""Timestamp utilities for IST timezone conversion."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def to_ist_iso8601(dt: datetime) -> str:
    """Convert a UTC datetime to IST ISO 8601 string.
    
    Args:
        dt: A datetime object (typically in UTC from database).
        
    Returns:
        ISO 8601 formatted string with IST timezone (+05:30).
        Example: "2026-10-14T15:30:45+05:30"
    """
    # If dt is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to IST timezone
    ist = ZoneInfo("Asia/Kolkata")
    dt_ist = dt.astimezone(ist)
    
    # Format as ISO 8601 with offset
    # Example: 2026-10-14T15:30:45+05:30
    return dt_ist.isoformat()
