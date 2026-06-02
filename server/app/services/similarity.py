"""相似度计算服务。

把两个人格的四维向量做归一化欧氏距离 → 映射成 0-100 的相似度百分比，
并用模板拼一段解读文案（风格参考原型 sim 页）。
"""
import math
from typing import Dict, List

from . import personas

# 四维满量程对角线长度（每维 0-100，4 维）
_MAX_DIST = math.sqrt(4 * (100 ** 2))


def _score(a: List[int], b: List[int]) -> int:
    """两个四维向量 -> 0-100 相似度百分比（距离越近分越高）。"""
    dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    sim = (1 - dist / _MAX_DIST) * 100
    return int(round(max(0, min(100, sim))))


def _reading(you: Dict, other: Dict, you_v: List[int], other_v: List[int], score: int) -> str:
    """拼一段解读。基于四维差异挑出最像 / 最不像的一维做文案。"""
    labels = personas.DIM_LABELS
    diffs = [abs(x - y) for x, y in zip(you_v, other_v)]
    closest = diffs.index(min(diffs))
    farthest = diffs.index(max(diffs))

    def side(v: int, dim_idx: int) -> str:
        left, right = labels[dim_idx]
        return left if v < 50 else right

    # 最像的一维：双方同侧时强调"都"
    cl, cr = labels[closest]
    same_side = (you_v[closest] < 50) == (other_v[closest] < 50)
    if same_side:
        common = f"你们都习惯把情绪藏在{side(you_v[closest], closest)}的那一面"
    else:
        common = f"在「{cl}—{cr}」这件事上，你们的距离其实很近"

    # 最不像的一维：强调差异，给"也许正好能聊聊"的引导
    you_side = side(you_v[farthest], farthest)
    other_side = side(other_v[farthest], farthest)
    if you_side != other_side:
        diff = f"不同的是，你更{you_side}，而 Ta 更{other_side}——也许正好能聊聊，对方看到的是什么。"
    else:
        diff = "你们看世界的方式也很接近，像两段会自然叠合的旋律。"

    return f"{common}。{diff}"


def compare(you_name: str, other_name: str) -> Dict:
    """返回契约结构：{score, you:{name}, other:{name}, reading}。"""
    you = personas.get_persona(you_name)
    other = personas.get_persona(other_name)
    you_v = you["dims"]
    other_v = other["dims"]
    score = _score(you_v, other_v)
    return {
        "score": score,
        "you": {"name": you["name"]},
        "other": {"name": other["name"]},
        "reading": _reading(you, other, you_v, other_v, score),
    }
