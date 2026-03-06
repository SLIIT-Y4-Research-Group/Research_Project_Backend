# Example API Usage with curl

## 1. Install Dependencies First
```bash
pip install -r requirements.txt
```

## 2. Update .env file
Add these variables to your .env:
```
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
BACKEND_BASE_URL=http://localhost:8000
BAD_MOOD_THRESHOLD=5
```

## 3. Start Server
```bash
python -m uvicorn app.main:app --reload
```

---

## Authentication Examples

### Register Parent
```bash
curl -X POST "http://localhost:8000/auth/parent/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "securepass123"
  }'
```

### Parent Login
```bash
curl -X POST "http://localhost:8000/auth/parent/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "parent": {
    "id": "507f1f77bcf86cd799439011",
    "email": "parent@example.com"
  }
}
```

### Child Login
```bash
curl -X POST "http://localhost:8000/auth/child/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "child_user",
    "password": "childpass123"
  }'
```

---

## Parent Operations (Requires Parent JWT)

### Create Child Account
```bash
curl -X POST "http://localhost:8000/parent/children" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <PARENT_TOKEN>" \
  -d '{
    "username": "child_user",
    "password": "childpass123",
    "name": "John Doe",
    "age": 10
  }'
```

### List Children
```bash
curl -X GET "http://localhost:8000/parent/children" \
  -H "Authorization: Bearer <PARENT_TOKEN>"
```

### Invite Trusted Contact
```bash
curl -X POST "http://localhost:8000/parent/children/CHILD_ID/trusted" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <PARENT_TOKEN>" \
  -d '{
    "email": "trusted@example.com"
  }'
```

### List Trusted Contacts
```bash
curl -X GET "http://localhost:8000/parent/children/CHILD_ID/trusted" \
  -H "Authorization: Bearer <PARENT_TOKEN>"
```

---

## Child Operations (Requires Child JWT)

### Get Profile
```bash
curl -X GET "http://localhost:8000/child/me" \
  -H "Authorization: Bearer <CHILD_TOKEN>"
```

### Update Alert Consent
```bash
curl -X PATCH "http://localhost:8000/child/me/consent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <CHILD_TOKEN>" \
  -d '{
    "alerts_consent": true
  }'
```

### Store Mood (Protected - Child JWT Required)
```bash
curl -X POST "http://localhost:8000/mood/store" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <CHILD_TOKEN>" \
  -d '{
    "userId": 123,
    "mood": "Bad",
    "datetime": "2026-03-05T10:30:00"
  }'
```

---

## Trusted Contact Operations

### Accept Invitation (via browser link)
```
http://localhost:8000/trusted/accept?token=<INVITATION_TOKEN>
```

This endpoint returns HTML and is meant to be opened in a browser.

---

## Existing Mood Endpoints (Still work as before)

### Predict Mood
```bash
curl -X POST "http://localhost:8000/mood/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "මම අද හරිම සතුටුයි"
  }'
```

### Predict Question
```bash
curl -X POST "http://localhost:8000/mood/predict_question" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 1,
    "text": "විශේෂ දෙයක් නෑ"
  }'
```

### Validate Answer
```bash
curl -X POST "http://localhost:8000/mood/validate_answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 1,
    "text": "හොඳයි"
  }'
```

### Predict Overall
```bash
curl -X POST "http://localhost:8000/mood/predict_overall" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": ["හොඳයි", "නෑ", "ඔව්", "නැහැ", "ඔව්"]
  }'
```

---

## Alert System Flow

1. Child enables consent: `PATCH /child/me/consent` with `alerts_consent: true`
2. Child stores mood: `POST /mood/store` with `mood: "Bad"`
3. System automatically checks last 7 days for bad moods
4. If bad mood count >= BAD_MOOD_THRESHOLD (default 5):
   - Sends email to parent
   - Sends email to all accepted trusted contacts
5. If consent is false, no email is sent

---

## Testing the Complete Flow

### Step 1: Parent Registration & Login
```bash
# Register parent
PARENT_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/parent/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "parent@example.com", "password": "securepass123"}')

# Extract token
PARENT_TOKEN=$(echo $PARENT_RESPONSE | jq -r '.access_token')
echo "Parent Token: $PARENT_TOKEN"
```

### Step 2: Create Child
```bash
CHILD_RESPONSE=$(curl -s -X POST "http://localhost:8000/parent/children" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -d '{
    "username": "child_user",
    "password": "childpass123",
    "name": "John Doe",
    "age": 10
  }')

CHILD_ID=$(echo $CHILD_RESPONSE | jq -r '.id')
echo "Child ID: $CHILD_ID"
```

### Step 3: Invite Trusted Contact
```bash
curl -X POST "http://localhost:8000/parent/children/$CHILD_ID/trusted" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -d '{"email": "trusted@example.com"}'
```

### Step 4: Child Login
```bash
CHILD_LOGIN=$(curl -s -X POST "http://localhost:8000/auth/child/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "child_user", "password": "childpass123"}')

CHILD_TOKEN=$(echo $CHILD_LOGIN | jq -r '.access_token')
echo "Child Token: $CHILD_TOKEN"
```

### Step 5: Enable Consent
```bash
curl -X PATCH "http://localhost:8000/child/me/consent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CHILD_TOKEN" \
  -d '{"alerts_consent": true}'
```

### Step 6: Store Bad Moods (5 times to trigger alert)
```bash
for i in {1..5}; do
  curl -X POST "http://localhost:8000/mood/store" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $CHILD_TOKEN" \
    -d "{\"userId\": 123, \"mood\": \"Bad\", \"datetime\": \"$(date -Iseconds)\"}"
  sleep 1
done
```

After the 5th bad mood, an alert email will be sent to parent and all accepted trusted contacts!

---

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
