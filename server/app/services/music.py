"""音乐生成服务 —— 可插拔接口 + 占位实现 + Suno 真实现。

- PlaceholderMusic：按 mood 返回预置兜底 wav（不依赖外部）。
- SunoMusic：调本地 suno-api（gcui-art）生成民乐 instrumental，轮询取 audio_url，
  把 mp3 转存到 static/generated/，返回我们自己的 URL。

注意：Suno 出曲 30s–2min，必须在后台线程里调（见 routes_generate 的异步 worker）。
SUNO_ENABLED=1 且 suno-api 跑在 SUNO_API_BASE 时才用 SunoMusic，否则用占位。
"""
import time
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .. import config
from .analysis import AnalysisResult

_MOOD_TO_FILE = {"dusk": "dusk.wav", "calm": "calm.wav", "bright": "bright.wav", "deep": "deep.wav", "rain": "rain.wav"}
_DEFAULT_FILE = "dusk.wav"


@dataclass
class MusicResult:
    url: str
    duration: int


class MusicService(ABC):
    @abstractmethod
    def generate(self, analysis: AnalysisResult) -> MusicResult:
        raise NotImplementedError


class PlaceholderMusic(MusicService):
    """占位：按 mood 返回预置兜底 wav。"""

    def generate(self, analysis: AnalysisResult) -> MusicResult:
        filename = _MOOD_TO_FILE.get(analysis.mood, _DEFAULT_FILE)
        path = config.FALLBACK_MUSIC_DIR / filename
        if not path.exists():
            path = config.FALLBACK_MUSIC_DIR / _DEFAULT_FILE
        return MusicResult(url=config.static_url(f"fallback_music/{path.name}"), duration=_wav_seconds(path))


class SunoMusic(MusicService):
    """调 suno-api 生成民乐 instrumental → 轮询 → 下载转存。失败抛异常（上层兜底）。"""

    def __init__(self, api_base: str, poll_timeout: int = 180, poll_interval: float = 5.0):
        self.base = api_base.rstrip("/")
        self.poll_timeout = poll_timeout
        self.poll_interval = poll_interval

    def generate(self, analysis: AnalysisResult) -> MusicResult:
        prompt = self._build_prompt(analysis)
        ids = self._start(prompt)
        clip = self._wait(ids)
        path = self._download(clip)
        dur = int(round(float(clip.get("duration") or 0))) or 30
        return MusicResult(url=config.static_url(f"generated/{path.name}"), duration=dur)

    def _build_prompt(self, analysis: AnalysisResult) -> str:
        raw = analysis.raw or {}
        params = raw.get("bucket_params") or {}
        return params.get("suno_tags") or "Chinese folk instrumental, solo guzheng, pentatonic, no vocals"

    def _start(self, prompt: str) -> List[str]:
        import httpx
        with httpx.Client(timeout=60) as c:
            r = c.post(f"{self.base}/api/generate",
                       json={"prompt": prompt, "make_instrumental": True, "wait_audio": False})
            r.raise_for_status()
            clips = r.json()
        ids = [cl.get("id") for cl in clips if cl.get("id")]
        if not ids:
            raise RuntimeError("suno-api 未返回 clip id")
        return ids

    def _wait(self, ids: List[str]) -> dict:
        import httpx
        deadline = time.monotonic() + self.poll_timeout
        idstr = ",".join(ids)
        with httpx.Client(timeout=30) as c:
            while time.monotonic() < deadline:
                r = c.get(f"{self.base}/api/get", params={"ids": idstr})
                if r.status_code == 200:
                    for clip in r.json():
                        if clip.get("audio_url") and clip.get("status") in ("streaming", "complete"):
                            return clip
                time.sleep(self.poll_interval)
        raise TimeoutError("Suno 出曲超时")

    def _download(self, clip: dict) -> Path:
        import httpx
        path = config.GENERATED_DIR / f"{clip.get('id', 'track')}.mp3"
        with httpx.Client(timeout=120) as c:
            r = c.get(clip["audio_url"])
            r.raise_for_status()
            path.write_bytes(r.content)
        return path


def _wav_seconds(path: Path) -> int:
    try:
        with wave.open(str(path), "rb") as w:
            return max(1, round(w.getnframes() / (w.getframerate() or 1)))
    except Exception:
        return 15


def _make_service() -> MusicService:
    if config.SUNO_ENABLED:
        print(f"[music] 使用 Suno 真实生成：{config.SUNO_API_BASE}")
        return SunoMusic(config.SUNO_API_BASE)
    return PlaceholderMusic()


# 单例（注入点）：SUNO_ENABLED 时用 Suno，否则占位
music_service: MusicService = _make_service()
# 兜底实例（Suno 失败时回退）
fallback_music: MusicService = PlaceholderMusic()
