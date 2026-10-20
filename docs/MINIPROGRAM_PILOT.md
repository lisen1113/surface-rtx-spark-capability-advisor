# 微信小程序内嵌试点

第一阶段只用 `web-view` 打开 `https://surfacedmp.com/account`，沿用现有邮箱/密码、审批、License 与管理员 MFA；不使用 AppSecret，不接入微信免登，不把访问令牌放入 URL。小程序 AppID 不是密码，但不要把 AppSecret 或登录验证码提交到仓库或聊天。

## 配置与测试

1. 确认小程序主体有 `web-view` 业务域名配置权限。在微信公众平台的开发设置中添加 `surfacedmp.com`，按控制台要求将下载的校验文件原样放在网站根路径，并从公网核对文件返回 200、内容与文件名完全一致。不要把校验文件放在仓库或开放任意文件上传；校验完成后依平台要求管理该文件。
2. 在微信开发者工具中导入 `miniprogram/`。将 `project.config.example.json` 复制为本地 `project.config.json`，只替换为已申请的小程序 AppID。`project.config.json` 不提交。不要以开发工具的“忽略域名校验”作为正式验收。
3. 用 iOS 和 Android 微信真机分别验证：打开账号页、登录、返回顾问、刷新后的会话、退出、过期 License 拒绝、FAQ、SKU 切换、报告 PDF。现有 PDF 通过受保护 API 获取后由网页 Blob 下载；微信内保存/预览是否可用尚未实测，未通过前不要承诺该功能在小程序内可用。
4. 验证报告弹窗、`window.print()`、外部来源链接、返回键、键盘遮挡、长表格和横屏。失败项记录机型、微信版本、系统版本、时间及脱敏错误；不要记录密码、令牌或客户原始数据。
5. 仅在真实业务域名、HTTPS、真机登录与访问控制通过后提交试点版本审核。此阶段仍是员工与内部代理商受限试点，不扩大为公开自助注册。

第二阶段若需在微信内可靠保存报告，应增加受保护的原生下载/预览桥接，并针对短期一次性下载授权、文件清理和分享范围做安全设计；不能将现有 Bearer 令牌拼接进 URL。微信免登也应另行设计服务端账号绑定与撤销流程。

参考：[微信 `web-view` 组件](https://developers.weixin.qq.com/miniprogram/dev/component/web-view.html)、[腾讯云业务域名配置说明](https://cloud.tencent.com/document/product/1301/100434)。
