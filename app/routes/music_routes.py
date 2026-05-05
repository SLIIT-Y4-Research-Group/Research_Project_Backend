from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.schemas.auth_schema import TokenData
from app.schemas.music_schema import TrackCreateResponse, TrackResponse, TrackUploader
from app.services.auth_service import get_current_user
from app.services.music_service import create_track
from app.database.db import tracks_col

router = APIRouter(prefix="/music", tags=["Music"])


def _to_track_response(track: dict) -> TrackResponse:
    return TrackResponse(
        id=str(track["_id"]),
        title=track.get("title", "Unknown Title"),
        artist=track.get("artist", "Unknown Artist"),
        emotions=track.get("emotions", []),
        music_url=track.get("music_url", ""),
        cover_url=track.get("cover_url"),
        created_at=track["created_at"],
    )


@router.get("/tracks", response_model=List[TrackResponse])
def list_tracks(emotion: Optional[str] = Query(default=None)):
    query = {}
    if emotion:
        query["emotions"] = {"$in": [emotion.strip()]}

    tracks = list(tracks_col.find(query).sort("created_at", -1))
    return [_to_track_response(t) for t in tracks]


@router.get("/tracks/{track_id}", response_model=TrackResponse)
def get_track(track_id: str):
    if not ObjectId.is_valid(track_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track id",
        )
    track = tracks_col.find_one({"_id": ObjectId(track_id)})
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    return _to_track_response(track)


@router.post("/tracks", response_model=TrackCreateResponse)
def upload_track(
    title: str = Form(...),
    artist: str = Form(...),
    emotions: str = Form(...),
    music_file: UploadFile = File(...),
    cover_image: UploadFile = File(...),
    # current_user: TokenData = Depends(get_current_user)  # Authentication removed
):
    emotions_list = [e.strip() for e in emotions.split(",") if e.strip()]

    track = create_track(
        title=title,
        artist=artist,
        emotions=emotions_list,
        music_file=music_file,
        cover_image=cover_image,
        uploader=None  # No authentication, uploader is None
    )

    uploader_payload = track.get("uploader") or {
        "id": "anonymous",
        "role": "guest",
        "email": None,
        "username": "anonymous",
    }

    return TrackCreateResponse(
        id=str(track["_id"]),
        title=track["title"],
        artist=track["artist"],
        emotions=track["emotions"],
        music_url=track["music_url"],
        cover_url=track["cover_url"],
        created_at=track["created_at"],
        uploader=TrackUploader(**uploader_payload)
    )
