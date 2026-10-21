Page({
  data: { companyUrl: 'https://yiheit.net/' },
  onWebViewError(error) {
    console.warn('公司官网加载失败', error.detail);
    wx.showToast({ title: '官网加载失败，请检查网络或业务域名', icon: 'none' });
  }
});
