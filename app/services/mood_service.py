from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
from app.database.db import moods_col
from bson import ObjectId
import logging

# Configure logging for mood service
logger = logging.getLogger(__name__)

# Sri Lanka timezone (UTC+5:30) - used for "today" calculations
# because the frontend sends datetime in local Sri Lanka time
SL_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def _now_sl() -> datetime:
    """Get current datetime in Sri Lanka timezone"""
    return datetime.now(SL_TIMEZONE)


def _today_sl() -> datetime:
    """Get today's date at midnight in Sri Lanka timezone (timezone-naive for consistency)"""
    return _now_sl().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

def save_mood(userId: int, mood: str, datetime: datetime):
    """Legacy function - kept for backward compatibility"""
    mood_data = {
        "userId": userId,
        "mood": mood,
        "datetime": datetime
    }
    result = moods_col.insert_one(mood_data)
    mood_data["_id"] = str(result.inserted_id)
    return mood_data


def get_date_key_from_datetime(dt: datetime) -> str:
    """
    Convert datetime to date_key string (YYYY-MM-DD format)
    Uses UTC timezone for consistency
    """
    return dt.strftime("%Y-%m-%d")


def get_today_date_key() -> str:
    """Get today's date_key (YYYY-MM-DD) in Sri Lanka timezone"""
    today_sl = _now_sl()
    key = today_sl.strftime("%Y-%m-%d")
    logger.debug(f"get_today_date_key() = {key} (SL time: {today_sl.strftime('%Y-%m-%d %H:%M:%S')})")
    return key


def get_mood_for_child_on_date(child_id: str, date_key: str) -> Optional[Dict]:
    """
    Get mood record for a specific child on a specific date
    Returns None if no mood recorded for that day
    
    Note: Uses UTC timezone for date calculations
    Includes fallback query for backward compatibility with moods missing date_key
    """
    child_oid = ObjectId(child_id)
    
    # Primary query: look for mood with date_key
    mood = moods_col.find_one({
        "child_id": child_oid,
        "date_key": date_key
    })
    
    if mood:
        logger.debug(f"Found mood for child {child_id} on date {date_key} (with date_key)")
        return mood
    
    # Fallback query: for old moods without date_key, query by datetime range
    # Convert date_key to datetime range (00:00:00 to 23:59:59 UTC)
    try:
        date_start = datetime.strptime(date_key, "%Y-%m-%d")
        date_end = date_start + timedelta(days=1)
        
        mood = moods_col.find_one({
            "child_id": child_oid,
            "datetime": {"$gte": date_start, "$lt": date_end},
            "date_key": {"$exists": False}  # Only match old moods without date_key
        })
        
        if mood:
            logger.warning(f"Found mood for child {child_id} on date {date_key} using fallback (missing date_key)")
            return mood
        else:
            logger.debug(f"No mood found for child {child_id} on date {date_key}")
            return None
            
    except Exception as e:
        logger.error(f"Error in fallback query for child {child_id} on date {date_key}: {e}")
        return None


def get_today_mood_for_child(child_id: str) -> Optional[Dict]:
    """
    Get today's mood record for a child
    Returns None if no mood recorded today
    """
    today_key = get_today_date_key()
    return get_mood_for_child_on_date(child_id, today_key)


def get_weekly_moods_for_child(child_id: str, days: int = 7) -> List[Dict]:
    """
    Get mood records for the last N days (including today)
    Returns list of dicts with date, mood, completed status
    
    Note: Uses UTC timezone for date calculations
    Includes fallback to find old moods without date_key field
    
    Example:
    [
        {"date": "2026-03-04", "mood": "Happy", "completed": True, "datetime": ...},
        {"date": "2026-03-05", "mood": None, "completed": False, "datetime": None},
        ...
    ]
    """
    today = _now_sl().replace(tzinfo=None)  # Use Sri Lanka time for "today"
    child_oid = ObjectId(child_id)
    date_keys = []
    
    # Generate last N days date keys
    for i in range(days - 1, -1, -1):  # Start from oldest to newest
        date = today - timedelta(days=i)
        date_keys.append(get_date_key_from_datetime(date))
    
    # Fetch all moods with date_key for these dates in one query
    moods = moods_col.find({
        "child_id": child_oid,
        "date_key": {"$in": date_keys}
    }).sort("date_key", 1)
    
    # Create a map of date_key -> mood
    mood_map = {}
    for mood in moods:
        mood_map[mood["date_key"]] = mood
    
    logger.debug(f"Found {len(mood_map)} moods with date_key for child {child_id} in last {days} days")
    
    # Fallback: Query for old moods without date_key
    # Get date range for the entire period
    oldest_date = today - timedelta(days=days-1)
    oldest_date_start = oldest_date.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    old_moods = moods_col.find({
        "child_id": child_oid,
        "datetime": {"$gte": oldest_date_start, "$lte": today_end},
        "date_key": {"$exists": False}
    }).sort("datetime", 1)
    
    # Add old moods to map if date not already present
    fallback_count = 0
    for mood in old_moods:
        date_key = get_date_key_from_datetime(mood["datetime"])
        if date_key in date_keys and date_key not in mood_map:
            mood_map[date_key] = mood
            fallback_count += 1
    
    if fallback_count > 0:
        logger.warning(f"Found {fallback_count} old moods without date_key for child {child_id} using fallback")
    
    # Build result with all dates (including missing ones)
    result = []
    for date_key in date_keys:
        if date_key in mood_map:
            mood_doc = mood_map[date_key]
            result.append({
                "date": date_key,
                "mood": mood_doc["mood"],
                "completed": True,
                "datetime": mood_doc["datetime"]
            })
        else:
            result.append({
                "date": date_key,
                "mood": None,
                "completed": False,
                "datetime": None
            })
    
    logger.debug(f"Returning {len([r for r in result if r['completed']])} completed days out of {days} for child {child_id}")
    
    return result


def create_daily_mood_if_not_exists(child_id: str, mood: str, dt: datetime) -> tuple[bool, Optional[Dict]]:
    """
    Create a mood record for today if it doesn't already exist
    
    Uses UTC timezone for date calculations to ensure consistency.
    Always adds date_key field when creating new moods.
    
    Returns:
        (created: bool, mood_doc: Dict or None)
        - (True, new_mood) if successfully created
        - (False, existing_mood) if already exists for today
    """
    date_key = get_date_key_from_datetime(dt)
    
    # Check if mood already exists for this date
    existing = get_mood_for_child_on_date(child_id, date_key)
    
    if existing:
        logger.info(f"Mood already exists for child {child_id} on date {date_key}")
        return (False, existing)
    
    # Create new mood record
    mood_doc = {
        "child_id": ObjectId(child_id),
        "mood": mood,
        "datetime": dt,
        "date_key": date_key
    }
    
    result = moods_col.insert_one(mood_doc)
    mood_doc["_id"] = result.inserted_id
    
    logger.info(f"Created new mood for child {child_id} on date {date_key}: mood={mood}")
    
    return (True, mood_doc)


def backfill_missing_date_keys() -> Dict[str, int]:
    """
    Utility function to backfill date_key field for old mood records
    
    This function:
    1. Finds all moods without date_key field
    2. Computes date_key from datetime field
    3. Updates the document with date_key
    
    Safe to run multiple times (idempotent).
    Should be run once during startup or as a migration script.
    
    Returns:
        Dict with statistics: {"total_found": int, "updated": int, "failed": int}
    """
    logger.info("Starting date_key backfill for old mood records...")
    
    stats = {"total_found": 0, "updated": 0, "failed": 0}
    
    try:
        # Find all moods without date_key
        moods_without_key = moods_col.find({
            "date_key": {"$exists": False},
            "datetime": {"$exists": True}
        })
        
        moods_list = list(moods_without_key)
        stats["total_found"] = len(moods_list)
        
        logger.info(f"Found {stats['total_found']} moods without date_key")
        
        if stats["total_found"] == 0:
            logger.info("No moods need backfilling")
            return stats
        
        # Update each mood with computed date_key
        for mood in moods_list:
            try:
                dt = mood["datetime"]
                date_key = get_date_key_from_datetime(dt)
                
                result = moods_col.update_one(
                    {"_id": mood["_id"]},
                    {"$set": {"date_key": date_key}}
                )
                
                if result.modified_count > 0:
                    stats["updated"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to backfill mood {mood.get('_id')}: {e}")
                stats["failed"] += 1
        
        logger.info(f"Backfill complete: {stats['updated']} updated, {stats['failed']} failed")
        
    except Exception as e:
        logger.error(f"Backfill process error: {e}")
        
    return stats
