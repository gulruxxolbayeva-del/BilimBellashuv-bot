import base64
import binascii
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

load_dotenv()
BASE = Path(__file__).resolve().parent
UPLOADS = BASE / "uploads"
UPLOADS.mkdir(exist_ok=True)
app = FastAPI(title="BilimBellashuv Mini App")
app.mount("/static", StaticFiles(directory=BASE / "miniapp"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")


class ImageUpload(BaseModel):
    data_url: str


@app.post("/upload-image")
def upload_image(payload: ImageUpload):
    if not payload.data_url.startswith("data:image/") or ";base64," not in payload.data_url:
        raise HTTPException(status_code=400, detail="Rasm formati noto‘g‘ri")
    header, encoded = payload.data_url.split(",", 1)
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=400, detail="Rasm ma’lumoti noto‘g‘ri") from exc
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Rasm 5 MB dan kichik bo‘lishi kerak")
    mime = header[5:].split(";", 1)[0].lower()
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}.get(mime)
    if not ext:
        raise HTTPException(status_code=400, detail="Faqat JPG, PNG, WEBP yoki GIF rasm qabul qilinadi")
    name = f"{secrets.token_urlsafe(18)}.{ext}"
    (UPLOADS / name).write_bytes(raw)
    return {"url": f"/uploads/{name}"}


@app.get("/")
def home():
    return FileResponse(BASE / "miniapp" / "index.html")


@app.get("/answer")
def answer():
    # The Mini App reads attempt_id and question_id from the query string.
    # The bot validates ownership and the active question when sendData arrives.
    return FileResponse(BASE / "miniapp" / "index.html")


@app.get("/health")
def health():
    return {"ok": True, "service": "bilimbellashuv-mini-app"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mini_server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
