"""种子数据 + 占位音乐生成。

- 用标准库 wave + math 生成几个不同基频的短 WAV（约 15 秒、单声道、8000Hz），
  代表不同 mood，写到 static/fallback_music/*.wav（已存在则跳过，不依赖 ffmpeg）。
- 把原型 PLAZA 的 10 条广场作品写进 DB（空库时才写）。
"""
import math
import struct
import wave

from .. import config
from . import db

# ---- 兜底曲：mood -> 基频(Hz)。不同基频代表不同情绪色彩 ----
_MUSIC_SPECS = {
    "dusk": 220.0,    # A3，温暖偏暗
    "calm": 196.0,    # G3，平静
    "bright": 330.0,  # E4，明亮
    "deep": 130.81,   # C3，低沉
    "rain": 261.63,   # C4，清亮
}

_SAMPLE_RATE = 8000
_DURATION_SEC = 15


def _gen_wav(path, freq: float) -> None:
    """生成单声道 8000Hz 约 15 秒的简单正弦波（带轻微泛音+包络）WAV。"""
    n = _SAMPLE_RATE * _DURATION_SEC
    amp = 18000.0
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)          # 16-bit
        w.setframerate(_SAMPLE_RATE)
        frames = bytearray()
        for i in range(n):
            t = i / _SAMPLE_RATE
            # 基频 + 八度泛音，让音色不那么单薄
            s = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)
            s /= 1.3
            # 简单淡入淡出包络，避免爆音
            env = 1.0
            fade = _SAMPLE_RATE  # 1 秒淡入淡出
            if i < fade:
                env = i / fade
            elif i > n - fade:
                env = (n - i) / fade
            val = int(max(-1.0, min(1.0, s)) * amp * env)
            frames += struct.pack("<h", val)
        w.writeframes(bytes(frames))


def ensure_fallback_music() -> None:
    """生成所有兜底曲（已存在则跳过）。"""
    for mood, freq in _MUSIC_SPECS.items():
        path = config.FALLBACK_MUSIC_DIR / f"{mood}.wav"
        if not path.exists():
            _gen_wav(path, freq)


# ---- 广场种子（来自原型 PLAZA 那 10 条）----
_PLAZA_SEED = [
    ("深海回声者", "习惯把情绪藏在平静的表面之下，望向远方多过回望过去。", 42),
    ("清晨骤雨型", "来得快去得也快，情绪像一阵突然的雨，落完天就晴了。", 31),
    ("黄昏独行者", "在人群散去后才开口，把很多话留在了心里。", 58),
    ("暗涌者", "表面安静，底下一直有自己的潮汐在走。", 19),
    ("晴窗型", "情绪透亮，愿意把心里的事摊开在光里说。", 27),
    ("夜航者", "喜欢在深夜独处时，才和自己的情绪对话。", 36),
    ("远雷型", "情绪在很远的地方滚动，等靠近时往往已经过去。", 23),
    ("退潮者", "习惯在喧闹退去之后，才慢慢露出心里的样子。", 44),
    ("薄雾型", "看不太真切，却始终笼在一层温柔的情绪里。", 15),
    ("潮间带", "在靠近与退开之间反复，像潮水来回的那条线。", 38),
]


def ensure_plaza_seed() -> None:
    if db.count_plaza() == 0:
        for name, desc, likes in _PLAZA_SEED:
            db.add_plaza(name=name, desc=desc, likes=likes)


def run_seed() -> None:
    """应用启动时调用：建表 + 生成兜底曲 + 写广场种子。"""
    db.init_db()
    ensure_fallback_music()
    ensure_plaza_seed()
