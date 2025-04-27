# All-in-One AI Platform

## "One AI to do it all"

A web-based, all-in-one AI platform that supports:
- Code creation & debugging
- Graphic design & image generation/editing
- Productivity enhancements (writing, scheduling, summarizing)

## Architecture Overview

### Frontend
- Built with HTML, Tailwind CSS/CSS, and JavaScript
- Interfaces for: Code Editor, Design Canvas, Productivity Workspace
- Drag-and-drop design tools, syntax-highlighted code editor, chat-style AI assistant

### Backend
- Language: Python with FastAPI
- Handles user requests, sessions, and task routing
- Authentication & database connection (PostgreSQL / MongoDB)

### AI Models Integration
- LLMs (e.g., GPT-4, Claude, Gemini) for writing/code tasks
- Image Models (e.g., DALL·E, Stable Diffusion, Clipdrop API)
- Audio/Transcription Models (e.g., Whisper)
- Scheduling/Calendar Integration (Google Calendar API, Notion API, etc.)

## Core Modules & Features

### Code AI Module
- Languages: Python, JS, C++, Java, SQL
- Features:
  - Autocomplete, Explain Code, Bug Fixing
  - API generator (REST, GraphQL)
  - Website/app scaffolding (React, Flutter, etc.)

### Design AI Module
- Features:
  - Logo/banner/post generator (text-to-image)
  - Background remover & photo enhancement
  - Drag-and-drop canvas for editing
  - Convert sketches to digital mockups

### Productivity AI Module
- Features:
  - Email/document summarizer
  - Content writer (blogs, posts, reports)
  - Audio to text, language translator
  - Smart calendar with meeting suggestions

## Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/all-in-one-ai-platform.git
cd all-in-one-ai-platform
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your API keys and configuration
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

6. Open your browser and navigate to http://localhost:8000

## API Documentation

After running the application, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tech Stack

- **Frontend**: HTML, JavaScript, CSS, Tailwind CSS
- **Backend**: FastAPI
- **Auth & DB**: JWT Authentication, PostgreSQL, MongoDB Atlas
- **AI APIs**: OpenAI, Stability AI, Whisper
- **File Storage**: AWS S3 or Firebase
- **Scheduling**: Google Calendar API
- **Deployment**: Vercel (frontend), Render/AWS (backend)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
