from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel
from datetime import datetime
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, PlainTextResponse
from pathlib import Path
import os

app = FastAPI()

# Get the base directory where main.py is located
BASE_DIR = Path(__file__).parent

# --- Runtime Debug Info ---
print("="*50)
print("Current working directory:", os.getcwd())
print("Base directory (where main.py is):", BASE_DIR)
print("Absolute path to templates:", BASE_DIR / "templates")
print("Absolute path to static:", BASE_DIR / "static")
print("Directory contents:")
for root, dirs, files in os.walk(BASE_DIR):
    print(f"DIR: {root}")
    for f in files:
        print(f" [F] {f}")

# Serve static files (images and CSS/JS)
static_dir = BASE_DIR / "static"
try:
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        print(f"Successfully mounted static files from: {static_dir}")
    else:
        print(f"Static directory not found at: {static_dir}")
except Exception as e:
    print("Failed to mount /static:", str(e))

# Setup templates with absolute path
templates_dir = BASE_DIR / "templates"
try:
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
        print(f"Templates loaded from: {templates_dir}")
        print("Template files available:", [f.name for f in templates_dir.glob('*')])
    else:
        print(f"Templates directory not found at: {templates_dir}")
        raise FileNotFoundError(f"Templates directory missing: {templates_dir}")
except Exception as e:
    print("Failed to load templates:", str(e))
    raise  # Re-raise the exception since templates are critical

# In-memory comment storage (resets on server restart)
comments_db = []

# Models (unchanged)
class CommentCreate(BaseModel):
    author: str
    content: str
    profile_id: str = "general"

class CommentOut(BaseModel):
    id: int
    author: str
    content: str
    profile_id: str
    timestamp: str

# Counter for unique IDs
comment_counter = 0

# Routes (unchanged except for serve_home)
@app.post("/comments", response_model=CommentOut)
async def add_comment(comment: CommentCreate):
    global comment_counter
    comment_counter += 1

    new_comment = CommentOut(
        id=comment_counter,
        **comment.dict(),
        timestamp=datetime.now().isoformat()
    )
    comments_db.append(new_comment)
    return new_comment

@app.get("/comments", response_model=List[CommentOut])
async def get_comments():
    return comments_db

@app.get("/comments/download")
async def download_comments():
    if not comments_db:
        return {"error": "No comments available"}

    text_output = ""
    for c in comments_db:
        text_output += f"ID: {c.id}\n"
        text_output += f"Author: {c.author}\n"
        text_output += f"Profile ID: {c.profile_id}\n"
        text_output += f"Timestamp: {c.timestamp}\n"
        text_output += f"Content: {c.content}\n"
        text_output += "-" * 40 + "\n"

    headers = {
        "Content-Disposition": "attachment; filename=rylan_forum_comments.txt"
    }
    return Response(content=text_output, media_type="text/plain", headers=headers)

# Updated serve_home endpoint with better error handling
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    try:
        # Get all algorithm images from static folder
        static_path = BASE_DIR / "static"
        algorithm_images = []
        if static_path.exists():
            algorithm_images = sorted([f"static/{f.name}" for f in static_path.glob("algo*.png")])
            print(f"Found algorithm images: {algorithm_images}")
        else:
            print(f"Static directory not found at: {static_path}")

        # Render template
        return templates.TemplateResponse("index.html", {
            "request": request,
            "algorithm_images": algorithm_images
        })

    except Exception as e:
        error_msg = f"""
        <h1>Server Error</h1>
        <pre>{str(e)}</pre>
        <h3>Debug Information:</h3>
        <pre>
        Base Directory: {BASE_DIR}
        Template Directory: {templates_dir} (exists: {templates_dir.exists()})
        Static Directory: {static_dir} (exists: {static_dir.exists()})
        Current Files:
        {os.listdir(BASE_DIR)}
        Template Files:
        {list(templates_dir.glob('*')) if templates_dir.exists() else 'N/A'}
        </pre>
        """
        return HTMLResponse(error_msg, status_code=500)
