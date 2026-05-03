from fastapi import APIRouter, Depends
from app.schemas.mood_schema import MoodCheckin, MoodData, MoodStoreRequest, MoodPredictRequest, MoodQuestionPredictRequest, ValidateAnswerRequest, MoodOverallRequest, AlertPermissionResponse
from app.services.mood_service import save_mood, get_today_mood_for_child, get_weekly_moods_for_child
from app.services.answer_validator import validate_answer, normalize_text
from app.ml.predictor import predict_with_probs
from app.services.auth_service import get_current_child
from app.schemas.auth_schema import TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mood", tags=["Mood"])


CONFLICT_NEGATIVE_KEYWORDS = {
    "ගහගත්තා",
    "ගහගත්ත",
    "ගහ ගත්තා",
    "ගහගත්තු",
    "ගැහුවා",
    "ගැහුවේ",
    "රණ්ඩු",
    "රණ්ඩුවක්",
    "බැනගත්තා",
    "ගොඩගැහිලා",
    "ගැටුම",
}


def simple_score_from_mood(mood: str) -> int:
    """Map mood label to a simple score (+1, 0, -1)."""
    mood_lower = str(mood).lower()
    if mood_lower == "happy":
        return 1
    if mood_lower == "bad":
        return -1
    return 0


def evaluate_answer(question_id: int, text: str) -> dict:
    """
    Unified evaluation pipeline used by both /predict_question and /predict_overall.

    Flow:
    1) validate_answer(question_id, text)
    2) route by status
    3) optionally run ML and compute score contribution
    """
    validation = validate_answer(question_id, text)
    status = validation.get("status", "UNKNOWN")
    normalized = validation.get("normalized", normalize_text(text or ""))

    result = {
        "question_id": question_id,
        "text": text,
        "validation": validation,
        "status": status,
        "normalized": normalized,
        "mood": "Unknown",
        "confidence": 0.0,
        "probs": {},
        "score": 0,
        "reason": status,
        "used_ml": False,
    }

    # Early return for invalid/non-informative answers.
    if status in {"EMPTY", "NEED_MORE_INFO", "IRRELEVANT"}:
        return result

    # Rule-only yes/no handling for Q2-Q5.
    if status == "YES_NO" and question_id in [2, 3, 4, 5]:
        yn_value = validation.get("yn_value")

        if yn_value not in {"YES", "NO"}:
            # Safe fallback: do not score ambiguous YES_NO payloads.
            result["status"] = "NEED_MORE_INFO"
            result["reason"] = "INVALID_YN_VALUE"
            return result

        if question_id in [2, 3, 4]:
            if yn_value == "YES":
                result["mood"] = "Bad"
                result["score"] = -1
            else:
                result["mood"] = "Happy"
                result["score"] = 1
        else:  # question_id == 5
            if yn_value == "YES":
                result["mood"] = "Happy"
                result["score"] = 1
            else:
                result["mood"] = "Normal"
                result["score"] = 0

        result["confidence"] = 1.0
        result["reason"] = "YES_NO_RULE"
        return result

    # Rule-only direct mood for Q1.
    if status == "Q1_DIRECT_MOOD" and question_id == 1:
        direct_mood = validation.get("direct_mood", "Normal")
        result["mood"] = direct_mood
        result["score"] = simple_score_from_mood(direct_mood)
        result["confidence"] = 1.0
        result["reason"] = "Q1_DIRECT_MOOD"
        return result

    # Rule-only neutral phrase for Q2-Q5 (do not call ML).
    if status == "NEUTRAL_PHRASE" and question_id in [2, 3, 4, 5]:
        result["mood"] = "Normal"
        result["score"] = 0
        result["confidence"] = 1.0
        result["reason"] = "NEUTRAL_PHRASE"
        return result

    # Rule-only override for strong conflict/violence phrases.
    if status == "VALID_TEXT":
        if any(keyword in normalized for keyword in CONFLICT_NEGATIVE_KEYWORDS):
            result["mood"] = "Bad"
            result["confidence"] = 1.0
            result["score"] = -1
            result["reason"] = "RULE_CONFLICT_BAD"
            return result

    # ML path for valid descriptive text.
    if status == "VALID_TEXT":
        ml_result = predict_with_probs(text)
        mood = ml_result.get("mood", "Unknown")
        result["mood"] = mood
        result["confidence"] = ml_result.get("confidence", 0.0)
        result["probs"] = ml_result.get("probs", {})
        result["used_ml"] = True
        result["reason"] = "ML"
        result["score"] = simple_score_from_mood(mood)
        return result

    # Defensive fallback for unknown statuses.
    return result

@router.post("/checkin")
def mood_checkin(data: MoodCheckin):
    result = save_mood(data.child_id, data.mood, data.note)
    return {"status": "success", "data": {
        "id": result.id,
        "child_id": result.child_id,
        "mood": result.mood,
        "note": result.note
    }}

@router.get("/today")
def get_today_mood(current_child: TokenData = Depends(get_current_child)):
    """
    Get today's mood for the current child
    
    Returns:
    - If mood recorded today: {status: "success", mood: {_id, mood, datetime, date_key}, completed: true}
    - If no mood today: {status: "success", mood: null, completed: false}
    """
    mood = get_today_mood_for_child(current_child.id)
    
    if mood:
        return {
            "status": "success",
            "completed": True,
            "mood": {
                "_id": str(mood["_id"]),
                "mood": mood["mood"],
                "datetime": mood["datetime"],
                "date_key": mood.get("date_key")
            }
        }
    else:
        return {
            "status": "success",
            "completed": False,
            "mood": None
        }

@router.get("/history")
def get_mood_history(
    days: int = 7,
    current_child: TokenData = Depends(get_current_child)
):
    """
    Get mood history for the last N days (default 7)
    
    Returns list of dates with mood status:
    [
        {date: "2026-03-11", mood: "Bad", completed: true, datetime: "..."},
        {date: "2026-03-10", mood: null, completed: false, datetime: null},
        ...
    ]
    """
    from datetime import datetime, timedelta
    
    # Limit to reasonable range
    if days < 1:
        days = 7
    if days > 30:
        days = 30
    
    moods = get_weekly_moods_for_child(current_child.id, days)
    
    return {
        "status": "success",
        "days": days,
        "moods": moods
    }

@router.post("/store")
def store_mood(data: MoodStoreRequest, current_child: TokenData = Depends(get_current_child)):
    """
    Store mood data (protected endpoint - child JWT required)
    
    NEW: Enforces one mood per day per child.
    If mood already exists for today, returns "already_exists" status.
    
    After storing, checks if alert should be sent based on:
    - 7-day bad mood count >= threshold
    - Child has enabled alerts_consent
    """
    from datetime import datetime, timedelta
    from app.database.db import moods_col, children_col
    from app.services.child_service import get_child_by_id
    from app.services.trusted_service import get_parent_and_trusted_emails
    from app.services.email_service import send_mood_alert
    from app.core.config import BAD_MOOD_THRESHOLD
    from bson import ObjectId
    from app.services.mood_service import create_daily_mood_if_not_exists
    
    logger.debug(f"POST /mood/store - child_id: {current_child.id}, mood: {data.mood}, datetime: {data.datetime}")
    
    # NEW: Use create_daily_mood_if_not_exists to enforce one mood per day
    created, mood_doc = create_daily_mood_if_not_exists(
        child_id=current_child.id,
        mood=data.mood,
        dt=data.datetime
    )
    
    # If mood already exists for today, return 409 Conflict
    if not created:
        logger.warning(f"Mood already exists for child {current_child.id} on {mood_doc.get('date_key')} - returning 409 Conflict")
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Mood already recorded for today",
                "date_key": mood_doc.get("date_key"),
                "existing_mood": mood_doc["mood"],
                "recorded_at": mood_doc["datetime"]
            }
        )
    
    # Mood successfully created - now check for alert logic
    alert_permission_needed = False
    bad_mood_count = 0
    
    logger.debug(f"Mood created successfully for child {current_child.id} - checking alert logic")
    
    try:
        child = get_child_by_id(current_child.id)
        
        # Only check if child exists AND has global consent enabled
        if child and child.get("alerts_consent", False):
            # Count bad moods in last 7 days using date_key (timezone-consistent)
            from app.services.mood_service import get_today_date_key, get_date_key_from_datetime
            today_key = get_today_date_key()
            date_keys_7d = []
            from datetime import datetime as dt_class
            today_dt = dt_class.strptime(today_key, "%Y-%m-%d")
            for i in range(7):
                d = today_dt - timedelta(days=i)
                date_keys_7d.append(d.strftime("%Y-%m-%d"))
            
            bad_mood_count = moods_col.count_documents({
                "child_id": ObjectId(current_child.id),
                "mood": {"$in": ["Bad", "bad", "BAD"]},
                "date_key": {"$in": date_keys_7d}
            })
            
            logger.info(f"Alert check - Child: {current_child.id}, Bad mood count (7 days): {bad_mood_count}, Threshold: {BAD_MOOD_THRESHOLD}, Alerts enabled: {child.get('alerts_consent')}")
            
            # NEW BEHAVIOR: Mark pending alert instead of sending immediately
            if bad_mood_count >= BAD_MOOD_THRESHOLD:
                logger.warning(f"🚨 Bad mood threshold reached! Child {current_child.id} has {bad_mood_count} bad moods (threshold: {BAD_MOOD_THRESHOLD})")
                # Check if there's already a pending alert to avoid duplicates
                pending_alert = child.get("pending_alert", {})
                if not pending_alert.get("exists", False):
                    # Mark alert as pending (requires student permission)
                    from app.services.child_service import set_pending_alert
                    set_pending_alert(current_child.id, bad_mood_count, mood_doc["_id"])
                    logger.info(f"✓ Pending alert set for child {current_child.id} - permission dialog will be shown")
                else:
                    logger.debug(f"Pending alert already exists for child {current_child.id}")
                
                # Signal to frontend that permission dialog should be shown
                alert_permission_needed = True
                logger.info(f"✓ Setting alert_permission_needed=True in response")
    except Exception as e:
        # Log error but don't fail the mood storage
        print(f"Alert check failed: {str(e)}")
    
    return {
        "status": "success",
        "data": {
            "_id": str(mood_doc["_id"]),
            "child_id": str(mood_doc["child_id"]),
            "mood": mood_doc["mood"],
            "datetime": mood_doc["datetime"],
            "date_key": mood_doc["date_key"]
        },
        "alert_permission_needed": alert_permission_needed,
        "bad_mood_count": bad_mood_count if alert_permission_needed else None
    }

@router.post("/predict")
def mood_predict(data: MoodPredictRequest):
    return predict_with_probs(data.text)

@router.post("/predict_question")
def predict_question(data: MoodQuestionPredictRequest):
    """
    Question-aware mood prediction with neutral phrase override.
    
    Applies neutral phrase detection BEFORE ML model:
    - If text matches specific neutral phrases (e.g., "විශේෂ දෙයක් නෑ"), returns Normal mood
    - Otherwise, uses ML model prediction
    
    Returns:
        JSON with question_id, text, normalized, mood, confidence, probs, and reason
    """
    evaluation = evaluate_answer(data.question_id, data.text)

    # Keep legacy response keys and add non-breaking details.
    return {
        "question_id": data.question_id,
        "text": data.text,
        "normalized": evaluation.get("normalized", ""),
        "mood": evaluation.get("mood", "Unknown"),
        "confidence": evaluation.get("confidence", 0.0),
        "probs": evaluation.get("probs", {}),
        "reason": evaluation.get("reason", "UNKNOWN"),
        "validation": evaluation.get("validation", {}),
        "score": evaluation.get("score", 0)
    }

@router.post("/validate_answer")
def validate_student_answer(data: ValidateAnswerRequest):
    """
    Validate student answer for relevance and informativeness.
    
    Returns validation result with status, normalized text, and yes/no flag.
    """
    result = validate_answer(data.question_id, data.text)
    return result

@router.post("/predict_overall")
def predict_overall(data: MoodOverallRequest):
    """
    Predict overall mood based on 5 question answers using hybrid rule-based + ML approach.
    
    Q1: Uses ML model prediction (required by frontend, but backend handles empty safely)
    Q2-Q5: YES answers indicate problems (negative score), NO = neutral, EMPTY = skipped
    Long descriptive answers use ML prediction with lower weight.
    
    Skipped questions (empty string) contribute: mood="Skipped", score=0, confidence=0.0
    
    Returns:
        JSON with final_mood, total_score, and per_question breakdown
    """
    # Helper function to map English mood to Sinhala display text
    def map_mood_to_sinhala(mood: str) -> str:
        mood_lower = mood.lower()
        if mood_lower == "happy":
            return "සතුටුයි"
        elif mood_lower == "normal":
            return "සාමාන්‍ය"
        elif mood_lower == "bad":
            return "දුකයි / හොඳ නෑ"
        else:
            return mood  # Return as-is if unknown
    
    # Initialize results
    per_question = []
    total_score = 0
    
    # Ensure we have at least one answer
    if not data.answers or len(data.answers) == 0:
        return {
            "final_mood": "Unknown",
            "total_score": 0,
            "per_question": []
        }
    
    # Process each question
    for i in range(5):
        question_id = i + 1
        answer_text = data.answers[i] if i < len(data.answers) else ""
        
        evaluation = evaluate_answer(question_id, answer_text)
        status = evaluation.get("status", "UNKNOWN")

        question_info = {
            "question_id": question_id,
            "answer": answer_text,
            "mood": "Unknown",
            "score": 0,
            "confidence": 0.0,
            "validation": evaluation.get("validation", {})
        }

        # Keep legacy skipped behavior for empty answers.
        if status == "EMPTY":
            question_info["mood"] = "Skipped"
            question_info["score"] = 0
            question_info["confidence"] = 0.0
            per_question.append(question_info)

            continue

        score = evaluation.get("score", 0)
        mood = evaluation.get("mood", "Unknown")
        confidence = evaluation.get("confidence", 0.0)

        # Keep existing frontend-facing Sinhala labels for rule branches.
        if status == "YES_NO" and question_id in [2, 3, 4]:
            question_info["mood"] = "දුකයි / හොඳ නෑ" if score < 0 else "සතුටුයි"
        elif status == "YES_NO" and question_id == 5:
            question_info["mood"] = "සතුටුයි" if score > 0 else "සාමාන්‍ය"
        elif mood == "Unknown":
            question_info["mood"] = "Unknown"
        else:
            question_info["mood"] = map_mood_to_sinhala(mood)

        question_info["score"] = score
        question_info["confidence"] = confidence
        total_score += score

        per_question.append(question_info)
    
    # Determine final mood from total score (simple thresholds)
    if total_score >= 2:
        final_mood = "Happy"
    elif total_score <= -1:
        final_mood = "Bad"
    else:
        final_mood = "Normal"
    
    return {
        "final_mood": final_mood,
        "total_score": total_score,
        "per_question": per_question
    }

@router.post("/respond_alert_permission")
def respond_alert_permission(
    data: AlertPermissionResponse, 
    current_child: TokenData = Depends(get_current_child)
):
    """
    Student responds to alert permission request (NEW: per-incident permission)
    
    After /mood/store returns alert_permission_needed=true, frontend shows dialog.
    Student approves or denies sending the alert email.
    
    Request body:
    {
        "approve": true   // or false
    }
    
    If approved: sends email to parent + trusted contacts
    If denied: no email sent
    Either way: clears pending alert flag
    """
    from fastapi import HTTPException
    from app.services.child_service import get_child_by_id, clear_pending_alert
    from app.services.trusted_service import get_parent_and_trusted_emails
    from app.services.email_service import send_mood_alert
    
    # Load child record
    child = get_child_by_id(current_child.id)
    
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    # Check if there's a pending alert
    pending_alert = child.get("pending_alert", {})
    
    if not pending_alert.get("exists", False):
        return {
            "status": "success",
            "message": "No pending alert to respond to"
        }
    
    # Handle student's decision
    if data.approve:
        logger.info(f"📧 Student {current_child.id} ({child.get('name')}) APPROVED alert - sending emails")
        
        # Student APPROVED - send email alerts
        recipients = get_parent_and_trusted_emails(current_child.id)
        logger.info(f"📧 Email recipients: {recipients}")
        
        email_sent = False
        if recipients:
            try:
                logger.info(f"📧 Attempting to send alert to {len(recipients)} recipient(s)")
                email_result = send_mood_alert(
                    recipients=recipients,
                    child_name=child.get("name", "the child"),
                    bad_mood_count=pending_alert.get("bad_mood_count", 0)
                )
                email_sent = bool(email_result)
                if email_sent:
                    logger.info(f"✅ SUCCESS: Email sent to {recipients}")
                else:
                    logger.error(f"❌ FAILED: send_mood_alert returned False")
            except Exception as e:
                logger.error(f"❌ EXCEPTION sending email: {str(e)}", exc_info=True)
                email_sent = False
        else:
            logger.warning(f"⚠️ No recipients found for child {current_child.id}")
        
        # Clear pending alert
        clear_pending_alert(current_child.id)
        logger.info(f"✓ Cleared pending alert for child {current_child.id}")
        
        return {
            "status": "success",
            "message": "Alert sent to parent and trusted contacts" if email_sent else "Alert approved but email sending failed",
            "email_sent": email_sent,
            "recipients_count": len(recipients) if recipients else 0
        }
    else:
        # Student DECLINED - do not send email
        logger.info(f"❌ Student {current_child.id} ({child.get('name')}) DECLINED alert - no email sent")
        clear_pending_alert(current_child.id)
        
        return {
            "status": "success",
            "message": "Alert not sent (student declined)",
            "email_sent": False
        }


# ============================================================================
# Example API Requests
# ============================================================================
#
# POST /mood/predict_question
# Request:
# {
#   "question_id": 1,
#   "text": "විශේෂ දෙයක් නෑ"
# }
# Response:
# {
#   "question_id": 1,
#   "text": "විශේෂ දෙයක් නෑ",
#   "normalized": "විශේෂ දෙයක් නෑ",
#   "mood": "Normal",
#   "confidence": 1.0,
#   "probs": {},
#   "reason": "NEUTRAL_OVERRIDE"
# }
#
# POST /mood/predict_question
# Request:
# {
#   "question_id": 1,
#   "text": "අද දවස හොඳයි"
# }
# Response:
# {
#   "question_id": 1,
#   "text": "අද දවස හොඳයි",
#   "normalized": "අද දවස හොඳයි",
#   "mood": "Happy",
#   "confidence": 0.95,
#   "probs": {"Happy": 0.95, "Normal": 0.03, "Bad": 0.02},
#   "reason": "ML"
# }
