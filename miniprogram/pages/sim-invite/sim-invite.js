const nav = require('../../utils/nav');
const auth = require('../../utils/auth');

Page({
  data: { fromName: '黄昏独行者' },

  onLoad(query) {
    // 从分享卡片进入也要先登录（#4：一打开就授权登录）
    if (!auth.isLoggedIn()) {
      const self = '/pages/sim-invite/sim-invite' + (query.from ? ('?from=' + encodeURIComponent(query.from)) : '');
      wx.reLaunch({ url: '/pages/login/login?redirect=' + encodeURIComponent(self) });
      return;
    }
    if (query.from) this.setData({ fromName: decodeURIComponent(query.from) });
  },

  // 去活动主页了解 / 开始
  goIntro() {
    nav.enterActivity('pages/act-home/act-home');
  },
  toBrand() {
    nav.toBrand('pages/home/home');
  }
});
