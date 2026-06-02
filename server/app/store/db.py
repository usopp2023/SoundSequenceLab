"""SQLite 持久化层（SQLModel）。

表：
  PlazaWork   广场作品（种子库）
  ResultRow   生成结果（用户历史档案）
  Like        用户对广场作品的收藏（openid + plaza_id）
"""
import json
from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select

from .. import config

_engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


# ---------------- 表定义 ----------------
class PlazaWork(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    desc: str
    likes: int = 0          # 基础赞数（种子值）
    by: str = "来自 一位匿名的朋友"


class ResultRow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    result_id: str = Field(index=True)
    openid: str = Field(index=True)
    persona_name: str
    persona_en: str
    report: str
    dims_json: str          # JSON: List[Dim]
    music_url: str
    music_duration: int
    curve_url: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Like(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    openid: str = Field(index=True)
    plaza_id: int = Field(index=True)


# ---------------- 引擎 / 会话 ----------------
def init_db() -> None:
    SQLModel.metadata.create_all(_engine)


def get_session() -> Session:
    return Session(_engine)


# ---------------- 广场 ----------------
def list_plaza() -> List[PlazaWork]:
    with get_session() as s:
        return list(s.exec(select(PlazaWork).order_by(PlazaWork.id)))


def get_plaza(plaza_id: int) -> Optional[PlazaWork]:
    with get_session() as s:
        return s.get(PlazaWork, plaza_id)


def count_plaza() -> int:
    with get_session() as s:
        return len(list(s.exec(select(PlazaWork))))


def add_plaza(name: str, desc: str, likes: int, by: str = "来自 一位匿名的朋友") -> None:
    with get_session() as s:
        s.add(PlazaWork(name=name, desc=desc, likes=likes, by=by))
        s.commit()


# ---------------- 收藏 / 点赞 ----------------
def is_liked(openid: str, plaza_id: int) -> bool:
    with get_session() as s:
        row = s.exec(
            select(Like).where(Like.openid == openid, Like.plaza_id == plaza_id)
        ).first()
        return row is not None


def liked_set(openid: str) -> set:
    with get_session() as s:
        rows = s.exec(select(Like).where(Like.openid == openid))
        return {r.plaza_id for r in rows}


def toggle_like(openid: str, plaza_id: int) -> bool:
    """切换收藏，返回切换后的 liked 状态。"""
    with get_session() as s:
        row = s.exec(
            select(Like).where(Like.openid == openid, Like.plaza_id == plaza_id)
        ).first()
        if row:
            s.delete(row)
            s.commit()
            return False
        s.add(Like(openid=openid, plaza_id=plaza_id))
        s.commit()
        return True


def plaza_like_count(plaza_id: int) -> int:
    """对外显示赞数 = 种子基础值 + 真实收藏数。"""
    with get_session() as s:
        work = s.get(PlazaWork, plaza_id)
        base = work.likes if work else 0
        extra = len(list(s.exec(select(Like).where(Like.plaza_id == plaza_id))))
        return base + extra


# ---------------- 结果 / 档案 ----------------
def save_result(
    result_id: str,
    openid: str,
    persona_name: str,
    persona_en: str,
    report: str,
    dims: list,
    music_url: str,
    music_duration: int,
    curve_url: str = "",
) -> None:
    with get_session() as s:
        s.add(ResultRow(
            result_id=result_id,
            openid=openid,
            persona_name=persona_name,
            persona_en=persona_en,
            report=report,
            dims_json=json.dumps(dims, ensure_ascii=False),
            music_url=music_url,
            music_duration=music_duration,
            curve_url=curve_url,
        ))
        s.commit()


def get_result(result_id: str) -> Optional[ResultRow]:
    with get_session() as s:
        return s.exec(select(ResultRow).where(ResultRow.result_id == result_id)).first()


def list_results(openid: str) -> List[ResultRow]:
    """某用户全部档案，按创建时间倒序。"""
    with get_session() as s:
        rows = list(s.exec(select(ResultRow).where(ResultRow.openid == openid)))
        rows.sort(key=lambda r: r.created_at, reverse=True)
        return rows


def result_row_to_dims(row: ResultRow) -> list:
    return json.loads(row.dims_json)
