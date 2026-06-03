"""声序实验室 · 情绪音乐 —— FastAPI 后端入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .api import (
    routes_auth,
    routes_generate,
    routes_kiosk,
    routes_me,
    routes_plaza,
    routes_upload,
)
from .store.seed import run_seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：建表 + 生成兜底曲 + 写广场种子
    run_seed()
    yield


app = FastAPI(title="声序实验室 · 情绪音乐 后端", version="0.1.0", lifespan=lifespan)

# CORS 全放开（dev）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源（兜底曲 / 上传音频 / 曲线图）挂到 /static
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

# 路由
app.include_router(routes_auth.router)
app.include_router(routes_upload.router)
app.include_router(routes_generate.router)
app.include_router(routes_me.router)
app.include_router(routes_plaza.router)
app.include_router(routes_kiosk.router)


@app.get("/")
def root():
    return {"app": "声序实验室 · 情绪音乐 后端", "docs": "/docs"}
