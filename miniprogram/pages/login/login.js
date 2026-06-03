const store = require('../../utils/store');

// 按需的「设置头像昵称」页（从 me / 我的活动 进入）。登录本身已在 app.js 静默完成。
Page({
  data: { avatarUrl: '', nickname: '', canSave: false, redirect: '' },

  onLoad(q) {
    const p = store.get().profile || {};
    this.setData({
      avatarUrl: p.avatarUrl || '',
      nickname: p.nickname || '',
      canSave: !!p.nickname,
      redirect: q && q.redirect ? decodeURIComponent(q.redirect) : ''
    });
  },

  onChooseAvatar(e) {
    this.setData({ avatarUrl: e.detail.avatarUrl });
  },
  onNickInput(e) {
    const v = (e.detail.value || '').trim();
    this.setData({ nickname: v, canSave: !!v });
  },

  save() {
    const nickname = (this.data.nickname || '').trim();
    if (!nickname) { wx.showToast({ title: '请填写昵称', icon: 'none' }); return; }
    const profile = { nickname, avatarUrl: this.data.avatarUrl || '' };
    store.update({ profile });
    getApp().globalData.profile = profile;
    // TODO(real): 同步昵称/头像到后端账号（需真实 openid，见 docs/未完成事项.md #3）
    wx.showToast({ title: '已保存', icon: 'success' });
    setTimeout(() => {
      const r = this.data.redirect;
      if (r) wx.reLaunch({ url: r, fail: () => wx.navigateBack() });
      else wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/me/me' }) });
    }, 500);
  }
});
