"""ASR（语音转文字）服务 —— 可插拔接口 + 占位实现。

未来真实形态：把音频送多模态大模型 / 专用 ASR，返回识别文本。
本轮占位：根据音频文件名做稳定抽样，返回一段固定/抽样文本。
"""
from abc import ABC, abstractmethod
from pathlib import Path

# 占位文本样本池（贴近答题语境，便于前端联调）
_SAMPLES = [
    "我最想待在黄昏的海边，等人都散了，才觉得能喘口气。",
    "最近有件事一直放在心里，没怎么跟人说，说不上来是难过还是别的。",
    "有句话我一直想对一个人说，可每次到嘴边又咽回去了。",
    "其实我挺好的，就是有时候安静下来会想很多。",
    "清晨的风很轻，那一刻我觉得什么都可以重新开始。",
]


class ASRService(ABC):
    """ASR 抽象接口。未来替换真实实现时保持此签名即可无痛切换。"""

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """把音频文件转写成文本。"""
        raise NotImplementedError


class PlaceholderASR(ASRService):
    """占位实现：按文件名稳定抽样，返回样本文本（不真正解码音频）。"""

    def transcribe(self, audio_path: str) -> str:
        # TODO(real): 调多模态大模型 / ASR，例如：
        #   resp = client.audio.transcriptions(file=open(audio_path,'rb'), model=...)
        #   return resp.text
        key = Path(audio_path).stem
        idx = (sum(ord(c) for c in key) if key else 0) % len(_SAMPLES)
        return _SAMPLES[idx]


# 单例（注入点：未来在这里换成真实实现）
asr_service: ASRService = PlaceholderASR()
