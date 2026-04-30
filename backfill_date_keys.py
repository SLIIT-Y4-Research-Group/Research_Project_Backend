"""
Standalone script to backfill missing date_key fields in mood records.

Usage:
    python backfill_date_keys.py

This script:
1. Connects to MongoDB
2. Finds all mood records without date_key field
3. Computes date_key from their datetime field
4. Updates each record with the computed date_key

Safe to run multiple times (idempotent).
"""

from dotenv import load_dotenv
load_dotenv()

import logging
from app.services.mood_service import backfill_missing_date_keys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting date_key backfill script")
    logger.info("=" * 60)
    
    try:
        stats = backfill_missing_date_keys()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Backfill Results:")
        logger.info(f"  Total moods without date_key: {stats['total_found']}")
        logger.info(f"  Successfully updated: {stats['updated']}")
        logger.info(f"  Failed updates: {stats['failed']}")
        logger.info("=" * 60)
        
        if stats['failed'] > 0:
            logger.warning(f"⚠ {stats['failed']} moods failed to update. Check logs for details.")
        elif stats['updated'] > 0:
            logger.info(f"✓ Successfully backfilled {stats['updated']} mood records")
        else:
            logger.info("✓ No moods needed backfilling")
            
    except Exception as e:
        logger.error(f"❌ Backfill script failed: {e}", exc_info=True)
        exit(1)
