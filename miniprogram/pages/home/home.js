const nav = require('../../utils/nav');

Page({
  onShow() {
    getApp().globalData.navLayer = 'brand';
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().update();
    }
  },
  // 进入「阿那亚 · 情绪民乐」活动（切到活动层）
  enterAct() {
    nav.enterActivity('pages/act-home/act-home');
  }
});
