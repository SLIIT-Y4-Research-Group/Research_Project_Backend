# Music Recommendation Workflow

## Overview
This system personalizes music suggestions using:
- face emotion before listening,
- face emotion after listening,
- user satisfaction rating (1-5),
- per-user session history with recency weighting.

It supports an end-to-end flow from recommendation -> playback -> feedback -> improved future recommendations.

## End-to-End Flow
1. Child opens music recommendation screen.
2. Frontend requests personalized tracks:
   - `GET /music/recommendations?current_emotion=<emotion>`
3. Child selects a song and opens player.
4. Player starts a listening session:
   - capture before-face image in frontend,
   - call `POST /music/session/start`.
5. Song plays normally.
6. When song completes:
   - collect satisfaction rating (1-5),
   - capture after-face image,
   - call `POST /music/session/{session_id}/complete`.
7. Backend stores impact metrics and uses them in future ranking.

## Backend Data Model
Collection: `music_sessions`

Stored fields:
- `user_id`
- `track_id`
- `started_at`
- `ended_at`
- `before_emotion`:
  - `emotion_idx`
  - `emotion_label`
  - `confidence`
- `after_emotion`:
  - `emotion_idx`
  - `emotion_label`
  - `confidence`
- `satisfaction_rating` (1-5)
- derived:
  - `emotion_changed` (bool)
  - `improvement_score` (0..1)
  - `impact_score` (0..1)

Indexes:
- `(user_id, ended_at desc)`
- `(track_id)`
- `(user_id, track_id)`

## Emotion Processing
Shared helper: `app/services/emotion_image_service.py`

The helper:
- decodes base64 image,
- normalizes to RGB,
- resizes to model input,
- runs emotion prediction,
- returns `emotion_idx`, `emotion_label`, `confidence`.

This avoids duplicated base64/image parsing logic between routes.

## Impact Calculation
Service: `app/services/music_recommendation_service.py`

### Positivity Mapping
Emotion labels are mapped to positivity values:
- angry: `0.1`
- disgust: `0.1`
- fear: `0.2`
- sad: `0.2`
- neutral: `0.5`
- surprise: `0.6`
- happy: `1.0`

### Scores
- `delta = positivity(after) - positivity(before)`
- `improvement_score = (delta + 1) / 2`, clamped to `0..1`
- `rating_score = satisfaction_rating / 5`
- `impact_score = 0.6 * rating_score + 0.4 * improvement_score`
- `emotion_changed = before_label != after_label`

## Recommendation Strategy (v1)
Endpoint: `GET /music/recommendations`

1. Build candidate tracks:
   - filter by `current_emotion` tag if provided,
   - otherwise use all tracks.
2. Load completed session history for current user.
3. Apply recency weighting per session:
   - `w = 1 / (1 + age_days / 7)`
4. Aggregate per track:
   - weighted avg impact,
   - weighted avg satisfaction,
   - weighted avg improvement.
5. Compute final recommendation score:
   - `0.5 * avg_impact + 0.3 * avg_satisfaction + 0.2 * avg_improvement + confidence_boost`
6. Sort descending by score.
7. Cold-start fallback:
   - if user has no history, return default neutral score and preserve base ordering.

## API Contracts
### Start Session
`POST /music/session/start`

Request:
- `track_id: string`
- `before_image: string` (base64)

Response:
- `session_id`
- `track_id`
- `user_id`
- `started_at`
- `before_emotion`

### Complete Session
`POST /music/session/{session_id}/complete`

Request:
- `after_image: string` (base64)
- `satisfaction_rating: int` (1..5)

Response:
- session metadata
- `before_emotion`
- `after_emotion`
- `satisfaction_rating`
- `emotion_changed`
- `improvement_score`
- `impact_score`

### Personalized Recommendations
`GET /music/recommendations?current_emotion=<optional>`

Response:
- track list with standard track fields
- `recommendation_score`

## Frontend Integration
Updated screens:
- `lib/screens/music_recommendation_screen.dart`
  - calls personalized endpoint with child JWT,
  - falls back to emotion-filtered tracks endpoint when unauthorized.
- `lib/screens/music_player_screen.dart`
  - starts session on first song load,
  - captures feedback on playback completion,
  - submits complete session payload.

## Error Handling
- invalid `track_id` -> `400` / `404`
- invalid `session_id` -> `400` / `404`
- completing already completed session -> `409`
- invalid rating -> validation error (`422`)
- if frontend user skips capture/rating, completion is safely skipped.

## Current Limitations
- Session start/complete currently depends on camera capture availability.
- If user skips post-listen feedback, no learning signal is recorded.
- v1 uses rule-based ranking, not a trained recommendation model.

## Future Improvements
- Add explicit "skip feedback" reason tracking.
- Add minimum playback-duration rule before accepting completion feedback.
- Add bandit/model-based recommendation for exploration vs exploitation.
- Track context features (time of day, repeat listens, session length).
