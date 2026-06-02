"""音乐生成服务 —— 可插拔接口 + 占位实现。

未来真实形态（务必保持这个骨架，将来无痛替换为真实实现）：
  1. _build_segment_prompts(): 根据情绪分析结果 build 出多段 prompt
     （如 intro / verse / outro，每段对应一段情绪走向）。
  2. _call_suno(prompt): 对每段 prompt 调 Suno 生成一个音乐片段，返回片段文件路径。
  3. _synthesize(segments): 用 ffmpeg 把多个片段合成一首完整曲子，返回最终文件路径。

本轮占位：generate() 内部按真实顺序走骨架，但每一步都直接返回兜底曲，
不真正调 Suno、不依赖 ffmpeg。兜底曲由 store.seed 用标准库 wave 预先生成。
"""
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .. import config
from .analysis import AnalysisResult

# mood -> 兜底曲文件名
_MOOD_TO_FILE = {
    "dusk": "dusk.wav",
    "calm": "calm.wav",
    "bright": "bright.wav",
    "deep": "deep.wav",
    "rain": "rain.wav",
}
_DEFAULT_FILE = "dusk.wav"


@dataclass
class MusicResult:
    url: str          # 对外可访问的静态 URL，如 /static/fallback_music/dusk.wav
    duration: int     # 秒


@dataclass
class _SegmentPrompt:
    """一段 Suno prompt（未来真实形态用）。"""
    section: str      # intro / verse / outro ...
    prompt: str


class MusicService(ABC):
    """音乐生成抽象接口。"""

    @abstractmethod
    def generate(self, analysis: AnalysisResult) -> MusicResult:
        raise NotImplementedError


class PlaceholderMusic(MusicService):
    """占位实现：按未来真实骨架走流程，但每步兜底，最终返回预置 wav。"""

    def generate(self, analysis: AnalysisResult) -> MusicResult:
        # —— 真实形态的三步骨架（占位下全部兜底）——
        prompts = self._build_segment_prompts(analysis)
        segments = [self._call_suno(p) for p in prompts]
        final_path = self._synthesize(segments, analysis)
        rel = f"fallback_music/{final_path.name}"
        return MusicResult(url=config.static_url(rel), duration=self._duration(final_path))

    # ---- 步骤 1：build 多段 prompt ----
    def _build_segment_prompts(self, analysis: AnalysisResult) -> List[_SegmentPrompt]:
        # TODO(real): 根据 analysis（人格/四维/情绪关键词）拼出多段、有情绪走向的 prompt。
        base = f"{analysis.persona_en}, mood={analysis.mood}"
        return [
            _SegmentPrompt("intro", f"{base}, soft ambient opening"),
            _SegmentPrompt("verse", f"{base}, emotional melodic core"),
            _SegmentPrompt("outro", f"{base}, gentle fade out"),
        ]

    # ---- 步骤 2：调 Suno 生成单个片段 ----
    def _call_suno(self, prompt: _SegmentPrompt) -> Path:
        # TODO(real): 调 Suno 渠道 API 生成该段音频，下载到本地，返回文件路径。
        #   注意：Suno 无官方公开 API，渠道需先确认；超时/失败要兜底。
        # 占位：不真正调用，直接返回 None 占位（合成步骤会忽略）。
        return None  # type: ignore[return-value]

    # ---- 步骤 3：合成完整曲子 ----
    def _synthesize(self, segments: List[Path], analysis: AnalysisResult) -> Path:
        # TODO(real): 用 ffmpeg 把 segments 按顺序拼接/淡入淡出，合成一首完整曲子。
        # 占位：忽略 segments，按 mood 返回预置兜底曲文件。
        filename = _MOOD_TO_FILE.get(analysis.mood, _DEFAULT_FILE)
        path = config.FALLBACK_MUSIC_DIR / filename
        if not path.exists():
            path = config.FALLBACK_MUSIC_DIR / _DEFAULT_FILE
        return path

    # ---- 工具：读 wav 时长 ----
    @staticmethod
    def _duration(path: Path) -> int:
        try:
            with wave.open(str(path), "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate() or 1
                return max(1, round(frames / rate))
        except Exception:
            return 15


# 单例（注入点）
music_service: MusicService = PlaceholderMusic()
