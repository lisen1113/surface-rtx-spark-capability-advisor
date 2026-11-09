"""Reviewed English wording for FAQ concepts; Chinese records remain authoritative.

Each tuple is term, plain answer, engineering answer, and misconception. The
paired question and sales guidance are generated from the same concept as the
Chinese FAQ, retaining its ID and evidence URL.
"""

CONCEPTS = (
    ("Artificial intelligence (AI)",
     "A broad term for computer systems performing tasks that usually require human judgment.",
     "AI covers rule-based systems, machine learning, generative models, and other approaches.",
     "AI is not synonymous with chatbots and does not guarantee correct answers."),
    ("Machine learning (ML)",
     "Systems learn patterns from data instead of relying on a hand-written rule for every case.",
     "A trained model is valid only within the scope of its data, objective, and evaluation.",
     "More data is not always better; quality and fit to the task matter."),
    ("Deep learning",
     "A way to learn complex patterns using neural networks with multiple layers.",
     "Many modern vision, speech, and large language models use deep learning, but their compute and memory needs differ greatly.",
     "Deep learning is not the best approach for every business problem."),
    ("Training",
     "The process of adjusting model parameters using data.",
     "Full training typically needs more compute, memory, time, and data governance than inference.",
     "Running a model does not mean the same device can train it."),
    ("Inference",
     "Using a trained model to process new input and produce an output.",
     "This local AI advisor mainly assesses inference; model format, runtime, and operator compatibility also matter.",
     "A model fitting in memory does not guarantee that inference will start or be usable."),
    ("Fine-tuning",
     "Continuing to train an existing model for a specific task or style.",
     "Parameter-efficient approaches such as LoRA can reduce cost, but still require a training framework, memory, and data.",
     "Fine-tuning is not the same as uploading documents to a model."),
    ("Prompt",
     "Instructions, context, and output requirements supplied to a model.",
     "Prompt structure affects output quality, input token count, time to first token, and reproducibility.",
     "A prompt cannot compensate for limited model capability, stale knowledge, or missing safety controls."),
    ("Token",
     "A basic text unit processed by a model; it is neither one Chinese character nor one English word.",
     "Tokenizers split text differently, so cost, context, and speed should use measured token counts.",
     "Character or word counts cannot be converted precisely into token counts by a fixed ratio."),
    ("Embedding vector",
     "A numerical representation of text, images, or other content that can be compared.",
     "Embeddings are often used for semantic search and RAG; model choice, dimensions, and chunking affect retrieval.",
     "High similarity does not prove factual correctness or business relevance."),
    ("Transformer",
     "A widely used model architecture that processes sequences with attention mechanisms.",
     "Transformer layer count, hidden size, attention design, and context implementation affect memory use and speed.",
     "Two Transformer models need not have the same performance or purpose."),
    ("Attention mechanism",
     "A mechanism that helps a model determine which parts of an input relate to one another.",
     "Long-context attention increases compute and KV-cache pressure; implementations have different costs.",
     "Doubling context length does not necessarily double resource use; it may cost more."),
    ("Mixture-of-experts (MoE) model",
     "A model that activates only some expert networks for each input rather than all of its parameters.",
     "MoE can reduce compute per token, while all expert weights usually still need storage and movement, with routing and communication overhead.",
     "Fewer active parameters do not mean only those parameters must be loaded into memory."),
    ("Dense model",
     "A model that typically uses all its main parameters for each inference step.",
     "Its capacity is relatively straightforward to estimate, and compute per token often tracks total parameter count more directly.",
     "The Dense or MoE label alone does not determine quality at the same parameter count."),
    ("Parameter count",
     "The number of trainable values in a model; B commonly means billions.",
     "Parameter count affects weight memory and compute, but does not by itself determine quality, speed, or task success.",
     "A 70B model is not necessarily better than a newer 32B model on every task."),
    ("Multimodal model",
     "A model that can process images, audio, or video in addition to text.",
     "Vision encoders, audio modules, and media resolution add memory and compute needs.",
     "Image input does not imply video input or image generation support."),
    ("Diffusion model",
     "A model that generates images or video through progressive denoising.",
     "Sampling steps, resolution, batch size, precision, and workflow graph all affect time and memory.",
     "A modest parameter count can still require substantial memory for intermediate tensors."),
    ("Autoregressive model",
     "A model that predicts the next token or element sequentially.",
     "LLM decoding is usually autoregressive, so output length directly affects total generation time.",
     "High peak compute does not necessarily remove per-token generation latency."),
    ("Small language model (SLM)",
     "A relatively compact language model suited to specific tasks and device-side deployment.",
     "An SLM often uses less memory and has lower latency, but suitability must be judged on the target task.",
     "A smaller model is not automatically low quality or inherently safer."),
)


def english_item(item: dict) -> dict:
    """Translate a reviewed entry or clearly mark its Chinese source status."""
    result = dict(item)
    index = int(item["id"].split("-")[1]) - 1
    if index >= 2 * len(CONCEPTS):
        result["translation_status"] = "pending"
        return result
    term, plain, engineering, misconception = CONCEPTS[index // 2]
    result["category"] = "AI fundamentals" if index < 18 else "Model architectures"
    if index % 2 == 0:
        result.update(
            question=f"What is {term}?",
            easy_answer=plain,
            expert_answer=engineering,
            misconception=misconception,
            sales_tip=f"First establish whether the customer needs {term}; explain its scope, verification conditions, and unknowns.",
        )
    else:
        result.update(
            question=f"How does {term} affect Surface Laptop Ultra selection and use?",
            easy_answer=engineering,
            expert_answer=f"Do not select a device based on the {term} label alone. Verify the exact Part Number, memory, software version, workload, and evidence level.",
            misconception=misconception,
            sales_tip=f"Do not turn {term} into a performance promise. Run a proof of concept using the customer's real workload.",
        )
    result["translation_status"] = "reviewed"
    return result
