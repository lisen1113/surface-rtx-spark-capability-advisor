Page({
  data: { guestUrl: 'https://surfacedmp.com/guest' },
  onShow() {
    wx.showShareMenu({ menus: ['shareAppMessage', 'shareTimeline'] });
  },
  onShareAppMessage() {
    return { title: '上海以和信息技术｜Surface 能力顾问', path: '/pages/home/index' };
  },
  onShareTimeline() {
    return { title: '上海以和信息技术｜Surface 能力顾问', query: '' };
  },
  onWebViewError(error) {
    console.warn('游客体验页面加载失败', error.detail);
    wx.showToast({ title: '页面加载失败，请检查网络或业务域名', icon: 'none' });
  }
});
