"""入库服务：自然语言归类描述 → 入库结果。

用户输入自然语言的归类描述（如"放到工具下面的切割工具"），
LLM 将其转化为标准路径+描述，系统执行入库。一步到位。（需求收集原话 15）
"""

import logging

from ..config import CategorySystemConfig
from ...llm.embedder import Embedder
from ...llm.client import LLMClient
from ..prompt.builder import PromptBuilder
from ..models import CategoryResult
from ..storage.category_store import CategoryStore
from ..engine.dispatcher import Dispatcher, parse_llm_response

logger = logging.getLogger(__name__)


class CommitService:
    """入库接口：自然语言归类描述 → 入库结果。

    用户输入自然语言的归类描述（如"放到工具下面的切割工具"），
    LLM 将其转化为标准路径+描述，系统执行入库。一步到位。（需求收集原话 15）
    """

    def __init__(self, store: CategoryStore, embedder: Embedder,
                 prompt_builder: PromptBuilder, llm_client: LLMClient,
                 dispatcher: Dispatcher, config: CategorySystemConfig):
        """初始化。

        Args:
            store: 分类存储
            embedder: 向量生成器
            prompt_builder: 提示语构建器
            llm_client: 大模型客户端（用于文本生成）
            dispatcher: 操作调度器
            config: 系统配置
        """
        self._store = store
        self._embedder = embedder
        self._prompt_builder = prompt_builder
        self._llm_client = llm_client
        self._dispatcher = dispatcher
        self._config = config

    async def commit(self, description: str) -> list[CategoryResult]:
        """入库分类。

        Args:
            description: 自然语言的归类描述

        Returns:
            入库的分类结果列表。
        """
        # 1. 向量生成
        embedding = await self._embedder.embed(description)

        # 2. 向量检索现有类别作为参考
        results = self._store.query_by_embedding(embedding, self._config.top_k)

        # 3. 构建提示语
        prompt = self._prompt_builder.build_for_commit(results, description)

        # 4. LLM 调用
        llm_response = await self._llm_client.complete(
            [{"role": "user", "content": prompt}],
            temperature=self._config.llm.temperature,
            max_tokens=self._config.llm.max_tokens,
        )

        # 5. 解析 LLM 输出
        actions = parse_llm_response(llm_response)

        # 6. 执行操作
        category_results = await self._dispatcher.execute(actions)

        # 7. 返回结果
        return category_results
