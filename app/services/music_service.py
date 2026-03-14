"""
Music Service
Handles Cloudinary uploads and track persistence
"""
from datetime import datetime
from typing import List
from fastapi import HTTPException, status, UploadFile
import cloudinary
import cloudinary.uploader

from app.core.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
from app.database.db import tracks_col
from app.schemas.auth_schema import TokenData


def _configure_cloudinary() -> None:
    if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cloudinary configuration is missing"
        )
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )


def _validate_uploads(music_file: UploadFile, cover_image: UploadFile) -> None:
    if not music_file or not cover_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both music_file and cover_image are required"
        )
    if not (music_file.content_type or "").startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="music_file must be an audio file"
        )
    if not (cover_image.content_type or "").startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cover_image must be an image file"
        )


def create_track(
    title: str,
    artist: str,
    emotions: List[str],
    music_file: UploadFile,
    cover_image: UploadFile,
    uploader: TokenData
) -> dict:
    _configure_cloudinary()
    _validate_uploads(music_file, cover_image)

    try:
        music_upload = cloudinary.uploader.upload(
            music_file.file,
            resource_type="video",
            folder="music/tracks",
            use_filename=True,
            unique_filename=True
        )
        cover_upload = cloudinary.uploader.upload(
            cover_image.file,
            resource_type="image",
            folder="music/covers",
            use_filename=True,
            unique_filename=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cloudinary upload failed: {str(e)}"
        )

    track_doc = {
        "title": title,
        "artist": artist,
        "emotions": emotions,
        "music_url": music_upload.get("secure_url") or music_upload.get("url"),
        "music_public_id": music_upload.get("public_id"),
        "cover_url": cover_upload.get("secure_url") or cover_upload.get("url"),
        "cover_public_id": cover_upload.get("public_id"),
        "created_at": datetime.utcnow(),
        "uploader": {
            "id": uploader.id,
            "role": uploader.role,
            "email": uploader.email,
            "username": uploader.username
        }
    }

    result = tracks_col.insert_one(track_doc)
    track_doc["_id"] = result.inserted_id
    return track_doc


def get_tracks_by_emotion(emotion: str) -> List[dict]:
    """
    Get all tracks that match the specified emotion
    
    Args:
        emotion: Emotion to filter by (e.g., "sad", "happy", "angry")
        
    Returns:
        List of track documents
    """
    # Case-insensitive search for the emotion in the emotions array
    query = {"emotions": {"$regex": f"^{emotion}$", "$options": "i"}}
    
    tracks = list(tracks_col.find(query).sort("created_at", -1))
    
    # Convert ObjectId to string
    for track in tracks:
        track["_id"] = str(track["_id"])
    
    return tracks
