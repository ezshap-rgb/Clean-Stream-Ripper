import os
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .downloader import fetch_info, start_download_job, get_job_status, DOWNLOAD_DIR

app = FastAPI(title="Clean Stream Ripper API")

# Allow requests from local network and mobile devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    mode: str = "video"  # "video" or "audio"
    quality: str = "1080"
    audio_format: str = "mp3"
    start_time: Optional[float] = None
    end_time: Optional[float] = None

@app.post("/api/info")
async def api_info(req: InfoRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, fetch_info, req.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def api_download(req: DownloadRequest):
    if not req.url:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        options = {
            "mode": req.mode,
            "quality": req.quality,
            "audio_format": req.audio_format,
            "start_time": req.start_time,
            "end_time": req.end_time,
        }
        job_id = start_download_job(req.url, options)
        return {"job_id": job_id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{job_id}")
async def api_progress(job_id: str, request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
                
            job = get_job_status(job_id)
            if not job:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Job not found"})
                }
                break

            yield {
                "event": "progress",
                "data": json.dumps(job)
            }

            if job.get("status") in ("completed", "error"):
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())

@app.get("/api/files/{filename}")
async def api_get_file(filename: str):
    # Sanitize filename against directory traversal
    safe_name = os.path.basename(filename)
    file_path = os.path.join(DOWNLOAD_DIR, safe_name)
    
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found or expired")
    
    # Extract friendly display name (after job_id prefix)
    display_name = safe_name
    if "_" in safe_name:
        display_name = safe_name.split("_", 1)[1]

    media_type = "audio/mpeg" if safe_name.endswith(".mp3") else "video/mp4"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=display_name,
        headers={
            "Content-Disposition": f'attachment; filename="{display_name}"',
            "Cache-Control": "no-cache",
        }
    )

# Serve frontend static assets
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
