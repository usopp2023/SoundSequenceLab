const nav = require('../../utils/nav');

Page({
  data: { fromName: '黄昏独行者' },

  onLoad(query) {
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
