Page({
  data: { guestUrl: 'https://surfacedmp.com/guest' },
  onWebViewError(error) {
    console.warn('游客体验页面加载失败', error.detail);
    wx.showToast({ title: '页面加载失败，请检查网络或业务域名', icon: 'none' });
  }
});
