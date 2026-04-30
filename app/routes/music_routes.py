from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.schemas.auth_schema import TokenData
from app.schemas.music_schema import TrackCreateResponse, TrackUploader
from app.services.auth_service import get_current_user
from app.services.music_service import create_track

router = APIRouter(prefix="/music", tags=["Music"])


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
