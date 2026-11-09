"""Chinese AI knowledge base for customer education and sales enablement."""
from fastapi import APIRouter, HTTPException, Query
from .faq_en import english_item

router = APIRouter(prefix="/api/faq", tags=["faq"])

SOURCES = {
    "AI基础知识": "https://learn.microsoft.com/windows/ai/",
    "模型架构": "https://huggingface.co/docs/transformers/index",
    "模型与内存": "https://docs.nvidia.com/rtx-spark/rtx-spark-porting-guide/latest/uma/umacuda.html",
    "推理性能": "https://docs.vllm.ai/en/latest/serving/metrics.html",
    "量化与精度": "https://github.com/ggml-org/llama.cpp",
    "Surface Laptop Ultra": "https://www.microsoft.com/en-us/d/surface-laptop-ultra-for-business/8wg5vqp0x4d1/",
    "RTX Spark硬件": "https://www.nvidia.com/en-us/products/rtx-spark/",
    "Windows与兼容": "https://learn.microsoft.com/en-us/windows/arm/add-arm-support",
    "本地AI部署": "https://developer.nvidia.com/topics/ai/local-ai/port-apps",
    "生成式AI": "https://blogs.nvidia.com/blog/rtx-ai-garage-ces-2026-open-models-video-generation/",
    "安全与隐私": "https://genai.owasp.org/",
    "选型与销售": "https://www.nvidia.com/en-us/products/rtx-spark/",
}

# Each entry is one independent teaching concept: term, plain explanation,
# engineering implication, and the misconception sales teams should avoid.
CONCEPTS = {
"AI基础知识": [
 ("人工智能（AI）","让计算机完成通常需要人类判断的任务的总称。","AI 是上位概念，包含规则系统、机器学习和生成式模型等多种方法。","AI 不等于聊天机器人，也不保证答案正确。"),
 ("机器学习（ML）","让系统从数据中学习规律，而不是把每条规则都手工写出。","训练得到的模型只对其数据、目标和评测范围负责。","数据更多不一定更好，数据质量和任务匹配更重要。"),
 ("深度学习","使用多层神经网络学习复杂模式。","现代视觉、语音和大语言模型多属于深度学习，但计算与内存需求差异很大。","深度学习不是所有业务问题的最佳方案。"),
 ("训练","用数据调整模型参数的过程。","完整训练通常比推理需要更多算力、内存、时间和数据治理。","能运行模型不等于能在同一设备上训练它。"),
 ("推理","使用已训练模型处理新输入并产生结果。","本地 AI 顾问主要评估推理；模型格式、运行时和算子兼容性同样关键。","模型能装入内存不代表推理一定能启动或可用。"),
 ("微调","在已有模型基础上继续训练，使其适应特定任务或风格。","LoRA 等参数高效微调可降低成本，但仍需要训练框架、显存和数据。","微调不是给模型上传文档的同义词。"),
 ("提示词（Prompt）","给模型的任务说明、上下文和输出要求。","提示结构会影响质量、输入 Token、首字延迟和复现性。","提示词不能弥补模型能力、知识时效或安全控制不足。"),
 ("Token","模型处理文本时使用的基本片段，不等于一个汉字或一个英文单词。","不同 tokenizer 的切分方式不同；成本、上下文和速度应按实际 Token 统计。","不能用字数直接精确换算 Token 数。"),
 ("Embedding向量","把文本、图像等内容表示为可比较的数字向量。","常用于语义搜索和 RAG；向量模型、维度和分块策略会影响召回质量。","相似度高不等于事实正确或业务上相关。"),
],
"模型架构": [
 ("Transformer","利用注意力机制处理序列的主流模型架构。","不同 Transformer 的层数、隐藏维度、注意力形式和上下文实现决定内存与速度。","同为 Transformer 不代表性能或用途相同。"),
 ("注意力机制","让模型判断输入中哪些部分彼此相关。","长上下文注意力会增加计算和 KV Cache 压力，不同实现复杂度不同。","上下文翻倍不一定只增加一倍开销。"),
 ("MoE混合专家模型","每次只激活模型中的部分专家网络，而不是使用全部参数。","MoE 可降低每 Token 计算量，但全部专家权重通常仍需存储和搬运，并带来路由与通信代价。","激活参数少不等于只需加载这些参数的内存。"),
 ("Dense稠密模型","每次推理通常使用全部主要模型参数。","容量估算较直观，但每 Token 计算量通常与总参数规模关系更直接。","同参数量下不能仅凭 Dense 或 MoE 标签判断质量。"),
 ("参数量","模型中可学习数值的数量，常用 B 表示十亿。","参数量影响权重内存和计算，但不是质量、速度或任务效果的充分条件。","70B 不一定在所有任务上优于较新的 32B。"),
 ("多模态模型","可以处理文本之外的图像、音频或视频。","视觉编码器、音频模块和媒体分辨率会额外消耗内存与计算。","支持图片不等于支持视频，也不等于能生成图片。"),
 ("扩散模型","通过逐步去噪生成图像或视频的模型。","采样步数、分辨率、批量、精度和节点图共同决定耗时与内存。","模型参数较小也可能因中间张量而占用大量内存。"),
 ("自回归模型","按顺序预测下一个 Token 或元素。","LLM 解码通常是自回归过程，因此输出长度直接影响总耗时。","高峰值算力不一定消除逐 Token 生成的延迟。"),
 ("小语言模型（SLM）","参数规模相对较小、适合特定任务和端侧部署的语言模型。","SLM 往往更省内存、延迟更低，但应以目标任务评测决定是否够用。","小模型不等于低质量，也不天然更安全。"),
],
"模型与内存": [
 ("模型权重","训练后保存的模型参数数据。","基础权重内存约等于参数量乘每参数位数再除以八，另有元数据和运行时开销。","权重文件大小不是运行时全部内存。"),
 ("统一内存","CPU、GPU 和系统共享的物理内存池。","Windows、显示、驱动、模型权重、KV Cache 和其他应用共同使用它。","统一内存不等于标称容量全部可当显存。"),
 ("独立显存（VRAM）","独立显卡专门连接的高速内存。","传统 PC 常需在系统内存与显存间复制数据；统一内存平台的预算方式不同。","统一内存容量大不代表带宽和独显显存完全等价。"),
 ("系统预留","操作系统、驱动、桌面和后台进程必须占用的内存。","能力估算应先扣除系统与运行时安全余量，不能使用理论满容量。","任务管理器的空闲值也会随缓存和应用变化。"),
 ("KV Cache","LLM 为已处理上下文保存的注意力键和值。","它随层数、维度、上下文长度、精度、批量和并发增长。","量化权重不会自动按同样比例压缩 KV Cache。"),
 ("上下文窗口","模型单次可处理的历史 Token 上限。","最大窗口是架构或配置上限，不代表在本机使用该长度仍快速、稳定或有高质量。","宣传的一百万上下文不是每个模型和 SKU 的默认能力。"),
 ("Batch批量","一次共同处理的请求或样本数量。","增大 batch 可能提高吞吐，但通常增加峰值内存和单请求等待。","batch 越大不代表交互体验越快。"),
 ("并发用户","同一服务同时处理的独立请求数量。","每个会话的上下文和 KV Cache 会竞争统一内存与计算资源。","单用户可用不能直接推导多人可用。"),
 ("内存卸载（Offload）","把部分权重或计算放到 CPU/系统内存或其他设备。","卸载可让更大模型启动，但数据搬运可能显著降低速度。","能靠卸载运行不等于达到可接受体验。"),
],
"推理性能": [
 ("延迟（Latency）","从提交请求到获得结果所需的时间。","应拆分首字延迟、生成阶段和端到端时间，并记录输入输出长度。","平均延迟不能描述最慢用户体验。"),
 ("首Token延迟（TTFT）","从请求开始到出现第一个输出 Token 的时间。","TTFT 主要受模型加载、排队和长输入预填充影响。","Token/s 高不代表首字一定快。"),
 ("Token/s","模型每秒生成的 Token 数。","必须注明模型版本、量化、运行时、输入输出长度、并发、电源和测量方法。","不同 tokenizer、模型和条件的 Token/s 不能直接横比。"),
 ("吞吐量","系统单位时间处理的总工作量。","服务端可牺牲单请求延迟换取更高总体吞吐。","吞吐高不代表每个用户响应快。"),
 ("Prefill预填充","模型处理全部输入上下文并建立缓存的阶段。","长文档和长提示会增加预填充时间与计算量。","只测短提示不能代表知识库问答体验。"),
 ("Decode解码","模型逐个生成输出 Token 的阶段。","解码常受内存访问、量化内核和并发调度影响。","峰值 FP4 算力不能直接换算解码速度。"),
 ("Warm-up预热","首次运行时加载模型、编译内核或建立缓存。","冷启动和热运行应分别测试，面向客户说明是否常驻服务。","只展示预热后最快一次会掩盖真实启动体验。"),
 ("基准测试","在明确条件下可重复测量性能或质量。","合格记录应包含硬件 SKU、软件版本、模型、精度、提示、输出、功耗与日期。","厂商平台结果不能自动成为具体 SKU 实测。"),
 ("持续性能与散热","设备长时间负载下能够保持的性能。","短时跑分可能受睿频影响；应观察功耗、温度、噪声和性能衰减。","峰值性能不等于持续性能。"),
],
"量化与精度": [
 ("Bit比特","表示一个数值使用的二进制位数。","位数越低通常越省内存和带宽，但实际格式还包含分组、尺度和元数据。","4-bit 模型运行内存不一定正好是 16-bit 的四分之一。"),
 ("FP32","32位浮点精度，范围和精度较高。","训练和部分科学计算常用，但 LLM 本地推理通常内存代价较大。","更高精度不保证最终回答更正确。"),
 ("FP16","16位浮点格式。","相较 FP32 通常节省约一半权重空间，并可利用 GPU 加速。","FP16 与 BF16 的数值范围和兼容性不同。"),
 ("BF16","保留较大指数范围的16位浮点格式。","常用于训练和推理，但是否高效取决于硬件与运行时支持。","文件标注 BF16 不代表所有算子都按 BF16 执行。"),
 ("FP8","8位浮点格式族。","可降低内存和计算成本，但需要模型、校准、内核和硬件路径共同支持。","FP8 不是单一统一格式。"),
 ("FP4与NVFP4","约4位的低精度浮点方案；NVFP4是 NVIDIA 的特定格式路径。","可显著降低权重内存并利用相应 Tensor Core，但需匹配模型检查点和软件栈。","看到1 PFLOP FP4不能推导任意模型Token/s。"),
 ("INT8","8位整数常见量化格式。","通常在质量和资源之间折中，实际效果取决于量化方法和算子覆盖。","INT8 名称相同不代表量化算法相同。"),
 ("INT4/Q4","约4位整数或分组量化的统称。","非常适合降低大模型权重空间，但不同 Q4 变体质量、大小和速度不同。","Q4 不能视为一个精确统一格式。"),
 ("GGUF","llama.cpp 生态常用的模型文件格式。","它可包含权重、量化和元数据；运行能力取决于架构支持及所选后端。","能下载 GGUF 不代表该模型一定与当前运行时兼容。"),
],
"Surface Laptop Ultra": [
 ("Surface Laptop Ultra定位","面向创作者、开发者、AI 与工程专业负载的高性能 Surface。","普通邮件和文档办公未必需要该级别设备，应以工作负载和总成本选型。","最贵配置不一定是每位员工的最佳设备。"),
 ("N1X 18 核 CPU 配置","NVIDIA RTX Spark™ N1X 的 18 核 CPU、5120 核 Blackwell GPU 配置。","具体性能仍受内存、功耗、散热、驱动和软件影响；核心数来自项目配置资料。","不同核心数不能线性换算性能差。"),
 ("N1X 20 核 CPU 配置","NVIDIA RTX Spark™ N1X 的 20 核 CPU、6144 核 Blackwell GPU 配置。","较多核心为重型任务提供潜力，但必须结合内存容量和实际测试；核心数来自项目配置资料。","较多核心不会让所有办公软件同比加速。"),
 ("Part Number","用于识别具体销售配置的料号。","同一产品名可能包含平台、内存、存储、颜色和价格差异，报告必须绑定料号。","只写 Surface Laptop Ultra 无法准确选型。"),
 ("24GB配置","统一内存入门配置。","适合办公、开发与轻量本地 AI；扣除系统后不宜默认承诺大型模型或重视频工作流。","24GB 不能全部作为模型权重空间。"),
 ("32GB配置","主流专业统一内存配置。","比24GB提供更多多任务和中型模型余量，但长上下文与视频生成仍需控制。","容量增加不一定提高同一模型的速度。"),
 ("48GB配置","进阶专业统一内存配置。","适合更大模型、中重度创作和开发并行，但仍需保留系统与中间张量空间。","48GB 不等于任何 48GB 独显。"),
 ("64GB配置","高阶专业统一内存配置。","可覆盖更多本地模型和创作工作流，是部分官方参考演示的容量档，但不能套用演示成绩。","相同容量不等于相同散热和持续性能。"),
 ("128GB配置","最高统一内存配置。","主要价值是容纳更大模型、场景和多工具并行；仍需核对兼容性与可用速度。","能装入120B模型不等于该模型体验一定优秀。"),
 ("Windows 11 Pro","商业配置使用的专业版 Windows。","提供企业管理与安全能力；AI软件的ARM64兼容仍取决于应用、驱动和插件。","Pro版本身不会让AI推理更快。"),
],
"RTX Spark硬件": [
 ("Grace CPU","RTX Spark 中基于 Arm 架构的 CPU。","应用应优先使用原生 ARM64 或验证 Prism 模拟路径。","Grace 名称不代表数据中心 Grace CPU 的全部规格。"),
 ("Blackwell RTX GPU","提供图形、CUDA、Tensor Core和光追能力的集成 GPU。","具体 SKU 核心数、功耗与内存容量不同，平台能力不是单机基准。","Blackwell 架构名不能直接推导应用速度。"),
 ("Tensor Core","针对矩阵与低精度 AI 运算优化的 GPU 单元。","只有软件使用受支持的数据类型和内核时才能发挥优势。","有 Tensor Core 不代表所有 AI 软件自动加速。"),
 ("RT Core","用于加速光线追踪相关计算的 GPU 单元。","主要影响支持 RTX/OptiX/DXR 的渲染和游戏工作流。","RT Core 不是 LLM 推理的主要指标。"),
 ("CUDA","NVIDIA 的并行计算平台与软件生态。","模型框架、驱动、CUDA版本和ARM64 wheel必须匹配。","支持CUDA不等于任意Linux项目可原样在Windows运行。"),
 ("NVENC硬件编码","GPU内置的视频编码引擎。","可加速受支持的H.264、HEVC或AV1导出，仍受软件与格式支持限制。","有编码器不代表所有导出设置都走硬件。"),
 ("NVDEC硬件解码","GPU内置的视频解码能力。","有助于受支持素材的回放和预处理，但编解码格式、位深与色度采样要匹配。","无法解码的格式不会因GPU强大而自动支持。"),
 ("OptiX","NVIDIA 的光线追踪与渲染开发接口。","Blender等应用可使用相关后端，但版本与ARM64支持需实机确认。","OptiX能力不等于每个渲染器都有原生支持。"),
 ("300GB/s峰值带宽","官方最高平台的理论内存带宽指标。","真实工作负载受到访问模式、共享竞争、功耗和软件效率影响。","不能用峰值带宽计算Token/s或渲染时间。"),
],
"Windows与兼容": [
 ("Windows on Arm","运行在ARM64处理器上的Windows。","系统支持原生ARM64应用，也可通过Prism运行许多x64应用。","能启动x64应用不代表全部插件和驱动兼容。"),
 ("ARM64原生应用","直接为ARM64编译的Windows应用。","通常具有更好的效率和平台集成，但还要验证GPU后端与依赖。","原生CPU架构不等于GPU加速已经启用。"),
 ("Prism模拟","Windows用于运行许多x86/x64应用的转换层。","它翻译CPU代码；GPU设备代码仍走平台GPU，但扩展和驱动可能受限。","模拟不是虚拟机，也不能模拟不兼容的内核驱动。"),
 ("ARM64EC","允许ARM64与x64组件逐步混合的Windows ABI。","适合分阶段移植大型应用，但依赖边界和性能关键路径要设计。","ARM64EC不是所有应用都需要的最终形态。"),
 ("设备驱动","让系统控制GPU、音频、采集卡等硬件的软件。","内核驱动必须支持Windows ARM64；Prism不能解决驱动架构不兼容。","应用可模拟运行不代表外设一定可用。"),
 ("插件兼容","主应用之外的扩展、编解码器、节点和脚本支持情况。","专业工作流常因单个x64插件或Python wheel无法使用而中断。","主程序原生ARM64不等于插件生态全部原生。"),
 ("WSL2","Windows中的Linux虚拟化环境。","可承载部分Linux工具，但GPU、ARM64容器、网络和文件IO均需验证。","WSL2不等于官方支持原生Windows的软件。"),
 ("Windows ML","Windows提供的本地模型推理与执行提供程序框架。","支持x64和ARM64，特定硬件优化路径要求相应系统版本和驱动。","支持Windows ML不代表所有模型算子都能落到GPU。"),
 ("Windows 11 24H2 Build 26100","部分新AI执行提供程序要求的最低系统版本。","企业镜像、更新通道和驱动版本应纳入部署基线。","只满足系统版本仍不能替代模型和应用测试。"),
],
"本地AI部署": [
 ("AI运行时","负责加载模型、执行算子和管理硬件后端的软件。","同一模型在不同运行时的格式、兼容性、内存和速度可能不同。","更换运行时后旧基准不能直接沿用。"),
 ("Ollama","面向本地模型管理与API服务的工具。","应固定版本、模型清单、后端和Windows ARM64支持状态再部署。","安装成功不代表每个模型都使用GPU。"),
 ("LM Studio","提供模型下载、聊天和本地API的桌面工具。","适合演示和个人使用，但企业部署仍需审核模型许可、版本和更新策略。","图形界面易用不等于生产服务治理完整。"),
 ("llama.cpp","面向高效LLM推理的开源C/C++项目。","支持多种量化和后端；模型架构与构建版本必须匹配。","llama.cpp支持某GPU不代表任意分支和构建都支持。"),
 ("vLLM","强调批处理和服务吞吐的LLM推理引擎。","官方重点是Linux；Windows通常考虑WSL2或外部服务器并验证ARM64/CUDA路径。","不能把Linux服务器文档当作原生Windows支持。"),
 ("TensorRT-LLM","NVIDIA面向LLM优化的推理栈。","现行官方支持矩阵要求 Linux x86_64 或 Linux aarch64；Windows 原生不应列为受支持路径。具体 GPU 架构、CUDA、容器和版本仍须逐项核验。","TensorRT与TensorRT-LLM不是同一个产品层，也不能把 Linux 支持推断为 Windows 支持。"),
 ("ComfyUI","使用节点图构建图像和视频生成工作流的工具。","自定义节点、Python依赖、模型格式和显存峰值决定实际兼容性。","工作流文件能打开不代表所有节点能执行。"),
 ("容器","把应用和依赖封装在镜像中的部署方式。","镜像架构、GPU透传、驱动和许可证仍依赖宿主机。","容器不能自动解决x64镜像在ARM64上的兼容问题。"),
 ("模型许可","规定模型权重可否商用、再分发或生成特定内容的条款。","企业部署必须记录模型版本、来源、许可与使用限制。","开源代码不代表模型权重可无限制商用。"),
],
"生成式AI": [
 ("文生图","根据文本提示生成图像。","模型、分辨率、步数、精度和随机种子共同影响结果与资源。","一次成功不代表所有分辨率都稳定。"),
 ("采样步数","扩散生成过程中迭代去噪的次数。","更多步数通常增加耗时，但质量收益可能递减且依赖采样器。","步数翻倍不保证质量翻倍。"),
 ("生成分辨率","输出图像或视频的像素尺寸。","分辨率提高会明显增加中间张量和计算，视频还叠加帧数。","最终4K可由超分获得，不一定是原生4K生成。"),
 ("随机种子","控制随机生成过程的起始状态。","固定模型、工作流和种子有助于复现对比。","相同种子跨版本或硬件不一定逐像素一致。"),
 ("LoRA","用较小适配参数改变模型风格或任务的技术。","可减少微调与分发成本，但多个LoRA组合会影响质量和资源。","LoRA文件小不代表基础模型不需要加载。"),
 ("图生图","以已有图像作为条件进行修改或再生成。","输入分辨率、去噪强度、控制网络和节点图影响内存与结果。","图生图不是无损编辑。"),
 ("视频生成","按文本、图像或关键帧生成连续画面。","模型权重、帧数、分辨率、音频、步骤和中间张量使资源需求很高。","平台支持4K工作流不等于所有SKU原生生成4K。"),
],
"安全与隐私": [
 ("本地AI与数据边界","模型在设备上运行可减少内容发往云端。","仍要检查遥测、模型下载、更新、日志、插件和外部工具是否联网。","本地运行不等于完全离线或自动合规。"),
 ("RAG数据隐私","检索增强会把企业文档片段提供给模型。","应控制索引权限、租户隔离、删除同步、日志和引用来源。","RAG不等于模型绝不会泄露检索内容。"),
 ("提示词注入","恶意内容试图让模型忽略原有规则或调用不当工具。","需要输入隔离、工具授权、输出验证和最小权限，不能只靠系统提示词。","模型拒答模板不是完整安全边界。"),
 ("模型供应链","模型、运行时、节点和插件的来源与更新链路。","应校验来源、哈希、签名、许可、漏洞和变更记录。","从热门网站下载不代表文件可信。"),
 ("审计日志","记录谁在何时执行了什么关键操作。","账号、审批、License、模型更新和管理动作应可追溯且防篡改。","日志不是越多越好，敏感内容也要最小化。"),
 ("磁盘加密与Windows安全","BitLocker、TPM和Secured-core等用于保护设备与密钥。","本地模型和知识库仍需账号权限、备份、补丁和丢失设备响应。","硬件安全功能不能替代应用权限控制。"),
],
"选型与销售": [
 ("装得下、能启动与好用","这是三个不同层次的判断。","容量足够只说明权重可能装入；还要验证运行时兼容、速度、稳定性和输出质量。","销售不能把装得下表述为流畅运行。"),
 ("官方声明、实测与工程估算","三者的证据强度和适用范围不同。","报告应记录来源、SKU、版本、条件、日期和限制，不能把平台声明改写成单机实测。","工程估算必须明确标注，不能包装成官方数据。"),
 ("未知与零","未知表示没有可靠数据，零表示测量结果为零。","数据库和报告必须保留NULL/unknown，避免排序与推荐误判。","不能为了表格完整而填0或编造平均值。"),
 ("PoC概念验证","用客户真实数据和工作流做小范围验证。","PoC应预先定义成功标准、版本、样本、性能、安全和复现步骤。","演示成功不等于生产环境通过验收。"),
 ("本地、云端与混合AI","三种部署方式各有隐私、质量、成本和扩展性取舍。","应按数据敏感度、模型能力、并发、SLA、单位成本和离线需求设计路由。","本地并非永远更便宜，云端也并非永远更强。"),
],
}

assert sum(len(items) for items in CONCEPTS.values()) == 100

FAQ = []
for category, concepts in CONCEPTS.items():
    if category == "Surface Laptop Ultra":
        continue  # This product needs curated, scenario-specific training, not paired template questions.
    for term, easy, expert, misconception in concepts:
        base = len(FAQ) + 1
        common = {"category": category, "keywords": [term, category], "source_url": SOURCES[category], "review_status": "reviewed_concept", "sku_relevance": "Surface Laptop Ultra / RTX Spark", "framework_relevance": []}
        if category == "Windows与兼容":
            if term == "Prism模拟":
                common["source_url"] = "https://learn.microsoft.com/en-us/windows/arm/apps-on-arm-x86-emulation"
            elif term == "ARM64EC":
                common["source_url"] = "https://learn.microsoft.com/en-us/windows/arm/arm64ec"
            elif term == "Windows ML":
                common["source_url"] = "https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/overview"
            elif term == "Windows 11 24H2 Build 26100":
                common["source_url"] = "https://learn.microsoft.com/en-us/windows/ai/new-windows-ml/supported-execution-providers"
        elif category == "本地AI部署":
            common["source_url"] = {
                "LM Studio": "https://lmstudio.ai/docs/app/system-requirements",
                "llama.cpp": "https://github.com/ggml-org/llama.cpp/blob/master/docs/build.md",
                "vLLM": "https://docs.vllm.ai/en/stable/getting_started/installation/gpu/",
                "TensorRT-LLM": "https://nvidia.github.io/TensorRT-LLM/reference/support-matrix.html",
            }.get(term, SOURCES[category])
        elif category == "安全与隐私":
            common["source_url"] = {
                "提示词注入": "https://genai.owasp.org/glossary/prompt-injection/",
                "RAG数据隐私": "https://genai.owasp.org/glossary/sensitive-data-exposure/",
                "磁盘加密与Windows安全": "https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/oem-highly-secure-11",
            }.get(term, SOURCES[category])
        FAQ.append({"id": f"FAQ-{base:03d}", "question": f"{term}是什么？", "easy_answer": easy, "expert_answer": expert, "misconception": misconception, "sales_tip": f"先确认客户是否真的涉及“{term}”，再说明适用范围、验证条件和未知项。", **common})
        FAQ.append({"id": f"FAQ-{base+1:03d}", "question": f"{term}对 Surface Laptop Ultra 选型和使用有什么影响？", "easy_answer": expert, "expert_answer": f"选型不能只看“{term}”标签；应结合具体 Part Number、内存、软件版本、任务条件和证据等级验证。", "misconception": misconception, "sales_tip": f"不要把“{term}”单项指标当成性能承诺；用客户真实任务做 PoC。", **common})

# Each entry is an independently useful sales-training answer. Product claims
# come from Microsoft; Apple comparisons link both vendors' current specs.
SURFACE_SOURCE = "https://www.microsoftstore.com.cn/surface/surface-laptop-ultra-for-business"
APPLE_SOURCE = "https://www.apple.com.cn/macbook-pro/specs/"
ARM_SOURCE = "https://learn.microsoft.com/en-us/windows/arm/add-arm-support"
NVIDIA_ARM_SOURCE = "https://developer.nvidia.com/topics/ai/local-ai/port-apps"
SURFACE_TRAINING = [
    ("客户该如何理解 Surface Laptop Ultra 的定位？", "它是兼顾 Windows 商务工作流、触控创作和 RTX Spark 本地 AI 的专业笔记本。", "先识别客户的 Windows 软件、CUDA 工作流、触控需求与移动性，再按具体料号评估；普通办公不一定需要最高配。", "产品定位不是每个 SKU 的性能承诺。", "让客户列出三个最耗时的真实任务，以任务而非宣传词选型。", SURFACE_SOURCE, None),
    ("与普通 Windows OEM 笔记本相比，优先展示哪些差异？", "展示微软自家 Surface 软硬件体验、15 英寸 3:2 触控屏、RTX Spark 平台和明确的端口配置。", "OEM 产品差异很大；只有在指定竞品型号后，才能逐项比较屏幕、接口、GPU、内存、售后和总成本。", "不能声称所有 OEM 都缺少触屏、USB-A 或 NVIDIA GPU。", "建立同价位具体型号对照表，并让客户亲自体验触控、扩展和工作流。", SURFACE_SOURCE, None),
    ("15 英寸 PixelSense Ultra 触控屏对专业工作有什么意义？", "3:2 屏幕适合查看长文档和时间线，触控可用于批注、演示与直接交互。", "微软公布 3270×2180 分辨率、最高 120Hz、DCI-P3 100%；色彩关键工作还需实测校准、软件色彩管理和外接屏需求。", "高分辨率和广色域不等于每台设备已经完成专业校色。", "演示客户自己的图纸、表格或创作素材，而非只展示桌面壁纸。", SURFACE_SOURCE, None),
    ("Surface Laptop Ultra 的接口优势应如何准确表述？", "机身含 USB-C、USB-A、HDMI、SD 读卡器和耳机接口，减少部分转接需求。", "微软称其在 Surface Laptop 系列中接口最丰富；这不是对所有 OEM 或所有 MacBook 的接口数量领先声明。", "不能把“Surface 系列最多”说成“行业最多”。", "列出客户必须直连的显示器、相机卡、旧 USB 设备和底座。", SURFACE_SOURCE, APPLE_SOURCE),
    ("RTX Spark N1X 的两种 CPU/GPU 档位如何解释？", "18 核 CPU/5120 核 GPU 与 20 核 CPU/6144 核 GPU 是不同硬件配置。", "核心数只是规格；实际速度受功耗、散热、内存、驱动和应用内核影响，不能按核心数比例推算 FPS 或 Token/s。", "高核心档不保证每个应用都更快。", "同时展示具体料号、内存与存储，做客户工作负载 PoC。", SURFACE_SOURCE, None),
    ("统一内存最高 128GB 的实际价值是什么？", "较大的统一内存可给本地模型、图形任务和多应用并行留出更大容量空间。", "最高值只属于相应 SKU；操作系统、图形与上下文缓存也占用内存，装得下、能运行与体验好要分别验证。", "128GB 并非每台机型标配，也不等于 128GB 独立显存。", "先记录模型格式、量化、上下文和并发，再选内存档位。", SURFACE_SOURCE, None),
    ("与 MacBook Pro 对比，本产品的销售切入点是什么？", "对依赖 Windows 软件、触控交互、USB-A 或 NVIDIA CUDA 生态的客户，Surface 值得优先验证。", "Apple 当前 MacBook Pro 也提供最高 128GB 统一内存、HDMI、SDXC 和高规格显示屏；比较必须锁定具体 M5 配置与 Surface 料号。", "不能说 MacBook Pro 没有 HDMI/读卡器，或 Surface 在所有任务都更快。", "让客户用同一项目、同一软件版本和外设清单分别试机。", SURFACE_SOURCE, APPLE_SOURCE),
    ("与 MacBook Pro 相比，触控和操作系统有什么取舍？", "Surface 提供 Windows 11 和机身触控，适合客户已有的 Windows 管理与笔触交互。", "MacBook Pro 的 macOS、ProRes/Final Cut 等工作流可能更合适；不能把不同系统中的软件兼容性或触控偏好当成通用性能胜负。", "不要宣称 macOS 无法做本地 AI，或 Windows 软件都已原生支持 ARM。", "先盘点客户现有软件、设备管理、外设与创作流程。", SURFACE_SOURCE, APPLE_SOURCE),
    ("与 MacBook Pro 比较续航时怎样避免误导？", "只报告两家官方各自的测试条件，并在客户的真实负载下复测。", "Surface 官方的本地视频与网页续航测试和 Apple 的视频/无线网页测试条件不同；AI 推理、亮度、网络与软件版本都会改变结果。", "不能直接用两个宣传小时数判定谁续航更长。", "安排相同亮度、网络、任务和电源模式的并行测试。", SURFACE_SOURCE, APPLE_SOURCE),
    ("MacBook Pro 的 Thunderbolt 5 是否是 Surface 的劣势？", "对超高速外设和特定扩展坞，它可能是 Apple 指定机型的优势。", "Surface 官方列出 USB4 USB-C；Apple 不同 MacBook Pro 配置提供不同接口代际。应核对客户实际存储、显示器和扩展坞带宽。", "不能只看接口名称而不看设备两端与线材规格。", "客户若使用高速阵列或多屏底座，应实测吞吐与稳定性。", SURFACE_SOURCE, APPLE_SOURCE),
    ("Windows on Arm 能否运行客户现有 x64 软件？", "部分 x86/x64 应用可通过仿真运行，但关键软件与驱动必须逐项核验。", "微软说明 Windows on Arm 有仿真能力，但内核驱动必须提供 ARM64 版本；插件、安装器、反作弊和硬件控制程序也可能影响交付。", "“能启动”不等于全部插件可用或性能等同原生。", "列出客户应用、版本、驱动、外设和验收动作，优先做 ARM64 原生验证。", ARM_SOURCE, None),
    ("CUDA 生态是否意味着所有 AI 工具开箱即用？", "NVIDIA 生态是有价值的开发路径，但每个工具链仍需核对 Windows ARM64 支持。", "NVIDIA 提供 Windows on Arm 移植资料；CUDA Toolkit、框架轮子、算子、驱动和模型后端的版本须分别验证。", "NVIDIA GPU 存在不代表任意 CUDA 应用在 Windows ARM64 可运行。", "按目标工具的官方兼容矩阵和客户模型建立安装与推理 PoC。", NVIDIA_ARM_SOURCE, None),
    ("本地 AI 与云端 AI 应怎样向客户解释？", "本地有助于降低部分任务的联网依赖，云端仍可提供更大模型和弹性服务。", "本地化的数据边界取决于应用遥测、模型下载、插件、日志和路由策略；成本要算购置、维护、利用率与云端回退。", "本地运行不等于完全离线、零成本或自动合规。", "先确定哪些数据不能出域，再追踪真实应用的数据流。", SURFACE_SOURCE, None),
    ("24GB、32GB、48GB、64GB、128GB 应怎样推荐？", "按模型容量、创作素材、并行应用和预算选择，不以容量单项决定。", "统一内存需预留系统、图形与中间张量；更大容量提高可容纳空间，不直接证明吞吐或任务成功率。", "不能把内存 GB 数直接换算成模型参数量或 Token/s。", "用目标模型与项目文件测峰值内存、稳定性和响应时间。", SURFACE_SOURCE, None),
    ("可拆卸 SSD 对企业部署有什么价值？", "有助于部分维修、设备交接和数据管理流程。", "微软列出可拆卸 SSD 的规格；具体拆装、保修、加密密钥、数据擦除和替换流程应遵守官方服务指南与企业制度。", "可拆卸不代表员工可随意拆卸或升级且不影响保修。", "把 BitLocker、资产交接和故障返修纳入采购方案。", SURFACE_SOURCE, None),
    ("如何向 IT 部门介绍 Surface 的商业价值？", "从 Windows 管理、安全、外设、服务和员工工作流统一评估。", "硬件安全功能不能替代设备管理、补丁、权限、备份与响应流程；企业价值需与现有 Intune/Entra、应用和服务合同匹配。", "产品页列出安全特性不等于客户已完成安全配置。", "请 IT 团队提供标准镜像、策略、资产与维修要求。", SURFACE_SOURCE, None),
    ("Surface 与 OEM/Apple 的 TCO 应如何比较？", "比较完整使用周期的设备、软件、适配、支持和员工时间，而非只比采购价。", "同一周期纳入外设/转接、应用迁移、管理、维修、能耗和云端 AI 服务；没有客户账单时只能做标注假设的情景估算。", "低首购价或高配置不能自动证明总成本最低。", "用客户现有财务数据和 PoC 工时替换模板默认值。", SURFACE_SOURCE, APPLE_SOURCE),
    ("给图形创作客户演示时应验证什么？", "演示客户真实项目的预览、渲染、导出和外设连接。", "Blackwell GPU 的架构能力与具体创作软件是否调用相应后端不同；记录插件、编解码器、素材、分辨率和电源状态。", "平台支持某功能不等于每个应用、每个 SKU 都能获得同样收益。", "在同一素材与版本上比完成时间、画质与稳定性。", SURFACE_SOURCE, None),
    ("给开发团队演示时应验证什么？", "验证目标 IDE、容器、SDK、依赖包和真实构建/推理任务。", "Windows ARM64 与 Linux/WSL、CUDA 工具链的支持状态可能不同；驱动和原生扩展是常见阻碍。", "一个 Hello World 成功不代表完整项目可迁移。", "让开发者带仓库、依赖锁文件与测试集做端到端 PoC。", NVIDIA_ARM_SOURCE, ARM_SOURCE),
    ("销售对比表的证据等级如何标注？", "把官方规格、客户实测、工程估算和未知分开列。", "对标 Apple 或 OEM 时记录具体型号、日期、版本和测试条件；没有同条件结果就不要填写 FPS、Token/s 或续航胜负。", "官方最高配置和发布会演示不能改写为本 SKU 实测。", "每张比较表附来源链接、测试记录和待验证项。", SURFACE_SOURCE, APPLE_SOURCE),
]
for question, easy, expert, misconception, sales_tip, url, comparison_url in SURFACE_TRAINING:
    FAQ.append({"id": f"FAQ-{len(FAQ)+1:03d}", "category": "Surface Laptop Ultra", "question": question,
                "easy_answer": easy, "expert_answer": expert, "misconception": misconception,
                "sales_tip": sales_tip, "keywords": [question, "Surface Laptop Ultra"] + (["N1X 18 核 CPU"] if "定位" in question or "N1X" in question else []),
                "source_url": url, "comparison_source_url": comparison_url,
                "review_status": "official_specs_with_sales_inference", "sku_relevance": "按具体 Part Number 核验", "framework_relevance": []})

# October 7, 2026 Microsoft/NVIDIA announcement: each question has its own
# official citation and release status, rather than inheriting a category URL.
MXC_SOURCE = "https://blogs.windows.com/windowsdeveloper/2026/10/07/microsoft-execution-containers-policy-driven-containment-for-ai-agents/"
HYBRID_SOURCE = "https://blogs.windows.com/windowsexperience/2026/10/07/building-windows-for-hybrid-intelligence/"
COPILOT_SOURCE = "https://commandline.microsoft.com/local-models-sandboxed-tools-github-windows/"
ANNOUNCEMENT_FAQ = [
    ("安全与隐私", "Microsoft Execution Containers（MXC）是什么？", "MXC 是微软已宣布正式提供的策略驱动执行隔离层，用来限制 AI 代理、插件、工具或模型生成代码可访问的资源。", "开发者或管理员声明文件、网络等权限；策略置于被隔离工作负载之外，工作负载不能自行扩大权限。它不是模型推理引擎。", "MXC 不会自动赋予代理可信身份，也不能替代应用权限审查。", "向客户演示代理操作前，先列出它需要读写的文件与联网范围。", MXC_SOURCE),
    ("安全与隐私", "MXC 能限制 AI 代理访问哪些资源？", "可以按策略控制文件读写、网络连接和桌面交互等。", "策略可分别定义可修改、只读与不可访问的位置，也可控制入站/出站及回环网络。实际边界取决于所选容器后端。", "允许读取某目录不等于允许修改它。", "用客户真实目录和目标网址列权限清单，再做拒绝访问验证。", MXC_SOURCE),
    ("安全与隐私", "MXC 的进程容器、会话容器、WSLc 和 MicroVM 有何区别？", "它们是不同隔离强度与软件环境的选项。", "进程容器适合轻量工具执行；Windows 11 会话容器把代理放在独立账户和桌面会话；WSLc 提供 Linux 环境；MicroVM 在 Windows 11/Linux 仍属实验性。", "不能把实验性的 MicroVM 说成所有设备已正式商用。", "先按代理需要的桌面、Linux 工具与风险级别选择后端，再在目标设备验证。", MXC_SOURCE),
    ("安全与隐私", "MXC 与 Docker/普通 Windows 容器是一回事吗？", "不是。MXC 是面向代理和动态代码的策略层，可映射到不同隔离后端。", "它通过统一配置描述权限，后端可使用 Windows AppContainer、独立会话、WSL 或 MicroVM；不是单一的容器镜像格式。", "安装 Docker 不等于已经为 AI 代理配置 MXC 策略。", "明确客户要隔离的是代理工具、生成代码还是整个代理，再设计策略。", MXC_SOURCE),
    ("安全与隐私", "MXC 已正式提供，是否意味着所有安全能力都已上线？", "MXC 隔离层已正式提供；代理身份与企业管理能力仍有分阶段交付。", "微软称 Entra 区分代理与用户身份、Agent 365 本地代理治理等能力将继续推出；部署时应按实际版本与租户许可确认。", "不能把路线图中的能力当作当前所有客户都可用。", "销售材料分开标明已提供、实验性与即将推出的功能。", MXC_SOURCE),
    ("安全与隐私", "MXC 能否防止提示词注入造成的一切风险？", "不能。它限制代理可执行操作的范围，但不能保证模型不被误导。", "应同时设置最小权限、敏感操作确认、身份与审计，并验证工具返回内容和外部数据；隔离主要降低越权后的影响范围。", "有沙箱不等于可以给代理无限文件或网络权限。", "请客户列出不可触碰的目录、服务和凭据，并实测边界。", MXC_SOURCE),
    ("选型与销售", "Hybrid intelligence（混合智能）是什么？", "让本地模型与云端模型按任务需要协同工作。", "微软在 10 月 7 日说明其依赖本地模型、智能路由、运行时和设备算力；路由应考虑质量、时延、成本、隐私与联网条件。", "混合智能不保证每个请求都留在本地。", "先确认客户对数据出域、离线运行、成本与质量的要求。", HYBRID_SOURCE),
    ("选型与销售", "混合智能如何决定任务在本地还是云端执行？", "智能路由可依据任务与策略选择合适的模型和计算位置。", "微软宣布 GitHub HydraFusion 将扩展到 Windows 本地模型；GitHub Copilot 应用、CLI 和 VS Code 的相关体验计划于 2026 年 10 月稍晚进入实验预览。", "发布会演示或计划中的预览不等于客户当前版本已能自动路由。", "在目标版本实测路由结果、成本与失败回退，并保留人工选择。", HYBRID_SOURCE),
    ("选型与销售", "混合智能一定会减少云端 Token 费用吗？", "不一定。节省取决于有多少任务适合本地完成及设备总成本。", "比较应包含模型质量、任务成功率、本地购置与维护、电力、利用率、云端单价和回退比例；不能由平台宣传直接推导 ROI。", "本地 Token 没有 API 计费，不等于设备运行零成本。", "用客户真实任务样本计算本地/云端路由比例和 TCO。", HYBRID_SOURCE),
    ("Surface Laptop Ultra", "Surface Laptop Ultra 在混合智能中扮演什么角色？", "它可提供 RTX Spark 本地计算能力，让适合端侧的模型与代理任务在设备上运行。", "微软将最高 128GB 统一内存设备列为 Builder PC 示例；平台级模型规模和参考测试不等于每个 Part Number 的可用速度或容量。", "不能把最高配置与预生产样机结果套用到 24GB 等其他 SKU。", "按具体料号、模型、量化、上下文和软件版本做 PoC。", HYBRID_SOURCE),
    ("AI基础知识", "本地 AI 与云端 AI 在混合智能中如何协作？", "本地可处理合适的低延迟或敏感任务，云端可提供更大模型或弹性算力。", "应用应明确数据传输边界、模型选择、离线回退和结果审计；实际路由是产品实现与策略问题，不是硬件自动决定。", "有 RTX Spark 设备不代表所有 AI 产品自动支持混合路由。", "询问客户哪些文件绝不能上传，并验证应用的实际数据流。", HYBRID_SOURCE),
    ("Windows与兼容", "Windows ML 与混合智能是什么关系？", "Windows ML 是本地模型推理运行时之一，可帮助应用调用 CPU、GPU 或 NPU。", "微软宣布将 llama.cpp 支持带入 Windows ML；模型格式、执行提供程序、驱动与目标设备仍需验证。混合智能的云端路由不由 Windows ML 单独决定。", "支持 Windows ML 不代表任意模型已经在 RTX Spark 上获得官方性能验证。", "检查目标模型与执行提供程序，再记录端到端任务体验。", HYBRID_SOURCE),
    ("安全与隐私", "Copilot 的本地上下文、本地操作和本地模型现在都可用吗？", "微软在发布会宣布了三类能力，预计未来数月在 Copilot+ PC 逐步推出。", "本地上下文需用户许可；文件范围、操作授权、模型可用性与地区/设备支持应以实际产品版本为准。", "发布公告中的未来功能不能写成所有设备已上线。", "向客户说明当前可用版本、权限提示与数据边界。", HYBRID_SOURCE),
    ("本地AI部署", "MXC 与本地模型运行时如何配合？", "本地模型负责推理，MXC 负责约束代理调用工具或执行代码时的权限。", "可只隔离工具、插件、生成代码或整个代理；文件/网络策略与模型部署是不同配置，均需验证。", "装好 Ollama、LM Studio 或 llama.cpp 不等于自动启用 MXC。", "在演示中分别检查模型运行、代理权限和拒绝访问行为。", MXC_SOURCE),
    ("选型与销售", "GitHub Copilot 的本地模型和 MXC 演示可作为现售承诺吗？", "应先确认客户使用的版本与发布阶段。", "微软与 GitHub 说明本地/云端协调体验计划于 2026 年 10 月稍晚提供实验预览；MXC 隔离层已正式提供，两者状态不同。", "不能把未来预览写成当前全量正式可用。", "报价与培训资料注明版本、地区、预览状态和验证日期。", COPILOT_SOURCE),
]
for category, question, easy, expert, misconception, sales_tip, url in ANNOUNCEMENT_FAQ:
    FAQ.append({"id": f"FAQ-{len(FAQ)+1:03d}", "category": category, "question": question,
                "easy_answer": easy, "expert_answer": expert, "misconception": misconception,
                "sales_tip": sales_tip, "keywords": [question, category, "10.7发布会"],
                "source_url": url, "review_status": "official_2026_10_07",
                "sku_relevance": "Surface Laptop Ultra / RTX Spark", "framework_relevance": []})

# Keep terminology and version boundaries visible in the searchable training FAQ.
AGENT_TOOL_FAQ = [
    ("AI基础知识", "MCP、CLI 与 NVIDIA Skills 是同一种东西吗？", "不是。MCP 提供代理调用工具的接口，CLI 是命令行入口，Skills 是教代理如何执行一套工作流的指引。", "NVIDIA 公告介绍应用 MCP 与 CUDA-X Skills；是否能连接取决于目标应用、MCP 服务、代理客户端、权限和版本。安装 Skill 不会自动安装或授权 MCP。", "看到 Skills 库不能说所有 NVIDIA 应用已自动接入代理。", "用一个只读、脱敏任务演示工具连接，并展示权限与调用记录。", "https://blogs.nvidia.com/blog/local-ai-rtx-spark-laptops-software-updates/"),
    ("本地AI部署", "RTX Spark 用户从哪本 NVIDIA 战术手册开始？", "首次体验先看首个 Agent 手册；办公、创作、开发和多机路由再按实际任务选择。", "NVIDIA 的 RTX Spark 页面分别链接首个 Agent、生产力、创作、开发、本地推理和 PAIR 手册。先用非敏感样本做单机基线，再决定是否连接工作应用或第二台设备。", "官方手册的示例模型、时间和命令不等于每个 SKU 的实测结果。", "推荐客户先完成一次问答，再选择与本职工作相关的一个场景。", "https://build.nvidia.com/rtx-spark"),
    ("安全与隐私", "给 Agent 连接邮件和 Windows 应用时应授予什么权限？", "从只读或草稿权限开始，发送、删除、购买、发布等操作保留人工确认。", "NVIDIA 首个 Agent 和生产力手册建议优先使用应用提供的连接器/插件，并核对权限；MCP 可能需要额外配置。还应验证沙箱、调用日志、凭据保护与撤权。", "连接成功不代表所有调用都在本地，或客户资料不会出域。", "先拿脱敏样本测试只读访问与拒绝写入，再逐步放权。", "https://build.nvidia.com/rtx-spark/start-with-agent"),
    ("本地AI部署", "NVIDIA PAIR 能把两台设备的统一内存合并来运行大模型吗？", "不能。PAIR 把独立请求路由给能处理它的某一台设备。", "NVIDIA PAIR 1.0.0 手册列出 RTX Spark 的 Windows ARM64 包和 llama.cpp、Ollama、LM Studio 引擎；每个服务节点仍须独立满足模型权重、上下文和运行时内存要求。", "多机配对不等于显存池化、模型切分或单次推理加速。", "单机验证后再在受信任局域网配对，记录每次请求实际由哪台节点处理。", "https://build.nvidia.com/rtx-spark/pair"),
]
for category, question, easy, expert, misconception, sales_tip, url in AGENT_TOOL_FAQ:
    FAQ.append({"id": f"FAQ-{len(FAQ)+1:03d}", "category": category, "question": question,
                "easy_answer": easy, "expert_answer": expert, "misconception": misconception,
                "sales_tip": sales_tip, "keywords": [question, category, "MCP", "RTX Spark"],
                "source_url": url, "review_status": "official_2026_10_18",
                "sku_relevance": "RTX Spark；具体料号待验证", "framework_relevance": []})


@router.get("")
def search_faq(q: str | None = None, category: str | None = None, limit: int = Query(default=20, ge=1, le=250), lang: str = "zh-CN"):
    items = FAQ
    if category:
        items = [x for x in items if x["category"] == category]
    if q and lang != "en":
        needle = q.casefold()
        items = [x for x in items if needle in (x["question"] + x["easy_answer"] + x["expert_answer"] + x["misconception"] + " ".join(x["keywords"])).casefold()]
    if lang == "en":
        # Search both the Chinese source and available English wording. Keep
        # the source ID, category filter, and evidence URL stable.
        translated = [english_item(item) for item in items]
        if q:
            needle = q.casefold()
            translated = [item for item in translated if needle in (
                item["question"] + item["easy_answer"] + item["expert_answer"]
                + item["misconception"] + " ".join(item["keywords"])
            ).casefold()]
        return {"items": translated[:limit], "total": len(translated), "indexed_total": len(FAQ),
                "concept_total": 100 + len(ANNOUNCEMENT_FAQ) + len(AGENT_TOOL_FAQ),
                "categories": sorted(CONCEPTS), "translated_total": sum(english_item(item)["translation_status"] == "translated_draft" for item in FAQ)}
    return {"items": items[:limit], "total": len(items), "indexed_total": len(FAQ), "concept_total": 100 + len(ANNOUNCEMENT_FAQ) + len(AGENT_TOOL_FAQ), "categories": sorted(CONCEPTS)}


@router.get("/{faq_id}")
def faq_detail(faq_id: str):
    item = next((x for x in FAQ if x["id"] == faq_id), None)
    if not item:
        raise HTTPException(404, "FAQ 不存在")
    return item
