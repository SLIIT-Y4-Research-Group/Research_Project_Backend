from sqlalchemy import Column, Integer, String
from app.database.db import Base

class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, index=True)
    mood = Column(String, index=True)
    note = Column(String, nullable=True)
