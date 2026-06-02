const { request } = require('../../utils/request');

// 后端不可用时的占位广场数据（照搬原型 PLAZA）
const DEMO_PLAZA = [
  { id: 0, name: '深海回声者', likes: 42, liked: false },
  { id: 1, name: '清晨骤雨型', likes: 31, liked: false },
  { id: 2, name: '黄昏独行者', likes: 58, liked: false },
  { id: 3, name: '暗涌者', likes: 19, liked: false },
  { id: 4, name: '晴窗型', likes: 27, liked: false },
  { id: 5, name: '夜航者', likes: 36, liked: false },
  { id: 6, name: '远雷型', likes: 23, liked: false },
  { id: 7, name: '退潮者', likes: 44, liked: false },
  { id: 8, name: '薄雾型', likes: 15, liked: false },
  { id: 9, name: '潮间带', likes: 38, liked: false }
];

Page({
  data: { tod: 'day', bubbles: [] },

  onShow() {
    getApp().globalData.navLayer = 'activity';
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().update();
    }
    this.setData({ tod: this.timeOfDay() });
    this.refresh();
  },

  // 按当前时间给海面定时段配色（照搬原型 applyTimeOfDay）
  timeOfDay() {
    const h = new Date().getHours();
    if (h >= 5 && h < 9) return 'dawn';
    if (h >= 9 && h < 17) return 'day';
    if (h >= 17 && h < 20) return 'dusk';
    return 'night';
  },

  refresh() {
    request('/api/plaza?n=6')
      .then((res) => {
        const items = (res && res.items && res.items.length) ? res.items : this.pickDemo();
        this.layout(items);
      })
      .catch(() => this.layout(this.pickDemo()));
  },

  pickDemo() {
    return DEMO_PLAZA.slice().sort(() => Math.random() - 0.5).slice(0, 6);
  },

  // 在海面带里错落不重叠地铺光球（照搬原型 renderPlaza 的布局算法）
  layout(items) {
    const q = wx.createSelectorQuery().in(this);
    q.select('#sea').boundingClientRect((rect) => {
      const W = (rect && rect.width > 100) ? rect.width : 360;
      const H = (rect && rect.height > 100) ? rect.height : 300;
      const placed = [];
      const bubbles = [];
      items.forEach((it) => {
        const size = Math.round(W * 0.19 + Math.random() * W * 0.07); // ≈ 0.19~0.26 屏宽
        const r = size / 2;
        let x = 0, y = 0, ok = false, tries = 0;
        while (!ok && tries < 120) {
          x = Math.random() * (W - size);
          y = Math.random() * (H - size - 24) + 6;
          const cx = x + r, cy = y + r;
          ok = placed.every((p) => Math.hypot(cx - p.x, cy - p.y) > (r + p.r + 12));
          tries++;
        }
        if (!ok) return; // 放不下就跳过，宁可少一个也不重叠
        placed.push({ x: x + r, y: y + r, r });
        const dur = (6.5 + Math.random() * 4).toFixed(1);
        const delay = (Math.random() * 3).toFixed(1);
        bubbles.push({
          id: it.id,
          name: it.name,
          likes: it.likes,
          liked: it.liked,
          style: `width:${size}px;height:${size}px;left:${x}px;top:${y}px;--dur:${dur}s;--delay:${delay}s;`
        });
      });
      this.setData({ bubbles });
    }).exec();
  },

  openDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: '/pages/plaza-detail/plaza-detail?id=' + id });
  }
});
