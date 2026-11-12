"""（原样迁入自 bionic_agent_v2/llm/summarizer.py）"""
import logging

from .client import LLMClient
from .config import SummarizerConfig

logger = logging.getLogger(__name__)

_SUMMARY_SYSTEM_PROMPT = "请对以下内容生成简洁摘要，保留关键信息和上下文。"


class Summarizer:
    def __init__(self, config: SummarizerConfig):
        self._config = config

        provider_params = {}
        if config.num_gpu is not None:
            provider_params["num_gpu"] = config.num_gpu

        self._client = LLMClient(
            model=config.model,
            api_base=config.api_base,
            api_key=config.api_key or "",
            timeout=120.0,
            **provider_params,
        )

    async def summarize(self, text: str, system_prompt: str = _SUMMARY_SYSTEM_PROMPT,
                        target_length: int = 0) -> str:
        if len(text) < self._config.summary_min_length:
            return text

        if target_length > 0:
            system_prompt += f"摘要长度控制在{target_length}字以内。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]

        last_error = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                return await self._client.complete(
                    messages,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                )
            except Exception as e:
                last_error = e
                logger.warning("Summarize attempt %d failed: %s", attempt, e)
        logger.error("Summarize failed after %d retries: %s", self._config.max_retries, last_error)
        return text
