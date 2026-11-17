import base64
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from . import advisor, asr, tts, weather

app = FastAPI(title="Fasl Dost")
SESSIONS: dict[str, advisor.Session] = {}
MAX_IMG = 6_000_000


@app.get("/api/health")
def health():
    return {"asr": asr.available(), "model": advisor.MODEL}


@app.get("/api/weather")
async def get_weather(location: str):
    return await weather.get_weather(location) or {"error": "unavailable"}


@app.post("/api/advise")
async def advise(session_id: str = Form(""), text: str = Form(""), crop: str = Form("Wheat"),
                 stage: str = Form(""), location: str = Form(""),
                 audio: UploadFile | None = File(None), image: UploadFile | None = File(None)):
    sid = session_id if session_id in SESSIONS else uuid.uuid4().hex
    s = SESSIONS.setdefault(sid, advisor.Session())
    lang = None
    if audio is not None:
        if not asr.available():
            return {"session_id": sid, "error": "asr_unavailable",
                    "message": "Speech recognition is not installed on the server; type your message instead."}
        text, lang, _ = asr.transcribe(await audio.read(),
                                       Path(audio.filename or "a.webm").suffix or ".webm")
    if not text.strip() and image is None:
        return {"session_id": sid, "error": "empty", "message": "No speech or text received."}
    img = None
    if image is not None:
        raw = await image.read()
        if len(raw) <= MAX_IMG:
            img = (image.content_type or "image/jpeg", base64.b64encode(raw).decode())
    out = await advisor.run_turn(s, text or "(photo only)", lang, img, crop, stage, location)
    return {"session_id": sid, "transcript": text, "asr_language": lang, **out}


@app.post("/api/tts")
async def speak(text: str = Form(...), lang: str = Form("ur")):
    return Response(await tts.synth(text, lang), media_type="audio/mpeg")


app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "dist", html=True), name="web")
