from pymongo import MongoClient, ASCENDING, DESCENDING
from app.core.config import MONGO_URI, MONGO_DB_NAME

# MongoDB Client Setup
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]


# collection: drawing analyses
drawing_analyses = db["drawing_analyses"]

moods = db["moods"]

# Collections
parents_col = db["parents"]
children_col = db["children"]
trusted_contacts_col = db["trusted_contacts"]
moods_col = db["moods"]
tracks_col = db["tracks"]
leaderboard_col = db["leaderboard"]

# Create indexes
def create_indexes():
    """Create necessary indexes for collections"""
    try:
        # Parents: unique email index
        parents_col.create_index([("email", ASCENDING)], unique=True)
        
        # Children: unique username index and parent_id index
        children_col.create_index([("username", ASCENDING)], unique=True)
        children_col.create_index([("parent_id", ASCENDING)])
        
        # Trusted contacts: indexes for querying
        trusted_contacts_col.create_index([("invite_token", ASCENDING)], unique=True, sparse=True)
        trusted_contacts_col.create_index([("child_id", ASCENDING)])
        trusted_contacts_col.create_index([("email", ASCENDING)])
        
        # Moods: index for child_id and datetime for efficient querying
        moods_col.create_index([("child_id", ASCENDING), ("datetime", ASCENDING)])

        # Tracks: index for created_at for sorting
        tracks_col.create_index([("created_at", ASCENDING)])

        # Leaderboard: indexes for sorting and player lookup
        leaderboard_col.create_index([("score", DESCENDING)])
        leaderboard_col.create_index([("created_at", ASCENDING)])
        leaderboard_col.create_index([("player_name", ASCENDING)])
        
        # Moods: unique index for child_id + date_key to enforce one mood per day
        # Partial index only applies to documents with date_key field (skips old records)
        try:
            moods_col.create_index(
                [("child_id", ASCENDING), ("date_key", ASCENDING)],
                unique=True,
                partialFilterExpression={"date_key": {"$exists": True, "$ne": None}}
            )
        except Exception as e:
            # If index already exists or conflicts, try to drop and recreate
            try:
                moods_col.drop_index("child_id_1_date_key_1")
                moods_col.create_index(
                    [("child_id", ASCENDING), ("date_key", ASCENDING)],
                    unique=True,
                    partialFilterExpression={"date_key": {"$exists": True, "$ne": None}}
                )
            except Exception as e2:
                print(f"⚠ Could not create date_key index: {str(e2)}")
        
        print("✓ MongoDB indexes created successfully")
    except Exception as e:
        print(f"⚠ MongoDB index creation issue: {str(e)}")

# Initialize indexes on import
create_indexes()
