from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from app.api.auth import get_current_active_user, User
from fastapi.templating import Jinja2Templates
import base64
from io import BytesIO

# Design AI router
router = APIRouter()

# Templates
templates = Jinja2Templates(directory="app/templates")

# Models
class ImageGenerationRequest(BaseModel):
    prompt: str
    style: Optional[str] = "realistic"
    size: Optional[str] = "512x512"
    num_images: Optional[int] = 1

class ImageEditRequest(BaseModel):
    image_id: str
    edits: List[dict]  # List of edit operations

class ImageResponse(BaseModel):
    image_id: str
    url: str
    generated_from: Optional[str] = None
    width: int
    height: int

class MockImageResponse:
    def __init__(self, prompt, style="realistic", size="512x512"):
        self.image_id = "mock-image-id-123"
        self.url = "/static/images/mock-image.jpg"  # In production, this would be a real image URL
        self.generated_from = prompt
        self.width, self.height = map(int, size.split("x"))

# Mock AI integration (replace with actual API calls in production)
def generate_image(prompt: str, style: str, size: str, num_images: int):
    """Mock function to generate images"""
    # In a real implementation, this would call an AI service like DALL·E or Stable Diffusion
    images = []
    for i in range(num_images):
        images.append(MockImageResponse(prompt, style, size))
    
    return [
        ImageResponse(
            image_id=img.image_id + f"-{i}",
            url=img.url,
            generated_from=img.generated_from,
            width=img.width,
            height=img.height
        ) for i, img in enumerate(images)
    ]

def edit_image(image_id: str, edits: List[dict]):
    """Mock function to edit images"""
    # In a real implementation, this would call an image editing API
    return ImageResponse(
        image_id=f"{image_id}-edited",
        url="/static/images/mock-edited-image.jpg",
        width=512,
        height=512
    )

def remove_background(image_file):
    """Mock function to remove background from an image"""
    # In a real implementation, this would call a background removal API
    return {
        "image_id": "mock-nobg-image-id",
        "url": "/static/images/mock-nobg-image.jpg",
        "width": 512,
        "height": 512
    }

# Routes
@router.get("/", response_class=HTMLResponse)
async def design_studio(request: Request):
    return templates.TemplateResponse("design_studio.html", {"request": request})

@router.post("/generate", response_model=List[ImageResponse])
async def generate_images(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_active_user)
):
    return generate_image(
        prompt=request.prompt,
        style=request.style,
        size=request.size,
        num_images=request.num_images
    )

@router.post("/edit", response_model=ImageResponse)
async def edit_existing_image(
    request: ImageEditRequest,
    current_user: User = Depends(get_current_active_user)
):
    return edit_image(request.image_id, request.edits)

@router.post("/remove-background")
async def upload_and_remove_bg(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Process the image
    contents = await file.read()
    
    # In a real application, this would call an AI service to remove background
    result = remove_background(BytesIO(contents))
    
    return result

@router.get("/styles")
async def get_available_styles():
    styles = [
        {"id": "realistic", "name": "Realistic"},
        {"id": "cartoon", "name": "Cartoon"},
        {"id": "digital-art", "name": "Digital Art"},
        {"id": "sketch", "name": "Sketch"},
        {"id": "oil-painting", "name": "Oil Painting"},
        {"id": "watercolor", "name": "Watercolor"},
        {"id": "pixel-art", "name": "Pixel Art"}
    ]
    return styles 