"""全局配置。仅从环境变量 / .env 读取，密钥永不写死在代码里。"""
import os
from pathlib import Path

# python-dotenv 为可选依赖：未安装时降级为「只读系统环境变量」，不影响启动。
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False

# 加载 .env（若存在）。本轮无真实 key，缺失也不报错。
BASE_DIR = Path(__file__).resolve().parent          # .../server/app
PROJECT_DIR = BASE_DIR.parent                        # .../server
load_dotenv(PROJECT_DIR / ".env")

# ---- 静态资源目录 ----
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
FALLBACK_MUSIC_DIR = STATIC_DIR / "fallback_music"
CURVES_DIR = STATIC_DIR / "curves"
for _d in (STATIC_DIR, UPLOADS_DIR, FALLBACK_MUSIC_DIR, CURVES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---- 可配置项（环境变量优先）----
STATIC_BASE = os.getenv("STATIC_BASE", "/static")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_DIR / 'shengxu.db'}")

# 第三方 key（占位）
WECHAT_APPID = os.getenv("WECHAT_APPID", "")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "")
ANALYSIS_API_KEY = os.getenv("ANALYSIS_API_KEY", "")
# 阶跃星辰 OpenAI 兼容端点 + 模型（.env 留空时用默认）
ANALYSIS_API_BASE = os.getenv("ANALYSIS_API_BASE") or "https://api.stepfun.com/v1"
ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL") or "step-2-16k"
SUNO_API_KEY = os.getenv("SUNO_API_KEY", "")
SUNO_API_BASE = os.getenv("SUNO_API_BASE", "")


def static_url(relative: str) -> str:
    """把相对静态路径（如 'fallback_music/dusk.wav'）转成对外 URL。"""
    return f"{STATIC_BASE}/{relative.lstrip('/')}"
