const { request, assetUrl } = require('../../utils/request');
const store = require('../../utils/store');

const WAVE_BARS = [40, 70, 30, 85, 55, 40, 75, 35, 60, 45, 80, 50, 30, 65, 42, 70];

// 后端不可用时的占位作品（照搬原型 PLAZA 的名字/描述）
const DEMO = [
  { name: '深海回声者', desc: '习惯把情绪藏在平静的表面之下，望向远方多过回望过去。', likes: 42 },
  { name: '清晨骤雨型', desc: '来得快去得也快，情绪像一阵突然的雨，落完天就晴了。', likes: 31 },
  { name: '黄昏独行者', desc: '在人群散去后才开口，把很多话留在了心里。', likes: 58 },
  { name: '暗涌者', desc: '表面安静，底下一直有自己的潮汐在走。', likes: 19 },
  { name: '晴窗型', desc: '情绪透亮，愿意把心里的事摊开在光里说。', likes: 27 },
  { name: '夜航者', desc: '喜欢在深夜独处时，才和自己的情绪对话。', likes: 36 },
  { name: '远雷型', desc: '情绪在很远的地方滚动，等靠近时往往已经过去。', likes: 23 },
  { name: '退潮者', desc: '习惯在喧闹退去之后，才慢慢露出心里的样子。', likes: 44 },
  { name: '薄雾型', desc: '看不太真切，却始终笼在一层温柔的情绪里。', likes: 15 },
  { name: '潮间带', desc: '在靠近与退开之间反复，像潮水来回的那条线。', likes: 38 }
];

Page({
  data: {
    work: { id: 0, name: '深海回声者', en: '', by: '来自 一位匿名的朋友', desc: '', likes: 0, liked: false, music: { url: '', duration: 15 } },
    enUpper: '',
    waveBars: WAVE_BARS,
    playing: false,
    playTimeLabel: '0:00 / 0:15'
  },

  onLoad(query) {
    this.pid = Number(query.id || 0);
    request('/api/plaza/' + this.pid)
      .then((w) => this.applyWork(w))
      .catch(() => {
        const d = DEMO[this.pid] || DEMO[0];
        this.applyWork({ id: this.pid, name: d.name, en: '', by: '来自 一位匿名的朋友', desc: d.desc, likes: d.likes, liked: false, music: { url: '', duration: 15 } });
      });
  },

  applyWork(w) {
    const dur = (w.music && w.music.duration) || 15;
    this.duration = dur;
    this.setData({
      work: w,
      enUpper: (w.en || '').toUpperCase(),
      playTimeLabel: '0:00 / 0:' + String(dur).padStart(2, '0')
    });
    this.setupAudio(w.music && w.music.url);
  },

  setupAudio(url) {
    if (this.audio) { try { this.audio.destroy(); } catch (e) {} this.audio = null; }
    if (!url) return;
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

  // 点赞 = 收藏
  toggleLike() {
    request('/api/plaza/' + this.pid + '/like', { method: 'POST' })
      .then((r) => {
        this.setData({ 'work.liked': r.liked, 'work.likes': r.likes });
        this.syncLocalCollected(r.liked);
      })
      .catch(() => {
        // 离线：本地切换
        const liked = !this.data.work.liked;
        this.setData({ 'work.liked': liked, 'work.likes': this.data.work.likes + (liked ? 1 : -1) });
        this.syncLocalCollected(liked);
      });
  },

  syncLocalCollected(liked) {
    const s = store.get();
    const set = new Set(s.collected || []);
    if (liked) set.add(this.pid); else set.delete(this.pid);
    store.update({ collected: Array.from(set) });
  },

  simWith() {
    this.stopPlay();
    getApp().globalData.navLayer = 'activity';
    wx.navigateTo({ url: '/pages/sim/sim?otherPlazaId=' + this.pid + '&other=' + encodeURIComponent(this.data.work.name) });
  },

  onUnload() {
    this.stopPlay();
    if (this.audio) { try { this.audio.destroy(); } catch (e) {} this.audio = null; }
  }
});
