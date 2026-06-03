const store = require('../../utils/store');

Page({
  data: { statusBar: 20, avatarUrl: '', nickname: '', canLogin: false, redirect: '' },

  onLoad(q) {
    const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    this.setData({
      statusBar: info.statusBarHeight || 20,
      redirect: q && q.redirect ? decodeURIComponent(q.redirect) : ''
    });
    // 已登录则直接放行
    const p = store.get().profile;
    if (p && p.nickname) { this.go(); return; }
    if (p && p.avatarUrl) this.setData({ avatarUrl: p.avatarUrl });
  },

  // 头像（微信「头像昵称填写能力」）
  onChooseAvatar(e) {
    this.setData({ avatarUrl: e.detail.avatarUrl });
  },
  onNickInput(e) {
    const v = (e.detail.value || '').trim();
    this.setData({ nickname: v, canLogin: !!v });
  },

  doLogin() {
    const nickname = (this.data.nickname || '').trim();
    if (!nickname) { wx.showToast({ title: '请填写昵称', icon: 'none' }); return; }
    const profile = { nickname, avatarUrl: this.data.avatarUrl || '' };
    store.update({ profile });
    getApp().globalData.profile = profile;
    // TODO(real): 把昵称/头像同步到后端账号（需真实 openid，见 docs/未完成事项.md #3）
    this.go();
  },

  go() {
    const url = this.data.redirect || '/pages/home/home';
    wx.reLaunch({ url, fail: () => wx.reLaunch({ url: '/pages/home/home' }) });
  }
});
