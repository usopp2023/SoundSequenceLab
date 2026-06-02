// 录音封装：wx.getRecorderManager()。对应原型 toggleRec 的真机实现。
// 录完得到本地音频临时文件，上传后端做（占位）识别 + 情绪分析。
const { upload } = require('./request');

function createRecorder() {
  const mgr = wx.getRecorderManager();
  return mgr;
}

// 申请麦克风授权
function ensureAuth() {
  return new Promise((resolve, reject) => {
    wx.getSetting({
      success(res) {
        if (res.authSetting['scope.record']) return resolve(true);
        wx.authorize({
          scope: 'scope.record',
          success: () => resolve(true),
          fail: () => reject(new Error('未授权麦克风'))
        });
      },
      fail: reject
    });
  });
}

// 上传录音到后端 /api/upload，返回 { text }（占位 ASR 结果，可编辑）
function uploadAudio(filePath, extra = {}) {
  return upload('/api/upload', filePath, extra);
}

module.exports = { createRecorder, ensureAuth, uploadAudio };
