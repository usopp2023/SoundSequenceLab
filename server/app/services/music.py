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
    """通过 suno-api 的浏览器生成（/api/ui_generate）触发出曲，再轮询 /api/get
    取回新出现的那首，最后经代理从 Suno CDN 下载转存到 static/generated。
    适配国内 + 当前 Suno UI（hCaptcha 无感、无头被拦）。失败抛异常（上层兜底）。
    需 suno-api 跑在 SUNO_API_BASE（BROWSER_HEADLESS=false），SUNO_PROXY 可达。
    """

    def __init__(self, api_base: str, proxy: str = "", poll_timeout: int = 360, poll_interval: float = 10.0):
        self.base = api_base.rstrip("/")
        self.proxy = proxy or None
        self.poll_timeout = poll_timeout
        self.poll_interval = poll_interval

    def generate(self, analysis: AnalysisResult) -> MusicResult:
        desc = self._build_prompt(analysis)
        before = self._existing_ids()
        ids = self._trigger(desc)                 # ui_generate（慢，~1-2min）
        clip = self._wait_clip(before, ids)       # 轮询 /api/get 取回新曲
        path = self._download(clip)
        dur = int(round(float(clip.get("duration") or 0))) or 30
        return MusicResult(url=config.static_url(f"generated/{path.name}"), duration=dur)

    def _build_prompt(self, analysis: AnalysisResult) -> str:
        raw = analysis.raw or {}
        params = raw.get("bucket_params") or {}
        return params.get("suno_tags") or "Chinese folk instrumental, solo guzheng, pentatonic, no vocals"

    def _get_clips(self) -> List[dict]:
        # /api/get 经代理调 Suno，时通时断；重试几次，拿到合法 JSON 列表才算
        import httpx
        for _ in range(3):
            try:
                # trust_env=False：不走系统/Clash 代理，直连本地 suno-api（否则 localhost 被代理→502）
                with httpx.Client(timeout=40, trust_env=False) as c:
                    r = c.get(f"{self.base}/api/get")
                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list):
                        return data
            except Exception:
                pass
            time.sleep(2)
        return []

    def _existing_ids(self) -> set:
        try:
            return {c.get("id") for c in self._get_clips()}
        except Exception:
            return set()

    def _trigger(self, desc: str) -> List[str]:
        import httpx
        try:
            with httpx.Client(timeout=200, trust_env=False) as c:
                r = c.post(f"{self.base}/api/ui_generate", json={"description": desc})
                r.raise_for_status()
                return [i for i in (r.json().get("ids") or []) if i]
        except Exception as e:
            # ui_generate 慢/超时是常态，生成多半仍在进行，靠 /api/get 取回
            print(f"[music] ui_generate 触发返回异常（继续轮询取回）：{e!r}")
            return []

    def _wait_clip(self, before: set, ids: List[str]) -> dict:
        deadline = time.monotonic() + self.poll_timeout
        while time.monotonic() < deadline:
            try:
                clips = self._get_clips()
            except Exception:
                clips = []
            # 候选：ui_generate 明确返回的 ids，或 /api/get 里新冒出来的 id
            for c in clips:
                cid = c.get("id")
                is_new = (cid in ids) or (cid not in before)
                if is_new and c.get("audio_url") and c.get("status") in ("streaming", "complete"):
                    return c
            time.sleep(self.poll_interval)
        raise TimeoutError("Suno 出曲超时（ui_generate 轮询）")

    def _download(self, clip: dict) -> Path:
        import httpx
        path = config.GENERATED_DIR / f"{clip.get('id', 'track')}.mp3"
        # 显式走代理下载 Suno CDN；trust_env=False 避免再叠加系统代理
        with httpx.Client(timeout=180, proxy=self.proxy, trust_env=False) as c:
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
        print(f"[music] 使用 Suno 真实生成：{config.SUNO_API_BASE}（proxy={config.SUNO_PROXY}）")
        return SunoMusic(config.SUNO_API_BASE, config.SUNO_PROXY)
    return PlaceholderMusic()


# 单例（注入点）：SUNO_ENABLED 时用 Suno，否则占位
music_service: MusicService = _make_service()
# 兜底实例（Suno 失败时回退）
fallback_music: MusicService = PlaceholderMusic()
