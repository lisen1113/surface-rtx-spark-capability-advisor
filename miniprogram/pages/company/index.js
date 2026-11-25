Page({
  data: { companyUrl: 'https://yiheit.net/' },
  onShow() {
    wx.showShareMenu({ menus: ['shareAppMessage', 'shareTimeline'] });
  },
  onShareAppMessage() {
    return { title: '上海以和信息技术｜走进以和', path: '/pages/home/index' };
  },
  onShareTimeline() {
    return { title: '上海以和信息技术｜走进以和', query: '' };
  },
  onWebViewError(error) {
    console.warn('公司官网加载失败', error.detail);
    wx.showToast({ title: '官网加载失败，请检查网络或业务域名', icon: 'none' });
  }
});
