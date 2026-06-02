"""广场：列表 / 详情 / 点赞收藏 / 相似度。"""
import random

from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..models import schemas
from ..services import personas, similarity
from ..store import db
from .deps import get_openid

router = APIRouter(prefix="/api", tags=["plaza"])


def _music_for(name: str) -> schemas.Music:
    """按人格 mood 选兜底曲（广场详情播放用）。"""
    p = personas.get_persona(name)
    mood = p.get("mood", "dusk")
    return schemas.Music(url=config.static_url(f"fallback_music/{mood}.wav"), duration=15)


@router.get("/plaza", response_model=schemas.PlazaListResp)
def plaza_list(n: int = 6, openid: str = Depends(get_openid)):
    works = db.list_plaza()
    if n < len(works):
        works = random.sample(works, n)
    liked = db.liked_set(openid)
    items = [
        schemas.PlazaListItem(
            id=w.id,
            name=w.name,
            desc=w.desc,
            likes=db.plaza_like_count(w.id),
            liked=w.id in liked,
        )
        for w in works
    ]
    return schemas.PlazaListResp(items=items)


@router.get("/plaza/{plaza_id}", response_model=schemas.PlazaDetailResp)
def plaza_detail(plaza_id: int, openid: str = Depends(get_openid)):
    w = db.get_plaza(plaza_id)
    if not w:
        raise HTTPException(status_code=404, detail="plaza work not found")
    p = personas.get_persona(w.name)
    return schemas.PlazaDetailResp(
        id=w.id,
        name=w.name,
        en=p["en"],
        desc=w.desc,
        by=w.by,
        likes=db.plaza_like_count(w.id),
        liked=db.is_liked(openid, w.id),
        music=_music_for(w.name),
    )


@router.post("/plaza/{plaza_id}/like", response_model=schemas.LikeResp)
def plaza_like(plaza_id: int, openid: str = Depends(get_openid)):
    w = db.get_plaza(plaza_id)
    if not w:
        raise HTTPException(status_code=404, detail="plaza work not found")
    liked = db.toggle_like(openid, plaza_id)
    return schemas.LikeResp(liked=liked, likes=db.plaza_like_count(plaza_id))


@router.post("/similarity", response_model=schemas.SimilarityResp)
def similarity_compare(req: schemas.SimilarityReq):
    # 确定对方人格名：优先 otherName，其次按 otherPlazaId 查广场
    other_name = req.otherName
    if not other_name and req.otherPlazaId is not None:
        w = db.get_plaza(req.otherPlazaId)
        if w:
            other_name = w.name
    if not other_name:
        raise HTTPException(status_code=400, detail="missing otherName / otherPlazaId")

    data = similarity.compare(req.meName, other_name)
    return schemas.SimilarityResp(
        score=data["score"],
        you=schemas.SimilarityPerson(**data["you"]),
        other=schemas.SimilarityPerson(**data["other"]),
        reading=data["reading"],
    )
