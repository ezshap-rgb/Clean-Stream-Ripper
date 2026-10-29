# Clean Stream Ripper

A high-performance YouTube and media stream ripper for **desktop** and **mobile**, designed with the signature dark gradient styling of **Clean Audio Trimmer**.

![Clean Stream Ripper](frontend/icon.png)

## Highlights

- **Desktop & Mobile Responsive**: Optimized for phone touch screens and desktop monitors alike.
- **Progressive Web App (PWA)**: Installable directly to your phone's home screen.
- **Web Share Target API**: In the official YouTube mobile app, tap **Share → Clean Stream Ripper** to open and rip links in one tap.
- **Smart Formats & Codecs**:
  - **Video (MP4)**: Best available (up to 4K), 1080p Full HD, 720p HD, 480p, 360p with audio automatically merged via FFmpeg.
  - **Audio (MP3 / M4A)**: High quality 320kbps MP3 extraction or original AAC audio.
- **Time-Range Trimmer**: Cut and rip specific segments without downloading multi-hour files.
- **Real-Time Progress**: Live SSE (Server-Sent Events) streaming download speed, size, and conversion state.
- **Zero Config FFmpeg**: Includes standalone bundled FFmpeg binaries via `imageio-ffmpeg`.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run.py
```

Output:
```text
 * Local Desktop URL:  http://localhost:8000
 * Mobile Phone URL:   http://192.168.x.x:8000
```

---

## Mobile Usage (PWA & Share Sheet)

1. Make sure your phone is connected to the same Wi-Fi network as your computer.
2. Open the **Mobile Phone URL** in Chrome (Android) or Safari (iOS).
3. Tap **Add to Home Screen** / **Install App**.
4. Now, whenever you are watching a video in the YouTube app:
   - Tap **Share** → **Clean Stream Ripper**
   - The app opens with the video loaded and ready to rip!
