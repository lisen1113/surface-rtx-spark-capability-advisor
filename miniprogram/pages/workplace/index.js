Page({
  data: { workplaceUrl: 'https://surfacedmp.com/workplace' },
  onShow() { wx.showShareMenu({ menus: ['shareAppMessage', 'shareTimeline'] }); },
  onShareAppMessage() { return { title: 'Surface AI Workplace租赁及订阅', path: '/pages/home/index' }; },
  onShareTimeline() { return { title: 'Surface AI Workplace租赁及订阅', query: '' }; },
  onWebViewError() { wx.showToast({ title: '页面加载失败，请检查网络或业务域名', icon: 'none' }); }
});
