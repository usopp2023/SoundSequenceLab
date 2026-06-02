"""人格预置数据。

每个人格包含：
  - name   中文名
  - en     英文名（自拟合理英文）
  - report 一段中文报告
  - dims   四维 value（4 个 0-100 数；含义见下）
  - mood   用于挑选兜底曲（决定 fallback wav 文件）

四维顺序固定，与前端契约一致：
  0: 独处(left) ←→ 共处(right)
  1: 涌动(left) ←→ 平静(right)
  2: 直说(left) ←→ 含蓄(right)
  3: 回望过去(left) ←→ 望向远方(right)

value = 圆点在 0-100 的「靠右程度」(0=完全靠左标签, 100=完全靠右标签)。
"""
from typing import Dict, List

# 四维标签（顺序不可变，前端按此渲染）
DIM_LABELS = [
    ("独处", "共处"),
    ("涌动", "平静"),
    ("直说", "含蓄"),
    ("回望过去", "望向远方"),
]

# mood -> 兜底曲文件名（不含扩展名），见 services/music.py 生成逻辑
MOODS = ["dusk", "calm", "bright", "deep", "rain"]

# 人格库：包含原型 PLAZA 的 10 个名字 + 「黄昏独行者」
# （注意 PLAZA 中已含「黄昏独行者」，这里它作为主角人格，dims 与原型结果页一致）
PERSONAS: List[Dict] = [
    {
        "name": "黄昏独行者",
        "en": "The Dusk Wanderer",
        "report": "你习惯在人群散去后才开口。情绪来得不急不缓，像黄昏的海——表面平静，底下有自己的潮汐。你把很多话留在了心里，但它们一直都在。",
        "dims": [22, 74, 80, 30],   # 与原型结果页四维一致
        "mood": "dusk",
    },
    {
        "name": "深海回声者",
        "en": "The Deep Echo",
        "report": "你习惯把情绪藏在平静的表面之下，望向远方多过回望过去。心里的话像深海里的回声，要很久才浮上来，但每一句都很真。",
        "dims": [28, 78, 76, 70],
        "mood": "deep",
    },
    {
        "name": "清晨骤雨型",
        "en": "The Morning Shower",
        "report": "你的情绪来得快去得也快，像一阵突然的雨，落完天就晴了。你不太憋着，喜欢痛快地把感受说出来，然后翻篇。",
        "dims": [60, 18, 22, 64],
        "mood": "rain",
    },
    {
        "name": "暗涌者",
        "en": "The Undercurrent",
        "report": "你表面安静，底下却一直有自己的潮汐在走。别人看不见的地方，你的情绪从未停歇，只是你选择不轻易显露。",
        "dims": [30, 32, 70, 36],
        "mood": "deep",
    },
    {
        "name": "晴窗型",
        "en": "The Bright Window",
        "report": "你的情绪透亮，愿意把心里的事摊开在光里说。和你相处的人会觉得轻松——因为你不绕弯子，也不让人猜。",
        "dims": [72, 66, 18, 60],
        "mood": "bright",
    },
    {
        "name": "夜航者",
        "en": "The Night Voyager",
        "report": "你喜欢在深夜独处时，才和自己的情绪对话。白天的你是给别人的，夜里的你才是给自己的。",
        "dims": [20, 60, 64, 58],
        "mood": "calm",
    },
    {
        "name": "远雷型",
        "en": "The Distant Thunder",
        "report": "你的情绪在很远的地方滚动，等靠近时往往已经过去。你不急于表达，更习惯让感受先沉淀一阵。",
        "dims": [44, 48, 68, 72],
        "mood": "deep",
    },
    {
        "name": "退潮者",
        "en": "The Ebbing Tide",
        "report": "你习惯在喧闹退去之后，才慢慢露出心里的样子。热闹时你收着，安静下来你才开始真正流动。",
        "dims": [26, 70, 72, 34],
        "mood": "calm",
    },
    {
        "name": "薄雾型",
        "en": "The Soft Mist",
        "report": "你看不太真切，却始终笼在一层温柔的情绪里。你不锋利，也不冷，像清晨的薄雾，包住了所有不愿被看清的部分。",
        "dims": [40, 76, 74, 50],
        "mood": "calm",
    },
    {
        "name": "潮间带",
        "en": "The Intertidal Zone",
        "report": "你在靠近与退开之间反复，像潮水来回的那条线。你既渴望共处，又需要独处，这份摇摆本身就是你的节奏。",
        "dims": [50, 52, 56, 48],
        "mood": "bright",
    },
    {
        "name": "晴窗薄雾间",
        "en": "The Clearing Haze",
        "report": "你在透亮与朦胧之间游走，有时愿意把话说尽，有时又把自己轻轻笼起来。你不强求被理解，但你一直在表达。",
        "dims": [54, 58, 46, 56],
        "mood": "bright",
    },
]

PERSONA_BY_NAME: Dict[str, Dict] = {p["name"]: p for p in PERSONAS}


def get_persona(name: str) -> Dict:
    """按名取人格，找不到则回退到主角人格。"""
    return PERSONA_BY_NAME.get(name, PERSONA_BY_NAME["黄昏独行者"])


def build_dims(values: List[int]) -> List[Dict]:
    """把 4 个 value 组装成契约里的 dims 数组。"""
    out = []
    for (left, right), v in zip(DIM_LABELS, values):
        v = max(0, min(100, int(v)))
        out.append({
            "left": left,
            "right": right,
            "value": v,
            "activeSide": "left" if v < 50 else "right",
        })
    return out
