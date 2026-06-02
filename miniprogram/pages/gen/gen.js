const { request } = require('../../utils/request');
const nav = require('../../utils/nav');

const GEN_STEPS = ['正在听你说的话……', '读出你藏起来的情绪……', '正在谱一段曲子……'];

// 后端不可用时的占位结果（黄昏独行者，与原型一致）
const DEMO_RESULT = {
  resultId: 'demo-fresh',
  persona: { name: '黄昏独行者', en: 'The Dusk Wanderer' },
  report: '你习惯在人群散去后才开口。情绪来得不急不缓，像黄昏的海——表面平静，底下有自己的潮汐。你把很多话留在了心里，但它们一直都在。',
  dims: [
    { left: '独处', right: '共处', value: 22, activeSide: 'left' },
    { left: '涌动', right: '平静', value: 74, activeSide: 'right' },
    { left: '直说', right: '含蓄', value: 80, activeSide: 'right' },
    { left: '回望过去', right: '望向远方', value: 30, activeSide: 'left' }
  ],
  curveUrl: '',
  music: { url: '', duration: 15 }
};

Page({
  data: { statusBar: 20, genText: GEN_STEPS[0] },

  onLoad() {
    const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    this.setData({ statusBar: info.statusBarHeight || 20 });
    this.steps = GEN_STEPS;
    this.result = null;
    this.tickerDone = false;
    this.cancelled = false;
    this.start();
  },

  start() {
    this.startTicker();
    const answers = getApp().globalData.quizAnswers || [];
    request('/api/generate', { method: 'POST', data: { answers, audioRefs: [] } })
      .then((res) => {
        if (res && res.jobId) this.poll(res.jobId);
        else this.fallback();
      })
      .catch(() => this.fallback());
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
        } else {
          setTimeout(() => this.poll(jobId), 800);
        }
      })
      .catch(() => this.fallback());
  },

  // 后端不可用：等动画走完后用占位结果
  fallback() {
    if (this.result) return;
    this.result = DEMO_RESULT;
    this.tryFinish();
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
