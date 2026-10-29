import os
import time
import uuid
import shutil
import logging
import threading
from typing import Dict, Any, Optional

# Configure Bundled FFmpeg & PATH so yt-dlp internal downloaders work smoothly
try:
    import imageio_ffmpeg
    raw_exe = imageio_ffmpeg.get_ffmpeg_exe()
    exe_dir = os.path.dirname(raw_exe)
    canonical_ffmpeg = os.path.join(exe_dir, "ffmpeg.exe")
    if not os.path.exists(canonical_ffmpeg):
        try:
            shutil.copyfile(raw_exe, canonical_ffmpeg)
        except Exception:
            pass
    if exe_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")
    DEFAULT_FFMPEG = canonical_ffmpeg if os.path.exists(canonical_ffmpeg) else raw_exe
except Exception:
    DEFAULT_FFMPEG = shutil.which("ffmpeg") or "ffmpeg"

import yt_dlp
from yt_dlp.utils import download_range_func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream_ripper")

# Save directly to user's Windows Downloads directory in a dedicated folder
USER_DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
DOWNLOAD_DIR = os.path.join(USER_DOWNLOADS, "Clean Stream Ripper")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory job state store
jobs: Dict[str, Dict[str, Any]] = {}

def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    return jobs.get(job_id)

def search_youtube(query: str, limit: int = 6) -> list:
    """Search YouTube videos directly using yt-dlp."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "socket_timeout": 12,
        "noplaylist": True,
    }
    search_target = f"ytsearch{limit}:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(search_target, download=False)
        entries = res.get("entries", []) or []

    results = []
    for entry in entries:
        duration = int(entry.get("duration") or 0)
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
        
        vid_id = entry.get("id")
        results.append({
            "id": vid_id,
            "url": f"https://www.youtube.com/watch?v={vid_id}",
            "title": entry.get("title", "Unknown Title"),
            "channel": entry.get("uploader") or entry.get("channel") or "Unknown Channel",
            "duration": duration,
            "duration_str": duration_str,
            "thumbnail": entry.get("thumbnail") or (entry.get("thumbnails")[-1]["url"] if entry.get("thumbnails") else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"),
        })
    return results

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

    # Range Download: Downloads ONLY the specified time window directly from stream!
    if start_time is not None or end_time is not None:
        s = float(start_time or 0)
        e = float(end_time) if end_time is not None else None
        ydl_opts["download_ranges"] = download_range_func(None, [(s, e)])
        ydl_opts["force_keyframes_at_cuts"] = True

    if mode == "audio":
        if audio_format.startswith("mp3"):
            # Extract bitrate (e.g. "mp3-320", "mp3-192", "mp3-128", "mp3-64")
            bitrate = "320"
            if "-" in audio_format:
                bitrate = audio_format.split("-", 1)[1]
            elif audio_format == "mp3":
                bitrate = "320"

            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": bitrate,
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
            ydl.download([url])
            
        # Find the generated file matching job_id
        final_file = None
        for fname in os.listdir(DOWNLOAD_DIR):
            if fname.startswith(f"{job_id}_"):
                final_file = fname
                break

        if final_file:
            clean_name = final_file[len(job_id) + 1:]
            old_path = os.path.join(DOWNLOAD_DIR, final_file)
            target_path = os.path.join(DOWNLOAD_DIR, clean_name)
            
            # Prevent overwriting existing file with identical name
            if os.path.exists(target_path):
                base, ext = os.path.splitext(clean_name)
                counter = 1
                while os.path.exists(os.path.join(DOWNLOAD_DIR, f"{base} ({counter}){ext}")):
                    counter += 1
                clean_name = f"{base} ({counter}){ext}"
                target_path = os.path.join(DOWNLOAD_DIR, clean_name)

            try:
                os.rename(old_path, target_path)
                actual_name = clean_name
                actual_path = target_path
            except Exception:
                actual_name = final_file
                actual_path = old_path

            size = os.path.getsize(actual_path)
            jobs[job_id].update({
                "status": "completed",
                "phase": "finished",
                "progress": 100.0,
                "filename": actual_name,
                "display_name": actual_name,
                "full_path": actual_path,
                "folder_path": DOWNLOAD_DIR,
                "size": size,
                "download_url": f"/api/files/{actual_name}",
            })
            logger.info(f"Download saved directly to user Downloads folder: {actual_path}")
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
