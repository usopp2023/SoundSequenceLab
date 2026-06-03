const { request } = require('../../utils/request');
const nav = require('../../utils/nav');

const GEN_STEPS = ['正在听你说的话……', '读出你藏起来的情绪……', '正在谱一段曲子……'];
const POLL_TIMEOUT_MS = 15000; // 轮询最长 15s，超时进失败态

Page({
  data: { statusBar: 20, genText: GEN_STEPS[0], failed: false },

  onLoad() {
    const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    this.setData({ statusBar: info.statusBarHeight || 20 });
    this.steps = GEN_STEPS;
    this.start();
  },

  start() {
    // 复位状态（支持「重新生成」）
    this.result = null;
    this.tickerDone = false;
    this.cancelled = false;
    this.deadline = Date.now() + POLL_TIMEOUT_MS;
    this.setData({ failed: false });
    this.startTicker();

    const answers = getApp().globalData.quizAnswers || [];
    request('/api/generate', { method: 'POST', data: { answers, audioRefs: [] } })
      .then((res) => {
        if (res && res.jobId) this.poll(res.jobId);
        else this.fail();
      })
      .catch(() => this.fail());
  },

  poll(jobId) {
    if (this.cancelled) return;
    request('/api/jobs/' + jobId)
      .then((res) => {
        if (this.cancelled) return;
        if (res && res.steps && res.steps.length) this.steps = res.steps;
        if (res && res.status === 'done' && res.result) {
          this.result = res.result;
          this.tryFinish();
        } else if (Date.now() > this.deadline) {
          this.fail(); // 超时
        } else {
          setTimeout(() => this.poll(jobId), 800);
        }
      })
      .catch(() => this.fail());
  },

  // 生成失败（网络错误 / 超时）→ 失败态，可重试
  fail() {
    if (this.cancelled || this.result) return;
    if (this.ticker) { clearInterval(this.ticker); this.ticker = null; }
    this.setData({ failed: true });
  },

  retryGen() { this.start(); },

  // 「稍后再说」→ 回活动主页
  later() {
    this.cancelled = true;
    if (this.ticker) { clearInterval(this.ticker); this.ticker = null; }
    nav.switchActTab('pages/act-home/act-home');
  },

  startTicker() {
    let step = 0;
    this.setData({ genText: this.steps[0] });
    this.ticker = setInterval(() => {
      step++;
      if (step < this.steps.length) {
        this.setData({ genText: '' });
        setTimeout(() => { if (!this.cancelled) this.setData({ genText: this.steps[step] }); }, 300);
      } else {
        clearInterval(this.ticker); this.ticker = null;
        this.tickerDone = true;
        this.tryFinish();
      }
    }, 1500);
  },

  tryFinish() {
    if (this.cancelled) return;
    if (this.result && this.tickerDone) this.finish();
  },

  finish() {
    getApp().globalData.currentResult = this.result;
    wx.redirectTo({ url: '/pages/result/result?mode=fresh' });
  },

  cancelGen() {
    wx.showModal({
      title: '',
      content: '要放弃这次生成吗？已填写的内容不会保存。',
      confirmText: '放弃',
      cancelText: '继续等待',
      success: (r) => {
        if (r.confirm) {
          this.cancelled = true;
          if (this.ticker) { clearInterval(this.ticker); this.ticker = null; }
          nav.switchActTab('pages/act-home/act-home');
        }
      }
    });
  },

  onUnload() { this.cancelled = true; if (this.ticker) { clearInterval(this.ticker); this.ticker = null; } }
});
