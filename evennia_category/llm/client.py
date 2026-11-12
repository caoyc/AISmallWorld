"""统一 LLM 客户端：基于 LiteLLM 封装，对外透明无感。

（原样迁入自 bionic_agent_v2/llm/client.py）
"""
import logging

import litellm

litellm.suppress_debug_info = True
logging.getLogger("LiteLLM").setLevel(logging.WARNING)


class LLMClient:
    """统一 LLM 客户端。所有 provider 差异由 LiteLLM 处理，调用方无需感知。"""

    def __init__(self, model: str, api_base: str = "", api_key: str = "",
                 timeout: float = 60.0, **provider_params):
        """
        Args:
            model: 完整模型名（含 provider 前缀），如 "ollama_chat/qwen3.5:4b"、"anthropic/deepseek-v4-flash"
            api_base: API 地址
            api_key: API Key
            timeout: 超时秒数
            **provider_params: provider 特有参数（如 num_gpu=-1, keep_alive=-1），自动透传
        """
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        self._timeout = timeout
        self._provider_params = provider_params

    async def complete(self, messages: list[dict], temperature: float | None = None,
                       max_tokens: int | None = None, **kwargs) -> str:
        """Chat completion，返回文本内容。

        Args:
            messages: OpenAI 格式消息列表
            temperature: 采样温度
            max_tokens: 最大输出 token 数
            **kwargs: 额外参数，透传给 LiteLLM
        """
        params = {
            "model": self._model,
            "messages": messages,
            "timeout": self._timeout,
            **self._provider_params,
            **kwargs,
        }
        if self._api_base:
            params["api_base"] = self._api_base
        if self._api_key:
            params["api_key"] = self._api_key
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens

        response = await litellm.acompletion(**params)
        return response.choices[0].message.content

    async def embed(self, text: str, dimensions: int | None = None, **kwargs) -> list[float]:
        """Embedding，返回向量。

        Args:
            text: 待嵌入文本
            dimensions: 向量维度（部分模型支持）
            **kwargs: 额外参数，透传给 LiteLLM
        """
        params = {
            "model": self._model,
            "input": [text],
            "timeout": self._timeout,
            **self._provider_params,
            **kwargs,
        }
        if self._api_base:
            params["api_base"] = self._api_base
        if self._api_key:
            params["api_key"] = self._api_key
        if dimensions is not None:
            params["dimensions"] = dimensions

        response = await litellm.aembedding(**params)
        return response.data[0]["embedding"]

    async def embed_batch(self, texts: list[str], dimensions: int | None = None,
                          batch_size: int = 32, **kwargs) -> list[list[float]]:
        """批量 Embedding。

        Args:
            texts: 文本列表
            dimensions: 向量维度
            batch_size: 每批数量
            **kwargs: 额外参数，透传给 LiteLLM
        """
        results = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            params = {
                "model": self._model,
                "input": batch,
                "timeout": self._timeout,
                **self._provider_params,
                **kwargs,
            }
            if self._api_base:
                params["api_base"] = self._api_base
            if self._api_key:
                params["api_key"] = self._api_key
            if dimensions is not None:
                params["dimensions"] = dimensions

            response = await litellm.aembedding(**params)
            batch_results = [item["embedding"] for item in response.data]
            results.extend(batch_results)
        return results
