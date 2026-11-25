Page({
  data: { status: '正在下载受保护的 PDF 报告…' },
  onLoad(options) {
    const ticket = String(options.ticket || '');
    const filename = String(options.filename || '');
    const workplace = options.kind === 'workplace';
    const namedFile = /^Surface-(?:Product|Laptop-Ultra-Capability|Workplace-Budget)-[A-Za-z0-9_-]{1,80}\.pdf$/.test(filename);
    if (!/^[A-Za-z0-9_-]{20,128}$/.test(ticket)) {
      this.setData({ status: '报告授权无效，请返回顾问重新生成。' });
      return;
    }
    wx.downloadFile({
      ...(namedFile ? { filePath: wx.env.USER_DATA_PATH + '/' + filename } : {}),
      url: (workplace ? 'https://surfacedmp.com/api/commercial/public/budget-download/' : 'https://surfacedmp.com/api/reports/mobile-download/') + encodeURIComponent(ticket),
      success: (result) => {
        const filePath = result.filePath || result.tempFilePath;
        if (result.statusCode !== 200 || !filePath) {
          this.setData({ status: '报告授权已过期或下载失败，请返回顾问重试。' });
          return;
        }
        wx.openDocument({
          filePath,
          fileType: 'pdf',
          showMenu: true,
          success: () => this.setData({ status: '已打开 PDF。可使用预览页右上角菜单保存；关闭预览后返回顾问。' }),
          fail: () => this.setData({ status: 'PDF 已下载，但无法打开预览。请返回顾问重试。' })
        });
      },
      fail: () => this.setData({ status: '下载失败。请检查小程序 downloadFile 合法域名是否包含 surfacedmp.com。' })
    });
  },
  goBack() { wx.navigateBack(); }
});
