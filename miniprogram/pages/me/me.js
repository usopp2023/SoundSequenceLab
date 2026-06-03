const nav = require('../../utils/nav');
const store = require('../../utils/store');

Page({
  data: { latestPersona: '黄昏独行者', rewardLocked: true, nickname: '微信用户', avatarUrl: '' },
  onShow() {
    getApp().globalData.navLayer = 'brand';
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().update();
    }
    const s = store.get();
    const p = s.profile || {};
    this.setData({
      latestPersona: s.latestPersona,
      rewardLocked: !s.offlineUnlocked,
      nickname: p.nickname || '微信用户',
      avatarUrl: p.avatarUrl || ''
    });
  },
  enterAct() {
    nav.enterActivity('pages/act-home/act-home');
  },
  openFlow(e) {
    const flow = e.currentTarget.dataset.flow;
    wx.navigateTo({ url: '/pages/' + flow + '/' + flow });
  }
});
