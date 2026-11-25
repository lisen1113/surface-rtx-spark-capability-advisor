"""Evidence-backed deployment compatibility catalog."""
from fastapi import APIRouter

router=APIRouter(prefix="/api/knowledge",tags=["knowledge"])

FRAMEWORKS=[
 {"project":"LM Studio","version":"0.4.24","native_windows_arm64":"supported","wsl2":"not_required","container":"not_primary","external_server":"supported","source_url":"https://lmstudio.ai/docs/app/system-requirements","verified_on":"2026-10-13","notes":"官方系统要求明确列出 Windows ARM；具体 RTX Spark GPU 加速运行时仍需在目标 SKU 实测。"},
 {"project":"llama.cpp","version":"b11430","native_windows_arm64":"supported","wsl2":"supported_via_linux","container":"linux_arm64_available","external_server":"supported","source_url":"https://github.com/ggml-org/llama.cpp/releases","verified_on":"2026-10-13","notes":"官方发布资产列出 Windows ARM64 CPU、CUDA 13 与 Vulkan；应固定发布版并逐一验证后端。"},
 {"project":"Ollama","version":"0.34.0","native_windows_arm64":"release_asset_present","wsl2":"linux_arm64_available","container":"linux_arm64_available","external_server":"supported","source_url":"https://github.com/ollama/ollama/releases/tag/v0.34.0","verified_on":"2026-10-13","notes":"官方发布流程包含 windows-arm64 资产；RTX Spark GPU 后端兼容性不能仅由安装包存在推断。"},
 {"project":"vLLM","version":"current official docs","native_windows_arm64":"not_supported_natively","wsl2":"documented_option_requires_validation","container":"linux_primary","external_server":"recommended","source_url":"https://docs.vllm.ai/en/latest/getting_started/installation/gpu/","verified_on":"2026-10-13","notes":"官方要求 Linux，并说明 Windows 可通过 WSL；Windows ARM64 与 RTX Spark 的 CUDA 路径须实测。"},
 {"project":"SGLang","version":"unverified","native_windows_arm64":"unknown","wsl2":"unknown","container":"linux_expected_unverified","external_server":"recommended_pending_verification","source_url":"https://docs.sglang.ai/","verified_on":"2026-10-13","notes":"尚未取得足以确认 Windows ARM64 支持的官方证据，保持未知。"},
 {"project":"TensorRT-LLM","version":"1.3.0rc27","native_windows_arm64":"not_supported","wsl2":"linux_only_requires_validation","container":"official_ngc_linux","external_server":"recommended","source_url":"https://nvidia.github.io/TensorRT-LLM/1.3.0rc27/installation/installation-guide.html","verified_on":"2026-10-13","notes":"官方安装路径为 Linux/NGC；原生 Windows 支持已弃用。WSL2 GPU 与目标硬件仍需验证。"},
]

@router.get("/frameworks")
def frameworks():
 return {"items":FRAMEWORKS,"disclaimer":"安装支持不等于目标模型、量化、GPU 后端或性能已验证。"}
