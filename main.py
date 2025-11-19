import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import (
    User, Counselor, Post, Comment, Session,
    Reminder, Message, EmotionRequest, EmotionResponse
)

app = FastAPI(title="Sahara API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"name": "Sahara", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                cols = db.list_collection_names()
                response["collections"] = cols
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:60]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response

# Simple auth placeholders (email/password) — for demo only
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/auth/login")
def login(req: LoginRequest):
    # NOTE: Real auth would verify password hash and issue JWT.
    # Here we just check user existence and return a mock token for demo.
    users = get_documents("user", {"email": req.email}, limit=1)
    if not users:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": "demo-token", "user": {"email": req.email}}

# Community posts (by age group)
@app.post("/posts")
def create_post(post: Post):
    post_id = create_document("post", post)
    return {"id": post_id}

@app.get("/posts")
def list_posts(audience: Optional[str] = None):
    filt = {"audience": audience} if audience else {}
    items = get_documents("post", filt, limit=100)
    # Convert ObjectId to str for safety
    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)
    return items

# Book a counselor session
@app.post("/sessions")
def book_session(s: Session):
    sid = create_document("session", s)
    return {"id": sid}

@app.get("/sessions")
def list_sessions(user_id: Optional[str] = None, counselor_id: Optional[str] = None):
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    if counselor_id:
        filt["counselor_id"] = counselor_id
    items = get_documents("session", filt, limit=100)
    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)
    return items

# Reminders
@app.post("/reminders")
def create_reminder(r: Reminder):
    rid = create_document("reminder", r)
    return {"id": rid}

@app.get("/reminders")
def list_reminders(user_id: str):
    items = get_documents("reminder", {"user_id": user_id}, limit=100)
    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)
    return items

# Messages (direct or room)
@app.post("/messages")
def send_message(m: Message):
    mid = create_document("message", m)
    return {"id": mid}

@app.get("/messages")
def list_messages(to_user_id: Optional[str] = None, room: Optional[str] = None):
    filt = {}
    if to_user_id:
        filt["to_user_id"] = to_user_id
    if room:
        filt["room"] = room
    items = get_documents("message", filt, limit=100)
    for it in items:
        _id = it.get("_id")
        if _id is not None:
            it["_id"] = str(_id)
    return items

# Emotion analysis (stubbed with simple heuristic; can be replaced with TF/OpenAI pipeline)
@app.post("/analyze", response_model=EmotionResponse)
def analyze_emotion(req: EmotionRequest):
    text = req.text.lower()
    label = "neutral"
    suggestions: List[str] = []

    if any(w in text for w in ["sad", "down", "lonely", "alone", "tired"]):
        label = "loneliness" if "lonely" in text or "alone" in text else "sadness"
        suggestions = [
            "Try a 5-minute breathing exercise",
            "Reach out to a friend or join a community room",
            "Take a short walk and hydrate",
        ]
    elif any(w in text for w in ["angry", "mad", "frustrated", "irritated"]):
        label = "anger"
        suggestions = [
            "Pause and note what triggered you",
            "Count 4-7-8 breaths",
            "Journal your thoughts for 3 minutes",
        ]
    elif any(w in text for w in ["anxious", "worried", "fear", "scared"]):
        label = "fear"
        suggestions = [
            "Ground with 5-4-3-2-1 technique",
            "Limit caffeine and news for a bit",
            "Text a counselor if available",
        ]
    elif any(w in text for w in ["burnout", "exhausted", "overworked", "stressed"]):
        label = "burnout" if "burnout" in text else "stress"
        suggestions = [
            "Schedule a 10-minute break block",
            "Delegate one small task",
            "Plan a wind-down routine tonight",
        ]
    else:
        label = "neutral"
        suggestions = [
            "Keep a gratitude note for today",
            "Share a supportive message in your community",
        ]

    score = 0.8 if label != "neutral" else 0.5
    return EmotionResponse(label=label, score=score, suggestions=suggestions)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
