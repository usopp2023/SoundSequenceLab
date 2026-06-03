// 登录态判断：以是否填过昵称为准（#11）。
// 真实账号体系需正式 AppID + code2session，见 docs/未完成事项.md。
const store = require('./store');

function isLoggedIn() {
  const p = store.get().profile;
  return !!(p && p.nickname);
}

module.exports = { isLoggedIn };
