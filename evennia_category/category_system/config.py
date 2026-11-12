"""动态优化分类体系——配置。

通用底座去副本：CoolingRate 直取 forgetting.cooling、EmbeddingConfig 直取 llm.config
（各真相源所在模块，规则1），不在本文件重定义（避免双真相源）；
本文件只保留 category 自有的 LLMConfig / StorageConfig / CategorySystemConfig。

配置成对（mirror cluster_system/cluster/config.py）：dataclass 默认值读本目录
config.toml（_load_local → _LOCAL），值单一真相源在 config.toml、可调。
"""
import os
try:
    import tomllib  # 3.11+ 内置
except ModuleNotFoundError:
    import tomli as tomllib  # 3.10 fallback（tomli 2.2.1）
from dataclasses import dataclass, field
from typing import Optional

from ..forgetting.cooling import CoolingRate
from ..llm.config import EmbeddingConfig


def _load_local() -> dict:
    """读本目录 config.toml（加载代码与配置文件同目录；本目录配置项即默认值源，代码不硬编码）。

    必填键缺失由 dataclass 默认 ``_LOCAL["key"]`` 取值时 KeyError 暴露配置未到位；
    可选键(llm_api_key)缺失为 None。config.toml 必须随 config.py 同目录提交。
    """
    cfg_path = os.path.join(os.path.dirname(__file__), "config.toml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "rb") as f:  # tomllib 要二进制模式
            return tomllib.load(f)
    return {}


_LOCAL = _load_local()


@dataclass
class LLMConfig:
    """LLM 文本生成配置（沿用 bionic_agent_v2 的 SummarizerConfig 模式）。

    Attributes:
        model: 完整模型名（含 provider 前缀），如 "anthropic/deepseek-v4-flash"（取自 config.toml llm_model；火山方舟 ark）。
        api_base: API 地址（取自 config.toml llm_api_base）。
        api_key: API Key（取自 config.toml llm_api_key；可选，缺失为 None）。
        temperature: 采样温度（结构性默认，不入 config.toml）。
        max_tokens: 最大输出 token 数（None=不限制；绝不设值，避免掐 thinking 模型 reasoning 预算）。
        num_gpu: Ollama GPU 层数（结构性默认）。
        timeout: 超时秒数（结构性默认）。
    """

    model: str = _LOCAL["llm_model"]
    api_base: str = _LOCAL["llm_api_base"]
    api_key: Optional[str] = _LOCAL.get("llm_api_key")
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    num_gpu: int = 0
    timeout: float = 60.0


@dataclass
class StorageConfig:
    """ChromaDB 存储配置（取自 config.toml）。

    Attributes:
        chroma_persist_dir: ChromaDB 持久化目录（config.toml）。
        collection_name: Collection 名称（config.toml）。
    """

    chroma_persist_dir: str = _LOCAL["chroma_persist_dir"]
    collection_name: str = _LOCAL["collection_name"]


@dataclass
class CategorySystemConfig:
    """动态优化分类体系配置。聚合各子系统配置。

    Attributes:
        storage: ChromaDB 存储配置（StorageConfig）。
        embedding: Embedding 模型配置（根共享 EmbeddingConfig，默认归 settings.py）。
        llm: LLM 文本生成配置（LLMConfig）。
        cooling_rate: 冷却速率档位名称（对应 CoolingRate 枚举；config.toml）。
        top_k: 向量检索返回数量（config.toml）。
        delta_t: 记忆添加频率（秒），物理含义为人阅读速度约每秒 7 个单元（config.toml）。
    """

    storage: StorageConfig = field(default_factory=StorageConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    cooling_rate: str = _LOCAL["cooling_rate"]
    top_k: int = _LOCAL["top_k"]
    delta_t: float = _LOCAL["delta_t"]
