Page({
  data: { surfaceUrl: 'https://surfacedmp.com/account?next=%2Fsurface' },
  onWebViewError() {
    wx.showToast({ title: '页面加载失败，请检查网络', icon: 'none' });
  }
});
