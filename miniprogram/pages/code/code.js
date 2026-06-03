const { request } = require('../../utils/request');
const store = require('../../utils/store');
const nav = require('../../utils/nav');

Page({
  data: { code: '' },

  onInput(e) { this.setData({ code: e.detail.value }); },

  redeem() {
    const v = (this.data.code || '').trim();
    if (!v) { wx.showToast({ title: '请输入兑换码', icon: 'none' }); return; }

    const unlock = () => {
      store.update({ offlineUnlocked: true });
      wx.showToast({ title: '解锁成功！', icon: 'success' });
      setTimeout(() => nav.switchActTab('pages/act-mine/act-mine'), 800);
    };

    request('/api/redeem', { method: 'POST', data: { code: v } })
      .then((res) => {
        if (res && res.ok) unlock();
        else wx.showToast({ title: (res && res.message) || '兑换码不正确，请检查后重试', icon: 'none' });
      })
      .catch(() => {
        // 后端不可用时本地校验固定演示码
        if (v.toLowerCase() === 'anysxzn2026') unlock();
        else wx.showToast({ title: '兑换码不正确，请检查后重试', icon: 'none' });
      });
  }
});
