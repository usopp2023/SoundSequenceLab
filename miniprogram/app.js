const store = require('./utils/store');
const { request } = require('./utils/request');

App({
  globalData: {
    navLayer: 'brand',          // 'brand' | 'activity'，custom-tab-bar 据此切两套底栏
    brandOrigin: 'pages/home/home',
    openid: '',
    store: null
  },

  onLaunch() {
    // 载入持久化的跨页状态
    this.globalData.store = store.load();
    this.globalData.profile = this.globalData.store.profile || { nickname: '', avatarUrl: '' };

    // 登录拿 openid（dev 后端返回伪 openid；真实环境走 code2session）
    wx.login({
      success: (res) => {
        if (!res.code) return;
        request('/api/login', { method: 'POST', data: { code: res.code } })
          .then((data) => {
            if (data && data.openid) this.globalData.openid = data.openid;
          })
          .catch(() => {
            // 后端没起也不阻塞 UI；联调时再排查
          });
      }
    });
  }
});
