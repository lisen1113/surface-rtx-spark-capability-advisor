Page({
  onShow() {
    wx.showShareMenu({ menus: ['shareAppMessage', 'shareTimeline'] });
  },
  onShareAppMessage() {
    return {
      title: '上海以和信息技术｜Surface 能力顾问',
      path: '/pages/home/index'
    };
  },
  onShareTimeline() {
    return {
      title: '上海以和信息技术｜Surface 能力顾问',
      query: ''
    };
  }
});
