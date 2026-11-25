Page({
  data: { surfaceUrl: 'https://surfacedmp.com/surface' },
  onWebViewError() {
    wx.showToast({ title: '页面加载失败，请检查网络', icon: 'none' });
  }
});
