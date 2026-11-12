"""（原样迁入自 bionic_agent_v2/llm/embedder.py）"""
import logging

from .client import LLMClient
from .config import EmbeddingConfig

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, config: EmbeddingConfig):
        self._config = config
        self._warmed = False

        provider_params = {}
        if config.num_gpu is not None:
            provider_params["num_gpu"] = config.num_gpu

        self._client = LLMClient(
            model=config.model,
            api_base=config.api_base,
            api_key=config.api_key or "",
            timeout=60.0,
            **provider_params,
        )

    async def warmup(self):
        """预热：通过一次 embed 调用加载模型（Ollama 由 keep_alive 常驻）。

        幂等：cl02/cl03/cl04 共享同一底层 Embedder（装配层注入单例），三 service 各调 warmup
        仅首次真预热（_warmed flag）——消除启动日志三次重复 + 三次 HTTP 往返。
        """
        if self._warmed:
            return
        logger.info("Warming up embedding model %s...", self._config.model)
        try:
            await self._client.embed("warmup", keep_alive=-1)
            logger.info("Embedding model warmed up.")
            self._warmed = True
        except Exception as e:
            logger.warning("Embedding warmup failed (server will still start): %s", e)

    async def embed(self, text: str) -> list[float]:
        last_error = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                return await self._client.embed(text, dimensions=self._config.dimension)
            except Exception as e:
                last_error = e
                logger.warning("Embedding attempt %d failed: %s", attempt, e)
        raise RuntimeError(f"Embedding failed after {self._config.max_retries} retries: {last_error}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return await self._client.embed_batch(
            texts, dimensions=self._config.dimension, batch_size=self._config.batch_size,
        )
