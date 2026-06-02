const nav = require('../../utils/nav');

Page({
  data: {
    items: [
      { id: 1, type: 'mine', read: false, title: '你的曲子已生成', text: '「黄昏独行者」的情绪音乐已经准备好了，点开听听看。', time: '今天 14:32' },
      { id: 2, type: 'sim', read: true, title: '有人和你的曲线很像', text: '一位朋友的情绪曲线与你相似度 82%，去看看你们有多像。', time: '昨天 21:08' },
      { id: 3, type: 'act', read: true, title: '阿那亚 · 情绪音乐 活动开启', text: '声序实验室来到阿那亚了，回答三个问题，把情绪留成一段曲子。', time: '3 天前' }
    ]
  },
  onTap(e) {
    const type = e.currentTarget.dataset.type;
    if (type === 'mine') {
      nav.enterActivity('pages/act-mine/act-mine');
    } else if (type === 'act') {
      nav.enterActivity('pages/act-home/act-home');
    } else if (type === 'sim') {
      // 进入相似度页（从通知触发，演示一条匹配）
      getApp().globalData.navLayer = 'activity';
      wx.navigateTo({ url: '/pages/sim/sim?from=notif&score=82&other=深海回声者' });
    }
  }
});
