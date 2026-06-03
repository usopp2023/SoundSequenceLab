// 跨页面状态：放在 app.globalData，并持久化到本地存储。
// 对应原型里散落在脚本顶部的全局变量（latestPersona / liked / 档案 / 解锁态）。
const KEY = 'sxlab_state_v1';

const defaultState = {
  profile: { nickname: '', avatarUrl: '' }, // 微信昵称/头像（登录授权后填，#11）
  latestPersona: '黄昏独行者', // 最近一次人格名（相似度匹配以它为准，原型 #4）
  archive: [],                 // 我的情绪档案：[{name, en, when, resultId}]
  collected: [],               // 广场收藏：plaza 作品 id 列表
  offlineUnlocked: false       // 线下完整权益是否已解锁（兑换码）
};

function load() {
  try {
    const s = wx.getStorageSync(KEY);
    return Object.assign({}, defaultState, s || {});
  } catch (e) {
    return Object.assign({}, defaultState);
  }
}

function save(state) {
  try {
    wx.setStorageSync(KEY, state);
  } catch (e) {}
}

// 读取/合并全局状态的便捷方法，统一从 getApp().globalData.store 取。
function get() {
  const app = getApp();
  if (!app.globalData.store) app.globalData.store = load();
  return app.globalData.store;
}

function update(patch) {
  const s = get();
  Object.assign(s, patch);
  save(s);
  return s;
}

module.exports = { get, update, load, save, defaultState };
