const nav = require('../../utils/nav');

Page({
  onShow() {
    getApp().globalData.navLayer = 'activity';
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().update();
    }
  },
  // 开始答题：清空上一轮答案，进入流程页
  startQuiz() {
    getApp().globalData.quizAnswers = [];
    wx.navigateTo({ url: '/pages/quiz/quiz' });
  },
  openCode() {
    wx.navigateTo({ url: '/pages/code/code' });
  },
  exitAct() {
    nav.exitActivity();
  }
});
