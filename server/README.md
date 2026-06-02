# 声序实验室 · 情绪音乐 — 后端

为「声序实验室 · 情绪音乐」微信小程序提供的 Python FastAPI 后端。

产品流程：用户答 3 题（语音/打字）→ 后端分析情绪 → 生成音乐 → 返回人格 + 四维曲线 + 音乐。

本轮分析（analysis）与音乐生成（music）均为**占位实现**，但接口已按真实形态设计，未来可无痛替换。

## 启动

```bash
cd E:\声序实验室\server
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- 交互式 API 文档（Swagger）：http://localhost:8000/docs
- 启动时自动建表、生成兜底曲 WAV、写入广场种子（已存在则跳过）。
- 复制 `.env.example` 为 `.env` 填真实 key（本轮无需）。

## 测试

```bash
cd E:\声序实验室\server
pytest -q
```

冒烟测试覆盖每个路由返回 200 + 关键字段，并跑一条完整链路：
generate → 轮询 jobs 到 done → 校验 Result → results/{id} 取回 → archive → plaza → like → similarity → redeem。

## 目录结构

```
server/
  requirements.txt  .env.example  README.md
  app/
    main.py          # FastAPI 入口、CORS、静态挂载、lifespan seed
    config.py        # 环境变量/路径配置（密钥只从 .env 读）
    api/             # routes_auth / routes_upload / routes_generate / routes_me / routes_plaza
    services/        # asr / analysis / music / similarity / personas（可插拔）
    models/schemas.py# pydantic 请求/响应模型（字段对齐前端契约）
    store/           # db.py(SQLModel/SQLite) + seed.py(WAV+广场种子)
    static/          # fallback_music/  uploads/  curves/
  tests/test_smoke.py
```

## 鉴权（dev）

所有业务接口用请求头 `X-Openid` 标识用户，dev 环境直接信任该值。
`POST /api/login` 用 code（或随机串）生成稳定伪 openid（`dev_<sha1前16位>`）。

## API 一览（均在 `/api` 下）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/login` | code → 伪 openid |
| POST | `/upload` | multipart(file+openid) → {text, audioUrl}，保存音频到磁盘 |
| POST | `/generate` | {answers, audioRefs} → {jobId} |
| GET  | `/jobs/{jobId}` | running/done + steps + result（约 2.5s 后 done） |
| GET  | `/me/archive` | 当前 openid 历史档案（倒序） |
| GET  | `/me/collected` | 当前 openid 收藏的广场作品 |
| GET  | `/results/{resultId}` | 取回历史 Result |
| GET  | `/plaza?n=6` | 随机 n 条广场作品（带 liked） |
| GET  | `/plaza/{id}` | 广场作品详情（带 music） |
| POST | `/plaza/{id}/like` | 切换收藏 → {liked, likes} |
| POST | `/similarity` | 两人格四维相似度 → {score, you, other, reading} |
| POST | `/redeem` | 兑换码（占位，任意非空码有效） |

## 未来如何替换真实「分析 / Suno」

各 service 都是「抽象接口 + 占位实现 + 模块级单例」，替换时**只改 service，不动路由与契约**。

- **ASR**（`services/asr.py`）：实现 `ASRService.transcribe(audio_path)->str`（调多模态/专用 ASR），
  把模块底部 `asr_service = PlaceholderASR()` 换成真实实现即可。
- **分析**（`services/analysis.py`）：实现 `AnalysisService.analyze(answers)->AnalysisResult`
  （组 prompt → 调多模态大模型 → 解析人格/四维/报告），替换 `analysis_service` 单例。
  铁律：分析归大模型，生成归 Suno。
- **音乐**（`services/music.py`）：`PlaceholderMusic` 已按真实三步骨架预留：
  1. `_build_segment_prompts()` 根据情绪 build 多段 prompt；
  2. `_call_suno()` 对每段调 Suno 生成片段；
  3. `_synthesize()` 用 ffmpeg 把片段合成完整曲子。
  当前每步兜底（直接返回预置 WAV，不依赖 ffmpeg）。真实化时填这三个方法 + 失败兜底即可。

密钥永远只在 `.env`，前端/小程序碰不到任何 key。

## Result 对象结构（契约，字段固定）

```json
{
  "resultId": "r_xxx",
  "persona": {"name": "黄昏独行者", "en": "The Dusk Wanderer"},
  "report": "……",
  "dims": [
    {"left": "独处", "right": "共处", "value": 22, "activeSide": "left"},
    {"left": "涌动", "right": "平静", "value": 74, "activeSide": "right"},
    {"left": "直说", "right": "含蓄", "value": 80, "activeSide": "right"},
    {"left": "回望过去", "right": "望向远方", "value": 30, "activeSide": "left"}
  ],
  "curveUrl": "",
  "music": {"url": "/static/fallback_music/dusk.wav", "duration": 15}
}
```

四维顺序固定不变；`value` = 圆点 0-100 的靠右程度；`activeSide` = value<50?'left':'right'；`curveUrl` 本轮留空。
