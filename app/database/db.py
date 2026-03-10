from pymongo import MongoClient, ASCENDING
from app.core.config import MONGO_URI, MONGO_DB_NAME

# MongoDB Client Setup
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collections
parents_col = db["parents"]
children_col = db["children"]
trusted_contacts_col = db["trusted_contacts"]
moods_col = db["moods"]

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
        
        print("✓ MongoDB indexes created successfully")
    except Exception as e:
        print(f"⚠ MongoDB index creation issue: {str(e)}")

# Initialize indexes on import
create_indexes()
