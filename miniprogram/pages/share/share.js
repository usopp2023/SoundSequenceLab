Page({
  data: {
    persona: { name: '黄昏独行者', en: 'The Dusk Wanderer' },
    enUpper: 'THE DUSK WANDERER'
  },

  onLoad() {
    const r = getApp().globalData.shareResult;
    if (r && r.persona) {
      this.setData({ persona: r.persona, enUpper: (r.persona.en || '').toUpperCase() });
    }
  },

  // open-type="share" 已触发原生分享，这里仅给点反馈
  onShareTap() {},

  // 转发到群/好友（带参数：对方点开后判断是否玩过 → 相似度 / 引导）
  onShareAppMessage() {
    const name = this.data.persona.name;
    return {
      title: `我是「${name}」，来测测你的情绪音乐，看看我们有多像`,
      path: '/pages/sim-invite/sim-invite?from=' + encodeURIComponent(name)
    };
  }
});
