from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.api.auth import get_current_active_user, User
from fastapi.templating import Jinja2Templates
import json
import base64

# Image AI router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Models
class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: Optional[int] = 512
    height: Optional[int] = 512
    num_images: Optional[int] = 1
    model: Optional[str] = "stable-diffusion-v1-5"

class ImageEditRequest(BaseModel):
    prompt: str
    mask_prompt: Optional[str] = None
    strength: Optional[float] = 0.8
    guidance_scale: Optional[float] = 7.5
    model: Optional[str] = "stable-diffusion-inpainting"

class ImageResponse(BaseModel):
    images: List[str]  # Base64 encoded images
    seed: Optional[int] = None
    model_used: str
    processing_time: Optional[float] = None

class ImageAnalysisResponse(BaseModel):
    labels: List[Dict[str, Any]]  # Object detection results or classifications
    image_caption: Optional[str] = None
    confidence: Optional[float] = None

# Mock AI processing functions
def process_image_generation(request: ImageGenerationRequest):
    """Mock function to generate images"""
    # In a real implementation, this would call an AI image generation service like DALL-E or Stable Diffusion
    
    # Create a base64 mock image (just a small colored square in this case)
    sample_image = base64.b64encode(bytes([255, 0, 0] * 64 * 64)).decode('utf-8')
    
    return ImageResponse(
        images=[sample_image] * request.num_images,
        seed=42,
        model_used=request.model,
        processing_time=3.2
    )

def process_image_edit(request: ImageEditRequest, image_data: bytes):
    """Mock function to edit images"""
    # In a real implementation, this would call an AI image editing service
    
    # Return a mock edited image
    sample_edited_image = base64.b64encode(bytes([0, 255, 0] * 64 * 64)).decode('utf-8')
    
    return ImageResponse(
        images=[sample_edited_image],
        seed=123,
        model_used=request.model,
        processing_time=2.8
    )

def analyze_image(image_data: bytes, task: str):
    """Mock function to analyze images"""
    # In a real implementation, this would call a computer vision API
    
    if task == "object_detection":
        return ImageAnalysisResponse(
            labels=[
                {"label": "person", "confidence": 0.92, "bbox": [10, 10, 100, 200]},
                {"label": "car", "confidence": 0.88, "bbox": [150, 50, 200, 100]}
            ],
            confidence=0.9
        )
    elif task == "classification":
        return ImageAnalysisResponse(
            labels=[
                {"label": "landscape", "confidence": 0.85},
                {"label": "nature", "confidence": 0.82},
                {"label": "mountain", "confidence": 0.76}
            ],
            confidence=0.85
        )
    elif task == "caption":
        return ImageAnalysisResponse(
            labels=[],
            image_caption="A beautiful landscape with mountains and a lake",
            confidence=0.91
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid analysis task")

# Routes
@router.get("/", response_class=HTMLResponse)
async def image_ai_page(request: Request):
    return templates.TemplateResponse("image_ai.html", {"request": request})

@router.post("/generate", response_model=ImageResponse)
async def generate_image(
    generation_request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    return process_image_generation(generation_request)

@router.post("/edit", response_model=ImageResponse)
async def edit_image(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    mask_prompt: Optional[str] = Form(None),
    strength: Optional[float] = Form(0.8),
    guidance_scale: Optional[float] = Form(7.5),
    model: Optional[str] = Form("stable-diffusion-inpainting"),
    current_user: User = Depends(get_current_active_user)
):
    # Read the uploaded image
    image_data = await image.read()
    
    # Create the edit request
    edit_request = ImageEditRequest(
        prompt=prompt,
        mask_prompt=mask_prompt,
        strength=strength,
        guidance_scale=guidance_scale,
        model=model
    )
    
    return process_image_edit(edit_request, image_data)

@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(
    image: UploadFile = File(...),
    task: str = Form(...),  # "object_detection", "classification", "caption"
    current_user: User = Depends(get_current_active_user)
):
    image_data = await image.read()
    return analyze_image(image_data, task)

@router.get("/models")
async def get_available_models():
    models = [
        {"id": "stable-diffusion-v1-5", "name": "Stable Diffusion v1.5", "type": "text-to-image"},
        {"id": "stable-diffusion-v2", "name": "Stable Diffusion v2", "type": "text-to-image"},
        {"id": "stable-diffusion-inpainting", "name": "SD Inpainting", "type": "image-editing"},
        {"id": "dall-e-2", "name": "DALL-E 2", "type": "text-to-image"},
        {"id": "dall-e-3", "name": "DALL-E 3", "type": "text-to-image"}
    ]
    return models

@router.get("/analysis-tasks")
async def get_analysis_tasks():
    tasks = [
        {"id": "object_detection", "name": "Object Detection", "description": "Detect and locate objects in images"},
        {"id": "classification", "name": "Image Classification", "description": "Categorize images into predefined classes"},
        {"id": "caption", "name": "Image Captioning", "description": "Generate textual descriptions of images"}
    ]
    return tasks 