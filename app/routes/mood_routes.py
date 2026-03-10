from fastapi import APIRouter, Depends
from app.schemas.mood_schema import MoodCheckin, MoodData, MoodStoreRequest, MoodPredictRequest, MoodQuestionPredictRequest, ValidateAnswerRequest, MoodOverallRequest
from app.services.mood_service import save_mood
from app.services.answer_validator import validate_answer, normalize_text
from app.ml.predictor import predict_with_probs
from app.services.auth_service import get_current_child
from app.schemas.auth_schema import TokenData

router = APIRouter(prefix="/mood", tags=["Mood"])

@router.post("/checkin")
def mood_checkin(data: MoodCheckin):
    result = save_mood(data.child_id, data.mood, data.note)
    return {"status": "success", "data": {
        "id": result.id,
        "child_id": result.child_id,
        "mood": result.mood,
        "note": result.note
    }}

@router.post("/store")
def store_mood(data: MoodStoreRequest, current_child: TokenData = Depends(get_current_child)):
    """
    Store mood data (protected endpoint - child JWT required)
    
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
    
    # Store mood with child_id from JWT token
    mood_doc = {
        "child_id": ObjectId(current_child.id),
        "mood": data.mood,
        "datetime": data.datetime
    }
    
    result = moods_col.insert_one(mood_doc)
    mood_doc["_id"] = result.inserted_id
    
    # Check if alert should be sent
    try:
        child = get_child_by_id(current_child.id)
        
        if child and child.get("alerts_consent", False):
            # Count bad moods in last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            bad_mood_count = moods_col.count_documents({
                "child_id": ObjectId(current_child.id),
                "mood": {"$in": ["Bad", "bad", "BAD"]},
                "datetime": {"$gte": seven_days_ago}
            })
            
            # Send alert if threshold reached
            if bad_mood_count >= BAD_MOOD_THRESHOLD:
                recipients = get_parent_and_trusted_emails(current_child.id)
                
                if recipients:
                    send_mood_alert(
                        recipients=recipients,
                        child_name=child.get("name", "the child"),
                        bad_mood_count=bad_mood_count
                    )
    except Exception as e:
        # Log error but don't fail the mood storage
        print(f"Alert check failed: {str(e)}")
    
    return {
        "status": "success",
        "data": {
            "_id": str(mood_doc["_id"]),
            "child_id": str(mood_doc["child_id"]),
            "mood": mood_doc["mood"],
            "datetime": mood_doc["datetime"]
        }
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
    # Define neutral override phrases (exact match after normalization)
    NEUTRAL_PHRASES = {
        "එහෙම විශේෂ දෙයක් නෑ",
        "විශේෂ දෙයක් නෑ",
        "විශේෂ නැහැ",
        "එහෙම දෙයක් නෑ",
        "කමක් නෑ",
        "අවුලක් නෑ",
        "වැඩක් නෑ"
    }
    
    # Normalize text
    normalized = normalize_text(data.text)
    
    # Check if empty
    if not normalized:
        return {
            "question_id": data.question_id,
            "text": data.text,
            "normalized": normalized,
            "mood": "Unknown",
            "confidence": 0.0,
            "probs": {},
            "reason": "EMPTY"
        }
    
    # Check if it's a neutral phrase override
    if normalized in NEUTRAL_PHRASES:
        return {
            "question_id": data.question_id,
            "text": data.text,
            "normalized": normalized,
            "mood": "Normal",
            "confidence": 1.0,
            "probs": {},
            "reason": "NEUTRAL_OVERRIDE"
        }
    
    # Fall back to ML prediction
    ml_result = predict_with_probs(data.text)
    
    return {
        "question_id": data.question_id,
        "text": data.text,
        "normalized": normalized,
        "mood": ml_result.get("mood", "Unknown"),
        "confidence": ml_result.get("confidence", 0.0),
        "probs": ml_result.get("probs", {}),
        "reason": "ML"
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
    
    Q1: Uses ML model prediction
    Q2-Q4: YES answers indicate problems (negative score), NO = neutral
    Q5: YES indicates happiness (positive score), NO = neutral
    Long descriptive answers use ML prediction with lower weight.
    
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
    
    # Define YES/NO word sets
    YES_WORDS = {"ඔව්", "ඔව්ව", "හරි", "ok", "okay", "ඔකේ"}
    NO_WORDS = {"නෑ", "නැහැ", "නොවෙයි", "no", "nope"}
    
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
        
        # Normalize text
        normalized = answer_text.strip().lower()
        normalized = " ".join(normalized.split())  # Collapse spaces
        
        question_info = {
            "question_id": question_id,
            "answer": answer_text,
            "mood": "Unknown",
            "score": 0,
            "confidence": 0.0
        }
        
        # Q1: Use ML model prediction
        if question_id == 1:
            if not normalized:
                question_info["mood"] = "Unknown"
                question_info["score"] = 0
            else:
                ml_result = predict_with_probs(answer_text)
                mood = ml_result.get("mood", "Unknown")
                confidence = ml_result.get("confidence", 0.0)
                
                # Map mood to score
                if mood in ["Happy", "happy", "HAPPY"]:
                    score = 2
                elif mood in ["Normal", "normal", "NORMAL"]:
                    score = 0
                elif mood in ["Bad", "bad", "BAD"]:
                    score = -2
                else:
                    score = 0
                
                question_info["mood"] = map_mood_to_sinhala(mood)
                question_info["score"] = score
                question_info["confidence"] = confidence
                total_score += score
        
        # Q2-Q4: YES = problems (negative), NO = neutral
        elif question_id in [2, 3, 4]:
            if normalized in YES_WORDS:
                # YES indicates a problem
                if question_id in [2, 3]:
                    score = -2
                else:  # Q4
                    score = -1
                question_info["mood"] = "දුකයි / හොඳ නෑ"
                question_info["score"] = score
                question_info["confidence"] = 1.0
                total_score += score
            elif normalized in NO_WORDS:
                # NO = no problem
                question_info["mood"] = "සතුටුයි"
                question_info["score"] = 0
                question_info["confidence"] = 1.0
            else:
                # Long text or descriptive answer
                word_count = len(normalized.split())
                if word_count >= 3 and normalized:
                    # Use ML with lower weight
                    ml_result = predict_with_probs(answer_text)
                    mood = ml_result.get("mood", "Unknown")
                    confidence = ml_result.get("confidence", 0.0)
                    
                    # Map with smaller weight
                    if mood in ["Happy", "happy", "HAPPY"]:
                        score = 1
                    elif mood in ["Normal", "normal", "NORMAL"]:
                        score = 0
                    elif mood in ["Bad", "bad", "BAD"]:
                        score = -1
                    else:
                        score = 0
                    
                    question_info["mood"] = map_mood_to_sinhala(mood)
                    question_info["score"] = score
                    question_info["confidence"] = confidence
                    total_score += score
                else:
                    # Short and ambiguous
                    question_info["mood"] = "Unknown"
                    question_info["score"] = 0
        
        # Q5: YES = happiness (positive), NO = neutral
        elif question_id == 5:
            if normalized in YES_WORDS:
                score = 2
                question_info["mood"] = "සතුටුයි"
                question_info["score"] = score
                question_info["confidence"] = 1.0
                total_score += score
            elif normalized in NO_WORDS:
                question_info["mood"] = "සාමාන්‍ය"
                question_info["score"] = 0
                question_info["confidence"] = 1.0
            else:
                # Long text or descriptive answer
                word_count = len(normalized.split())
                if word_count >= 3 and normalized:
                    # Use ML with lower weight
                    ml_result = predict_with_probs(answer_text)
                    mood = ml_result.get("mood", "Unknown")
                    confidence = ml_result.get("confidence", 0.0)
                    
                    # Map with smaller weight
                    if mood in ["Happy", "happy", "HAPPY"]:
                        score = 1
                    elif mood in ["Normal", "normal", "NORMAL"]:
                        score = 0
                    elif mood in ["Bad", "bad", "BAD"]:
                        score = -1
                    else:
                        score = 0
                    
                    question_info["mood"] = map_mood_to_sinhala(mood)
                    question_info["score"] = score
                    question_info["confidence"] = confidence
                    total_score += score
                else:
                    question_info["mood"] = "Unknown"
                    question_info["score"] = 0
        
        per_question.append(question_info)
    
    # Determine final mood from total score
    if total_score <= -3:
        final_mood = "Bad"
    elif -2 <= total_score <= 1:
        final_mood = "Normal"
    else:  # total_score >= 2
        final_mood = "Happy"
    
    return {
        "final_mood": final_mood,
        "total_score": total_score,
        "per_question": per_question
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
