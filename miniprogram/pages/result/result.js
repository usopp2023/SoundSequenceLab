const { request, assetUrl } = require('../../utils/request');
const store = require('../../utils/store');
const nav = require('../../utils/nav');

const WAVE_BARS = [40, 70, 30, 85, 55, 40, 75, 35, 60, 45, 80, 50, 30, 65, 42, 70];

const DEMO_RESULT = {
  resultId: 'demo',
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
  data: {
    result: DEMO_RESULT,
    waveBars: WAVE_BARS,
    playing: false,
    playTimeLabel: '0:00 / 0:15',
    sourceText: '',
    showSaved: true,
    showFinish: true
  },

  onLoad(query) {
    const mode = query.mode || 'fresh';
    if (mode === 'fresh' || mode === 'claimed') {
      const r = getApp().globalData.currentResult || DEMO_RESULT;
      this.applyResult(r, {
        sourceText: mode === 'claimed'
          ? '已认领 · 来自你在阿那亚现场的体验'
          : '以下人格、曲线与音乐，都来自你刚才的回答',
        showSaved: true, showFinish: true
      });
      // 更新「最近人格」（相似度匹配以它为准）
      store.update({ latestPersona: r.persona.name });
    } else {
      // 历史档案
      this.setData({ sourceText: '这是你生成的记录', showSaved: false, showFinish: false });
      const id = query.resultId;
      if (id && id.indexOf('demo') !== 0) {
        request('/api/results/' + id)
          .then((r) => this.applyResult(r, { sourceText: '这是你生成的记录', showSaved: false, showFinish: false }))
          .catch(() => {});
      }
    }
  },

  applyResult(r, extra) {
    const dur = (r.music && r.music.duration) || 15;
    this.setData(Object.assign({
      result: r,
      playTimeLabel: '0:00 / 0:' + String(dur).padStart(2, '0')
    }, extra));
    this.duration = dur;
    this.setupAudio(r.music && r.music.url);
  },

  setupAudio(url) {
    if (this.audio) { try { this.audio.destroy(); } catch (e) {} this.audio = null; }
    if (!url) return; // 无音频则只做波形动画 + 假计时
    const ctx = wx.createInnerAudioContext();
    ctx.src = assetUrl(url);
    ctx.onTimeUpdate(() => {
      const cur = Math.floor(ctx.currentTime || 0);
      this.setData({ playTimeLabel: '0:' + String(cur).padStart(2, '0') + ' / 0:' + String(this.duration).padStart(2, '0') });
    });
    ctx.onEnded(() => this.stopPlay());
    this.audio = ctx;
  },

  togglePlay() {
    if (this.data.playing) { this.stopPlay(); return; }
    this.setData({ playing: true });
    if (this.audio) {
      this.audio.play();
    } else {
      // 无音频：假计时驱动波形（与原型一致）
      let sec = 0;
      this.fakeTimer = setInterval(() => {
        sec = (sec + 1) % (this.duration + 1);
        this.setData({ playTimeLabel: '0:' + String(sec).padStart(2, '0') + ' / 0:' + String(this.duration).padStart(2, '0') });
      }, 1000);
    }
  },

  stopPlay() {
    this.setData({ playing: false });
    if (this.audio) { try { this.audio.pause(); } catch (e) {} }
    if (this.fakeTimer) { clearInterval(this.fakeTimer); this.fakeTimer = null; }
  },

  openShare() {
    getApp().globalData.shareResult = this.data.result;
    wx.navigateTo({ url: '/pages/share/share' });
  },

  // 完成 → 进入活动层「我的活动」
  finishToMine() {
    this.stopPlay();
    nav.switchActTab('pages/act-mine/act-mine');
  },

  onUnload() {
    this.stopPlay();
    if (this.audio) { try { this.audio.destroy(); } catch (e) {} this.audio = null; }
  }
});
