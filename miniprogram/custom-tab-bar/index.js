Component({
  data: {
    layer: 'brand',           // 'brand' | 'activity'
    selected: 'pages/home/home',
    brand: [
      { key: 'home', path: 'pages/home/home', text: '实验室', ic: 'lab' },
      { key: 'me', path: 'pages/me/me', text: '我的', ic: 'user' }
    ],
    activity: [
      { key: 'act-home', path: 'pages/act-home/act-home', text: '活动主页', ic: 'house' },
      { key: 'act-plaza', path: 'pages/act-plaza/act-plaza', text: '广场', ic: 'plaza' },
      { key: 'act-mine', path: 'pages/act-mine/act-mine', text: '我的活动', ic: 'user' }
    ]
  },
  methods: {
    // 每个 Tab 页 onShow 调用：读取当前导航层 + 当前路由，刷新高亮与层级
    update() {
      const g = getApp().globalData;
      const pages = getCurrentPages();
      const route = pages.length ? pages[pages.length - 1].route : '';
      this.setData({ layer: g.navLayer || 'brand', selected: route });
    },
    onTap(e) {
      const path = e.currentTarget.dataset.path;
      if (path === this.data.selected) return;
      wx.switchTab({ url: '/' + path });
    }
  }
});
