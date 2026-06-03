const store = require('../../utils/store');
const { request } = require('../../utils/request');

// 后端不可用时的占位档案（纯前端开发期也能看到效果）
const DEMO_ARCHIVE = [
  { resultId: 'demo-1', name: '黄昏独行者', when: '今天' },
  { resultId: 'demo-2', name: '深海回声者', when: '3 天前' }
];

Page({
  data: {
    nickname: '微信用户',        // 登录授权后的微信昵称（#11）
    avatarUrl: '',
    latestPersona: '黄昏独行者',
    offlineUnlocked: false,
    archive: DEMO_ARCHIVE,
    collected: [],
    perkOpen: [false, false]
  },

  onShow() {
    getApp().globalData.navLayer = 'activity';
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().update();
    }
    const s = store.get();
    const p = s.profile || {};
    this.setData({
      latestPersona: s.latestPersona,
      offlineUnlocked: s.offlineUnlocked,
      nickname: p.nickname || '微信用户',
      avatarUrl: p.avatarUrl || ''
    });
    this.loadArchive();
    this.loadCollected();
  },

  loadArchive() {
    request('/api/me/archive')
      .then((res) => {
        if (res && res.items && res.items.length) this.setData({ archive: res.items });
      })
      .catch(() => {});
  },
  loadCollected() {
    request('/api/me/collected')
      .then((res) => {
        if (res && res.items) this.setData({ collected: res.items });
      })
      .catch(() => {});
  },

  openArchive(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/result/result?resultId=' + id + '&mode=archive' });
  },
  openCollected(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/plaza-detail/plaza-detail?id=' + id });
  },
  // 取消收藏（#13）：再次点赞=取消，并从本地与列表移除
  uncollect(e) {
    const id = Number(e.currentTarget.dataset.id);
    request('/api/plaza/' + id + '/like', { method: 'POST' }).catch(() => {});
    const s = store.get();
    store.update({ collected: (s.collected || []).filter((x) => x !== id) });
    this.setData({ collected: this.data.collected.filter((it) => it.plazaId !== id) });
  },
  startQuiz() {
    getApp().globalData.quizAnswers = [];
    wx.navigateTo({ url: '/pages/quiz/quiz' });
  },
  togglePerk(e) {
    const i = Number(e.currentTarget.dataset.i);
    const perkOpen = this.data.perkOpen.slice();
    perkOpen[i] = !perkOpen[i];
    this.setData({ perkOpen });
  },
  openCode() {
    wx.navigateTo({ url: '/pages/code/code' });
  }
});
