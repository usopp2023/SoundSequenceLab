// 全局配置。开发期连本地后端，需在「微信开发者工具 → 详情 → 本地设置」勾选
// 「不校验合法域名、web-view、TLS 版本以及 HTTPS 证书」。
// 真机预览 / 上线时改成已备案的 https 域名（见 原始资料/小程序落地文档.md §9）。
const ENV = 'dev';

const API_BASE_MAP = {
  dev: 'http://localhost:8000',
  prod: 'https://your-backend-domain.example.com' // TODO: 备案后替换
};

module.exports = {
  ENV,
  API_BASE: API_BASE_MAP[ENV],
  // 活动元信息（原型里写死的「阿那亚 · 情绪音乐」）
  ACTIVITY: {
    id: 'anerya-emotion-music',
    name: '阿那亚 · 情绪音乐',
    place: '阿那亚'
  }
};
