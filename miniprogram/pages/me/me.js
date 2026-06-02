const nav = require('../../utils/nav');
const store = require('../../utils/store');

Page({
  data: { latestPersona: '黄昏独行者' },
  onShow() {
    getApp().globalData.navLayer = 'brand';
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().update();
    }
    const s = store.get();
    this.setData({ latestPersona: s.latestPersona });
  },
  enterAct() {
    nav.enterActivity('pages/act-home/act-home');
  },
  openFlow(e) {
    const flow = e.currentTarget.dataset.flow;
    wx.navigateTo({ url: '/pages/' + flow + '/' + flow });
  }
});
