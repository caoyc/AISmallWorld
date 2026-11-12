"""llm 配置（Embedder/Summarizer 创建函数所在模块，规则1）：config.py + config.toml 成对。

配置类从 config/settings.py 迁入（真相源归创建函数模块），默认值读本目录 config.toml（_LOCAL），
模式同 cluster_system/cluster/config.py。api_key 可选（缺失为 None），其余必填（缺失 KeyError 暴露
配置未到位）。context_length 已删（Embedder/Summarizer 两 config 均清：warmup 连带死字段，零消费）。

config/settings.py re-export 壳已删：消费方直取 llm.config（EmbeddingConfig/SummarizerConfig），不再经转发壳。
"""
from __future__ import annotations
import os
try:
    import tomllib  # 3.11+ 内置
except ModuleNotFoundError:
    import tomli as tomllib  # 3.10 fallback（tomli 2.2.1）
from dataclasses import dataclass
from typing import Optional


def _load_local() -> dict:
    """读本目录 config.toml（加载代码与配置文件同目录；本目录配置项即默认值源，代码不硬编码）。"""
    cfg_path = os.path.join(os.path.dirname(__file__), "config.toml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "rb") as f:  # tomllib 要二进制模式
            return tomllib.load(f)
    return {}


_LOCAL = _load_local()
_EMBED = _LOCAL.get("embedding", {})
_SUMM = _LOCAL.get("summarizer", {})

# max_tokens：TOML 无 null，用 -1 表达 None（不限制）。键省略(None)/≤0 → None；正值透传。
_mt_raw = _SUMM.get("max_tokens")
_MAX_TOKENS: Optional[int] = None if (_mt_raw is None or _mt_raw <= 0) else _mt_raw


@dataclass
class EmbeddingConfig:
    """Embedding 模型配置（Embedder 创建函数消费）。默认值取自本目录 config.toml[embedding]。

    Attributes:
        model: 完整模型名（含 provider 前缀）。
        api_base: API 地址。
        api_key: API Key（可选，缺失为 None）。
        dimension: 向量维度。
        batch_size: 批量 embed 每批数量。
        max_retries: embed 失败重试次数。
        num_gpu: Ollama GPU 层数（provider 参数）。
    """
    model: str = _EMBED["model"]
    api_base: str = _EMBED["api_base"]
    api_key: Optional[str] = _EMBED.get("api_key")
    dimension: int = _EMBED["dimension"]
    batch_size: int = _EMBED["batch_size"]
    max_retries: int = _EMBED["max_retries"]
    num_gpu: int = _EMBED["num_gpu"]


@dataclass
class SummarizerConfig:
    """摘要 LLM 配置（Summarizer 创建函数消费）。默认值取自本目录 config.toml[summarizer]。

    Attributes:
        model: 完整模型名（含 provider 前缀）。
        api_base: API 地址。
        api_key: API Key（可选，缺失为 None）。
        temperature: 采样温度。
        max_tokens: 最大输出 token 数。-1/省略/≤0 → None（不限制）；正值透传。TOML 无 null，用 -1 表达 None；绝不设正值（避免掐 thinking 模型 reasoning 预算）。
        summary_min_length: 短文本阈值（低于此长度不调 LLM，原样返回）。
        max_retries: summarize 失败重试次数。
        num_gpu: Ollama GPU 层数（provider 参数）。
    """
    model: str = _SUMM["model"]
    api_base: str = _SUMM["api_base"]
    api_key: Optional[str] = _SUMM.get("api_key")
    temperature: float = _SUMM["temperature"]
    max_tokens: Optional[int] = _MAX_TOKENS   # -1/省略/≤0→None（不限制）；TOML 无 null 用 -1 表 None；绝不设正值
    summary_min_length: int = _SUMM["summary_min_length"]
    max_retries: int = _SUMM["max_retries"]
    num_gpu: int = _SUMM["num_gpu"]
