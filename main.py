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

# --- Runtime Debug Info ---
print("Current working directory:", os.getcwd())
print("Directory contents:")
for root, dirs, files in os.walk("."):
    print(f"DIR: {root}")
    for d in dirs:
        print(f" [D] {d}")
    for f in files:
        print(f" [F] {f}")

# Serve static files (images and CSS/JS)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print("Failed to mount /static:", str(e))

# Setup templates
try:
    templates = Jinja2Templates(directory="templates")
except Exception as e:
    print("Failed to load templates:", str(e))


# In-memory comment storage (resets on server restart)
comments_db = []

# Models
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


# Serve the main page with images
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    try:
        # Get all algorithm images from static folder
        static_path = Path("static")
        algorithm_images = sorted([f"static/{f.name}" for f in static_path.glob("algo*.png")])

        # Render template
        return templates.TemplateResponse("index.html", {
            "request": request,
            "algorithm_images": algorithm_images
        })

    except Exception as e:
        error_msg = f"<h1>Server Error</h1><pre>{str(e)}</pre>"
        error_msg += "<h3>Template Dir Exists?</h3><pre>" + str(os.path.exists("templates")) + "</pre>"
        error_msg += "<h3>Static Dir Exists?</h3><pre>" + str(os.path.exists("static")) + "</pre>"
        return HTMLResponse(error_msg, status_code=500)
