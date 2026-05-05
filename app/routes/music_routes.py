from fastapi import APIRouter, Depends, File, Form, UploadFile, Query
from app.schemas.auth_schema import TokenData
from app.schemas.music_schema import TrackCreateResponse, TrackUploader, TracksListResponse, TrackResponse
from app.services.auth_service import get_current_user
from app.services.music_service import create_track, get_tracks_by_emotion

router = APIRouter(prefix="/music", tags=["Music"])


@router.get("/tracks", response_model=TracksListResponse)
def get_tracks(emotion: str = Query(..., description="Emotion to filter tracks (e.g., sad, happy, angry)")):
    """
    Get all music tracks that match the specified emotion
    
    Query params:
    - emotion: Emotion to filter by (case-insensitive)
    
    Example: GET /music/tracks?emotion=sad
    """
    tracks = get_tracks_by_emotion(emotion)
    
    track_responses = []
    for track in tracks:
        # Handle tracks without uploader info (backward compatibility)
        if track.get("uploader"):
            uploader = TrackUploader(**track["uploader"])
        else:
            # Default uploader for old tracks
            uploader = TrackUploader(
                id="unknown",
                role="admin",
                email=None,
                username="System"
            )
        
        track_responses.append(
            TrackResponse(
                id=track["_id"],
                title=track["title"],
                artist=track["artist"],
                emotions=track["emotions"],
                music_url=track["music_url"],
                cover_url=track["cover_url"],
                created_at=track["created_at"],
                uploader=uploader
            )
        )
    
    return TracksListResponse(
        tracks=track_responses,
        count=len(track_responses)
    )


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

    return TrackCreateResponse(
        id=str(track["_id"]),
        title=track["title"],
        artist=track["artist"],
        emotions=track["emotions"],
        music_url=track["music_url"],
        cover_url=track["cover_url"],
        created_at=track["created_at"],
        uploader=TrackUploader(**track["uploader"])
    )
