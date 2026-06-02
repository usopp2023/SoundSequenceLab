"""我的：历史档案 + 收藏 + 单个结果。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..models import schemas
from ..store import db
from .deps import get_openid
from .routes_generate import _row_to_result

router = APIRouter(prefix="/api", tags=["me"])


def _fmt_when(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso


@router.get("/me/archive", response_model=schemas.ArchiveResp)
def my_archive(openid: str = Depends(get_openid)):
    rows = db.list_results(openid)  # 已倒序
    items = [
        schemas.ArchiveItem(
            resultId=r.result_id,
            name=r.persona_name,
            en=r.persona_en,
            when=_fmt_when(r.created_at),
        )
        for r in rows
    ]
    return schemas.ArchiveResp(items=items)


@router.get("/me/collected", response_model=schemas.CollectedResp)
def my_collected(openid: str = Depends(get_openid)):
    ids = db.liked_set(openid)
    items = []
    for pid in sorted(ids):
        work = db.get_plaza(pid)
        if work:
            items.append(schemas.CollectedItem(plazaId=pid, name=work.name))
    return schemas.CollectedResp(items=items)


@router.get("/results/{result_id}", response_model=schemas.Result)
def get_result(result_id: str):
    row = db.get_result(result_id)
    if not row:
        raise HTTPException(status_code=404, detail="result not found")
    return _row_to_result(row)
