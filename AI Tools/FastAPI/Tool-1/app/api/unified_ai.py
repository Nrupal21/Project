from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from app.api.auth import get_current_active_user, User
from fastapi.templating import Jinja2Templates

# Import handlers from each AI model type
from app.api.text_ai import process_text_request, process_chat_request
from app.api.image_ai import process_image_generation, process_image_edit, analyze_image
from app.api.audio_ai import process_speech_to_text, process_text_to_speech, analyze_audio, generate_audio
from app.api.video_ai import generate_video, edit_video, analyze_video

# Unified AI router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")

# --------------------------------------------------
# Unified Models
# --------------------------------------------------
class UnifiedAIRequest(BaseModel):
    model_type: str  # "text", "image", "audio", "video", "code"
    task: str  # Task specific to the model type
    content: Optional[str] = None  # Text content, prompts, etc.
    options: Optional[Dict[str, Any]] = None  # Model-specific options

class UnifiedAIResponse(BaseModel):
    result: Optional[Any] = None  # Could be text, base64 images, URLs, etc.
    model_used: str
    processing_time: Optional[float] = None
    confidence: Optional[float] = None
    additional_info: Optional[Dict[str, Any]] = None

# --------------------------------------------------
# Main Routes
# --------------------------------------------------
@router.get("/", response_class=HTMLResponse)
async def unified_ai_page(request: Request):
    return templates.TemplateResponse("unified_ai.html", {"request": request})

@router.post("/process", response_model=UnifiedAIResponse)
async def process_ai_request(
    request: UnifiedAIRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Universal endpoint for processing AI requests.
    Routes to the appropriate handler based on model_type and task.
    """
    try:
        # Route to the appropriate handler
        if request.model_type == "text":
            return await handle_text_request(request)
        elif request.model_type == "image":
            return await handle_image_request(request)
        elif request.model_type == "audio":
            return await handle_audio_request(request)
        elif request.model_type == "video":
            return await handle_video_request(request)
        elif request.model_type == "code":
            return await handle_code_request(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model type: {request.model_type}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------------------------------
# Model-Specific Handlers
# --------------------------------------------------
async def handle_text_request(request: UnifiedAIRequest):
    """Handle text AI processing requests"""
    
    if request.task == "chat":
        # Parse messages from the content
        if not request.options or "messages" not in request.options:
            raise HTTPException(status_code=400, detail="Chat requests require messages in options")
        
        # Create a chat request
        from app.api.text_ai import ChatRequest
        chat_request = ChatRequest(
            messages=request.options["messages"],
            model=request.options.get("model", "gpt-3.5-turbo"),
            max_tokens=request.options.get("max_tokens", 500),
            temperature=request.options.get("temperature", 0.7)
        )
        
        # Process with chat handler
        chat_response = process_chat_request(chat_request)
        
        # Map to unified response
        return UnifiedAIResponse(
            result=chat_response.response,
            model_used=chat_response.model_used,
            additional_info={"usage": chat_response.usage} if chat_response.usage else None
        )
        
    else:
        # Text processing tasks (summarize, translate, sentiment, etc.)
        if not request.content:
            raise HTTPException(status_code=400, detail="Text content is required")
        
        # Create a text request
        from app.api.text_ai import TextRequest
        text_request = TextRequest(
            text=request.content,
            task=request.task,
            options=request.options
        )
        
        # Process with text handler
        text_response = process_text_request(text_request)
        
        # Map to unified response
        return UnifiedAIResponse(
            result=text_response.result,
            model_used=request.options.get("model", "text-processing"),
            confidence=text_response.confidence,
            additional_info=text_response.additional_info
        )

async def handle_image_request(request: UnifiedAIRequest):
    """Handle image AI processing requests"""
    
    if request.task == "image-generation":
        # Create an image generation request
        from app.api.image_ai import ImageGenerationRequest
        image_request = ImageGenerationRequest(
            prompt=request.content,
            negative_prompt=request.options.get("negative_prompt"),
            width=request.options.get("width", 512),
            height=request.options.get("height", 512),
            num_images=request.options.get("num_images", 1),
            model=request.options.get("model", "stable-diffusion-v1-5")
        )
        
        # Process with image generation handler
        image_response = process_image_generation(image_request)
        
        # Map to unified response
        return UnifiedAIResponse(
            result=image_response.images,
            model_used=image_response.model_used,
            processing_time=image_response.processing_time,
            additional_info={"seed": image_response.seed}
        )
        
    # Handle other image tasks similarly
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported image task: {request.task}")

async def handle_audio_request(request: UnifiedAIRequest):
    """Handle audio AI processing requests"""
    
    if request.task == "text-to-speech":
        # Create a TTS request
        from app.api.audio_ai import TextToSpeechRequest
        tts_request = TextToSpeechRequest(
            text=request.content,
            voice_id=request.options.get("voice_id", "echo"),
            language=request.options.get("language", "en-US"),
            speed=request.options.get("speed", 1.0),
            pitch=request.options.get("pitch", 0.0)
        )
        
        # Process with TTS handler
        audio_response = process_text_to_speech(tts_request)
        
        # Map to unified response
        return UnifiedAIResponse(
            result=audio_response.audio_data,
            model_used=request.options.get("model", "tts-default"),
            processing_time=audio_response.duration,
            additional_info=audio_response.additional_info
        )
        
    # Handle other audio tasks similarly
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported audio task: {request.task}")

async def handle_video_request(request: UnifiedAIRequest):
    """Handle video AI processing requests"""
    
    if request.task == "video-generation":
        # Create a video generation request
        from app.api.video_ai import VideoGenerationRequest
        video_request = VideoGenerationRequest(
            prompt=request.content,
            duration=request.options.get("duration", 5.0),
            width=request.options.get("width", 512),
            height=request.options.get("height", 512),
            fps=request.options.get("fps", 24),
            model=request.options.get("model", "gen-2")
        )
        
        # Process with video generation handler
        video_response = generate_video(video_request)
        
        # Map to unified response
        return UnifiedAIResponse(
            result={
                "video_url": video_response.video_url,
                "preview_image": video_response.preview_image
            },
            model_used=video_response.additional_info.get("model_used", "video-gen"),
            processing_time=video_response.processing_time,
            additional_info={
                "frames_processed": video_response.frames_processed,
                "resolution": video_response.additional_info.get("resolution")
            }
        )
        
    # Handle other video tasks similarly
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported video task: {request.task}")

async def handle_code_request(request: UnifiedAIRequest):
    """Handle code AI processing requests"""
    
    # Import code AI handlers
    from app.api.code_ai import process_code_request
    from app.api.code_ai import CodeRequest
    
    # Create a code request
    code_request = CodeRequest(
        code=request.content or "",
        language=request.options.get("language", "python"),
        task=request.task.replace("code-", ""),  # Convert from "code-generation" to "generation"
        context=request.options.get("context")
    )
    
    # Process with code handler
    code_response = process_code_request(code_request)
    
    # Map to unified response
    return UnifiedAIResponse(
        result=code_response.result,
        model_used=request.options.get("model", "code-ai"),
        additional_info={
            "suggestions": code_response.suggestions,
            "explanation": code_response.explanation
        }
    )

# --------------------------------------------------
# Utility Endpoints
# --------------------------------------------------
@router.get("/models")
async def get_all_models():
    """Get a list of all available AI models across all types"""
    return {
        "text": [
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "type": "chat"},
            {"id": "gpt-4", "name": "GPT-4", "type": "chat"}
        ],
        "image": [
            {"id": "stable-diffusion-v1-5", "name": "Stable Diffusion v1.5", "type": "text-to-image"},
            {"id": "dall-e-3", "name": "DALL-E 3", "type": "text-to-image"}
        ],
        "audio": [
            {"id": "whisper-large-v3", "name": "Whisper Large v3", "type": "speech-to-text"},
            {"id": "musicgen-medium", "name": "MusicGen Medium", "type": "music-generation"}
        ],
        "video": [
            {"id": "gen-2", "name": "Gen-2", "type": "text-to-video"},
            {"id": "sora", "name": "Sora", "type": "text-to-video"}
        ],
        "code": [
            {"id": "code-davinci", "name": "Davinci Codex", "type": "code-generation"},
            {"id": "codellama", "name": "CodeLlama", "type": "code-completion"}
        ]
    }

@router.get("/tasks")
async def get_all_tasks():
    """Get a list of all available AI tasks across all types"""
    return {
        "text": [
            {"id": "summarize", "name": "Text Summarization"},
            {"id": "translate", "name": "Translation"},
            {"id": "sentiment", "name": "Sentiment Analysis"},
            {"id": "paraphrase", "name": "Paraphrasing"},
            {"id": "chat", "name": "Chat with AI"}
        ],
        "image": [
            {"id": "image-generation", "name": "Image Generation"},
            {"id": "image-editing", "name": "Image Editing"},
            {"id": "object-detection", "name": "Object Detection"},
            {"id": "image-caption", "name": "Image Captioning"}
        ],
        "audio": [
            {"id": "speech-to-text", "name": "Speech to Text"},
            {"id": "text-to-speech", "name": "Text to Speech"},
            {"id": "audio-analysis", "name": "Audio Analysis"},
            {"id": "audio-generation", "name": "Audio Generation"}
        ],
        "video": [
            {"id": "video-generation", "name": "Video Generation"},
            {"id": "video-editing", "name": "Video Editing"},
            {"id": "object-tracking", "name": "Object Tracking"},
            {"id": "action-recognition", "name": "Action Recognition"}
        ],
        "code": [
            {"id": "code-generation", "name": "Code Generation"},
            {"id": "code-completion", "name": "Code Completion"},
            {"id": "code-explanation", "name": "Code Explanation"},
            {"id": "code-debug", "name": "Code Debugging"}
        ]
    } 