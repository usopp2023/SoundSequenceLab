const { request } = require('../../utils/request');
const store = require('../../utils/store');

const DEFAULT_READING = '你们都习惯把情绪藏在平静的表面之下。不同的是，你回望过去，而 Ta 望向远方——也许正好能聊聊，对方看到的是什么。';

Page({
  data: {
    score: 82,
    you: { name: '黄昏独行者' },
    other: { name: '深海回声者' },
    reading: DEFAULT_READING
  },

  onLoad(query) {
    const meName = store.get().latestPersona;
    this.setData({ 'you.name': meName });

    // 先用 query 兜底显示，再尝试后端精确计算
    if (query.score) this.setData({ score: Number(query.score) });
    if (query.other) this.setData({ 'other.name': decodeURIComponent(query.other) });

    const body = { meName };
    if (query.otherPlazaId !== undefined) body.otherPlazaId = Number(query.otherPlazaId);
    else if (query.other) body.otherName = decodeURIComponent(query.other);

    request('/api/similarity', { method: 'POST', data: body })
      .then((res) => {
        if (!res) return;
        this.setData({
          score: res.score,
          you: res.you || this.data.you,
          other: res.other || this.data.other,
          reading: res.reading || DEFAULT_READING
        });
      })
      .catch(() => {});
  },

  onShareAppMessage() {
    const name = this.data.you.name;
    return {
      title: `我是「${name}」，来测测你的情绪音乐，看看我们有多像`,
      path: '/pages/sim-invite/sim-invite?from=' + encodeURIComponent(name)
    };
  }
});
