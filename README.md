# 声序实验室 · 情绪音乐

阿那亚「情绪音乐」微信小程序 + FastAPI 后端。用户答 3 题（语音/打字）→ 后端分析情绪 → 生成音乐 → 得到人格、四维曲线与曲子，可存档、分享、与朋友比相似度、逛广场。

由原型 `原始资料/小程序V2.html` 按 `原始资料/小程序落地文档.md` 落地而成。

## 目录

```
project.config.json        微信开发者工具项目配置（miniprogramRoot=miniprogram/，appid=测试号）
miniprogram/               小程序前端
  app.js/json/wxss         全局：导航层状态、登录、设计 token
  custom-tab-bar/          双层 TabBar（品牌层 实验室/我的 ↔ 活动层 活动主页/广场/我的活动）
  config/                  API_BASE 等配置
  utils/                   request / store / nav / recorder
  pages/                   15 个页面
  assets/_gen-scene.js     广场海滩 4 时段背景生成脚本（产物 pages/act-plaza/scene.wxss 已提交）
server/                    FastAPI 后端（见 server/README.md）
kiosk/                     现场公用体验机（H5 单文件，接同一套后端）
docs/                      产品文档 / Suno接入说明 / 方案选型 / 未完成事项
原始资料/                   原始原型与落地文档
```

## 情绪分析 + 音乐生成（已接真实）

- **情绪分析**：阶跃星辰（`server/app/services/analysis.py`，9 桶情绪本体在 `buckets.py`）。配 `ANALYSIS_API_KEY` 即启用，无 key 回退占位。
- **音乐生成**：真 Suno 民乐——自建 `suno-api`（有头浏览器生成）+ 代理下载转存。`SUNO_ENABLED=1` 启用。**完整搭建 / 排障 / 局限见 `docs/Suno接入说明.md`**。
- 生成异步：答题 → 分析秒出人格/四维 → 音乐后台出曲（~2-3min）→ 结果页「生成中→自动点亮」。
- 密钥/代理放 `server/.env`（gitignore）；suno-api 第三方服务不入库。

## 线下体验机 + 认领（kiosk）

阿那亚现场用一台公用平板跑 `kiosk/index.html`（H5）：答题 → 生成 → 结果 → 出**二维码 + 8 位认领码**。用户用**自己手机**的小程序进「我的活动 → 兑换码」，点「扫码认领」扫现场二维码（`wx.scanCode`），或手输码，把人格/曲子/权益**认领到本人账号**（一次性）。

- 答题流程与小程序一致：**语音优先**（浏览器 `MediaRecorder` 录音 → `/api/upload` 占位识别）+ **打字兜底**，支持上一题、答案恢复、空输入禁用下一题。
- 打开方式：浏览器开 `kiosk/index.html`，默认连 `http://localhost:8000`；指定后端用 `kiosk/index.html?api=http://你的后端`。
- ⚠️ 浏览器录音需 **https 或 localhost**（安全上下文）；现场若用普通 http 访问，录音会自动降级为打字（小程序端用微信原生录音无此限制）。
- 后端接口：`POST /api/kiosk/claim-code` 出码（带 `qrUrl`）、`GET /api/kiosk/claim-qr?code=` 出二维码、`POST /api/redeem` 同时处理演示码与认领码。
- 「微信原生冷扫码直接打开小程序」（小程序码）需正式 AppID，见 `docs/未完成事项.md`；现阶段是"小程序内扫码 / 手输码"，不需 AppID。

## 运行

### 后端
```
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
接口文档：http://localhost:8000/docs

### 小程序
1. 微信开发者工具 → 导入项目，目录选 `E:\声序实验室`（已含 project.config.json，测试号即可）。
2. **详情 → 本地设置 → 勾「不校验合法域名、web-view、TLS 版本以及 HTTPS 证书」**，这样模拟器才能连本地 `http://localhost:8000`。
3. 后端已启动后，编译预览。

## 前后端约定
- 所有接口在 `/api` 下，请求头 `X-Openid` 标识用户（dev 由 `/api/login` 生成伪 openid）。
- 前端在 `miniprogram/config/index.js` 配 `API_BASE`；后端不可用时各页有占位数据兜底，UI 仍可浏览。

## 本轮范围与后续
- **本轮**：15 页全部重写 + 后端全功能端到端跑通；情绪分析与音乐生成为**占位实现**（接口已按真实形态留好）。
- **后续**：
  - 接真实多模态大模型做音频情绪分析（替换 `server/app/services/analysis.py`、`asr.py`）。
  - 接 Suno「多片段生成 + ffmpeg 合成一首」（替换 `server/app/services/music.py`，骨架已留）。
  - ICP 备案 + https 生产域名，把 `API_BASE` 改成 prod，关闭「不校验域名」，真机/上线（见落地文档 §9/§10）。
  - 真实 `code2session`（需正式 AppID + secret；当前 `/api/login` 为伪 openid）。

## 待你确认
- **正式 AppID**：测试号可跑 UI 与本地联调；真机预览/登录态/上线需已注册的 AppID + secret。
