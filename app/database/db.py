from pymongo import MongoClient, ASCENDING, DESCENDING
from app.core.config import MONGO_URI, MONGO_DB_NAME

# MongoDB Client Setup
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collections
drawing_analyses = db["drawing_analyses"]
moods = db["moods"]

parents_col = db["parents"]
children_col = db["children"]
trusted_contacts_col = db["trusted_contacts"]
moods_col = db["moods"]
tracks_col = db["tracks"]
music_sessions_col = db["music_sessions"]
leaderboard_col = db["leaderboard"]
therapy_sessions_col = db["therapy_sessions"]   # ✅ moved outside function


def create_indexes():
    """Create necessary indexes for collections"""
    try:
        # ================= PARENTS =================
        parents_col.create_index([("email", ASCENDING)], unique=True)

        # ================= CHILDREN =================
        children_col.create_index([("username", ASCENDING)], unique=True)
        children_col.create_index([("parent_id", ASCENDING)])

        # ================= TRUSTED CONTACTS =================
        trusted_contacts_col.create_index(
            [("invite_token", ASCENDING)],
            unique=True,
            sparse=True
        )
        trusted_contacts_col.create_index([("child_id", ASCENDING)])
        trusted_contacts_col.create_index([("email", ASCENDING)])

        # ================= MOODS =================
        moods_col.create_index([("child_id", ASCENDING), ("datetime", ASCENDING)])

        # ================= TRACKS =================
        tracks_col.create_index([("created_at", ASCENDING)])
        
        # Music sessions: indexes for personalization queries
        music_sessions_col.create_index([("user_id", ASCENDING), ("ended_at", DESCENDING)])
        music_sessions_col.create_index([("track_id", ASCENDING)])
        music_sessions_col.create_index([("user_id", ASCENDING), ("track_id", ASCENDING)])

        # ================= LEADERBOARD =================
        leaderboard_col.create_index([("score", DESCENDING)])
        leaderboard_col.create_index([("created_at", ASCENDING)])
        leaderboard_col.create_index([("player_name", ASCENDING)])

        # ================= DRAWING ANALYSES =================
        drawing_analyses.create_index([("child_id", ASCENDING), ("created_at", DESCENDING)])
        drawing_analyses.create_index([("parent_id", ASCENDING), ("created_at", DESCENDING)])
        drawing_analyses.create_index([("parent_email", ASCENDING), ("created_at", DESCENDING)])
        drawing_analyses.create_index([("emotion.label", ASCENDING)])
        drawing_analyses.create_index([("source_mode", ASCENDING)])

        # ================= THERAPY SESSIONS =================
        therapy_sessions_col.create_index([("child_id", ASCENDING), ("created_at", DESCENDING)])
        therapy_sessions_col.create_index([("activity_type", ASCENDING)])

        # ================= MOODS DATE_KEY UNIQUE INDEX =================
        try:
            moods_col.create_index(
                [("child_id", ASCENDING), ("date_key", ASCENDING)],
                unique=True,
                partialFilterExpression={
                    "date_key": {"$exists": True, "$ne": None}
                }
            )
        except Exception:
            try:
                moods_col.drop_index("child_id_1_date_key_1")
                moods_col.create_index(
                    [("child_id", ASCENDING), ("date_key", ASCENDING)],
                    unique=True,
                    partialFilterExpression={
                        "date_key": {"$exists": True, "$ne": None}
                    }
                )
            except Exception as e2:
                print(f"⚠ Could not create date_key index: {str(e2)}")

        print("✓ MongoDB indexes created successfully")

    except Exception as e:
        print(f"⚠ MongoDB index creation issue: {str(e)}")


# Run on startup
create_indexes()