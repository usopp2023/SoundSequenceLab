# Suno 民乐生成接入说明（已跑通）

> 2026-06-06 实测端到端打通：答题 → 阶跃情绪分析(9桶) → 真 Suno 生成民乐 → 转存 → 结果页点亮。
> 本文记录**怎么跑起来、坑在哪、关键修复**，便于复现与排障。

## 一、它怎么工作（架构）

```
小程序/现场机 → FastAPI 后端（异步 worker）
   ├─ 阶跃星辰 API（情绪分析，走系统代理直达）
   └─ suno-api（本地 :3000，有头浏览器）→ Suno（经 Clash 代理）
        后端再经代理从 cdn1.suno.ai 下载 mp3 → 转存 /static/generated
```

**关键：不是用 suno-api 的 API token 流程**（那条被 Suno 改版+hCaptcha 打死了）。
我们走的是 **`/api/ui_generate`：有头浏览器把我们的 9 桶 tags 输进 suno.com 创作框 → 点 Create → Suno 真生成**（有头模式下无感 hCaptcha 自动通过，**不需要 2captcha**）→ 后端轮询 `/api/get` 取回新曲 → 代理下载转存。

## 二、跑起来需要什么

1. **Clash 代理**开着（系统代理模式），本地端口如 `127.0.0.1:7897`。访问 Suno 必需。
2. **suno-api**（`E:\声序实验室\suno-api\`，已 gitignore，第三方）：
   - `npm install`（用国内镜像：`--registry=https://registry.npmmirror.com`）
   - Playwright chromium：`npx playwright install chromium`
   - `suno-api/.env`：
     - `SUNO_COOKIE=<登录 suno.com 后从 Network 复制的整串 Cookie>`
     - `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY=http://127.0.0.1:7897`
     - `BROWSER_HEADLESS=false` ← **必须有头**（无头被 hCaptcha 拦）
     - `TWOCAPTCHA_KEY=` 实测**用不到**（有头无感验证自动过），可留空/留作备用
   - 本地补丁（已在 `src/lib/SunoApi.ts`，gitignore 不入库）：新增 `uiGenerate()` 方法 + 给 `launchBrowser` 的 `launch()` 加了 `proxy`；新增路由 `src/app/api/ui_generate/route.ts`。
   - 启动：`npm run dev` → `:3000`；验证 `curl http://localhost:3000/api/get_limit` 返回额度。
3. **FastAPI 后端** `server/.env`：
   - `SUNO_ENABLED=1`
   - `SUNO_API_BASE=http://localhost:3000`
   - `SUNO_PROXY=http://127.0.0.1:7897`（下载 Suno CDN 用）
   - 重启 FastAPI 生效。

之后答题生成，结果页人格秒出、音乐 ~2-3 分钟后自动点亮。

## 三、关键修复（踩过的坑，排障必看）

1. **国内访问 Suno**：suno-api 的 axios 走 `HTTPS_PROXY`（.env），**无头浏览器也要单独配 `proxy`**（已补到 `launchBrowser`），否则 suno.com 加载不出来。
2. **无头被 hCaptcha 拦**：`BROWSER_HEADLESS=false` 有头模式，无感 hCaptcha 自动通过；无头模式 hCaptcha 既不弹挑战也不放行 → 死。
3. **选择器过时**：Suno 改版后旧选择器失效。当前用 `textarea:visible`（Song Description 框）+ `button[aria-label="Create song"]`，并先点 `Simple` 模式 + 开 `Instrumental`。**Suno 再改版需重抓 DOM 改 `uiGenerate`**（用截图调试：在浏览器流程里 `page.screenshot()` 存图再看）。
4. **`/api/get` 经代理时通时断**：`_get_clips` 加了 3 次重试。
5. **致命坑：后端 httpx 调 localhost 被系统代理劫持返 502**。Clash 系统代理会让 httpx 把 `localhost:3000` 也走代理 → 502。修复：后端调 suno-api 的 httpx 全部 `trust_env=False`（直连）；只有下载 Suno CDN 显式 `proxy=`。
6. **token 同步返回失效**：Suno 现在的 hCaptcha 是无感的，gcui-api"等交互式验证码"超时会关浏览器。我们绕开它，用浏览器生成的**副作用**（真出曲）+ `/api/get` 取回。

## 四、局限 / 后续（务必知道）

- **有头浏览器**：每次生成弹一个浏览器窗口、约 2-3 分钟/首；机器要有屏幕 + 挂 Clash。适合 dev/小规模，不适合无人服务器。
- **cookie 会过期**：失效后要重新登录 suno.com 取 cookie 填回。
- **Suno 改版风险**：UI 一改 `uiGenerate` 选择器可能失效（按 §三.3 重抓）。团队判断短期不会改。
- **duration**：取的是 `streaming` 状态的时长字段（可能是占位 30），不影响播放，仅时间标签显示。要准确可改成等 `complete`。
- **真民乐天花板**：Suno 出的是"国风近似"。要"真民乐技法"仍建议后续上 **ACE-Step + LoRA**（见 `音乐生成方案选型.md`），届时换个 `MusicService` 适配器即可，前端/异步不动。

## 五、代码落点

- 后端 `server/app/services/buckets.py`：9 桶情绪本体（调式/BPM/乐器/技法/suno_tags）。
- 后端 `server/app/services/analysis.py`：`StepFunAnalysis`（阶跃，输出 9 桶 + 人格/四维/报告）。
- 后端 `server/app/services/music.py`：`SunoMusic`（ui_generate 触发 → 轮询 `/api/get` → 代理下载转存；失败回退兜底曲）。
- 后端 `server/app/api/routes_generate.py`：异步 worker（分析先出，音乐后台出）。
- suno-api（本地、gitignore）：`uiGenerate()` + `/api/ui_generate` + 浏览器代理补丁。
