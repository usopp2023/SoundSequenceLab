"""测试隔离：强制用占位分析/音乐，避免冒烟测试打真实外部 API（阶跃/Suno）。"""
import pytest

from app.api import routes_generate
from app.services.analysis import PlaceholderAnalysis
from app.services.music import PlaceholderMusic


@pytest.fixture(autouse=True, scope="session")
def _offline_services():
    # 即使 .env 配了真实 key / SUNO_ENABLED，测试也走占位，保证离线、确定、不花额度
    routes_generate.analysis_service = PlaceholderAnalysis()
    routes_generate.music_service = PlaceholderMusic()
    routes_generate.fallback_music = PlaceholderMusic()
    yield
