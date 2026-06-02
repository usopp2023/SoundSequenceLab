"""生成任务：创建 job + 轮询 job 状态（用创建时间模拟异步）。"""
import time
import uuid
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from ..models import schemas
from ..services.analysis import analysis_service
from ..services.music import music_service
from ..services import personas
from ..store import db
from .deps import get_openid

router = APIRouter(prefix="/api", tags=["generate"])

# 生成步骤文案（前端按此展示进度）
STEPS = ["正在听你说的话……", "读出你藏起来的情绪……", "正在谱一段曲子……"]

# job 完成所需时间（秒）：创建后约 2.5 秒变 done
_JOB_DELAY_SEC = 2.5

# 内存 job 表：jobId -> {openid, created, answers, result_id?}
_JOBS: Dict[str, dict] = {}


def _build_and_save_result(job: dict) -> str:
    """跑分析 + 音乐，落库一条新档案，返回 resultId。"""
    answers = job["answers"]
    analysis = analysis_service.analyze(answers)
    music = music_service.generate(analysis)
    dims = personas.build_dims(analysis.dim_values)
    result_id = "r_" + uuid.uuid4().hex[:12]
    db.save_result(
        result_id=result_id,
        openid=job["openid"],
        persona_name=analysis.persona_name,
        persona_en=analysis.persona_en,
        report=analysis.report,
        dims=dims,
        music_url=music.url,
        music_duration=music.duration,
        curve_url="",
    )
    return result_id


@router.post("/generate", response_model=schemas.GenerateResp)
def generate(req: schemas.GenerateReq, openid: str = Depends(get_openid)):
    job_id = "j_" + uuid.uuid4().hex[:12]
    _JOBS[job_id] = {
        "openid": openid,
        "created": time.monotonic(),
        "answers": [a.model_dump() for a in req.answers],
        "result_id": None,
    }
    return schemas.GenerateResp(jobId=job_id)


@router.get("/jobs/{job_id}", response_model=schemas.JobResp)
def get_job(job_id: str):
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    elapsed = time.monotonic() - job["created"]
    if elapsed < _JOB_DELAY_SEC:
        return schemas.JobResp(status="running", steps=STEPS, result=None)

    # 到点：首次访问时生成并落库，之后复用
    if not job["result_id"]:
        job["result_id"] = _build_and_save_result(job)

    row = db.get_result(job["result_id"])
    result = _row_to_result(row)
    return schemas.JobResp(status="done", steps=STEPS, result=result)


def _row_to_result(row) -> schemas.Result:
    dims = db.result_row_to_dims(row)
    return schemas.Result(
        resultId=row.result_id,
        persona=schemas.Persona(name=row.persona_name, en=row.persona_en),
        report=row.report,
        dims=[schemas.Dim(**d) for d in dims],
        curveUrl=row.curve_url,
        music=schemas.Music(url=row.music_url, duration=row.music_duration),
    )
