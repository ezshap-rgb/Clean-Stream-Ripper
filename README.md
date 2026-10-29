# Clean Stream Ripper

A high-performance personal desktop YouTube and media stream ripper with native Windows support, featuring the custom 3D gradient play-and-download badge and the dark aesthetic of **Clean Audio Trimmer**.

![Clean Stream Ripper](frontend/icon.png)

## Highlights

- **Standalone Windows Desktop App**: Launches directly in a native desktop window with no browser tab or command prompt required.
- **Custom 3D App Icon**: Branded with the glossy 3D purple/magenta play & download arrow logo (`icon.ico` / `icon.png`).
- **Direct Stream Slicing (HTTP Range Fetching)**: Download and clip *only* the specific timestamps you want (`00:01:30 - 00:03:00`) directly from YouTube's stream without downloading the entire video first.
- **High Quality MP3 & M4A Extraction**: 320 kbps MP3 conversion or original AAC audio.
- **Video Modes (MP4)**: Best available (up to 4K), 1080p Full HD, 720p HD, 480p, 360p with audio automatically merged via bundled FFmpeg.
- **Live SSE Progress**: Real-time progress percentage, download speed in MB/s, size transferred, and ETA.
- **Bundled FFmpeg Engine**: Runs out of the box with zero system PATH configuration needed.

---

## How to Run

### 1. Launch the Desktop Window Directly
```powershell
python desktop_main.py
```
This opens the native desktop app window directly with your custom icon.

### 2. Standalone Built Executable (`.exe`)
Run:
```powershell
dist\"Clean Stream Ripper"\"Clean Stream Ripper.exe"
```
You can create a shortcut to this `.exe` on your Desktop or pin it to your Windows Taskbar!

### 3. Rebuilding the Executable
If you make code or style changes and want to update the `.exe`:
```powershell
python build_exe.py
```
