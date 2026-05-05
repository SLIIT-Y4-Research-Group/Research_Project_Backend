from typing import List, Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.schemas.auth_schema import TokenData
from app.schemas.music_schema import (
    CompleteMusicSessionRequest,
    CompleteMusicSessionResponse,
    PersonalizedTrackResponse,
    StartMusicSessionRequest,
    StartMusicSessionResponse,
    TrackCreateResponse,
    TrackResponse,
    TrackUploader,
)
from app.services.auth_service import get_current_child, get_current_user
from app.services.music_service import create_track
from app.services.music_recommendation_service import (
    complete_music_session,
    personalized_recommendations,
    start_music_session,
)
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


@router.post("/session/start", response_model=StartMusicSessionResponse)
def start_listening_session(
    request: StartMusicSessionRequest,
    current_user: TokenData = Depends(get_current_child),
):
    session = start_music_session(
        user_id=current_user.id,
        track_id=request.track_id,
        before_image=request.before_image,
    )
    return StartMusicSessionResponse(
        session_id=str(session["_id"]),
        track_id=session["track_id"],
        user_id=session["user_id"],
        started_at=session["started_at"],
        before_emotion=session["before_emotion"],
    )


@router.post("/session/{session_id}/complete", response_model=CompleteMusicSessionResponse)
def complete_listening_session(
    session_id: str,
    request: CompleteMusicSessionRequest,
    current_user: TokenData = Depends(get_current_child),
):
    session = complete_music_session(
        session_id=session_id,
        user_id=current_user.id,
        after_image=request.after_image,
        satisfaction_rating=request.satisfaction_rating,
    )
    return CompleteMusicSessionResponse(
        session_id=str(session["_id"]),
        track_id=session["track_id"],
        user_id=session["user_id"],
        started_at=session["started_at"],
        ended_at=session["ended_at"],
        before_emotion=session["before_emotion"],
        after_emotion=session["after_emotion"],
        satisfaction_rating=session["satisfaction_rating"],
        emotion_changed=session["emotion_changed"],
        improvement_score=session["improvement_score"],
        impact_score=session["impact_score"],
    )


@router.get("/recommendations", response_model=List[PersonalizedTrackResponse])
def get_personalized_recommendations(
    current_emotion: Optional[str] = Query(default=None),
    current_user: TokenData = Depends(get_current_child),
):
    ranked_tracks = personalized_recommendations(
        user_id=current_user.id,
        current_emotion=current_emotion,
    )
    return [
        PersonalizedTrackResponse(
            id=str(track["_id"]),
            title=track.get("title", "Unknown Title"),
            artist=track.get("artist", "Unknown Artist"),
            emotions=track.get("emotions", []),
            music_url=track.get("music_url", ""),
            cover_url=track.get("cover_url"),
            created_at=track["created_at"],
            recommendation_score=float(track.get("recommendation_score", 0.0)),
        )
        for track in ranked_tracks
    ]
