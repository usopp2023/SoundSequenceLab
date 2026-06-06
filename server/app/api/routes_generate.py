"""生成任务：真异步。

/generate 起后台线程：先跑分析→落库（音乐标记 generating）→job 立即 done，
再在后台继续调 Suno 出曲、回填音乐（失败兜底）。/jobs 只读状态，不阻塞。

分析快（秒级~20s），Suno 慢（1–2min）。所以结果（人格/四维/报告）先到，
音乐稍后点亮 —— 对齐"异步+稍后听"。
"""
import queue
import threading
import uuid
from typing import Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException

from .. import config
from ..models import schemas
from ..services.analysis import analysis_service
from ..services.music import music_service, fallback_music
from ..services import personas
from ..store import db
from .deps import get_openid

router = APIRouter(prefix="/api", tags=["generate"])

STEPS = ["正在听你说的话……", "读出你藏起来的情绪……", "正在谱一段曲子……"]

# 内存 job 表：jobId -> {openid, answers, status, result_id, error}
# status: running（分析中）| done（结果已就绪，音乐可能仍在生成）| error
_JOBS: Dict[str, dict] = {}

# ── 音乐生成的「单一直列队列」──────────────────────────────────────────
# 为什么要队列：suno-api 是「一个有头浏览器 + 一个 Suno 账号」的单一共享资源，
# 不能多人同时驱动（会抢同一个浏览器；而且靠「快照差分」取回新曲，多首并行就分不清谁的）。
# 所以：分析照常并行（快、无状态，结果页秒出人格），但**音乐一律进队列、一个 worker 一首首串行出**。
# 这样：①任务有序排队 ②同一时刻只一首在生成 → 快照差分无歧义 → 谁的曲子是谁的，绝不会拿错。
# 单账号天花板：约 2-3min/首，N 人同时答 → 第 N 首约等 N×2-3min（线下排队场景可接受）。
_MUSIC_Q: "queue.Queue[Tuple[str, object]]" = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


def _ensure_music_worker() -> None:
    """懒启动唯一的音乐 worker 线程（首个需要出曲的请求触发）。"""
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        threading.Thread(target=_music_worker_loop, daemon=True).start()
        _worker_started = True


def _music_worker_loop() -> None:
    """唯一消费者：一首首串行出曲，绝不并发驱动浏览器。"""
    while True:
        result_id, analysis = _MUSIC_Q.get()
        try:
            _generate_music(result_id, analysis)
        except Exception as e:  # 单首失败不拖垮队列
            print(f"[music] 队列 worker 处理 {result_id} 异常：{e!r}")
        finally:
            _MUSIC_Q.task_done()


@router.post("/generate", response_model=schemas.GenerateResp)
def generate(req: schemas.GenerateReq, openid: str = Depends(get_openid)):
    job_id = "j_" + uuid.uuid4().hex[:12]
    _JOBS[job_id] = {
        "openid": openid,
        "answers": [a.model_dump() for a in req.answers],
        "status": "running",
        "result_id": None,
        "error": None,
    }
    threading.Thread(target=_worker, args=(job_id,), daemon=True).start()
    return schemas.GenerateResp(jobId=job_id)


@router.get("/jobs/{job_id}", response_model=schemas.JobResp)
def get_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    if job["status"] == "running":
        return schemas.JobResp(status="running", steps=STEPS, result=None)
    if job["status"] == "error":
        return schemas.JobResp(status="error", steps=STEPS, result=None)
    row = db.get_result(job["result_id"])
    return schemas.JobResp(status="done", steps=STEPS, result=_row_to_result(row))


def _worker(job_id: str) -> None:
    job = _JOBS[job_id]
    try:
        analysis = analysis_service.analyze(job["answers"])     # 分析（占位/阶跃）
        dims = personas.build_dims(analysis.dim_values)
        result_id = "r_" + uuid.uuid4().hex[:12]

        if config.SUNO_ENABLED:
            # 先落库：音乐 generating，结果立刻可见
            db.save_result(
                result_id=result_id, openid=job["openid"],
                persona_name=analysis.persona_name, persona_en=analysis.persona_en,
                report=analysis.report, dims=dims,
                music_url="", music_duration=0, curve_url="", music_status="generating",
            )
            job["result_id"] = result_id
            job["status"] = "done"
            # 不在本线程出曲（会和别人抢浏览器）；丢进单一直列队列，由唯一 worker 一首首串行出
            _ensure_music_worker()
            _MUSIC_Q.put((result_id, analysis))
        else:
            music = music_service.generate(analysis)            # 占位：即时
            db.save_result(
                result_id=result_id, openid=job["openid"],
                persona_name=analysis.persona_name, persona_en=analysis.persona_en,
                report=analysis.report, dims=dims,
                music_url=music.url, music_duration=music.duration, curve_url="", music_status="ready",
            )
            job["result_id"] = result_id
            job["status"] = "done"
    except Exception as e:
        print(f"[generate] worker 失败：{e!r}")
        job["status"] = "error"
        job["error"] = str(e)


def _generate_music(result_id: str, analysis) -> None:
    """调 Suno 出曲，回填音乐；失败回退兜底曲。"""
    try:
        music = music_service.generate(analysis)                # Suno 1–2min
        db.update_music(result_id, music.url, music.duration, "ready")
    except Exception as e:
        print(f"[music] Suno 失败回退兜底：{e!r}")
        fb = fallback_music.generate(analysis)
        db.update_music(result_id, fb.url, fb.duration, "ready")


def _row_to_result(row) -> schemas.Result:
    dims = db.result_row_to_dims(row)
    return schemas.Result(
        resultId=row.result_id,
        persona=schemas.Persona(name=row.persona_name, en=row.persona_en),
        report=row.report,
        dims=[schemas.Dim(**d) for d in dims],
        curveUrl=row.curve_url,
        music=schemas.Music(url=row.music_url, duration=row.music_duration, status=row.music_status),
    )
