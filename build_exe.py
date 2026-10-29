import os
import sys
import subprocess
import shutil

def build():
    import imageio_ffmpeg

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    icon_path = os.path.join(base_dir, "icon.ico")
    frontend_dir = os.path.join(base_dir, "frontend")
    backend_dir = os.path.join(base_dir, "backend")

    print("=" * 60)
    print("   BUILDING CLEAN STREAM RIPPER STANDALONE DESKTOP EXE")
    print("=" * 60)

    # PyInstaller arguments
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Clean Stream Ripper",
        "--onedir",
        "--windowed",
        "--noconfirm",
        f"--icon={icon_path}",
        f"--add-data={frontend_dir};frontend",
        f"--add-data={backend_dir};backend",
        f"--add-data={ffmpeg_dir};imageio_ffmpeg/binaries",
        f"--add-data={icon_path};.",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespans",
        "--hidden-import=uvicorn.lifespans.on",
        "--hidden-import=sse_starlette",
        "--hidden-import=yt_dlp",
        "--hidden-import=clr",
        "--hidden-import=pythonnet",
        "--hidden-import=webview",
        os.path.join(base_dir, "desktop_main.py")
    ]

    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        exe_path = os.path.join(base_dir, "dist", "Clean Stream Ripper", "Clean Stream Ripper.exe")
        print("\n" + "=" * 60)
        print("   BUILD SUCCESSFUL!")
        print(f"   Desktop executable is located at:")
        print(f"   {exe_path}")
        print("=" * 60)
    else:
        print("\nBuild failed with exit code:", result.returncode)

if __name__ == "__main__":
    build()

