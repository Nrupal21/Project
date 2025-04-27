from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.api.auth import get_current_active_user, User
from fastapi.templating import Jinja2Templates
import json

# Productivity AI router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Models
class SummaryRequest(BaseModel):
    text: str
    length: Optional[str] = "medium"  # short, medium, long
    focus: Optional[str] = None  # optional focus area

class ContentGenerationRequest(BaseModel):
    topic: str
    content_type: str  # blog, email, report, social post
    tone: Optional[str] = "professional"
    keywords: Optional[List[str]] = None
    length: Optional[str] = "medium"

class TranslationRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = None

class CalendarEvent(BaseModel):
    title: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None

class CalendarRequest(BaseModel):
    action: str  # add, get, suggest
    event: Optional[CalendarEvent] = None
    date_range: Optional[Dict[str, str]] = None

# Mock AI integration (replace with actual API calls in production)
def generate_summary(text: str, length: str, focus: Optional[str] = None):
    """Mock function to generate a summary"""
    # In a real implementation, this would call an AI service
    summary_lengths = {
        "short": max(len(text) // 10, 50),
        "medium": max(len(text) // 5, 100),
        "long": max(len(text) // 3, 200)
    }
    max_length = summary_lengths.get(length, 100)
    
    if focus:
        return f"Summary focusing on {focus}: " + text[:max_length] + "..."
    else:
        return f"Summary: " + text[:max_length] + "..."

def generate_content(request: ContentGenerationRequest):
    """Mock function to generate content"""
    # In a real implementation, this would call an AI service
    content_types = {
        "blog": f"# Blog Post About {request.topic}\n\nIntroduction paragraph goes here...",
        "email": f"Subject: {request.topic}\n\nDear [Recipient],\n\nI hope this email finds you well...",
        "report": f"# Report: {request.topic}\n\n## Executive Summary\n\nThis report analyzes...",
        "social": f"Check out our thoughts on {request.topic}! #{'#'.join(request.keywords or [])}"
    }
    
    return content_types.get(request.content_type, f"Content about {request.topic}")

def translate_text(text: str, target_language: str, source_language: Optional[str] = None):
    """Mock function to translate text"""
    # In a real implementation, this would call a translation API
    return f"[Translated to {target_language}]: {text[:100]}..."

def process_calendar_request(request: CalendarRequest):
    """Mock function to process calendar operations"""
    # In a real implementation, this would interact with a calendar API
    if request.action == "add":
        return {"status": "success", "message": f"Event '{request.event.title}' added to calendar"}
    elif request.action == "get":
        return {
            "events": [
                {
                    "title": "Team Meeting",
                    "start_time": "2023-06-01T10:00:00",
                    "end_time": "2023-06-01T11:00:00"
                },
                {
                    "title": "Project Review",
                    "start_time": "2023-06-02T14:00:00",
                    "end_time": "2023-06-02T15:30:00"
                }
            ]
        }
    elif request.action == "suggest":
        return {
            "suggestions": [
                {
                    "title": "Suggested Meeting Time",
                    "start_time": "2023-06-03T09:00:00",
                    "end_time": "2023-06-03T10:00:00",
                    "reason": "All attendees are available at this time"
                }
            ]
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid calendar action")

# Routes
@router.get("/", response_class=HTMLResponse)
async def productivity_dashboard(request: Request):
    return templates.TemplateResponse("productivity.html", {"request": request})

@router.post("/summarize")
async def summarize_text(
    summary_request: SummaryRequest,
    current_user: User = Depends(get_current_active_user)
):
    summary = generate_summary(
        summary_request.text,
        summary_request.length,
        summary_request.focus
    )
    return {"summary": summary}

@router.post("/generate-content")
async def create_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    content = generate_content(request)
    return {"content": content}

@router.post("/translate")
async def translate(
    request: TranslationRequest,
    current_user: User = Depends(get_current_active_user)
):
    translated = translate_text(
        request.text,
        request.target_language,
        request.source_language
    )
    return {"translated_text": translated}

@router.post("/calendar")
async def manage_calendar(
    request: CalendarRequest,
    current_user: User = Depends(get_current_active_user)
):
    return process_calendar_request(request)

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # In a real application, this would call a transcription service like Whisper
    return {
        "transcription": "This is a mock transcription of the uploaded audio file.",
        "confidence": 0.95
    } 