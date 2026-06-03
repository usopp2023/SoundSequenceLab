const { uploadAudio } = require('../../utils/recorder');
const nav = require('../../utils/nav');

const QUESTIONS = [
  { idx: '第 1 个问题 / 共 3 个', text: '此刻在阿那亚，你最想待着的是什么时间？', hint: '清晨、黄昏，还是深夜的海边？', ph: '随便写写，不用想太多……' },
  { idx: '第 2 个问题 / 共 3 个', text: '最近有没有什么事，一直放在心里、没怎么跟人说？', hint: '不用具体，写个大概的感觉也行。', ph: '写下心里的那件事……' },
  { idx: '第 3 个问题 / 共 3 个', text: '有没有一句话，你一直想对某个人说，却始终没说出口？', hint: '不用是什么大事——可能只是一个具体的瞬间，一个具体的人。', ph: '那句没说出口的话……' }
];

Page({
  data: {
    statusBar: 20,
    questions: QUESTIONS,
    qi: 0,
    q: QUESTIONS[0],
    mode: 'voice',           // 'voice' | 'type'
    nextLabel: '下一题',
    // 语音态
    recording: false,
    showTimer: false,
    recSecLabel: '00:00',
    voiceHint: '点击麦克风，说说就好',
    showResult: false,
    voiceText: '',
    // 打字态
    typeText: '',
    // 「下一题」是否可点（当前题有输入才可，#1）
    canNext: false
  },

  onLoad() {
    const info = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    this.setData({ statusBar: info.statusBarHeight || 20 });
    if (!getApp().globalData.quizAnswers) getApp().globalData.quizAnswers = [];
    this.recSec = 0;
    this.recTimer = null;
    this.initRecorder();
    this.renderQ();
  },

  initRecorder() {
    const mgr = wx.getRecorderManager();
    this.recorder = mgr;
    mgr.onStop((res) => {
      this.stopTimer();
      this.setData({ recording: false, voiceHint: '识别中…' });
      // 上传音频，后端（占位）返回识别文字
      if (res && res.tempFilePath) {
        uploadAudio(res.tempFilePath, { q: this.data.qi })
          .then((r) => {
            this.setData({
              showResult: true,
              voiceText: (r && r.text) || '（这里是识别出来的文字，可以修改…）',
              voiceHint: '识别完成，可点麦克风重录'
            });
            this.updateNextState();
          })
          .catch(() => {
            // 后端不可用时的占位识别结果（与原型一致）
            this.setData({
              showResult: true,
              voiceText: '（这里是识别出来的文字，可以修改…）',
              voiceHint: '识别完成，可点麦克风重录'
            });
            this.updateNextState();
          });
      }
    });
    mgr.onError(() => {
      this.stopTimer();
      this.setData({ recording: false, voiceHint: '录音失败，点麦克风重试' });
    });
  },

  renderQ() {
    const q = QUESTIONS[this.data.qi];
    // 恢复该题之前的答案（#2 答案数据链）
    const saved = (getApp().globalData.quizAnswers || [])[this.data.qi];
    const savedText = saved && saved.text ? saved.text : '';
    this.setData({
      q,
      nextLabel: this.data.qi === QUESTIONS.length - 1 ? '完成，生成我的曲子' : '下一题',
      recording: false, showTimer: false, recSecLabel: '00:00',
      voiceHint: savedText ? '识别完成，可点麦克风重录' : '点击麦克风，说说就好',
      showResult: !!savedText,    // 语音模式下回显识别区
      voiceText: savedText,
      typeText: savedText
    });
    this.recSec = 0;
    this.updateNextState();
  },

  // 当前题是否有输入 → 控制「下一题」可点
  updateNextState() {
    const text = this.data.mode === 'voice' ? this.data.voiceText : this.data.typeText;
    this.setData({ canNext: !!(text && text.trim()) });
  },

  useVoice() { this.setData({ mode: 'voice' }); this.updateNextState(); },
  useType() { this.stopRecIfAny(); this.setData({ mode: 'type' }); this.updateNextState(); },

  onVoiceInput(e) { const v = e.detail.value; this.setData({ voiceText: v, canNext: !!v.trim() }); },
  onTypeInput(e) { const v = e.detail.value; this.setData({ typeText: v, canNext: !!v.trim() }); },

  toggleRec() {
    if (!this.data.recording) {
      this.setData({ recording: true, showTimer: true, recSecLabel: '00:00', voiceHint: '正在聆听…再次点击结束', showResult: false });
      this.recSec = 0;
      this.recorder.start({ format: 'mp3', duration: 60000, sampleRate: 16000, numberOfChannels: 1, encodeBitRate: 48000 });
      this.recTimer = setInterval(() => {
        this.recSec++;
        const m = String(Math.floor(this.recSec / 60)).padStart(2, '0');
        const s = String(this.recSec % 60).padStart(2, '0');
        this.setData({ recSecLabel: m + ':' + s });
      }, 1000);
    } else {
      this.recorder.stop(); // 触发 onStop
    }
  },

  stopRecIfAny() {
    if (this.data.recording) {
      try { this.recorder.stop(); } catch (e) {}
      this.stopTimer();
      this.setData({ recording: false });
    }
  },
  stopTimer() { if (this.recTimer) { clearInterval(this.recTimer); this.recTimer = null; } },

  quizNext() {
    this.stopRecIfAny();
    const text = this.data.mode === 'voice' ? this.data.voiceText : this.data.typeText;
    if (!text || !text.trim()) return;   // 兜底：空答案不放行
    const answers = getApp().globalData.quizAnswers || [];
    answers[this.data.qi] = { q: this.data.qi, text: text || '' };
    getApp().globalData.quizAnswers = answers;

    if (this.data.qi < QUESTIONS.length - 1) {
      this.setData({ qi: this.data.qi + 1 });
      this.renderQ();
    } else {
      // 进入生成页（redirect：让生成/结果替换答题，返回栈保持干净）
      wx.redirectTo({ url: '/pages/gen/gen' });
    }
  },

  quizBack() {
    this.stopRecIfAny();
    if (this.data.qi > 0) {
      this.setData({ qi: this.data.qi - 1 });
      this.renderQ();
    } else {
      // 第一题再返回 = 退出答题，回活动主页
      wx.navigateBack({ delta: 1, fail: () => nav.switchActTab('pages/act-home/act-home') });
    }
  },

  onUnload() { this.stopTimer(); }
});
