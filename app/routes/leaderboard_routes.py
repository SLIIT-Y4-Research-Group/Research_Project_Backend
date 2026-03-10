from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.leaderboard_schema import LeaderboardCreateRequest, LeaderboardEntryResponse
from app.services.leaderboard_service import (
    create_entry,
    get_entry,
    list_entries,
    list_top,
    list_by_player,
    delete_entry
)

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


@router.post("", response_model=LeaderboardEntryResponse)
def create_leaderboard_entry(payload: LeaderboardCreateRequest):
    entry = create_entry(
        player_name=payload.player_name,
        score=payload.score,
        level=payload.level,
        time=payload.time
    )
    return LeaderboardEntryResponse(
        id=str(entry["_id"]),
        player_name=entry["player_name"],
        score=entry["score"],
        level=entry["level"],
        time=entry["time"],
        created_at=entry["created_at"]
    )


@router.get("/top", response_model=list[LeaderboardEntryResponse])
def get_top_scores(limit: int = Query(10, ge=1, le=100)):
    entries = list_top(limit)
    return [
        LeaderboardEntryResponse(
            id=str(e["_id"]),
            player_name=e["player_name"],
            score=e["score"],
            level=e["level"],
            time=e["time"],
            created_at=e["created_at"]
        )
        for e in entries
    ]


@router.get("", response_model=list[LeaderboardEntryResponse])
def get_leaderboard(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    entries = list_entries(skip=skip, limit=limit)
    return [
        LeaderboardEntryResponse(
            id=str(e["_id"]),
            player_name=e["player_name"],
            score=e["score"],
            level=e["level"],
            time=e["time"],
            created_at=e["created_at"]
        )
        for e in entries
    ]


@router.get("/player/{player_name}", response_model=list[LeaderboardEntryResponse])
def get_player_scores(
    player_name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    entries = list_by_player(player_name=player_name, skip=skip, limit=limit)
    return [
        LeaderboardEntryResponse(
            id=str(e["_id"]),
            player_name=e["player_name"],
            score=e["score"],
            level=e["level"],
            time=e["time"],
            created_at=e["created_at"]
        )
        for e in entries
    ]


@router.get("/{entry_id}", response_model=LeaderboardEntryResponse)
def get_leaderboard_entry(entry_id: str):
    entry = get_entry(entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    return LeaderboardEntryResponse(
        id=str(entry["_id"]),
        player_name=entry["player_name"],
        score=entry["score"],
        level=entry["level"],
        time=entry["time"],
        created_at=entry["created_at"]
    )


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_leaderboard_entry(entry_id: str):
    delete_entry(entry_id)
    return None
