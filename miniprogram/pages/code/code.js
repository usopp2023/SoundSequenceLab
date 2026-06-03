const { request } = require('../../utils/request');
const store = require('../../utils/store');
const nav = require('../../utils/nav');

Page({
  data: { code: '' },

  onInput(e) { this.setData({ code: e.detail.value }); },

  // 扫现场二维码认领（wx.scanCode 读到认领码 → 直接走认领）
  scan() {
    wx.scanCode({
      onlyFromCamera: false,
      success: (res) => {
        const code = (res.result || '').trim();
        if (!code) { wx.showToast({ title: '没读到认领码', icon: 'none' }); return; }
        this.setData({ code }, () => this.redeem());
      },
      fail: () => {}
    });
  },

  redeem() {
    const v = (this.data.code || '').trim();
    if (!v) { wx.showToast({ title: '请输入兑换码', icon: 'none' }); return; }

    // 演示码 / 权益码：仅解锁权益
    const unlockPerks = () => {
      store.update({ offlineUnlocked: true });
      wx.showToast({ title: '解锁成功！', icon: 'success' });
      setTimeout(() => nav.switchActTab('pages/act-mine/act-mine'), 800);
    };
    // 现场认领码：把作品绑到本人 + 解锁权益 → 打开认领到的结果
    const claimWork = (res) => {
      store.update({ offlineUnlocked: true, latestPersona: res.result.persona.name });
      getApp().globalData.currentResult = res.result;
      getApp().globalData.navLayer = 'activity';
      wx.showToast({ title: '认领成功！', icon: 'success' });
      setTimeout(() => wx.redirectTo({ url: '/pages/result/result?mode=claimed' }), 800);
    };

    request('/api/redeem', { method: 'POST', data: { code: v } })
      .then((res) => {
        if (!res || !res.ok) {
          wx.showToast({ title: (res && res.message) || '兑换码不正确，请检查后重试', icon: 'none' });
          return;
        }
        if (res.claimed && res.result) claimWork(res);
        else unlockPerks();
      })
      .catch(() => {
        // 后端不可用：只能本地校验固定演示码（认领码必须后端校验）
        if (v.toLowerCase() === 'anysxzn2026') unlockPerks();
        else wx.showToast({ title: '兑换码不正确（或未连接后端）', icon: 'none' });
      });
  }
});
