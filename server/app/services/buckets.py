"""9 桶情绪本体（proposal_v15 §03 第一层 · 情绪表征）。

九桶：悲伤 · 思念 · 宁静 · 期待 · 激昂 · 狂喜 · 焦虑 · 迷茫 · 中性。
每桶映射固定的「五声调式 / BPM 区间 / 主乐器 / 代表技法 / Suno 风格关键词」。

⚠️ 待校准：proposal 只给了 2 个示例映射（悲伤→D羽/60/二胡，狂喜→G徵/120/唢呐），
其余为合理初版，需请演奏者（20 年民乐经验）逐桶过一遍数值与技法。

bucket["suno_tags"]：阶段 2 给 Suno 的英文风格 tag 片段（民乐 instrumental）。
bucket["mood"]：映射到现有兜底曲（dusk/calm/bright/deep/rain），阶段 1 占位音乐用。
"""
from typing import Dict, List

# 顺序即对外稳定顺序；key 用于 LLM 概率分布的键
BUCKETS: List[Dict] = [
    {
        "key": "悲伤", "en": "Sorrow", "mode": "D 羽", "bpm": [56, 64],
        "instrument": "二胡", "technique": "揉弦·滑音", "mood": "deep",
        "suno_tags": "Chinese folk instrumental, solo erhu, pentatonic D-yu mode, ~60 BPM, mournful and weeping, deep vibrato and portamento, no vocals",
    },
    {
        "key": "思念", "en": "Longing", "mode": "A 羽", "bpm": [66, 76],
        "instrument": "古筝+箫", "technique": "吟揉·颤音", "mood": "calm",
        "suno_tags": "Chinese folk instrumental, guzheng and xiao flute, pentatonic A-yu mode, ~70 BPM, nostalgic and tender longing, vibrato, no vocals",
    },
    {
        "key": "宁静", "en": "Serenity", "mode": "C 宫", "bpm": [60, 72],
        "instrument": "古琴/箫", "technique": "泛音·绰注", "mood": "calm",
        "suno_tags": "Chinese folk instrumental, guqin and xiao, pentatonic C-gong mode, ~66 BPM, serene meditative and airy, harmonics, no vocals",
    },
    {
        "key": "期待", "en": "Anticipation", "mode": "G 徵", "bpm": [84, 96],
        "instrument": "笛子", "technique": "历音·颤音", "mood": "bright",
        "suno_tags": "Chinese folk instrumental, dizi bamboo flute, pentatonic G-zhi mode, ~90 BPM, hopeful and bright with a gentle build, no vocals",
    },
    {
        "key": "激昂", "en": "Fervor", "mode": "D 商", "bpm": [100, 116],
        "instrument": "琵琶+二胡", "technique": "滚奏·快弓", "mood": "bright",
        "suno_tags": "Chinese folk instrumental, pipa and erhu, pentatonic D-shang mode, ~108 BPM, stirring driving and intense, tremolo and fast bowing, no vocals",
    },
    {
        "key": "狂喜", "en": "Euphoria", "mode": "G 徵", "bpm": [116, 132],
        "instrument": "唢呐", "technique": "花舌·滑音", "mood": "bright",
        "suno_tags": "Chinese folk instrumental, suona horn with percussion, pentatonic G-zhi mode, ~124 BPM, euphoric festive and exuberant, flutter-tongue, no vocals",
    },
    {
        "key": "焦虑", "en": "Anxiety", "mode": "B 商", "bpm": [90, 108],
        "instrument": "琵琶", "technique": "绞弦·扫拂", "mood": "rain",
        "suno_tags": "Chinese folk instrumental, pipa, pentatonic B-shang mode with slight dissonance, ~100 BPM, tense restless and agitated, strumming, no vocals",
    },
    {
        "key": "迷茫", "en": "Bewilderment", "mode": "E 角", "bpm": [68, 80],
        "instrument": "箫/古筝", "technique": "揉弦·泛音", "mood": "dusk",
        "suno_tags": "Chinese folk instrumental, xiao flute and guzheng, pentatonic E-jue mode, ~74 BPM, hazy drifting and uncertain, no vocals",
    },
    {
        "key": "中性", "en": "Neutral", "mode": "C 宫", "bpm": [72, 84],
        "instrument": "古筝", "technique": "平稳", "mood": "calm",
        "suno_tags": "Chinese folk instrumental, solo guzheng, pentatonic C-gong mode, ~78 BPM, calm balanced and simple, no vocals",
    },
]

BUCKET_KEYS = [b["key"] for b in BUCKETS]
BUCKET_BY_KEY = {b["key"]: b for b in BUCKETS}


def dominant(dist: Dict[str, float]) -> Dict:
    """从 9 桶概率分布里取主桶；缺失/异常回退『中性』。"""
    if not dist:
        return BUCKET_BY_KEY["中性"]
    key = max(BUCKET_KEYS, key=lambda k: float(dist.get(k, 0) or 0))
    return BUCKET_BY_KEY.get(key, BUCKET_BY_KEY["中性"])


def top2(dist: Dict[str, float]):
    """返回 (主桶, 副桶)；副桶用于影响副乐器/变奏（阶段 2）。"""
    ranked = sorted(BUCKETS, key=lambda b: float((dist or {}).get(b["key"], 0) or 0), reverse=True)
    return ranked[0], (ranked[1] if len(ranked) > 1 else ranked[0])
