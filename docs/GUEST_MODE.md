# RTX Spark 完整游客顾问

2026-11-08 用户明确授权：RTX Spark 产品顾问能力全部开放，无需注册。服务器设置 `CAPABILITY_PUBLIC_ADVISOR=1`；保留 `CAPABILITY_REQUIRE_AUTH=1`，两者用途独立。关闭公开顾问开关即可恢复原顾问授权边界。

`/guest` 重定向到 `/?advisor=public`。首页和小程序原有游客入口进入同一完整顾问，可查看 11 个配置、按用途推荐、AI 模型、游戏、生成式 AI、生产力、部署、知识库、TCO、证据限制及客户报告。原 `/api/guest/*` 精简投影为兼容旧客户端保留；新页面直接使用完整顾问接口。

公开接口包括 `/api/catalog/imported-skus`、`/api/catalog/models`、`/api/catalog/advisor/{pn}`、推荐、内存估算、知识库、部署、TCO、顾问 HTML/PDF 报告及移动 PDF 票据。公开列表、能力接口、推荐、HTML/PDF 均移除内部 ERP 价格、原始配置、内部备注与导入指纹；推荐不使用内部价格筛选，预算仅供后续沟通。TCO 采购价由客户填写，初始 0 元仅为空白占位，不能用于判断节省。管理、客户资料、商业后台、导入及原始来源台账不属于公开顾问；Surface 查询授权边界保持原状。

小程序顾问 PDF 通过原有原生下载页面，使用随机 90 秒单次票据，不绑定账号，过期、使用后或服务重启后失效。票据表在进程内有容量限制和互斥保护；当前单进程部署适用，多进程部署须迁移到共享票据存储。原有登录用户票据继续验证原 License。Surface 查询 PDF 仍走授权逻辑。

仅调整共用网页和服务端，不改变原生 URL 与下载契约，无须重新上传小程序包。微信审核及正式发布仍由既有版本流程处理；本轮浏览器模拟不能替代 iOS/Android 真机验收。

验证：后端 `pytest` 193 项通过、1 项跳过；`scripts/test-public-advisor-browser.cjs` 在全新匿名浏览器检查 11 个 SKU、8 个栏目、HTML 预览、PDF 及单次移动票据。`scripts/verify-public-guest.py https://surfacedmp.com` 检查完整游客入口、兼容投影和管理员边界。能力数据仍区分官方平台资料、工程估算和未知，不新增 FPS 或 Token/s 实测承诺。

增量发布采用 `deploy/update_workplace.py archive.zip sha256 --public-advisor`：先备份和副本预检，再安装代码并开启独立开关，失败恢复原代码及环境文件。数据库、用户和既有参数不替换。