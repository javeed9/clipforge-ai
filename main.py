from pathlib import Path
import shutil, subprocess, uuid
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
UPLOADS, OUTPUTS = DATA / "uploads", DATA / "outputs"
for folder in (UPLOADS, OUTPUTS): folder.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="ClipForge AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/health")
def health():
    return {"status": "ok", "service": "ClipForge AI"}

@app.post("/api/create-clips")
async def create_clips(video: UploadFile = File(...), clip_count: int = Form(3), clip_seconds: int = Form(30)):
    if clip_count not in (3, 5, 10) or clip_seconds not in (15, 30, 45, 60, 90):
        raise HTTPException(400, "Choose 3, 5, or 10 clips and a supported duration.")
    suffix = Path(video.filename or "").suffix.lower()
    if suffix not in {".mp4", ".mov", ".m4v", ".webm", ".mkv"}:
        raise HTTPException(400, "Upload an MP4, MOV, M4V, WEBM, or MKV video.")
    job = uuid.uuid4().hex[:12]
    source = UPLOADS / f"{job}{suffix}"
    try:
        with source.open("wb") as target: shutil.copyfileobj(video.file, target)
    finally:
        await video.close()
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(source)], capture_output=True, text=True)
    if probe.returncode:
        source.unlink(missing_ok=True)
        raise HTTPException(400, "Could not read the video. Try a standard MP4.")
    try: duration = float(probe.stdout.strip())
    except ValueError:
        source.unlink(missing_ok=True)
        raise HTTPException(400, "Could not determine video duration.")
    if duration < 2:
        source.unlink(missing_ok=True)
        raise HTTPException(400, "Video is too short.")
    count = min(clip_count, max(1, int(duration // 2)))
    span = max(0.0, duration - clip_seconds)
    starts = [span * i / (count - 1) for i in range(count)] if count > 1 else [span / 2]
    clips = []
    for n, start in enumerate(starts, 1):
        output = OUTPUTS / f"{job}-clip-{n:02d}.mp4"
        cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", str(source), "-t", str(min(clip_seconds, duration-start)), "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode:
            output.unlink(missing_ok=True)
            source.unlink(missing_ok=True)
            raise HTTPException(500, "Rendering failed. Try a smaller MP4.")
        clips.append({"name": output.name, "start_seconds": round(start, 1), "download_url": f"/api/download/{output.name}"})
    source.unlink(missing_ok=True)
    return {"job_id": job, "message": "Clips created as evenly spaced segments. AI highlight detection is not included yet.", "clips": clips}

@app.get("/api/download/{filename}")
def download(filename: str):
    if Path(filename).name != filename or not filename.endswith(".mp4"):
        raise HTTPException(404, "Clip not found.")
    path = OUTPUTS / filename
    if not path.is_file(): raise HTTPException(404, "Clip not found.")
    return FileResponse(path, media_type="video/mp4", filename=filename)
