from pymongo import MongoClient
from app.core.config import MONGO_URI, MONGO_DB_NAME

# MongoDB Client Setup
client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]


# collection: drawing analyses
drawing_analyses = db["drawing_analyses"]

moods = db["moods"]