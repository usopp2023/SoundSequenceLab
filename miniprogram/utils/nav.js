// 双层导航助手：对应原型的 switchTab / enterAct / switchAct / exitAct。
// navLayer = 'brand' | 'activity'，存在 app.globalData，custom-tab-bar 据此渲染两套底栏。

const BRAND_TABS = ['pages/home/home', 'pages/me/me'];

function g() {
  return getApp().globalData;
}

function currentRoute() {
  const pages = getCurrentPages();
  return pages.length ? pages[pages.length - 1].route : '';
}

// 进入活动层（记住进入前所在的品牌 Tab，退出时回到那里）
function enterActivity(tab) {
  const route = currentRoute();
  if (BRAND_TABS.indexOf(route) !== -1) {
    g().brandOrigin = route;
  }
  g().navLayer = 'activity';
  wx.switchTab({ url: '/' + (tab || 'pages/act-home/act-home') });
}

// 活动层内部切 Tab
function switchActTab(tab) {
  g().navLayer = 'activity';
  wx.switchTab({ url: '/' + tab });
}

// 退出活动层 → 回到进入前的品牌 Tab
function exitActivity() {
  g().navLayer = 'brand';
  wx.switchTab({ url: '/' + (g().brandOrigin || 'pages/home/home') });
}

// 切到某个品牌 Tab
function toBrand(tab) {
  g().navLayer = 'brand';
  wx.switchTab({ url: '/' + tab });
}

module.exports = { enterActivity, switchActTab, exitActivity, toBrand, BRAND_TABS };
