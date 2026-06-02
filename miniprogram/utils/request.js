// 统一封装 wx.request / wx.uploadFile。所有后端调用都走这里。
const { API_BASE } = require('../config/index');

function getOpenid() {
  const app = getApp();
  return (app && app.globalData && app.globalData.openid) || '';
}

// 通用请求。返回 Promise，data 直接是后端 JSON。
function request(path, { method = 'GET', data = {}, header = {} } = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: API_BASE + path,
      method,
      data,
      header: Object.assign({ 'content-type': 'application/json', 'X-Openid': getOpenid() }, header),
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(res);
        }
      },
      fail: reject
    });
  });
}

// 上传文件（录音音频）。formData 里带上 openid。
function upload(path, filePath, formData = {}) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: API_BASE + path,
      filePath,
      name: 'file',
      formData: Object.assign({ openid: getOpenid() }, formData),
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data));
          } catch (e) {
            resolve(res.data);
          }
        } else {
          reject(res);
        }
      },
      fail: reject
    });
  });
}

// 把后端返回的相对静态路径（/static/...）补成完整 URL，供 <image>/audio 使用。
function assetUrl(p) {
  if (!p) return '';
  if (/^https?:\/\//.test(p)) return p;
  return API_BASE + p;
}

module.exports = { request, upload, assetUrl };
