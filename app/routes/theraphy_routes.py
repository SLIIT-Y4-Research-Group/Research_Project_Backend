"""
Therapy Engagement Router
Handles logging therapy sessions and serving report data for parents
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
import logging

from app.schemas.auth_schema import TokenData
from app.services.auth_service import get_current_child, get_current_parent
from app.services.therapy_service import (
    create_therapy_session,
    get_therapy_summary_for_child,
    get_therapy_sessions_for_child,
)
from app.services.child_service import verify_child_belongs_to_parent
from app.database.db import drawing_analyses, children_col
from app.schemas.therapy_schema import TherapySessionCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/therapy", tags=["Therapy Engagement"])


# ── Child endpoints ────────────────────────────────────────────────────────────

@router.post("/session")
def log_therapy_session(
    request: TherapySessionCreate,
    current_child: TokenData = Depends(get_current_child),
):
    """
    Called by Flutter when a child completes or exits a therapy activity.
    Log bubble_pop or breath_game session details.
    """
    try:
        doc = create_therapy_session(
            child_id=current_child.id,
            activity_type=request.activity_type,
            duration_seconds=request.duration_seconds,
            score=request.score,
            rounds_completed=request.rounds_completed,
            triggered_by_emotion=request.triggered_by_emotion,
        )
        logger.info(
            f"Therapy session logged: child={current_child.id}, "
            f"type={request.activity_type}, duration={request.duration_seconds}s"
        )
        return {
            "status": "success",
            "session_id": str(doc["_id"]),
            "message": "Session recorded",
        }
    except Exception as e:
        logger.error(f"Failed to log therapy session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log session: {str(e)}",
        )


# ── Parent report endpoint ─────────────────────────────────────────────────────

@router.get("/report/{child_id}")
def get_child_report(
    child_id: str,
    days: int = 30,
    current_parent: TokenData = Depends(get_current_parent),
):
    """
    Full aggregated report for a child:
    - Emotion trend data (from drawing_analyses)
    - Weekly emotion breakdown
    - Therapy engagement summary
    - Per-session therapy timeline
    - Drawing feature trends (color pressure, stroke control)

    Used by Flutter to render charts and generate a downloadable PDF report.
    """
    try:
        # Verify ownership
        if not verify_child_belongs_to_parent(child_id, current_parent.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: child does not belong to this parent",
            )

        child = children_col.find_one({"_id": ObjectId(child_id)})
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")

        since = datetime.utcnow() - timedelta(days=days)

        # ── Drawing emotion data ───────────────────────────────────────────
        drawings = list(
            drawing_analyses.find(
                {"child_id": child_id, "created_at": {"$gte": since}}
            ).sort("created_at", 1)
        )

        emotion_timeline = []
        weekly_buckets: dict = {}    # "YYYY-WW" → {happy: 0, sad: 0}
        feature_timeline = []

        for d in drawings:
            date_str = d["created_at"].strftime("%Y-%m-%d")
            week_key = d["created_at"].strftime("%Y-W%W")
            emotion_label = d.get("emotion", {}).get("label", "unknown")
            confidence = d.get("emotion", {}).get("confidence", "low")

            emotion_timeline.append({
                "date": date_str,
                "emotion": emotion_label,
                "confidence": confidence,
                "analysis_id": str(d["_id"]),
            })

            # Weekly bucket
            if week_key not in weekly_buckets:
                weekly_buckets[week_key] = {"week": week_key, "happy": 0, "sad": 0, "total": 0}
            weekly_buckets[week_key][emotion_label] = weekly_buckets[week_key].get(emotion_label, 0) + 1
            weekly_buckets[week_key]["total"] += 1

            # Feature trends from llm_review
            llm = d.get("llm_review", {}) or {}
            stroke = llm.get("stroke_analysis", {}) or {}
            color = llm.get("color_analysis", {}) or {}
            feature_timeline.append({
                "date": date_str,
                "stroke_pressure": stroke.get("pressure", ""),
                "stroke_control": stroke.get("control", ""),
                "detail_level": stroke.get("detail_level", ""),
                "palette_mood": color.get("palette_mood", ""),
                "warm_cool": color.get("warm_cool_balance", ""),
            })

        # Emotion counts for pie chart
        emotion_counts = {"happy": 0, "sad": 0}
        for e in emotion_timeline:
            label = e["emotion"]
            emotion_counts[label] = emotion_counts.get(label, 0) + 1

        total_drawings = len(drawings)
        sad_pct = round(emotion_counts.get("sad", 0) / total_drawings * 100, 1) if total_drawings else 0
        happy_pct = round(emotion_counts.get("happy", 0) / total_drawings * 100, 1) if total_drawings else 0

        weekly_list = sorted(weekly_buckets.values(), key=lambda x: x["week"])

        # ── Therapy data ───────────────────────────────────────────────────
        therapy = get_therapy_summary_for_child(child_id, days=days)

        # Therapy per-week buckets
        therapy_weekly: dict = {}
        for s in therapy["sessions"]:
            wk = s["created_at"].strftime("%Y-W%W")
            if wk not in therapy_weekly:
                therapy_weekly[wk] = {"week": wk, "bubble_pop": 0, "breath_game": 0, "total_minutes": 0}
            therapy_weekly[wk][s["activity_type"]] = therapy_weekly[wk].get(s["activity_type"], 0) + 1
            therapy_weekly[wk]["total_minutes"] += round(s.get("duration_seconds", 0) / 60, 1)

        therapy_weekly_list = sorted(therapy_weekly.values(), key=lambda x: x["week"])

        # Therapy after sad drawings (correlation)
        sad_sessions_with_therapy = 0
        sad_drawing_dates = {e["date"] for e in emotion_timeline if e["emotion"] == "sad"}
        for s in therapy["sessions"]:
            sdate = s["created_at"].strftime("%Y-%m-%d")
            if sdate in sad_drawing_dates:
                sad_sessions_with_therapy += 1

        engagement_rate = (
            round(sad_sessions_with_therapy / emotion_counts.get("sad", 1) * 100, 1)
            if emotion_counts.get("sad", 0) > 0 else 0
        )

        return {
            "status": "success",
            "child_name": child.get("name"),
            "child_age": child.get("age"),
            "report_period_days": days,
            "generated_at": datetime.utcnow().isoformat(),

            # Summary numbers (for stat cards)
            "summary": {
                "total_drawings": total_drawings,
                "happy_count": emotion_counts.get("happy", 0),
                "sad_count": emotion_counts.get("sad", 0),
                "happy_pct": happy_pct,
                "sad_pct": sad_pct,
                "total_therapy_sessions": therapy["total_sessions"],
                "total_therapy_minutes": therapy["total_duration_minutes"],
                "therapy_engagement_rate_pct": engagement_rate,
            },

            # Time-series emotion line chart data
            "emotion_timeline": emotion_timeline,

            # Weekly bar/stacked chart data
            "weekly_emotion": weekly_list,

            # Feature trend data (stroke, color over time)
            "feature_timeline": feature_timeline,

            # Therapy engagement data
            "therapy_summary": {
                "total_sessions": therapy["total_sessions"],
                "bubble_pop_sessions": therapy["bubble_pop_sessions"],
                "breath_game_sessions": therapy["breath_game_sessions"],
                "total_duration_minutes": therapy["total_duration_minutes"],
                "avg_bubble_pop_score": therapy["avg_bubble_pop_score"],
                "last_session_at": therapy["last_session_at"].isoformat() if therapy["last_session_at"] else None,
            },

            # Weekly therapy engagement for bar chart
            "therapy_weekly": therapy_weekly_list,

            # Full session list for timeline
            "therapy_sessions": [
                {
                    "date": s["created_at"].strftime("%Y-%m-%d"),
                    "activity_type": s["activity_type"],
                    "duration_seconds": s.get("duration_seconds", 0),
                    "score": s.get("score"),
                    "rounds_completed": s.get("rounds_completed"),
                    "triggered_by_emotion": s.get("triggered_by_emotion"),
                }
                for s in therapy["sessions"]
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}",
        )