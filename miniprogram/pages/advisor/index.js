Page({
  data: { advisorUrl: 'https://surfacedmp.com/account' },
  onWebViewError(error) {
    console.warn('能力顾问网页加载失败', error.detail);
    wx.showToast({ title: '页面加载失败，请检查网络或业务域名', icon: 'none' });
  }
});
