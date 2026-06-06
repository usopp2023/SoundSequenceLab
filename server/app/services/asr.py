"""ASR（语音转文字）服务 —— 可插拔接口 + 占位实现 + 阶跃星辰真实现。

- PlaceholderASR：无 key / 不支持的格式时用，按文件名稳定抽样返回样本文本。
- StepFunASR：调阶跃 `POST /v1/audio/transcriptions`（OpenAI 兼容，multipart 上传，
  模型 stepaudio-2.5-asr，返回 {text}）。用同一个阶跃 key。
"""
from abc import ABC, abstractmethod
from pathlib import Path

# 占位文本样本池（无 key / 转写失败时兜底，贴近答题语境）
_SAMPLES = [
    "我最想待在黄昏的海边，等人都散了，才觉得能喘口气。",
    "最近有件事一直放在心里，没怎么跟人说，说不上来是难过还是别的。",
    "有句话我一直想对一个人说，可每次到嘴边又咽回去了。",
    "其实我挺好的，就是有时候安静下来会想很多。",
    "清晨的风很轻，那一刻我觉得什么都可以重新开始。",
]

# 阶跃 ASR 支持的格式 → multipart 文件 content-type（小程序录的是 mp3）
_FMT_CT = {"mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg", "pcm": "audio/pcm"}


class ASRService(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError


class PlaceholderASR(ASRService):
    """占位：按文件名稳定抽样返回样本文本（不真正解码音频）。"""

    def transcribe(self, audio_path: str) -> str:
        key = Path(audio_path).stem
        idx = (sum(ord(c) for c in key) if key else 0) % len(_SAMPLES)
        return _SAMPLES[idx]


class StepFunASR(ASRService):
    """阶跃星辰一次性 SSE 转写。"""

    def __init__(self, api_key: str, api_base: str, model: str = "stepaudio-2.5-asr"):
        self.key = api_key
        self.base = api_base.rstrip("/")
        self.model = model

    def transcribe(self, audio_path: str) -> str:
        p = Path(audio_path)
        ct = _FMT_CT.get(p.suffix.lower().lstrip(".")) or "audio/mpeg"  # 小程序默认 mp3
        try:
            return self._call(p, ct) or PlaceholderASR().transcribe(audio_path)
        except Exception as e:
            print(f"[asr] 阶跃 ASR 失败，回退占位：{e!r}")
            return PlaceholderASR().transcribe(audio_path)

    def _call(self, p: Path, content_type: str) -> str:
        import httpx
        with httpx.Client(timeout=60) as c:
            with open(p, "rb") as f:
                r = c.post(
                    f"{self.base}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.key}"},
                    files={"file": (p.name, f, content_type)},
                    data={"model": self.model},
                )
        # 没识别到语音（非语音/静音）→ 返回空，上层回退占位
        if r.status_code == 400 and "no speech" in r.text.lower():
            return ""
        r.raise_for_status()
        return (r.json().get("text") or "").strip()


def _make_service() -> ASRService:
    from .. import config
    if config.ANALYSIS_API_KEY:
        print("[asr] 使用阶跃星辰真实语音转写：stepaudio-2.5-asr")
        return StepFunASR(config.ANALYSIS_API_KEY, config.ANALYSIS_API_BASE)
    return PlaceholderASR()


# 单例（注入点）：有 key 用阶跃，无 key 用占位
asr_service: ASRService = _make_service()
