import os
import time
import uuid
import threading
import logging
from typing import Dict, Any, Optional

try:
    import imageio_ffmpeg
    DEFAULT_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    import shutil
    DEFAULT_FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream_ripper")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory job state store
jobs: Dict[str, Dict[str, Any]] = {}

def cleanup_old_files(max_age_seconds: int = 7200):
    """Clean up files in DOWNLOAD_DIR older than max_age_seconds (default 2 hours)."""
    now = time.time()
    try:
        for fname in os.listdir(DOWNLOAD_DIR):
            fpath = os.path.join(DOWNLOAD_DIR, fname)
            if os.path.isfile(fpath):
                if now - os.path.getmtime(fpath) > max_age_seconds:
                    try:
                        os.remove(fpath)
                        logger.info(f"Cleaned up expired file: {fname}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {fpath}: {e}")
    except Exception as e:
        logger.warning(f"Error during file cleanup: {e}")

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    return jobs.get(job_id)

def fetch_info(url: str) -> Dict[str, Any]:
    """Inspect YouTube video metadata without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "socket_timeout": 15,
        "noplaylist": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
    duration = info.get("duration", 0)
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
    
    # Available video heights
    formats = info.get("formats", [])
    heights = sorted(list({f.get("height") for f in formats if f.get("height") and f.get("vcodec") != "none"}), reverse=True)
    
    return {
        "id": info.get("id"),
        "title": info.get("title", "Unknown Title"),
        "channel": info.get("uploader", "Unknown Channel"),
        "duration": duration,
        "duration_str": duration_str,
        "thumbnail": info.get("thumbnail") or (info.get("thumbnails")[-1]["url"] if info.get("thumbnails") else ""),
        "view_count": info.get("view_count", 0),
        "available_resolutions": heights,
        "is_live": info.get("is_live", False),
    }

def _download_worker(job_id: str, url: str, options: Dict[str, Any]):
    cleanup_old_files()
    jobs[job_id]["status"] = "downloading"
    jobs[job_id]["progress"] = 0.0
    jobs[job_id]["speed"] = 0
    jobs[job_id]["eta"] = 0
    jobs[job_id]["phase"] = "downloading"
    
    mode = options.get("mode", "video") # 'video' or 'audio'
    quality = options.get("quality", "1080")
    audio_format = options.get("audio_format", "mp3") # 'mp3' or 'm4a'
    start_time = options.get("start_time") # in seconds or None
    end_time = options.get("end_time")     # in seconds or None

    output_template = os.path.join(DOWNLOAD_DIR, f"{job_id}_%(title).80B.%(ext)s")

    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total > 0 else 0.0
            
            jobs[job_id].update({
                "status": "downloading",
                "progress": round(percent, 1),
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "speed": d.get("speed") or 0,
                "eta": d.get("eta") or 0,
                "phase": "downloading",
            })
        elif d["status"] == "finished":
            jobs[job_id].update({
                "status": "processing",
                "phase": "muxing",
                "progress": 99.0,
            })

    def postprocessor_hook(d):
        if d["status"] == "started":
            jobs[job_id].update({
                "status": "processing",
                "phase": "converting",
                "progress": 99.0,
            })

    ydl_opts: Dict[str, Any] = {
        "outtmpl": output_template,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ffmpeg_location": DEFAULT_FFMPEG,
    }

    # Time range clipping
    if start_time is not None or end_time is not None:
        def custom_download_ranges(info_dict, ydl):
            s = float(start_time or 0)
            e = float(end_time or info_dict.get("duration", 0))
            return [{"start_time": s, "end_time": e}]
        ydl_opts["download_ranges"] = custom_download_ranges

    if mode == "audio":
        if audio_format == "mp3":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }],
            })
        else: # m4a
            ydl_opts.update({
                "format": "bestaudio[ext=m4a]/bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                }],
            })
    else: # Video mode
        if quality == "best":
            ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        else:
            h = int(quality) if str(quality).isdigit() else 1080
            ydl_opts["format"] = f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
        # Find the generated file matching job_id
        final_file = None
        for fname in os.listdir(DOWNLOAD_DIR):
            if fname.startswith(f"{job_id}_"):
                final_file = fname
                break

        if final_file:
            full_path = os.path.join(DOWNLOAD_DIR, final_file)
            size = os.path.getsize(full_path)
            jobs[job_id].update({
                "status": "completed",
                "phase": "finished",
                "progress": 100.0,
                "filename": final_file,
                "display_name": final_file[len(job_id) + 1:],
                "size": size,
                "download_url": f"/api/files/{final_file}",
            })
            logger.info(f"Download completed for job {job_id}: {final_file}")
        else:
            raise FileNotFoundError("Output file was not found after yt-dlp execution.")

    except Exception as e:
        logger.error(f"Download failed for job {job_id}: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "error",
            "phase": "error",
            "error": str(e),
        })

def start_download_job(url: str, options: Dict[str, Any]) -> str:
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "job_id": job_id,
        "url": url,
        "status": "queued",
        "phase": "queued",
        "progress": 0.0,
        "created_at": time.time(),
    }
    
    t = threading.Thread(target=_download_worker, args=(job_id, url, options), daemon=True)
    t.start()
    return job_id
