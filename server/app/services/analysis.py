"""情绪分析服务 —— 可插拔接口 + 占位实现。

未来真实形态：把答案文本（+音频特征）送多模态大模型，返回情绪/人格/四维/报告。
本轮占位：用答案文本的 hash 稳定地挑一个预置人格，返回其预置数据。
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List

from . import personas


@dataclass
class AnalysisResult:
    """分析输出（service 内部结构，由上层组装成 API 的 Result）。"""
    persona_name: str
    persona_en: str
    report: str
    dim_values: List[int]          # 4 个 0-100
    mood: str
    raw: Dict = field(default_factory=dict)   # 预留：未来放大模型原始输出


class AnalysisService(ABC):
    """情绪分析抽象接口。"""

    @abstractmethod
    def analyze(self, answers: List[Dict]) -> AnalysisResult:
        """answers: [{"q": 0, "text": "..."}, ...] -> AnalysisResult"""
        raise NotImplementedError


class PlaceholderAnalysis(AnalysisService):
    """占位实现：根据答案文本 hash 稳定挑一个人格，返回预置数据。"""

    def analyze(self, answers: List[Dict]) -> AnalysisResult:
        # TODO(real): 组 prompt → 调多模态大模型 → 解析出 persona/dims/report。
        #   分析归大模型，生成归 Suno；这里只做"分析"。
        text = "".join((a.get("text") or "") for a in (answers or []))
        # 用文本长度 + 字符和做稳定 hash，落到某个人格
        seed = (len(text) * 31 + sum(ord(c) for c in text)) % len(personas.PERSONAS)
        p = personas.PERSONAS[seed]
        return AnalysisResult(
            persona_name=p["name"],
            persona_en=p["en"],
            report=p["report"],
            dim_values=list(p["dims"]),
            mood=p["mood"],
            raw={"_placeholder": True, "answer_chars": len(text)},
        )


# 单例（注入点）
analysis_service: AnalysisService = PlaceholderAnalysis()
