"""Customer-facing local model deployment and private-data guide."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse

from .capability import estimate_capacity
from .catalog import connection
from .advisor_access import require_advisor_user
from .platform_display import platform_label
from .branding import apply_theme

router = APIRouter()

# Trial order is an engineering PoC ladder, not an assertion of model support.
TRIAL_LADDERS = {
    24: [(3, 4), (8, 4)],
    32: [(8, 4), (14, 4)],
    48: [(14, 4), (32, 4)],
    64: [(32, 4), (70, 4)],
    128: [(70, 4), (120, 4)],
}


def sku_deployment_plan(sku: dict) -> dict:
    memory = int(sku["memory_gb"] or 0)
    storage = float(sku["storage_tb"] or 0)
    # These explicit reserves are deliberately conservative screening inputs.
    os_reserve = 8 if memory <= 32 else 12
    runtime_reserve = 3 if memory <= 32 else 8
    kv_cache = 2 if memory <= 32 else 8
    trials = []
    for size, bits in TRIAL_LADDERS.get(memory, [(3, 4)]):
        result = estimate_capacity(parameters_billion=size, bits_per_weight=bits,
                                   unified_memory_gb=memory, os_reserve_gb=os_reserve,
                                   runtime_reserve_gb=runtime_reserve, kv_cache_gb=kv_cache)
        trials.append({"size_label": f"{size}B Q{bits}", "required_gb": result.required_gb,
                       "weight_gb": result.weight_gb, "fit": result.fits_in_memory,
                       "compatible": result.compatible, "usable": result.usable})
    if storage <= 0.5:
        storage_note = "0.5TB 配置：先只缓存一个已批准模型及一份小型脱敏测试集；下载前检查剩余空间，避免多个量化副本挤占系统更新和索引空间。"
    elif storage >= 2:
        storage_note = "2TB 配置：可分开存放已批准模型、RAG 索引与测试日志，但仍应设置配额、加密和定期清理，不把容量当作数据授权。"
    else:
        storage_note = "1TB 配置：为模型权重、嵌入索引、临时文件和系统更新分别留余量；先确认实际可用空间，再规划多个模型版本。"
    platform_note = ("CPU/GPU 核心数映射来自项目提供的配置资料，尚需按具体料号与实机核验；"
                     "核对驱动、Windows ARM64 运行时和 GPU 后端，不能把核心数换算成 Token/s。")
    return {
        "part_number": sku["part_number"], "platform_code": sku["platform_code"],
        "platform_label": platform_label(sku["platform_code"]),
        "memory_gb": memory, "storage_tb": storage, "cpu_model": sku["cpu_model"],
        "gpu_model": sku["gpu_model"], "operating_system": sku["operating_system"],
        "evidence_level": "engineering_estimate", "source_reference": sku["source_reference"],
        "assumptions": {"bits_per_weight": 4, "os_reserve_gb": os_reserve,
                        "runtime_reserve_gb": runtime_reserve, "kv_cache_gb": kv_cache,
                        "quantization_overhead_ratio": 0.10, "concurrent_users": 1,
                        "first_context_tokens": 2048},
        "trials": trials, "storage_note": storage_note, "platform_note": platform_note,
        "first_step": "先用已获许可的较小指令模型、单用户和 2048 token 上下文建立基线；每次只增加一个变量。",
        "capacity_boundary": "Q4 参数量仅是筛选代理值；尤其不能把 Nemotron 3.5 Bolt 74B-A9B 的官方 2-bit/24GB 模型包当作普通 74B Q4。MoE 活跃参数、实际权重文件、KV 格式与共享内存分配均可能改变结果。容量适配不证明可启动、GPU 加速、准确性或速度。",
    }


@router.get("/api/deployment/sku/{part_number}")
def deployment_plan(part_number: str, _user=Depends(require_advisor_user)):
    with connection() as conn:
        row = conn.execute("SELECT * FROM imported_skus WHERE part_number=?", (part_number,)).fetchone()
    if not row:
        raise HTTPException(404, "未找到该 Part Number")
    return sku_deployment_plan(dict(row))


@router.get("/deployment", response_class=HTMLResponse)
def deployment_page():
    return apply_theme('''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Surface Laptop Ultra 模型部署</title><style>
body{font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif;color:#172033;background:#f6f8fb;margin:0}header{background:#111d35;color:white;padding:30px max(20px,calc((100vw - 1100px)/2))}main{max-width:1100px;margin:auto;padding:24px}section{background:white;border:1px solid #dce2ec;border-radius:12px;padding:22px;margin:18px 0}h1{line-height:1.25}h2{margin-top:0}li{margin:8px 0}a{color:#175cd3}code,pre{background:#eef3fa;border-radius:5px;padding:2px 5px;overflow:auto}pre{padding:12px;white-space:pre-wrap}.note{border-left:4px solid #b54708;padding:10px 14px;background:#fff8ed}.good{border-left:4px solid #175cd3;padding:10px 14px;background:#eff4ff}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}.card{border:1px solid #dce2ec;border-radius:10px;padding:14px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #dce2ec;padding:9px;text-align:left;vertical-align:top}th{background:#eef3fa}label{display:block;font-weight:600}select{padding:10px;max-width:100%;width:440px}small{color:#586476}footer{text-align:center;padding:24px;color:#586476}
</style><style>@media print{body{background:white;color:#111;font-size:11pt}header{background:white;color:#111;padding:0}main{padding:0;max-width:none}section{box-shadow:none;border:0;border-bottom:1px solid #bbb;border-radius:0;padding:12px 0;margin:0;break-inside:avoid}a{color:#111;text-decoration:none}a::after{content:" (" attr(href) ")";font-size:8pt}header a,.print-action,select,.print-hint{display:none!important}table{font-size:9pt}td,th{padding:5px}.note,.good{background:white!important;color:#111!important}footer{padding:10px}h1,h2,h3{break-after:avoid}@page{size:A4;margin:16mm}}</style></head><body><header><a href="/" style="color:#bcd4ff">← 返回能力顾问</a><h1>Surface Laptop Ultra 本地模型部署与验收</h1><p>面向客户 PoC 的操作手册。请先选择实际料号，再按场景部署；可安装不等于该 SKU 已验证 GPU 加速或性能。</p><button id="print-guide" class="print-action" type="button" disabled>打印报告／另存为 PDF</button><p id="print-filename" class="print-hint"></p></header><main>
<section><h2>1. 锁定设备与目标</h2><label for="sku">实际 Part Number</label><select id="sku"><option>正在读取已导入配置…</option></select><p id="device" class="good" aria-live="polite">加载中…</p><p>记录 Windows 11 Pro 版本、CPU 架构（ARM64/x64）、GPU 与驱动版本、统一内存、可用磁盘、模型文件版本及许可证、运行工具版本。核对系统信息和设备管理器，不要只看产品系列名称。</p><pre>Get-ComputerInfo | Select-Object WindowsProductName,WindowsVersion,OsArchitecture<br>Get-CimInstance Win32_VideoController | Select-Object Name,DriverVersion</pre><p class="note">统一内存不是全部可给模型的显存；系统、图形、运行时、上下文/KV Cache 与其他程序都要预留。不同内存 SKU 须分别测试。这里不预设可运行的参数规模或 Token/s。</p></section>
<section><h2>2. 选部署路线</h2><div class="grid"><div class="card"><h3>个人试用 / 离线演示</h3><p>优先选 LM Studio 图形界面：安装官方 Windows 对应架构版本，在 Discover 选具有明确商用许可的模型与量化，下载后在 Chat 中加载、提问。需要应用接入时再启动本地 API，默认仅本机访问。</p><a href="https://lmstudio.ai/docs/app/basics" target="_blank" rel="noopener">LM Studio 官方入门</a></div><div class="card"><h3>开发集成 / 可复现服务</h3><p>用 Ollama 或 llama.cpp。固定运行时版本、模型文件与量化；先在 127.0.0.1 运行，记录加载日志和实际计算后端，再接入内部应用。llama.cpp 可用 GGUF 和本地 HTTP 服务。</p><a href="https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md" target="_blank" rel="noopener">llama.cpp 官方服务文档</a></div><div class="card"><h3>企业多人 / 较高并发</h3><p>先验证单机服务稳定，再评估独立 Linux GPU 服务器、vLLM、SGLang 或 TensorRT-LLM。Windows ARM64、WSL2、CUDA 和容器镜像支持必须按当前版本逐项实测；不把 Linux 文档当作原生 Windows 支持。</p><a href="/api/knowledge/frameworks">查看已核查的兼容性矩阵</a></div></div></section>
<section><h2>官方战术手册：按目标快速上手</h2><p>先在当前料号完成下方单机基线，再选一条任务路线。这里提供操作入口和验收重点；NVIDIA 的示例时间与模型推荐是官方手册信息，不是本 SKU 的实测结果。</p><div class="grid"><div class="card"><h3>首次使用：Agent 回答一个问题</h3><p>按官方入门手册选择 Agent 与本地模型，先用非敏感样例提问，确认模型实际运行位置。连接工作应用时优先只读权限，写入或发送动作需人工确认。</p><a href="https://build.nvidia.com/rtx-spark/start-with-agent" target="_blank" rel="noopener noreferrer">打开 NVIDIA 首个 Agent 手册</a></div><div class="card"><h3>办公：制作待审核摘要</h3><p>先连接获准的邮件、日历或文档，限定只读与草稿权限；让 Agent 汇总一份待人工核对的日报，不自动发送。</p><a href="https://build.nvidia.com/rtx-spark/agents-for-productivity" target="_blank" rel="noopener noreferrer">打开 NVIDIA 生产力手册</a></div><div class="card"><h3>创作：从素材到输出</h3><p>先确认创作应用和插件版本、素材授权与导出目标，再按官方创作路线验证 GPU 后端、效果质量和稳定性；不承诺特定渲染速度。</p><a href="https://build.nvidia.com/rtx-spark/agents-for-creators" target="_blank" rel="noopener noreferrer">打开 NVIDIA 创作手册</a></div><div class="card"><h3>开发：本地模型与编码代理</h3><p>先核对 Windows ARM64、驱动、模型许可和运行后端。可从 llama.cpp、LM Studio 或 Ollama 选一个；官方开发环境脚本会变更系统并启用 WSL，企业设备应先审查脚本和变更范围。</p><a href="https://build.nvidia.com/rtx-spark/setting-up-your-dev-environment" target="_blank" rel="noopener noreferrer">开发环境手册</a> · <a href="https://build.nvidia.com/rtx-spark/running-llamacpp" target="_blank" rel="noopener noreferrer">本地推理手册</a></div><div class="card"><h3>进阶：PAIR 多机路由</h3><p>单机通过后，在受信任局域网按 PAIR 1.0.0 手册选择 Windows ARM64 安装包与引擎，先发一次本机请求再配对第二节点；每个请求只交给一台设备，不聚合内存。</p><a href="https://build.nvidia.com/rtx-spark/pair" target="_blank" rel="noopener noreferrer">打开 NVIDIA PAIR 手册</a></div></div><p class="note">不要照搬最高配置的模型推荐或直接执行未经审查的远程脚本。安装包、模型与代理连接器须核对签名、许可证、架构和权限；每一步记录版本与失败原因。</p></section>
<section><h2>Agent 连接应用：MCP、CLI 与 Skills</h2><p>NVIDIA 公告介绍 NVIDIA App、Broadcast、PAIR、Omniverse、RTX Remix 等应用的 MCP 连接，以及 CUDA-X Skills。MCP 是让代理调用外部工具的接口；CLI 是命令行入口；Skills 是教代理完成工作流的指引。三者可以协作，但不能互相替代，也不表示应用默认已经连接。</p><ol><li>选一个场景：例如让 Broadcast 处理一段获授权的非敏感录音，或让开发代理查阅 CUDA-X 工具用法。</li><li>核对目标应用、MCP 服务、代理客户端和 Skills 的官方版本与安装来源；先在隔离测试账户中启用。</li><li>先授予只读或草稿权限，只暴露必要目录和工具；任何删除、发送、购买、发布或系统设置更改都要人工批准。</li><li>用脱敏样本验证代理调用记录、输出质量、权限拒绝、网络去向与断开连接后的撤权。</li></ol><p><a href="https://blogs.nvidia.com/blog/local-ai-rtx-spark-laptops-software-updates/" target="_blank" rel="noopener noreferrer">NVIDIA 应用 MCP 公告</a> · <a href="https://github.com/NVIDIA/skills" target="_blank" rel="noopener noreferrer">NVIDIA Skills 官方库</a></p><p class="note">本页不自动安装或启用任何 MCP/Skill；具体功能是否可用取决于应用、代理和发布版本，须在目标设备验证。</p></section>
<section><h2>3. 从空机到第一次回答</h2><ol><li><b>批准软件与模型。</b> 从项目官方站点下载与系统架构一致的安装包；核对签名、哈希、版本、模型权重来源、许可证和商用/再分发权限。不要把客户文件上传到不明模型站点。</li><li><b>建立基线。</b> 更新 Windows、官方固件和 GPU 驱动；保存设备信息，关闭不必要的重负载程序。首次试验使用较小且已获许可的指令模型，记录量化与上下文长度，不以参数规模标签直接推断适配。</li><li><b>安装与加载。</b> LM Studio：Discover 下载 → Chat 选择模型 → 调整上下文和内存配置 → Load → 用非敏感样例提问。llama.cpp：取官方对应架构发布包及兼容 GGUF，在 PowerShell 中用实际模型路径启动：</li></ol><pre>.\\llama-server.exe -m "C:\\Models\\approved-model.gguf" -c 2048 --host 127.0.0.1 --port 8080</pre><ol start="4"><li><b>核对执行后端。</b> 查看日志是否真正使用预期 GPU/加速后端，记录 GPU 占用、系统内存峰值、首次响应与稳定响应。CPU 回退须如实记录；成功回答不等于 GPU 加速。</li><li><b>做三组任务。</b> 通用问答（正确性/中文）、真实业务任务（脱敏材料）、长上下文或多轮（内存和稳定性）。固定提示词、模型版本、量化、上下文、并发、温度和重复次数；记录失败、拒答、幻觉、耗时及电源状态。</li><li><b>验收。</b> 模型许可合法、数据不外传、答案可核查、运行不崩溃、延迟达到客户自定阈值，才标记此设备此配置通过 PoC。任何 Token/s 结论仅属于该测试环境。</li></ol><p class="note">已下载的 LM Studio 模型可离线聊天、文档问答和本地服务，但下载/更新可能联网；本地还须验证嵌入、日志、遥测、插件和调用链均未向外发送私有数据。</p></section>
<section><h2>4. 企业私有数据：先检索，再考虑训练</h2><table><tr><th>目的</th><th>建议路径</th><th>边界</th></tr><tr><td>内部手册、合同、知识库问答</td><td><b>RAG</b>：授权文档 → 脱敏与解析 → 分块/版本标记 → 本地嵌入与索引 → 按用户权限检索 → 附来源片段生成回答。</td><td>文档通常不写入模型权重；仍要保护原件、索引、提示词和日志。更新文档后可重建索引。</td></tr><tr><td>固定语气、格式、分类流程</td><td>先用提示词、模板和少量示例；不足时再评估经许可的 LoRA/PEFT 微调。</td><td>微调会产生派生权重，需数据使用权、隔离、标注质量、评测集和泄漏测试；笔记本能否训练须另做容量与热/电源验证。</td></tr><tr><td>高保密 / 多部门共享</td><td>按身份和文档 ACL 过滤检索结果，审计访问；敏感系统可采用企业内网服务与审批后的混合路由。</td><td>不能先全库检索再让模型自己决定是否透露；模型不是权限边界。</td></tr></table><h3>私有知识 PoC 顺序</h3><ol><li>选一组获授权的代表性文档，剔除密码、密钥和无关个人信息；记录所有者、密级、版本、保留期限。</li><li>选本地嵌入模型与本地向量库；解析 PDF/Office 后抽检表格、扫描件 OCR 和页码，按文档与段落存来源定位。</li><li>查询时先鉴权，用文档/段落级权限过滤，再做关键词与向量检索；只把授权片段送入本地模型。要求引用来源，无证据则回答不知道。</li><li>用真实但脱敏的问答验证命中率、引用正确性、跨部门越权、提示注入、过期文档与无答案场景，记录人工复核。</li><li>通过后再扩大范围，建立增量更新、删除同步、备份与撤销访问流程；涉及云端或外部 API 时单独取得数据处理授权。</li></ol><p class="good">RAG 不是训练；把文件拖进聊天窗口也不代表模型学会了企业知识。微调更适合可重复的任务行为，事实会变的企业知识优先检索。</p></section>
<section><h2>5. 验收记录与风险清单</h2><p>每次测试保存：Part Number、架构、Windows/驱动/工具版本、模型来源与许可证、权重校验值、量化、上下文、后端、并发、电源模式、任务与提示词、正确性与引用、内存峰值、冷/热启动耗时、实际 Token/s（若测得）、失败日志及测试日期。没有测量的数据保持未知。</p><ul><li>仅监听本机地址；若开放给团队使用，必须增加身份验证、TLS、网络边界、限流和审计，不直接把推理端口暴露公网。</li><li>防止提示注入、恶意文档、输出泄密；工具调用和执行代码须单独授权与隔离。</li><li>原件、索引、缓存、调试日志都按企业数据分类、加密、备份、删除及留存策略处理。</li><li>模型权重与运行时升级后重新回归测试；性能与兼容性不能跨 SKU 或软件版本继承。</li></ul><p><a href="https://learn.microsoft.com/en-us/azure/foundry-local/tutorials/tutorial-build-rag-app" target="_blank" rel="noopener">微软本地 RAG 教程</a> · <a href="https://learn.microsoft.com/en-us/azure/search/search-security-best-practices" target="_blank" rel="noopener">微软检索权限与安全建议</a> · <a href="https://lmstudio.ai/docs/app/offline" target="_blank" rel="noopener">LM Studio 离线说明</a></p><small>以上筛选和测试流程属于工程建议，不是微软或 NVIDIA 对特定 SKU 的性能保证。框架兼容性以当前官方文档和目标设备 PoC 为准。</small></section>
<section><h2>6. RTX Spark 软件生态更新（NVIDIA 2026-10-13 公告）</h2><p>以下是平台与软件生态信息，不是所选 Part Number 的安装成功率或性能实测；按已提供、测试版和计划中分别核对实际发布资产。</p><table><tr><th>路径</th><th>部署与验收要点</th></tr><tr><td>Nemotron 3.5 Bolt 74B-A9B</td><td>公告中的约 24GB 指特定 2-bit 量化权重，不含系统、运行时和上下文开销；确认模型许可证、权重哈希、精确量化与所用推理工具版本。不得用本页通用 Q4 表判断该模型一定适配。</td></tr><tr><td>NVIDIA PAIR 多机路由</td><td>NVIDIA PAIR 1.0.0 手册已列出 RTX Spark Windows ARM64 安装包、llama.cpp/Ollama/LM Studio 引擎和受信任局域网配对路径；逐节点验证模型、后端、网络与访问控制。它路由独立请求，不聚合显存，也不拆分单次推理。</td></tr><tr><td>Windows on Arm 开发</td><td>NVIDIA 公告列出原生 PyTorch-CUDA、Python/Conda 路径与 llama.cpp Windows 应用。按当前发布资产核对 ARM64 wheel、CUDA/驱动版本和依赖；生态覆盖率不是任意 Python 包均可安装的保证。</td></tr><tr><td>Agent 沙箱与云路由</td><td>OpenShell/MXC 和本地/云端混合路由属于不同应用、不同版本的功能。先限制工具、文件和密钥权限，用脱敏样本检查实际路由；启用云服务前单独确认客户数据授权、地区和费用。</td></tr></table><p><a href="https://blogs.nvidia.com/blog/local-ai-rtx-spark-laptops-software-updates/" target="_blank" rel="noopener">NVIDIA 发布说明</a> · <a href="https://build.nvidia.com/rtx-spark/pair" target="_blank" rel="noopener">PAIR 1.0.0 官方手册</a> · <a href="https://github.com/ggml-org/Llama-Windows" target="_blank" rel="noopener">llama.cpp Windows 应用</a></p></section>
</main><section style="max-width:1052px;margin:18px auto"><h2>当前 SKU 的试验路线</h2><div id="skuplan" aria-live="polite">正在计算工程筛选起点…</div></section><footer>© 2026 上海以和信息技术有限公司。保留所有权利。 · <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">沪ICP备17029250号-4</a></footer><script>
const sku=document.querySelector('#sku'),out=document.querySelector('#device'),plan=document.querySelector('#skuplan'),printButton=document.querySelector('#print-guide'),fileHint=document.querySelector('#print-filename');
const fetch=(url,options={})=>{const token=sessionStorage.getItem('cap_token');return window.fetch(url,{...options,headers:{...(options.headers||{}),...(token?{Authorization:'Bearer '+token}:{})}})};
const brandLogo='<img src="/assets/yihe-logo.png" alt="上海以和信息技术有限公司" style="display:block;width:min(240px,70vw);height:auto;background:white;border-radius:6px;padding:5px;margin-bottom:18px">';
document.querySelector('header').insertAdjacentHTML('afterbegin',brandLogo);
const originalTitle=document.title;
function reportTitle(){return 'Surface-Laptop-Ultra-Deployment-'+sku.value.replace(/[^A-Za-z0-9-]/g,'-')}
printButton.addEventListener('click',()=>{document.title=reportTitle();window.print()});
window.addEventListener('afterprint',()=>{document.title=originalTitle});
document.querySelector('main section').after(plan.parentElement);
function element(tag,value){let n=document.createElement(tag);n.textContent=value;return n}
function renderPlan(d){plan.replaceChildren();plan.append(element('p',`${d.part_number} · ${d.platform_label} · ${d.memory_gb}GB / ${d.storage_tb}TB。以下为工程试验顺序，不是官方认证或实测结果。`));plan.append(element('p',d.first_step));let table=document.createElement('table'),head=document.createElement('tr');for(let x of ['试验级别','估算所需内存','容量筛选','下一步'])head.append(element('th',x));table.append(head);for(let t of d.trials){let row=document.createElement('tr');for(let x of [t.size_label,`${t.required_gb} GB`,t.fit==='fits'?'估算可容纳':'估算超出容量','核对许可证与格式 → 加载 → 查 GPU 后端 → 跑客户任务'])row.append(element('td',x));table.append(row)}plan.append(table);let a=d.assumptions;plan.append(element('p',`计算假设：Q${a.bits_per_weight}、系统预留 ${a.os_reserve_gb}GB、运行时预留 ${a.runtime_reserve_gb}GB、KV Cache ${a.kv_cache_gb}GB、量化开销 10%、单用户、首轮上下文 2048 token。改变上下文或并发时必须重算。`));plan.append(element('p',d.storage_note));plan.append(element('p',d.platform_note));let warning=element('p',d.capacity_boundary);warning.className='note';plan.append(warning)}
async function show(){printButton.disabled=true;fileHint.textContent='';try{let r=await fetch('/api/deployment/sku/'+encodeURIComponent(sku.value)),d=await r.json();if(!r.ok)throw Error('配置读取失败');out.textContent=`当前配置：${d.part_number} · ${d.platform_label} · 统一内存 ${d.memory_gb} GB · ${d.storage_tb} TB · ${d.operating_system}。具体模型、后端与速度均需按本页验收。`;renderPlan(d);printButton.disabled=false;fileHint.textContent='建议 PDF 文件名：'+reportTitle()+'.pdf'}catch(e){out.textContent=e.message;plan.textContent='暂不能生成该料号的试验路线'}}
async function init(){try{let r=await fetch('/api/catalog/imported-skus');if(r.status===401||r.status===403){out.textContent='请先在账号页登录并确认 License 有效，再查看部署指南。';return}let d=await r.json();if(!r.ok)throw Error(d.detail||'请求失败');sku.replaceChildren();for(let s of d.items)sku.add(new Option(`${s.part_number} · ${s.memory_gb}GB / ${s.storage_tb}TB`,s.part_number));let requested=new URLSearchParams(location.search).get('sku');if(requested&&d.items.some(s=>s.part_number===requested))sku.value=requested;if(d.items.length)show();else out.textContent='尚无已导入 SKU，请先完成授权数据导入。'}catch(e){out.textContent='无法读取产品数据：'+e.message}}sku.addEventListener('change',show);init();</script></body></html>''')
