from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.api.auth import get_current_active_user, User
from fastapi.templating import Jinja2Templates
import json

# Text AI router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Models
class TextRequest(BaseModel):
    text: str
    task: str  # "summarize", "translate", "sentiment", "paraphrase", "generate"
    options: Optional[Dict[str, Any]] = None  # For task-specific options like target language

class TextResponse(BaseModel):
    result: str
    confidence: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]  # List of message objects with "role" and "content"
    model: str = "gpt-3.5-turbo"    # Default model
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.7

class ChatResponse(BaseModel):
    response: str
    usage: Optional[Dict[str, int]] = None
    model_used: str

# Mock AI processing functions
def process_text_request(request: TextRequest):
    """Mock function to process text requests"""
    # In a real implementation, this would call an AI service API
    
    if request.task == "summarize":
        return TextResponse(
            result="This is a summary of the provided text.",
            confidence=0.92,
            additional_info={"original_length": len(request.text), "summary_length": 30}
        )
    
    elif request.task == "translate":
        target_lang = request.options.get("target_language", "Spanish")
        return TextResponse(
            result=f"[Translated content to {target_lang}]",
            confidence=0.85,
            additional_info={"source_language": "English", "target_language": target_lang}
        )
    
    elif request.task == "sentiment":
        return TextResponse(
            result="positive",
            confidence=0.78,
            additional_info={"positive": 0.78, "neutral": 0.18, "negative": 0.04}
        )
    
    elif request.task == "paraphrase":
        return TextResponse(
            result="This is a paraphrased version of your text that conveys the same meaning.",
            confidence=0.91
        )
    
    elif request.task == "generate":
        prompt = request.options.get("prompt", "")
        return TextResponse(
            result=f"AI generated text based on: {prompt or 'your input'}",
            additional_info={"generated_tokens": 150}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid task type")

def process_chat_request(request: ChatRequest):
    """Mock function to process chat requests"""
    # In a real implementation, this would call an LLM API like OpenAI
    
    # Extract the last user message for the mock response
    last_message = "Hello"
    for msg in reversed(request.messages):
        if msg.get("role") == "user":
            last_message = msg.get("content", "Hello")
            break
    
    return ChatResponse(
        response=f"This is a response to: '{last_message}' using {request.model}",
        usage={"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
        model_used=request.model
    )

# Routes
@router.get("/", response_class=HTMLResponse)
async def text_ai_page(request: Request):
    return templates.TemplateResponse("text_ai.html", {"request": request})

@router.post("/process", response_model=TextResponse)
async def process_text(
    text_request: TextRequest,
    current_user: User = Depends(get_current_active_user)
):
    return process_text_request(text_request)

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    return process_chat_request(chat_request)

@router.get("/models")
async def get_available_models():
    models = [
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "type": "chat", "context_length": 4096},
        {"id": "gpt-4", "name": "GPT-4", "type": "chat", "context_length": 8192},
        {"id": "text-davinci-003", "name": "Davinci", "type": "completion", "context_length": 4097},
        {"id": "text-ada-001", "name": "Ada", "type": "completion", "context_length": 2049}
    ]
    return models

@router.get("/tasks")
async def get_supported_tasks():
    tasks = [
        {"id": "summarize", "name": "Text Summarization", "description": "Condense text while preserving key information"},
        {"id": "translate", "name": "Translation", "description": "Translate text between languages"},
        {"id": "sentiment", "name": "Sentiment Analysis", "description": "Determine the emotional tone of text"},
        {"id": "paraphrase", "name": "Paraphrasing", "description": "Rewrite text while preserving meaning"},
        {"id": "generate", "name": "Text Generation", "description": "Generate text based on prompts"}
    ]
    return tasks 