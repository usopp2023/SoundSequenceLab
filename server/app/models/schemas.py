"""Pydantic 请求/响应模型。字段名与前端契约逐字段一致。"""
from typing import List, Optional

from pydantic import BaseModel


# ---------- 通用 ----------
class Persona(BaseModel):
    name: str
    en: str


class Dim(BaseModel):
    left: str
    right: str
    value: int
    activeSide: str


class Music(BaseModel):
    url: str
    duration: int
    status: str = "ready"      # ready | generating（Suno 异步出曲时）


class Result(BaseModel):
    resultId: str
    persona: Persona
    report: str
    dims: List[Dim]
    curveUrl: str = ""
    music: Music


# ---------- /api/login ----------
class LoginReq(BaseModel):
    code: Optional[str] = None


class LoginResp(BaseModel):
    openid: str


# ---------- /api/upload ----------
class UploadResp(BaseModel):
    text: str
    audioUrl: str


# ---------- /api/generate ----------
class Answer(BaseModel):
    q: int
    text: str = ""


class GenerateReq(BaseModel):
    answers: List[Answer] = []
    audioRefs: List[str] = []


class GenerateResp(BaseModel):
    jobId: str


# ---------- /api/jobs/{jobId} ----------
class JobResp(BaseModel):
    status: str
    steps: List[str]
    result: Optional[Result] = None


# ---------- /api/me/archive ----------
class ArchiveItem(BaseModel):
    resultId: str
    name: str
    en: str
    when: str


class ArchiveResp(BaseModel):
    items: List[ArchiveItem]


# ---------- /api/me/collected ----------
class CollectedItem(BaseModel):
    plazaId: int
    name: str


class CollectedResp(BaseModel):
    items: List[CollectedItem]


# ---------- /api/plaza ----------
class PlazaListItem(BaseModel):
    id: int
    name: str
    desc: str
    likes: int
    liked: bool


class PlazaListResp(BaseModel):
    items: List[PlazaListItem]


class PlazaDetailResp(BaseModel):
    id: int
    name: str
    en: str
    desc: str
    by: str
    likes: int
    liked: bool
    music: Music


class LikeResp(BaseModel):
    liked: bool
    likes: int


# ---------- /api/similarity ----------
class SimilarityReq(BaseModel):
    meName: str
    otherPlazaId: Optional[int] = None
    otherName: Optional[str] = None


class SimilarityPerson(BaseModel):
    name: str


class SimilarityResp(BaseModel):
    score: int
    you: SimilarityPerson
    other: SimilarityPerson
    reading: str


# ---------- /api/redeem ----------
class RedeemReq(BaseModel):
    code: Optional[str] = None


class RedeemResp(BaseModel):
    ok: bool
    unlocked: Optional[bool] = None
    badge: Optional[str] = None
    perkCode: Optional[str] = None
    message: Optional[str] = None
    claimed: Optional[bool] = None
    resultId: Optional[str] = None
    result: Optional[Result] = None


# ---------- /api/kiosk/claim-code ----------
class ClaimCodeReq(BaseModel):
    resultId: str


class ClaimCodeResp(BaseModel):
    ok: bool
    code: Optional[str] = None
    qrUrl: Optional[str] = None      # 二维码地址（编码认领码，现场屏显示 + 小程序扫码认领）
    message: Optional[str] = None
