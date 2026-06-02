"""音频上传 + ASR 占位转写。"""
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from .. import config
from ..models import schemas
from ..services.asr import asr_service

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=schemas.UploadResp)
async def upload(file: UploadFile = File(...), openid: str = Form(default="anon")):
    """保存音频到磁盘，返回占位识别文字 + 可访问 audioUrl。"""
    ext = Path(file.filename or "").suffix or ".dat"
    name = f"{openid}_{uuid.uuid4().hex}{ext}"
    dest = config.UPLOADS_DIR / name
    data = await file.read()
    dest.write_bytes(data)

    text = asr_service.transcribe(str(dest))
    return schemas.UploadResp(text=text, audioUrl=config.static_url(f"uploads/{name}"))
