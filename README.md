# ClipForge AI — starter MVP

A FastAPI + FFmpeg application that accepts a video upload, makes evenly spaced segments, converts them to a vertical 1080×1920 MP4 frame, and provides download links.

## Included
- Browser upload interface
- Clip count and duration options
- FFmpeg rendering endpoint
- MP4 download endpoint
- `/health` health-check endpoint
- Dockerfile with FFmpeg installed
- `render.yaml` for Render Blueprint deployment

## Important feature limits
This is a working starter video processor, **not yet an AI highlight generator**. It does not accept YouTube URLs, identify interesting moments, transcribe audio, add captions, manage accounts/payments, or publish to social media. Those features need to be built and tested separately.

## Local run
Install Python 3.11+ and FFmpeg (including ffprobe), then:

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

## Docker run
```bash
docker build -t clipforge-ai .
docker run --rm -p 8000:8000 clipforge-ai
```

## Deploy on Render
Push the contents of this folder to your GitHub repository. In Render, connect GitHub and create a Blueprint from the repository, or create a Docker Web Service. Review the settings before deploying. Test `/health` on the deployed URL.

## Hosting limitations
Render free web services can spin down when idle, have limited CPU/RAM, and use ephemeral local storage. Uploaded and generated videos may disappear after restarts, redeploys, or spin-downs. Large video jobs may be too slow or exceed resource limits. For production, add persistent object storage, background job processing, upload-size limits, authentication, monitoring, and suitable paid compute.

Only upload content you own or have permission to process. Follow applicable copyright rules and platform terms.
