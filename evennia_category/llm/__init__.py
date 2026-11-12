"""bionic_agent_v4 公共 LLM 基础设施层。

原样迁入自 bionic_agent_v2/llm/（CL-15 去引用化）：
- client.LLMClient / embedder.Embedder / summarizer.Summarizer

保持版本间绝对独立（v3 自持副本，零 bionic_agent_v2 import）。
"""
from .client import LLMClient
from .embedder import Embedder
from .summarizer import Summarizer

__all__ = ["LLMClient", "Embedder", "Summarizer"]
