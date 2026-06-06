"""情绪分析服务 —— 可插拔接口 + 占位实现 + 阶跃星辰真实现。

- PlaceholderAnalysis：无 key 时用，文本 hash 稳定挑人格。
- StepFunAnalysis：调阶跃星辰（OpenAI 兼容）一次结构化调用，输出
  9 桶情绪概率分布 + 强度 + 关键词 + 现有结果页要的（人格/四维/报告）。
分析归大模型、生成归 Suno；这里只做分析。
"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List

from . import personas, buckets


@dataclass
class AnalysisResult:
    """分析输出（service 内部结构，由上层组装成 API 的 Result）。"""
    persona_name: str
    persona_en: str
    report: str
    dim_values: List[int]          # 4 个 0-100，顺序见 personas.DIM_LABELS
    mood: str                      # 兜底曲挑选用
    raw: Dict = field(default_factory=dict)   # 9 桶分布/主桶/关键词等（阶段 2 Suno 用）


class AnalysisService(ABC):
    @abstractmethod
    def analyze(self, answers: List[Dict]) -> AnalysisResult:
        """answers: [{"q": 0, "text": "..."}, ...] -> AnalysisResult"""
        raise NotImplementedError


class PlaceholderAnalysis(AnalysisService):
    """占位实现：根据答案文本 hash 稳定挑一个人格。"""

    def analyze(self, answers: List[Dict]) -> AnalysisResult:
        text = "".join((a.get("text") or "") for a in (answers or []))
        seed = (len(text) * 31 + sum(ord(c) for c in text)) % len(personas.PERSONAS)
        p = personas.PERSONAS[seed]
        return AnalysisResult(
            persona_name=p["name"], persona_en=p["en"], report=p["report"],
            dim_values=list(p["dims"]), mood=p["mood"],
            raw={"_placeholder": True},
        )


# 9 桶风格锚点（把现有 suno_tags 当成给 LLM 的「风格参考」，由 LLM 按情绪个性化）
_STYLE_ANCHORS = "\n".join(f"  - {b['key']}：{b['suno_tags']}" for b in buckets.BUCKETS)

_SYSTEM_PROMPT = (
    "你是「声序实验室·情绪民乐」的情绪分析引擎。用户回答了三个关于此刻心境的问题，"
    "请基于回答做情绪语义分析，并严格只返回一个 JSON 对象（不要任何多余文字、不要代码块）。\n\n"
    "九桶情绪本体：悲伤、思念、宁静、期待、激昂、狂喜、焦虑、迷茫、中性。\n"
    "复合情绪用概率分布表达（例如『思念中带一点宁静』→ 思念 0.6 / 宁静 0.3 / 其余少量），所有桶之和=1。\n\n"
    "同时给出结果页要用的四维坐标，每维 0-100 的整数，0=完全靠左标签，100=完全靠右标签：\n"
    "  独处_共处（0独处↔100共处）、涌动_平静（0涌动↔100平静）、"
    "直说_含蓄（0直说↔100含蓄）、回望过去_望向远方（0回望过去↔100望向远方）。\n\n"
    "返回 JSON 结构：\n"
    "{\n"
    '  "buckets": {"悲伤":0,"思念":0,"宁静":0,"期待":0,"激昂":0,"狂喜":0,"焦虑":0,"迷茫":0,"中性":0},\n'
    '  "intensity": 0.0,\n'
    '  "tempo": "slow|medium|fast",\n'
    '  "keywords": ["", ""],\n'
    '  "persona": {"name": "中文人格名(2-6字, 诗意, 如 黄昏独行者)", "en": "English Name"},\n'
    '  "report": "一段第二人称的『关于你』解读, 60-120字, 温柔克制",\n'
    '  "dims": {"独处_共处":0,"涌动_平静":0,"直说_含蓄":0,"回望过去_望向远方":0},\n'
    '  "music_prompt": "英文；给音乐生成模型的提示词，写法见下方要求"\n'
    "}\n\n"
    "【music_prompt 怎么写】这是最关键的一项，要真正『根据这个人的情绪』来写，不要只堆通用风格词：\n"
    "  1. 必须是中国民乐、纯器乐 instrumental、no vocals（绝不能有人声/歌词）。\n"
    "  2. 必须有 1-2 个『情景/氛围』短语，从 ta 回答里的处境/画面/动作化用而来（如黄昏海边、欲言又止、人散后独处），\n"
    "     转成音乐能表达的画面感与情绪张力——这是重点，别只写通用风格词；但不要原样复述句子、不要出现任何中文。\n"
    "  3. 结合你判断的主/副情绪，参考下表对应桶的乐器/调式/BPM/技法；按 intensity 调力度（弱=克制亲密、留白，强=饱满浓烈）；按 tempo 调快慢。\n"
    "  4. 40-70 个英文词，逗号分隔的描述短语（风格 + 乐器 + 调式/速度 + 情景意象 + 情绪 + 演奏技法 + no vocals）。\n"
    "示例（仅示范『情景+技法』的写法与浓度，绝不要照抄内容）：\n"
    "  Chinese folk instrumental, solo erhu over sparse guqin, D-yu pentatonic, slow ~58 BPM, "
    "the ache of words held back at dusk by an emptying shore, weeping portamento and long breathing silences, "
    "intimate and restrained, no vocals\n"
    "九桶风格锚点（按你判断的主情绪选用，并据 ta 的具体情绪个性化，不要照抄）：\n"
    + _STYLE_ANCHORS
)

_DIM_ORDER = ["独处_共处", "涌动_平静", "直说_含蓄", "回望过去_望向远方"]


class StepFunAnalysis(AnalysisService):
    """阶跃星辰（OpenAI 兼容 /chat/completions）真实分析。"""

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model

    def analyze(self, answers: List[Dict]) -> AnalysisResult:
        try:
            data = self._call(answers)
            return self._to_result(data)
        except Exception as e:  # 任何失败都回退占位，保证流程不崩
            print(f"[analysis] StepFun 调用失败，回退占位：{e!r}")
            return PlaceholderAnalysis().analyze(answers)

    def _call(self, answers: List[Dict]) -> Dict:
        import httpx
        qa = "\n".join(
            f"问题{(a.get('q', i) or 0) + 1}的回答：{(a.get('text') or '').strip()}"
            for i, a in enumerate(answers or [])
        ) or "（用户没有作答）"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": qa},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }
        with httpx.Client(timeout=40) as c:
            r = c.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        return json.loads(_strip_fence(content))

    def _to_result(self, data: Dict) -> AnalysisResult:
        dist = {k: float(v) for k, v in (data.get("buckets") or {}).items()}
        main, second = buckets.top2(dist)
        dims = data.get("dims") or {}
        dim_values = [int(round(float(dims.get(k, 50) or 50))) for k in _DIM_ORDER]
        persona = data.get("persona") or {}
        name = (persona.get("name") or "").strip() or main["key"] + "者"
        en = (persona.get("en") or "").strip() or main["en"]
        report = (data.get("report") or "").strip() or "你的情绪此刻落在一片说不清的色彩里。"
        return AnalysisResult(
            persona_name=name, persona_en=en, report=report,
            dim_values=dim_values, mood=main["mood"],
            raw={
                "buckets": dist,
                "dominant": main["key"],
                "second": second["key"],
                "intensity": data.get("intensity"),
                "tempo": data.get("tempo"),
                "keywords": data.get("keywords") or [],
                "bucket_params": {k: main.get(k) for k in ("mode", "bpm", "instrument", "technique", "suno_tags")},
                # 给 Suno 的成品描述：优先用 LLM 按本人情绪写的 music_prompt；缺失退回桶模板拼装
                "suno_prompt": _pick_music_prompt(data, dist),
            },
        )


def _pick_music_prompt(data: Dict, dist: Dict[str, float]) -> str:
    """优先用 LLM 按本人情绪写的 music_prompt；为空/异常退回桶模板。
    并兜底保证 instrumental / no vocals（防 Suno 自作主张加人声）。"""
    p = (data.get("music_prompt") or "").strip()
    if not p or len(p) < 12:
        return buckets.build_prompt(dist, data.get("intensity"), data.get("tempo"))
    low = p.lower()
    if "no vocal" not in low and "instrumental" not in low:
        p += ", instrumental, no vocals"
    return p


def _strip_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s.rsplit("```", 1)[0]
    return s.strip()


def _make_service() -> AnalysisService:
    from .. import config
    if config.ANALYSIS_API_KEY:
        print(f"[analysis] 使用阶跃星辰真实分析：model={config.ANALYSIS_MODEL}")
        return StepFunAnalysis(config.ANALYSIS_API_KEY, config.ANALYSIS_API_BASE, config.ANALYSIS_MODEL)
    return PlaceholderAnalysis()


# 单例（注入点）：有 key 用阶跃，无 key 用占位
analysis_service: AnalysisService = _make_service()
