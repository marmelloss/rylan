from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from datetime import datetime
from typing import List

app = FastAPI()

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

@app.get("/")
def health_check():
    """
    Basic health check endpoint.
    Useful for deployment platforms that ping `/` to verify app is running.
    """
    return {"status": "ok", "message": "Rylan backend is running"}

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

# Serve static files from dist/
from fastapi.staticfiles import StaticFiles
try:
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")
except RuntimeError as e:
    print(f"[ERROR] 'dist/' directory not found. Serving only API routes. Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
