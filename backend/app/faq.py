"""Indexed Chinese FAQ generated from reviewed, source-linked topic definitions."""
from fastapi import APIRouter, Query

router=APIRouter(prefix="/api/faq",tags=["faq"])

TOPICS=[
 ("选型基础","统一内存和显存有什么区别？","统一内存由 CPU、GPU 和系统共享，不能把标称容量全部当作模型权重空间。","容量评估需扣除 Windows、运行时、量化元数据、KV Cache 和其他进程；能装入不等于兼容或可用。","https://docs.nvidia.com/rtx-spark/rtx-spark-porting-guide/latest/overview.html","统一内存 显存 容量"),
 ("设备硬件","S2 和 S3 应该如何选择？","先按工作负载、内存和预算筛选，再比较 GPU 平台，不只看核心数。","S2/S3 核心数差异不能线性换算 Token/s 或 FPS；需要同条件 SKU 实测。","https://www.nvidia.com/en-us/products/rtx-spark/","S2 S3 GPU 选型"),
 ("AI模型","参数量越大效果一定越好吗？","不一定。任务、模型版本、量化和提示词都会影响效果。","参数量不是质量的充分条件；应基于目标任务评测准确率、延迟、吞吐、内存和许可证。","https://www.nvidia.com/en-sg/products/rtx-spark/help-me-choose/","参数量 模型质量"),
 ("AI模型","量化格式如何影响内存？","位数越低通常越省内存，但可能损失质量。","权重内存约为参数量×位数/8，另加量化元数据、KV Cache、运行时和系统预留。","https://github.com/ggml-org/llama.cpp","量化 Q4 Q5 内存"),
 ("AI模型","上下文长度为什么会增加内存？","模型记住的内容越长，KV Cache 通常越大。","KV Cache 随层数、隐藏维度、精度、序列长度及并发增长；需按具体架构计算。","https://github.com/ggml-org/llama.cpp","上下文 KV Cache"),
 ("部署运行时","Windows ARM64 推荐什么本地运行时？","优先选择官方明确支持 Windows ARM64 的版本，并逐机验证。","LM Studio 与 llama.cpp 有明确 ARM64 路径；其他框架需按固定版本、后端和驱动验证。","https://lmstudio.ai/docs/app/system-requirements","Windows ARM64 运行时"),
 ("部署运行时","vLLM 能否原生运行在 Windows？","官方不支持原生 Windows，通常考虑 WSL2 或外部 Linux 服务器。","vLLM 官方要求 Linux；WSL2 仍需验证 ARM64、CUDA、驱动和目标 GPU 路径。","https://docs.vllm.ai/en/latest/getting_started/installation/gpu/","vLLM Windows WSL2"),
 ("部署运行时","TensorRT-LLM 能否原生运行在 Windows？","当前官方重点是 Linux 和容器，不应按原生 Windows 方案销售。","原生 Windows 支持已弃用；建议 NGC/Linux 外部服务器，WSL2 仅在完成验证后采用。","https://nvidia.github.io/TensorRT-LLM/1.3.0rc27/installation/installation-guide.html","TensorRT-LLM Windows Linux"),
 ("游戏","平台宣传的 1440p 100 FPS 适用于每款游戏吗？","不适用。必须知道具体游戏、画质、驱动和帧生成设置。","平台级宣传缺少可复现测试条件，不能作为具体 SKU 或游戏的 FPS 保证。","https://nvidianews.nvidia.com/news/nvidia-microsoft-windows-pcs-agents-rtx-spark","FPS 平台宣传"),
 ("游戏","Windows ARM 游戏为什么要检查反作弊？","部分反作弊驱动可能不兼容 ARM，游戏可能无法启动。","需逐款验证游戏版本、ARM64/仿真路径、内核驱动、反作弊和发行商支持状态。","https://blogs.windows.com/windowsexperience/2026/05/31/introducing-a-powerful-new-chapter-for-windows-pcs-accelerated-by-nvidia-rtx-spark/","游戏 ARM 反作弊"),
 ("游戏","内存更大是否一定提高 FPS？","不一定。同一 GPU 平台增加内存主要提升余量。","FPS 受 GPU、功耗、散热、驱动、API 和场景影响；容量不足解除后才可能改善。","https://www.nvidia.com/en-us/products/rtx-spark/","内存 FPS"),
 ("生产力","软件兼容性应该如何确认？","检查软件版本、Windows ARM 支持、插件、驱动和实际项目。","最低配置仅说明门槛；需建立版本化兼容矩阵并用代表性文件验证功能与性能。","https://learn.microsoft.com/windows/arm/overview","软件兼容 Windows ARM"),
 ("生产力","视频剪辑能力如何评估？","要看分辨率、编码格式、特效、素材规模和导出要求。","记录 NLE 版本、编解码器、时间线、代理、GPU 加速、驱动与持续导出耗时。","https://www.nvidia.com/en-us/studio/","视频剪辑 GPU"),
 ("生成式AI","图像生成的官方倍数能换算成秒数吗？","不能。没有原始秒数就不能计算绝对时间。","相对加速比仅适用于声明中的模型、精度、步数、分辨率和对比设备。","https://blogs.windows.com/windowsexperience/2026/10/07/building-windows-for-hybrid-intelligence/","图像生成 相对性能"),
 ("生成式AI","视频生成需要关注哪些设置？","帧数、分辨率、采样步数、模型和精度都会影响时间与内存。","必须记录模型版本、精度、帧数、FPS、步数、输出尺寸、运行时及峰值内存。","https://blogs.windows.com/windowsexperience/2026/10/07/building-windows-for-hybrid-intelligence/","视频生成 设置"),
 ("证据与基准","官方声明、实测和估算有什么区别？","官方声明说明厂商口径；实测可复现；估算用于规划但不是保证。","记录 evidence_level、来源 URL、版本、测试条件、日期、置信度、适用范围和限制。","https://www.nvidia.com/en-us/products/rtx-spark/","证据 实测 估算"),
 ("证据与基准","为什么未知数据不能填零？","零表示测量结果，未知表示没有可靠数据，两者含义不同。","数据库应使用 NULL/unknown，避免聚合、排序和推荐引擎把缺失值解释为真实性能。","https://www.nvidia.com/en-us/products/rtx-spark/","未知 NULL 数据质量"),
 ("成本TCO","本地 AI 的 TCO 包含什么？","设备净成本、电费、维护，以及用户选择纳入的其他成本。","应公开价格、残值、功耗、利用率、电价、维护、周期和云端 Token 单价假设。","https://www.nvidia.com/en-sg/products/rtx-spark/help-me-choose/","TCO 本地 云端"),
 ("成本TCO","什么时候适合本地加云端混合？","隐私或高频任务放本地，复杂或突发任务使用云端。","按数据敏感度、SLA、模型质量、峰值并发、单位成本和可用性设计路由。","https://developer.nvidia.com/topics/ai/local-ai","混合AI 云端 本地"),
 ("成本TCO","Token 节省能直接等同 ROI 吗？","不能，还要考虑设备、能源、人员、维护和业务收益。","ROI 需定义基线、增量现金流、周期、残值和不可量化收益，避免只比较 Token 单价。","https://developer.nvidia.com/topics/ai/local-ai","Token ROI"),
 ("安全与账号","为什么用户注册后还不能立即登录？","需要完成邮箱验证、管理员审批和 License 授权。","服务端依次校验 email_verified、status、组织 License 到期和席位，不能只靠前端隐藏。","https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html","注册 审批 License"),
 ("安全与账号","密码如何保存？","只保存不可逆的 Argon2id 哈希，不保存明文。","使用独立盐、合理内存与时间成本，并支持未来 rehash；秘密仅从环境变量读取。","https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html","Argon2id 密码"),
 ("安全与账号","License 席位如何执行？","由服务端统计有效用户会话，席位用完就拒绝新的用户登录。","校验必须与组织隔离、到期时间、撤销状态和审计日志组合，避免仅做 UI 限制。","https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html","License 席位"),
 ("报告与销售","客户报告为什么必须列限制？","限制能防止把平台能力误解为具体设备保证。","报告应包含配置、证据等级、测试条件、未知项、成本假设、适用范围和复核日期。","https://www.nvidia.com/en-us/products/rtx-spark/","客户报告 限制"),
 ("数据维护","数据库多久更新一次？","价格、驱动、模型和软件变化时都应更新并重新审核。","以版本化导入保存来源哈希、发布日期、有效期、审核人和变更审计，旧数据不可静默覆盖。","https://www.nvidia.com/en-us/products/rtx-spark/","数据更新 审计"),
]
CONTEXTS=["个人日常使用","企业知识库","AI Coding","销售选型","隐私敏感场景","多人并发","长上下文任务","采购评估"]

FAQ=[]
for topic_index,(category,question,easy,expert,url,keywords) in enumerate(TOPICS):
 for context_index,context in enumerate(CONTEXTS):
  FAQ.append({"id":f"FAQ-{topic_index*8+context_index+1:03d}","category":category,"question":f"{context}：{question}","easy_answer":easy,"expert_answer":expert,"keywords":keywords.split()+[context],"source_url":url,"review_status":"reviewed_seed","sku_relevance":"all","framework_relevance":[]})

@router.get("")
def search_faq(q:str|None=None,category:str|None=None,limit:int=Query(default=20,ge=1,le=200)):
 items=FAQ
 if category: items=[x for x in items if x["category"]==category]
 if q:
  needle=q.casefold()
  items=[x for x in items if needle in (x["question"]+x["easy_answer"]+x["expert_answer"]+" ".join(x["keywords"])).casefold()]
 return {"items":items[:limit],"total":len(items),"indexed_total":len(FAQ),"categories":sorted({x["category"] for x in FAQ})}

@router.get("/{faq_id}")
def faq_detail(faq_id:str):
 from fastapi import HTTPException
 item=next((x for x in FAQ if x["id"]==faq_id),None)
 if not item: raise HTTPException(404,"FAQ 不存在")
 return item
