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
  music: { url: '', duration: 15, status: 'ready' }
};

function fmt(s) {
  s = Math.max(0, Math.floor(s || 0));
  return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
}

Page({
  data: {
    result: DEMO_RESULT,
    waveBars: WAVE_BARS,
    playing: false,
    musicGenerating: false,
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
      store.update({ latestPersona: r.persona.name });
    } else {
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
    const music = r.music || {};
    const dur = music.duration || 15;
    const generating = music.status === 'generating';
    this.duration = dur;
    this.setData(Object.assign({
      result: r,
      musicGenerating: generating,
      playTimeLabel: '0:00 / ' + fmt(dur)
    }, extra));
    if (generating) {
      this.startMusicPoll(r.resultId);   // 音乐异步出曲，轮询到就绪再点亮
    } else {
      this.setupAudio(music.url);
    }
  },

  // 轮询 /results 直到音乐就绪（Suno 1–2 分钟）
  startMusicPoll(resultId) {
    if (!resultId || resultId.indexOf('demo') === 0) return;
    this.stopMusicPoll();
    this.musicDeadline = Date.now() + 420000; // 最多等 ~7min（Suno 出曲慢）
    const tick = () => {
      request('/api/results/' + resultId)
        .then((r) => {
          if (r && r.music && r.music.status === 'ready' && r.music.url) {
            this.onMusicReady(r);
          } else if (Date.now() > this.musicDeadline) {
            this.stopMusicPoll();
          } else {
            this.musicPoll = setTimeout(tick, 5000);
          }
        })
        .catch(() => { this.musicPoll = setTimeout(tick, 5000); });
    };
    this.musicPoll = setTimeout(tick, 5000);
  },
  onMusicReady(r) {
    this.stopMusicPoll();
    const dur = (r.music && r.music.duration) || 15;
    this.duration = dur;
    this.setData({ musicGenerating: false, 'result.music': r.music, playTimeLabel: '0:00 / ' + fmt(dur) });
    this.setupAudio(r.music.url);
    wx.showToast({ title: '你的曲子好了', icon: 'none' });
  },
  stopMusicPoll() { if (this.musicPoll) { clearTimeout(this.musicPoll); this.musicPoll = null; } },

  setupAudio(url) {
    if (this.audio) { try { this.audio.destroy(); } catch (e) {} this.audio = null; }
    if (!url) return;
    const ctx = wx.createInnerAudioContext();
    ctx.src = assetUrl(url);
    ctx.onTimeUpdate(() => {
      this.setData({ playTimeLabel: fmt(ctx.currentTime) + ' / ' + fmt(this.duration) });
    });
    ctx.onEnded(() => this.stopPlay());
    this.audio = ctx;
  },

  togglePlay() {
    if (this.data.musicGenerating) { wx.showToast({ title: '民乐生成中…稍后回来听', icon: 'none' }); return; }
    if (this.data.playing) { this.stopPlay(); return; }
    this.setData({ playing: true });
    if (this.audio) {
      this.audio.play();
    } else {
      let sec = 0;
      this.fakeTimer = setInterval(() => {
        sec = (sec + 1) % (this.duration + 1);
        this.setData({ playTimeLabel: fmt(sec) + ' / ' + fmt(this.duration) });
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

  finishToMine() {
    this.stopPlay();
    nav.switchActTab('pages/act-mine/act-mine');
  },

  onUnload() {
    this.stopPlay();
    this.stopMusicPoll();
    if (this.audio) { try { this.audio.destroy(); } catch (e) {} this.audio = null; }
  }
});
