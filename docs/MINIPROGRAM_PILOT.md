# 微信小程序内嵌试点

第一阶段首页分为三个入口：公开官网通过 `web-view` 打开 `https://yiheit.net/`；游客体验打开 `https://surfacedmp.com/guest`，仅提供公开配置与能力映射；内部能力顾问通过另一 `web-view` 打开 `https://surfacedmp.com/account`，沿用现有邮箱/密码、审批、License 与管理员 MFA。非管理员可在私人设备勾选“保持登录 7 天”：服务端会话由 HttpOnly、SameSite=Strict Cookie 恢复，密码不会写入小程序缓存；退出、重置密码、License 失效或会话到期后不能恢复。管理员始终需要重新登录。不使用 AppSecret，不接入微信免登，不把长期访问令牌放入 URL。小程序 AppID 不是密码，但不要把 AppSecret 或登录验证码提交到仓库或聊天。

## 配置与测试

1. 确认小程序主体有 `web-view` 业务域名配置权限。在微信公众平台的开发设置中添加 `surfacedmp.com`，按控制台要求将下载的校验文件原样放在网站根路径，并从公网核对文件返回 200、内容与文件名完全一致。不要把校验文件放在仓库或开放任意文件上传；校验完成后依平台要求管理该文件。
2. 在微信开发者工具中导入 `miniprogram/`。将 `project.config.example.json` 复制为本地 `project.config.json`，只替换为已申请的小程序 AppID。`project.config.json` 不提交。不要以开发工具的“忽略域名校验”作为正式验收。
3. 确认 `yiheit.net` 与 `surfacedmp.com` 均已配置为小程序的 `web-view` 业务域名；将 `surfacedmp.com` 同时配置为 `downloadFile` 合法域名。若官网跳转到其他主机名，须先核实最终 URL 是否在允许范围内。受保护网页先签发 90 秒、单次使用的 PDF 下载票据；小程序原生页通过 `wx.downloadFile` 下载并用 `wx.openDocument` 预览。票据不是账号 Bearer 令牌。生产 PostgreSQL 先运行仓库 `backend/sql/auth_postgres_v1.sql` 的幂等建表语句，确认 `pdf_download_tickets` 表存在，再部署本版本后端与小程序体验版；不能只上传小程序代码。
4. 用 iOS 和 Android 微信真机分别验证：首页三个入口、公开官网的实际跳转地址、游客产品切换与四个能力模块、内部账号页、登录、关闭并重新进入小程序后的恢复、返回顾问、退出、过期 License 拒绝、FAQ、SKU 切换、内嵌报告预览、PDF 原生预览及右上角保存菜单。模拟器不算真机验收；微信文件预览和保存行为尚未双平台实测，未通过前不要承诺已保存。
5. 验证外部来源链接、返回键、键盘遮挡、长表格和横屏。失败项记录机型、微信版本、系统版本、时间及脱敏错误；不要记录密码、票据、令牌或客户原始数据。
6. 仅在真实业务域名、HTTPS、真机登录与访问控制通过后提交试点版本审核。此阶段仍是员工与内部代理商受限试点，不扩大为公开自助注册。

原生预览页是试点实现，用户是否能保存到目标位置取决于真机微信的文件菜单；不要把网页 Blob 的点击动作当成下载成功。微信免登仍需另行设计服务端账号绑定与撤销流程。

参考：[微信 `web-view` 组件](https://developers.weixin.qq.com/miniprogram/dev/component/web-view.html)、[腾讯云业务域名配置说明](https://cloud.tencent.com/document/product/1301/100434)。
