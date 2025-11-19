"""
Database Schemas for Sahara

Each Pydantic model corresponds to a MongoDB collection. The collection
name is the lowercase of the class name (e.g., User -> "user").

These schemas are used both for validation at the API boundary and
as guides for the database structure.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# Core user and auth
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Unique email")
    password_hash: str = Field(..., description="Password hash (server-side only)")
    age: Optional[int] = Field(None, ge=0, le=120)
    gender: Optional[str] = Field(None, description="Gender identity (free text)")
    language: str = Field("en", description="Preferred language code, e.g., en, es, hi")
    age_group: Optional[Literal["teen","young-adult","adult","senior"]] = None
    role: Literal["user","counselor","admin"] = "user"
    verified: bool = False

class Counselor(BaseModel):
    user_id: str = Field(..., description="Reference to user _id")
    specialties: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=lambda: ["en"]) 
    years_experience: Optional[int] = Field(None, ge=0)
    license_id: Optional[str] = None
    bio: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)

# Social/community
class Post(BaseModel):
    user_id: str
    content: str
    audience: Optional[Literal["all","teen","young-adult","adult","senior"]] = "all"
    tags: List[str] = Field(default_factory=list)

class Comment(BaseModel):
    post_id: str
    user_id: str
    content: str

# Sessions with real psychiatrists / counselors
class Session(BaseModel):
    user_id: str
    counselor_id: str
    scheduled_at: datetime
    mode: Literal["chat","audio","video"] = "chat"
    status: Literal["pending","confirmed","completed","cancelled"] = "pending"
    notes: Optional[str] = None

# Reminders
class Reminder(BaseModel):
    user_id: str
    title: str
    schedule: str = Field(..., description="ISO 8601 or cron-like string")
    channel: Literal["push","email","sms"] = "push"
    active: bool = True

# Messaging (simple direct or group by age)
class Message(BaseModel):
    from_user_id: str
    to_user_id: Optional[str] = None
    room: Optional[str] = Field(None, description="e.g., age:teen, language:en")
    text: str

# Emotion analysis request/response
class EmotionRequest(BaseModel):
    text: str
    language: str = "en"

class EmotionResponse(BaseModel):
    label: Literal["joy","sadness","anger","fear","love","neutral","stress","burnout","loneliness"]
    score: float
    suggestions: List[str]
