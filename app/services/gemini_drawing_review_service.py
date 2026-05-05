import io
import json
import time
import random
from typing import Dict, Any, List, Tuple
from PIL import Image
from google import genai

from app.core.config import (
    GEMINI_API_KEYS,
    GEMINI_MODEL,
    ENABLE_GEMINI_REVIEW,
)

_clients: List[Tuple[int, genai.Client]] = []

for index, api_key in enumerate(GEMINI_API_KEYS, start=1):
    try:
        _clients.append((index, genai.Client(api_key=api_key)))
    except Exception as e:
        print(f"[Gemini] Failed to initialize key_{index}: {e}")

_current_key_index = 0
_blocked_keys: Dict[int, float] = {}

RATE_LIMIT_COOLDOWN_SECONDS = 90
MAX_RETRIES_PER_KEY = 1


def _is_rate_limit_error(error_text: str) -> bool:
    text = error_text.lower()
    return (
        "429" in text
        or "quota" in text
        or "rate limit" in text
        or "resource_exhausted" in text
        or "too many requests" in text
    )


def _is_key_temporarily_blocked(key_number: int) -> bool:
    blocked_until = _blocked_keys.get(key_number)
    if blocked_until is None:
        return False

    if time.time() >= blocked_until:
        _blocked_keys.pop(key_number, None)
        return False

    return True


def _mark_key_blocked(key_number: int):
    _blocked_keys[key_number] = time.time() + RATE_LIMIT_COOLDOWN_SECONDS
    print(
        f"[Gemini] key_{key_number} temporarily blocked for "
        f"{RATE_LIMIT_COOLDOWN_SECONDS}s due to rate/quota limit"
    )


def _ordered_clients_for_failover() -> List[Tuple[int, genai.Client]]:
    global _current_key_index

    if not _clients:
        return []

    ordered = []

    for offset in range(len(_clients)):
        idx = (_current_key_index + offset) % len(_clients)
        ordered.append(_clients[idx])

    _current_key_index = (_current_key_index + 1) % len(_clients)

    return ordered


def _call_gemini_with_failover(contents):
    if not _clients:
        raise RuntimeError("No Gemini API keys configured.")

    errors = []

    for key_number, client in _ordered_clients_for_failover():
        if _is_key_temporarily_blocked(key_number):
            errors.append(f"key_{key_number}: skipped because cooldown active")
            continue

        for attempt in range(1, MAX_RETRIES_PER_KEY + 1):
            try:
                print(
                    f"[Gemini] Trying key_{key_number}, "
                    f"attempt {attempt}, model={GEMINI_MODEL}"
                )

                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=contents,
                )

                text = (response.text or "").strip()

                if not text:
                    raise RuntimeError("Gemini returned empty response")

                print(f"[Gemini] Success with key_{key_number}")
                return text

            except Exception as e:
                error_text = str(e)
                errors.append(f"key_{key_number}: {error_text}")
                print(f"[Gemini] Error with key_{key_number}: {error_text}")

                if _is_rate_limit_error(error_text):
                    _mark_key_blocked(key_number)
                    break

                time.sleep(0.8 + random.random())

    raise RuntimeError("All Gemini API keys failed: " + " | ".join(errors))
# ─── Prompt for SCAN / UPLOAD (uses CV analysis data + image) ───────────────

SCAN_PROMPT_TEMPLATE = """
You are a specialist child psychologist and art therapist with 20+ years of experience 
interpreting children's drawings for emotional wellbeing assessment.

You are analyzing a drawing submitted by a child. This is NOT a clinical diagnosis — 
it is a compassionate, in-depth observation report for parents.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHILD CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Name: {child_name}
- Age: {child_age}
- Child's note about the drawing: {note}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TECHNICAL ANALYSIS FROM LOCAL SYSTEM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{analysis_payload}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK — DEEP VISUAL + PSYCHOLOGICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Study the image carefully and produce a rich, layered analysis:

1. EMOTION CLASSIFICATION
   - Classify overall emotion as ONLY: happy OR sad
   - Look beyond surface colors — prioritize facial expressions, body language of figures,
     symbolic content, relational dynamics between elements

2. OBJECT DETECTION (from the image itself — do NOT rely on automated detector)
   Identify ALL meaningful visual elements:
   - Human/animal figures (expressions, posture, isolation vs grouping)
   - Nature elements (sun, clouds, rain, trees, flowers — wilting vs blooming?)
   - Structures (houses, walls, fences, barriers, doors)
   - Symbolic objects (hearts, crosses, stars, lightning, dark scribbles)
   - Relational symbols (holding hands, pushing away, separation lines)
   - Abstract marks (heavy scribbling, dark areas, erasures, pressing)
   For EACH object: describe WHERE it appears, HOW it's drawn, and WHAT it may suggest psychologically

3. COLOR PSYCHOLOGY (deep read)
   - List all colors used and their proportions
   - Analyze color choices relative to the child's age (age {child_age})
   - Consider: Are colors age-appropriate? Unusually dark/light? Applied with pressure?
   - What emotional states do these color combinations suggest?
   - Compare warm vs cool color balance
   - Note any notable absence of color (e.g., no skin tones, no green in nature scenes)

4. SPATIAL ARRANGEMENT (psychological meaning)
   - Where are key figures placed? (center = self-importance; corners = anxiety/withdrawal)
   - Are figures connected or separated?
   - Is there empty space (loneliness) or crowding (overwhelm)?
   - Are figures large or small relative to page? (size = perceived importance/power)
   - Is there a clear ground line? (developmental and emotional indicator)
   - Are there any barriers or dividing lines between figures?

5. STROKE & LINE QUALITY (psychological read)
   - Are lines heavy/pressed (tension, strong emotion) or light/tentative (uncertainty)?
   - Are strokes controlled or chaotic?
   - Are there repeated marks or scribbling over areas?
   - Is the drawing detailed or minimal?

6. DEVELOPMENTAL APPROPRIATENESS
   - Is the drawing style expected for age {child_age}?
   - Any regressions (drawing much simpler than expected)?
   - Any notable advanced detail for the age?

7. OVERALL EMOTIONAL NARRATIVE
   - What story does this drawing tell?
   - What might the child be communicating that they cannot verbalize?
   - What should the parent pay attention to?
   - What gentle follow-up questions could a parent ask?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- DO NOT default to happy just because colors are bright
- SAD indicators override bright colors: downturned mouths, isolation, barriers, dark scribbling
- Separation lines between people = strong conflict/sadness cue
- Small figures in corners = anxiety/low self-worth
- Missing facial features = emotional avoidance
- This is NOT a clinical diagnosis — use warm, observational language
- Be specific — reference actual visual elements you see
- Be thorough — parents deserve a complete picture

🌐 LANGUAGE RULE — VERY IMPORTANT:
ALL text values in the JSON (reason, evidence, symbolism, interpretation,
placement_notes, relationship_notes, notable_marks, observations, key_observations,
suggested_questions, follow_up_reason, emotional_condition, description — every
human-readable string) MUST be written in SINHALA (සිංහල).
Only JSON keys, "happy"/"sad", "low"/"medium"/"high", "positive"/"neutral"/"concerning",
"true"/"false", layout type values, and color names may remain in English.
Do NOT write any explanatory sentences in English.

Return ONLY valid JSON with this EXACT structure:

{{
  "final_emotion": "happy or sad",
  "confidence_level": "low or medium or high",
  "reason": "2-3 sentence explanation of the primary emotional indicators",
  "detected_objects": [
    {{
      "label": "object name in Sinhala (e.g. හිරු, මල, ගෙය, මිනිසා)",
      "evidence": "exactly where and how it appears — written in Sinhala",
      "symbolism": "psychological meaning in Sinhala",
      "emotional_weight": "positive / neutral / concerning"
    }}
  ],
  "missed_objects": [
    {{
      "label": "theme or pattern — in Sinhala",
      "reason": "why it matters — in Sinhala"
    }}
  ],
  "color_analysis": {{
    "dominant_colors": ["list all colors observed"],
    "palette_mood": "single descriptive phrase",
    "warm_cool_balance": "description",
    "pressure_observations": "light / medium / heavy / mixed",
    "interpretation": [
      "specific observation 1",
      "specific observation 2",
      "specific observation 3",
      "specific observation 4"
    ]
  }},
  "spatial_analysis": {{
    "layout_type": "centered / peripheral / divided / scattered / other",
    "figure_sizes": "description of relative sizes and what they may mean",
    "connections": "how figures relate to each other spatially",
    "empty_space": "description and psychological meaning",
    "placement_notes": [
      "specific observation 1",
      "specific observation 2",
      "specific observation 3"
    ],
    "relationship_notes": [
      "what the arrangement suggests about relationships or inner world"
    ]
  }},
  "stroke_analysis": {{
    "pressure": "light / medium / heavy / mixed",
    "control": "controlled / chaotic / mixed",
    "detail_level": "minimal / moderate / detailed",
    "notable_marks": "any repeated marks, scribbling, erasures"
  }},
  "developmental_notes": {{
    "age_appropriate": true or false,
    "observations": "2-3 sentences on developmental alignment"
  }},
  "parent_guidance": {{
    "key_observations": [
      "most important thing for parent to know",
      "second observation",
      "third observation"
    ],
    "suggested_questions": [
      "gentle question parent could ask the child",
      "another conversation starter"
    ],
    "follow_up_needed": true or false,
    "follow_up_reason": "why follow-up may or may not be needed"
  }},
  "emotional_condition": "one warm, parent-friendly sentence summarizing the child's emotional state",
  "description": "a rich, 4-6 sentence narrative paragraph for parents — warm, clear, specific, referencing actual visual elements"
}}
"""

# ─── Prompt for DRAWING BOARD (no CV data — image only) ─────────────────────

DRAWING_BOARD_PROMPT_TEMPLATE = """
You are a specialist child psychologist and art therapist with 20+ years of experience 
interpreting children's drawings for emotional wellbeing assessment.

A child has just drawn this picture digitally using a drawing app. 
This is NOT a clinical diagnosis — it is a compassionate, in-depth observation report for parents.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHILD CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Name: {child_name}
- Age: {child_age}
- Child's note about the drawing: {note}
- Input method: Digital drawing board (finger/stylus drawing)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK — COMPLETE VISUAL + PSYCHOLOGICAL ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Study the image carefully and produce a rich, layered analysis:

1. EMOTION CLASSIFICATION
   - Classify overall emotion as ONLY: happy OR sad
   - Look beyond surface colors — prioritize facial expressions, body language,
     symbolic content, relational dynamics

2. OBJECT DETECTION
   Identify ALL meaningful visual elements:
   - Human/animal figures (expressions, posture, isolation vs grouping)
   - Nature elements (sun, clouds, rain, trees, flowers — condition matters)
   - Structures (houses, walls, fences, barriers, doors, windows)
   - Symbolic objects (hearts, stars, lightning, dark areas)
   - Relational symbols (holding hands, separation lines, distance between figures)
   - Abstract marks (heavy dark areas, erratic lines, pressing)
   For EACH: where it is, how it's drawn, what it may psychologically suggest

3. COLOR PSYCHOLOGY
   - List all colors used and approximate proportions
   - Consider age-appropriateness for age {child_age}
   - Warm vs cool color balance and emotional meaning
   - Color combinations and what they suggest
   - Any notable absences (no skin tone, no green)

4. SPATIAL ARRANGEMENT
   - Placement of key elements (center vs corners vs edges)
   - Figure connections vs separations
   - Empty space vs crowding
   - Relative sizes of figures
   - Any barriers or dividing elements

5. STROKE & DIGITAL DRAWING QUALITY
   - Are strokes confident or hesitant?
   - Are there areas of heavy color/multiple layers?
   - Is the drawing detailed or minimal?
   - Evidence of care and intention in specific areas?

6. DEVELOPMENTAL APPROPRIATENESS for age {child_age}
   - Expected vs actual complexity
   - Any regressions or advanced elements?

7. OVERALL EMOTIONAL NARRATIVE
   - What story does this drawing tell?
   - What might the child be communicating?
   - What should the parent pay attention to?
   - Gentle follow-up questions for the parent to ask

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- DO NOT default to happy just because colors are bright
- SAD indicators override bright colors
- Separation lines between people = strong conflict cue
- Isolated small figures = anxiety indicator
- Be specific — reference actual visual elements you see
- Be thorough and warm

🌐 LANGUAGE RULE — VERY IMPORTANT:
ALL text values in the JSON (reason, evidence, symbolism, interpretation,
placement_notes, relationship_notes, notable_marks, observations, key_observations,
suggested_questions, follow_up_reason, emotional_condition, description — every
human-readable string) MUST be written in SINHALA (සිංහල).
Only JSON keys, "happy"/"sad", "low"/"medium"/"high", "positive"/"neutral"/"concerning",
"true"/"false", layout type values, and color names may remain in English.
Do NOT write any explanatory sentences in English.

Return ONLY valid JSON with this EXACT structure:

{{
  "final_emotion": "happy or sad",
  "confidence_level": "low or medium or high",
  "reason": "2-3 sentence explanation of primary emotional indicators",
  "detected_objects": [
    {{
      "label": "object name in Sinhala (e.g. හිරු, මල, ගෙය, මිනිසා)",
      "evidence": "exactly where and how it appears — written in Sinhala",
      "symbolism": "psychological meaning in Sinhala",
      "emotional_weight": "positive / neutral / concerning"
    }}
  ],
  "missed_objects": [],
  "color_analysis": {{
    "dominant_colors": ["all colors observed"],
    "palette_mood": "single descriptive phrase",
    "warm_cool_balance": "description",
    "pressure_observations": "light / medium / heavy / mixed",
    "interpretation": [
      "specific color observation 1",
      "specific color observation 2",
      "specific color observation 3"
    ]
  }},
  "spatial_analysis": {{
    "layout_type": "centered / peripheral / divided / scattered / other",
    "figure_sizes": "description and meaning",
    "connections": "how figures relate spatially",
    "empty_space": "description and meaning",
    "placement_notes": [
      "placement observation 1",
      "placement observation 2"
    ],
    "relationship_notes": [
      "what arrangement suggests about inner world"
    ]
  }},
  "stroke_analysis": {{
    "pressure": "light / medium / heavy / mixed",
    "control": "controlled / chaotic / mixed",
    "detail_level": "minimal / moderate / detailed",
    "notable_marks": "any notable patterns"
  }},
  "developmental_notes": {{
    "age_appropriate": true or false,
    "observations": "2-3 sentences"
  }},
  "parent_guidance": {{
    "key_observations": [
      "most important thing for parent to know",
      "second observation",
      "third observation"
    ],
    "suggested_questions": [
      "gentle question parent could ask",
      "another conversation starter"
    ],
    "follow_up_needed": true or false,
    "follow_up_reason": "explanation"
  }},
  "emotional_condition": "one warm parent-friendly sentence",
  "description": "rich 4-6 sentence narrative for parents — warm, clear, specific"
}}
"""


def review_drawing_analysis_with_gemini_image(
    image_bytes: bytes,
    mime_type: str,
    analysis_payload: Dict[str, Any],
    source_mode: str = "photo_scan",
) -> Dict[str, Any]:
    """
    Analyze a drawing image using Gemini.
    For drawing_board source: uses image-only prompt (no CV data).
    For photo_scan source: uses full prompt with CV analysis data.
    """
    if not ENABLE_GEMINI_REVIEW:
        return build_fallback_description(analysis_payload)

    is_drawing_board = source_mode == "drawing_board"

    if is_drawing_board:
        prompt = DRAWING_BOARD_PROMPT_TEMPLATE.format(
            child_name=analysis_payload.get("child_name", "the child"),
            child_age=analysis_payload.get("child_age", "unknown"),
            note=analysis_payload.get("note") or "No note provided",
        )
    else:
        prompt = SCAN_PROMPT_TEMPLATE.format(
            child_name=analysis_payload.get("child_name", "the child"),
            child_age=analysis_payload.get("child_age", "unknown"),
            note=analysis_payload.get("note") or "No note provided",
            analysis_payload=json.dumps(analysis_payload, ensure_ascii=False, indent=2),
        )

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        contents = [prompt, image]
        raw = _call_gemini_with_failover(contents)

        try:
            parsed = json.loads(raw)
            parsed["review_enabled"] = True
            return parsed
        except Exception:
            # Try stripping markdown fences
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[1:])
            if cleaned.endswith("```"):
                cleaned = "\n".join(cleaned.split("\n")[:-1])
            try:
                parsed = json.loads(cleaned)
                parsed["review_enabled"] = True
                return parsed
            except Exception:
                fallback = build_fallback_description(analysis_payload)
                fallback["review_enabled"] = True
                fallback["reason"] = "Failed to parse Gemini JSON output."
                fallback["description"] = raw if raw else fallback["description"]
                return fallback

    except Exception as e:
        fallback = build_fallback_description(analysis_payload)
        fallback["reason"] = f"Gemini review failed: {str(e)}"
        return fallback