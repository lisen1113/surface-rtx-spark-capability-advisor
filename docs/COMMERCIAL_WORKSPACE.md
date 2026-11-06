# Surface 与 M365 Copilot 本地商业工作台

本模块在现有 FastAPI 应用中增加独立客户入口 `/workplace`，无需登录即可按功能选型、浏览全部目录、计算预算和下载 PDF。管理入口为 `/workplace/admin`，管理员登录后维护价格、成本比例、汇率、税率、租赁政策和 Azure 合同。客户资料和正式报价接口继续受保护。2026-11-06 经用户授权部署到 surfacedmp.com，小程序新开发版本已上传；详见 [发布记录](WORKPLACE_RELEASE_2026_11_06.md)。

## 已确认业务口径

| 对象 | 成本及报价规则 |
|---|---|
| M365 / Copilot | 美元公开标准价为基数，内部成本为其 85%，客户按公开标准价报价，不自动套用促销 |
| Surface | 采购成本＝ERP 原价 × 管理员成本比例（默认 100%）；保留原价、折扣与折后成本，不修改 ERP / ADR |
| 硬件月租 | 12 / 24 / 36 月系数固定为 1.15 / 1.30 / 1.45；总租金＝采购成本 ×（计价系数 − 品牌残值比例） |
| 品牌残值 | Surface、Apple、Think 分别配置三种租期残值；初始 50% / 40% / 30% 是原表通用示例，不是品牌评估结果 |
| 整体优惠 | 项目总额单独扣减，保留优惠说明和审批记录；不改变产品基准价 |
| 汇率及税费 | 管理员发布汇率、日期、对外依据与软件税率；客户无须输入，不能把人民币换算视为原始美元价 |
| 软件周期 | 本次工作簿为年度承诺、年付；月价是月均参考，不能作为月付合同 |
| Azure / cowork | 另签合同，明确服务、Azure 订阅、计量项目及单价，按实际用量计算独立美元账单 |

客户资料包括使用公司、可选的香港公司、地址、电话、域名、负责人邮箱、银行账户及开票资料。签约、付款、使用和开票公司可以不同。银行资料加密保存，不进入客户报价 PDF、报价快照的公开部分或审计日志。

## 本地启动

在仓库根目录执行。默认使用项目已有虚拟环境。

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
.\backend\.venv\Scripts\python.exe .\scripts\prepare-commercial-local.py
.\backend\.venv\Scripts\python.exe .\scripts\import-cloud-prices.py '<用户提供的价格表绝对路径>' --database .\.commercial-local\commercial.sqlite3
.\backend\.venv\Scripts\python.exe .\scripts\prepare-commercial-public.py
.\backend\.venv\Scripts\python.exe .\scripts\serve-commercial-local.py --port 8020
```

客户打开 <http://127.0.0.1:8020/workplace>，不需要账号。管理员打开 <http://127.0.0.1:8020/workplace/admin>。原预览随机账号保存在 `.commercial-local/credentials.json`。

本次修复将身份库与商品目录分开：`prepare-commercial-public.py` 首次把 `data/capability.sqlite3` 的旧本地身份完整备份至 `.commercial-local/identity.sqlite3`，保留密码哈希、审批、邮箱验证、组织授权和 MFA；再合并此前独立预览库中不重复的注册账号及组织。已有目标身份库不覆盖，原库不写入。MFA 与用户编号相关的独立预览管理员若需要重映射，会停止迁移而不移除 MFA。需要原有 MFA 主密钥才能沿用其动态码；不会绕过验证。服务器上独有、尚未同步到本地的账号不在此副本中。未验证邮箱、待审批或授权过期账号仍返回对应原因，客户选型不受这些账号状态影响。

新的 `.commercial-local/commercial-public.sqlite3` 从旧商业库只复制价格来源和政策，不混入旧组织编号的客户资料或报价；旧库保留。预览设置初始为示例汇率 7.2、软件税率 0、成本比例 0.85，租赁仍使用未正式确认的试算政策，管理员应确认后发布。重新运行准备脚本不会覆盖已经发布的参数。

本轮已准备的预览库包含 237 条原始查询记录，其中 11 条 NVIDIA 记录仍在数据层保留；原有 11 条 RTX Spark 能力记录完整保留。新增租赁入口排除 NVIDIA / RTX Spark。租赁设备、配件和延保按类别分组，配件和延保不能单独充当设备租赁方案。

本轮从用户工作簿导入 14 项软件产品，原始工作表、公式文本、来源行、文件名及 SHA-256 保存在独立本地商业库。脚本默认导入草稿，不信任源表中的 `Approved`、不套用促销价；相同文件重复导入不会新增价格版本。本轮独立预览库已启用这些来源价格，供本地功能验收；没有宣称重新核验了微软当前网站价格。

本次预览已切换为用户提供的《硬件租赁费用计算示例表.docx》常规算法。管理员在“硬件租赁计算规则”中调整三品牌残值和 Surface ERP 成本比例，点击“保存并应用”。成本比例初始为 100%，未擅自给定实际采购折扣。旧 8% 资金成本与 20% / 10% 残值的 PMT 政策仅保留为历史版本，不与新系数叠加。新规则在正式条款核验前仍为预算用途。

参考文件 SHA-256：`936e5e433f5317aa04722920afbcf4342d9ebbdf581b7065e28843d95f02c77b`。只采纳用户授权的计算规则；文档末尾拆分资金、利润、风险的建议没有作为额外费用实施。当前产品仍来自已有 ERP，未添加未提供数据的 Apple / Think 机型。

## 客户与内部操作

1. 客户直接打开独立页面，选择桌面办公、安全管理、Copilot 等功能，填写团队人数与实际 AI 用户数。推荐按普通办公与 AI 用户分组，比较满足相同功能与人数的已发布 Business 标准价；默认选择最低预算。Bundle 直接呈现在推荐区，基础许可与附加许可的较贵备选折叠展示；完整目录仍可查询两款套餐。
2. 筛选 Surface 形态、内存、配置或料号，选择 12 / 24 / 36 月和数量，也可只选设备或只选订阅。配件需随设备添加。
3. 右侧查看分项预算，直接修改项目数量、移除项目；可查看逐月付款计划及下载带预算标识的 PDF。
4. 客户选择 Azure 仅表示独立服务需求，不并入固定预算，也不自动开通。特殊优惠需后续按整个客户项目评估。
5. 管理员登录独立后台，发布汇率、税率、软件成本比例及当前租赁政策。政策和价格均保留版本；新参数立即作用于下一次预算计算。
6. 匿名预算不保存客户资料、账户或报价记录；小程序原生下载临时保存 PDF 供 90 秒内一次领取，领取后删除，过期条目在下次签发时清理。正式订购时另行收集公司、香港公司、地址、电话、域名、负责人邮箱、公司银行账户和开票资料，并核验许可资格。
7. 原有受保护的客户资料、报价保存、审批和正式签发 API 保留，尚未在匿名页面开放提交。已签发文件保持原快照，不随参数更新重写。

许可资格未确认、使用试算政策、已过期、源价格版本失效或当前 ERP 记录变更的方案，不能直接批准签发。管理员应要求客户复制方案、补充核验信息并按当前数据创建新版本。已签发报价仍保持历史快照。

正式商务依据必须明确供应方法定信息、付款、税务、租赁归还、提前终止及损坏责任等合同条款，不能只填写“已审批”。系统保存依据并显示在正式文档中，实际合同文本由业务负责人维护。

### 订阅组合推荐

未选 Copilot 时只推荐满足办公功能的基础订阅。选择 Copilot 后，只给实际 AI 用户配置 AI 许可，普通用户单独选择最低价且满足功能的基础版本；对 AI 用户同时比较单独增购及 Standard / Premium Bundle，不假定 Bundle 永远更便宜。需要设备安全管理时，所有用户均满足 Premium 档功能要求；没有选择安全管理时，Premium 作为可选升级说明增量费用。相同产品的不同用户组在展示中合并席位，实际报价仍保留用户组边界，防止重复许可。

以当前表价、10 人团队和 3 个 AI 用户为例：完整桌面办公推荐 Standard 7 人 + Standard/Copilot Bundle 3 人，月均 USD 168.50，较最低单独增购方案每年省 USD 414；只需网页办公时为 Basic 7 人 + Standard/Copilot Bundle 3 人，月均 USD 119.50；全员需要安全管理则 Premium 7 人 + Premium/Copilot Bundle 3 人，月均 USD 250。已有合格基础许可则仅增加 Copilot 3 人，月均 USD 63。所有金额来自已发布标准价，不套用促销；许可资格和市场仍需正式核验。超过 300 人转 Enterprise 人工核验，不宣称全产品库最优。

## 金融计算边界

全部金额和资金参数使用 `Decimal`，金额四舍五入至分。旧 ERP 库的 REAL 字段只读，通过字符串转 Decimal 后形成独立报价快照，未改写既有字段类型。

当前 `fixed-term-v1` 采用：采购成本＝ERP 原价 × 成本比例（Surface 可折扣，其他品牌按原价）；租赁总额＝采购成本 ×（固定租期系数 − 品牌及租期残值比例）；月租＝总额 ÷ 期数。采购成本保留分位，总租金按原式计算后保留分位，常规月租四舍五入至分，末期＝总额 − 前期租金合计。例如 319.44 × 36 比 11,500 少 0.16 元，末期补足。数量按单台计算后相乘，目录、报价、付款和 PDF 共用计算。配件和延保使用固定系数，残值为零；可识别为 Surface 的硬件同样使用 Surface 成本比例。

固定系数已包含资金、利润和风险因素，不另加资金、管理、处置费用。新规则内部 NPV 使用零折现率，仅作现金合计比较，快照中明确口径。历史 PMT 政策继续按原资金现值法重现；12 月只支持新规则。历史已保存、签发的报价和文件均不重算。

内部输出软件年度成本及标准毛利、项目现金流、NPV、IRR、资金占用和回本月份。IRR 存在多次现金流符号变化、无法确认唯一值时返回空值，不强给收益率。压力情景把期末净残值降为零。

“项目现金贡献”包含净残值，尚未扣除独立服务人工成本和设备租赁税负调整，不应称为完整会计毛利。正式审批需要财务核对这些项目。多期软件合同默认用当前标准价估算续订；跨年锁价必须另录依据，由审批人核验。

## 权限与数据存储

- `/public/*` 只提供公开目录、推荐及无状态预算，不需要登录；采用字段白名单，不输出 ERP 单价、成本比例或资金参数。其他业务接口继续复用登录、组织授权和管理员 MFA。
- 客户注册接口 `/api/commercial/register` 创建 `customer_owner`，仍需邮箱验证、管理员审批和 License。内部原有注册保持 `owner`。
- 受保护部署中，`customer_owner` / `customer_member` 不能访问原有内部 ERP、能力报告和成本查询入口。原有内部 `owner` / `member` 的权限保持原样。
- 公司银行资料仅组织负责人及管理员可读取。组织成员只能读取去除银行字段的资料。
- 商业记录单独存放，默认 `data/commercial-local.sqlite3`；当前预览使用 `.commercial-local/commercial-public.sqlite3`，身份使用 `.commercial-local/identity.sqlite3`，目录已被 Git 忽略。`CAPABILITY_AUTH_SQLITE_PATH` 可独立指定 SQLite 身份库，配置不存在的路径会报错，不回退到空账号库。生产 PostgreSQL 身份配置优先级保持不变。
- SQLite 写入使用事务与串行化检查，避免重叠价格发布、重复签发和重叠用量账期并发通过。
- 本地加密密钥首次使用时生成在商业库同目录的 `.key` 文件，不进入 Git。共享或公网部署必须从环境提供 `CAPABILITY_COMMERCIAL_KEY`，不自动生成密钥。数据库备份与密钥需分开保存，丢失原密钥无法解密客户资料。
- 共享或公网部署默认关闭商业模块，需要显式配置 `CAPABILITY_COMMERCIAL_ENABLED=1`；不能直接把本地预览服务开放到公网。

主要表：`cloud_prices`、`commercial_imports`、`lease_policies`、`commercial_profiles`、`commercial_quotes`、`commercial_documents`、`azure_contracts`、`azure_usage` 和 `commercial_audit`。新增表没有覆盖 `sku_lookup` 或 `imported_skus`。

## 接口分组

所有业务接口以 `/api/commercial` 开头。

| 路径 | 用途 |
|---|---|
| `GET /public/catalog` | 匿名查询全部对客产品及发布的换算参数 |
| `POST /public/recommendations` | 按功能与席位匹配标准价组合 |
| `POST /public/estimate`、`POST /public/budget.pdf` | 匿名无状态预算，不接受成本、汇率、优惠等财务覆盖 |
| `GET/PUT /admin/settings` | 管理员维护并发布预算参数版本 |
| `GET/PUT /admin/rental-rules` | 品牌残值、Surface ERP 成本比例；计价系数固定，保存时发布新政策并切换预算配置 |
| `GET /products`、`GET /hardware` | 客户产品目录，不返回内部成本 |
| `POST /recommendations`、`POST /cloud-recommendations` | 设备筛选及软件组合比较 |
| `GET /policies`、`POST /estimate` | 可用政策名称和预算计算 |
| `GET/PUT /profile` | 组织客户资料 |
| `GET/POST /quotes`、`GET /quotes/{id}` | 保存及读取不可变方案快照 |
| `GET /quotes/{id}/inputs` | 复制原配置，再按新价格保存 |
| `POST /quotes/{id}/submit` | 提交正式报价申请 |
| `GET /quotes/{id}/document.pdf` | 预算或已签发正式文档，授权后下载 |
| `/admin/prices`、`/admin/prices/{id}/publish` | 草稿、发布、替换及历史价格版本 |
| `/admin/policies` | 新增政策版本及内部参数查询 |
| `/admin/profiles/{organization_id}` | 授权管理员核验客户银行及开票资料，读取留痕 |
| `/admin/quotes/{id}`、`/review`、`/issue` | 内部测算、审批与签发 |
| `/azure/contracts`、`/azure/{id}/usage` | 组织独立合同与用量账单 |
| `/admin/azure/{organization_id}/contracts` | 登记已签合同，不自动创建 Azure 资源 |
| `/admin/azure/{contract_id}/usage` | 按合同单价登记实际用量，拒绝账期重叠 |
| `/admin/audit` | 内部操作审计，不含银行资料 |

同一 Azure 合同可以分别登记输入、输出等不同计量项目的单价；同一组织、合同和计量项目不能重复登记，重叠账期按各计量项目分别检查。

## 验证

本轮完整后端回归：187 项通过、1 项跳过；跳过项是没有配置外部 PostgreSQL 测试连接的既有集成测试。使用隔离回归库，未在原数据库运行测试写入。新规则覆盖文档两组示例、三品牌差异、ERP 折扣、固定系数不可覆盖、末期尾差、匿名信息隔离及历史快照保留。

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial.py tests/test_commercial_public.py -q --basetemp=./.pytest-commercial-check
```

`scripts/test-commercial-public-browser.cjs` 使用 Playwright，对仅限本机的服务执行真实浏览器验收。可通过 `CAPABILITY_PLAYWRIGHT_MODULE` 指定现有 Playwright 安装，通过 `CAPABILITY_BROWSER_EXECUTABLE` 指定 Edge。脚本不自动安装浏览器、不输出密码。检查匿名选型、设备与配件、租期与数量调整、付款计划、PDF 下载、手机布局、管理员及原预览测试账号登录，以及后台参数发布后公开接口使用新配置；测试后恢复参数。原 `test-commercial-browser.cjs` 对应旧版登录工作台，当前不作为验收入口。

验证截图、预算样例和浏览器结果放在被忽略的 `artifacts/commercial/`，不作为生产文件上传。原始桌面 Word/Excel、同步 `sources/` 文件、开发账号、加密密钥和数据库均未写入 Git。

`scripts/test-rental-rules-browser.cjs` 用本地实际管理员验证三品牌残值、ERP 折扣的保存及重新载入，检查匿名客户 12 / 24 / 36 月目录价格、预算与付款总额、PDF 和手机布局；结束后恢复原参数。截图和 PDF 是测试期间的 90% 成本、55% / 45% / 35% Surface 残值示例，并非最终默认参数。

## 更新 GitHub 和服务器前

本地业务流程完成不等同于已经具备真实交易参数。以下项目需要业务配置和发布验收：

1. 已确认的资金成本、残值、服务成本、设备租赁税务与最终合同条款。
2. 人民币汇率来源、软件适用税率、跨年锁价安排及实际软件许可资格。
3. Azure/cowork 对应的确切服务、合同和计量项目。当前实现人工登记，不自动消费 Azure，不自动扣款。
4. 将商业库、正式文档和客户资料密钥纳入服务器备份恢复，配置商业数据库持久化路径和专用加密密钥。
5. 更新隐私告知以覆盖银行和开票资料，核对新增客户角色在目标部署中的注册、授权、MFA 和接口隔离。
6. 在独立环境演练发布、数据初始化和回退，再审阅本轮改动后更新 GitHub 和服务器。关闭商业功能即可隐藏入口及拒绝业务访问，历史数据保留。

本轮没有自动下单、自动电子签约、自动开通 Azure、支付或完整租赁资产台账。

