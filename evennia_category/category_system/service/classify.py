"""检索服务：自然语言描述 → 最终分类结果。

用户输入自然语言的对象描述或类别描述，系统内部完成
向量检索→提示语→LLM判别→调度执行全流程，
返回最终确定的分类结果。一步到位。（需求收集原话 15）
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


class SearchService:
    """检索接口：自然语言描述 → 最终分类结果。

    用户输入自然语言的对象描述或类别描述，系统内部完成
    向量检索→提示语→LLM判别→调度执行全流程，
    返回最终确定的分类结果。一步到位。（需求收集原话 15）
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

    async def search(self, description: str, top_k: int | None = None) -> list[CategoryResult]:
        """检索分类。

        Args:
            description: 自然语言的对象描述或类别描述
            top_k: 向量检索返回数量，默认取配置值

        Returns:
            最终确定的分类结果列表。可以是一条或多条。
        """
        # 1. 向量生成
        embedding = await self._embedder.embed(description)

        # 2. 向量检索
        actual_top_k = top_k or self._config.top_k
        results = self._store.query_by_embedding(embedding, actual_top_k)

        # 3-4. 构建提示语
        if not results:
            prompt = self._prompt_builder.build_empty(description)
        else:
            prompt = self._prompt_builder.build_for_search(results, description)

        # 5. LLM 调用
        llm_response = await self._llm_client.complete(
            [{"role": "user", "content": prompt}],
            temperature=self._config.llm.temperature,
            max_tokens=self._config.llm.max_tokens,
        )

        # 6. 解析 LLM 输出
        actions = parse_llm_response(llm_response)

        # 7. 执行操作
        category_results = await self._dispatcher.execute(actions)

        # 8. 返回结果
        return category_results

    async def find_similar(self, description: str, top_k: int | None = None) -> list[CategoryResult]:
        """只读语义查询：给定物品名或描述，返回库中向量最相似的若干类别。

        即 search 流程的"向量检索"中间结果直接输出——不调 LLM、不加热、不新建，
        纯只读。适合"看这个描述当前库里匹配哪些类"的查询用途。

        Args:
            description: 物品名称或自然语言描述
            top_k: 返回数量，默认取配置值

        Returns:
            按相似度（cosine 距离）从近到远排序的 CategoryResult 列表。
            复用 CategoryResult（path/document/record_id），不含距离数值；
            顺序即相似度排序。库为空时返回空列表。
        """
        # 1. 向量生成（本地 Ollama，不联网 LLM）
        embedding = await self._embedder.embed(description)

        # 2. 向量检索（只读，无任何写副作用）
        actual_top_k = top_k or self._config.top_k
        results = self._store.query_by_embedding(embedding, actual_top_k)

        # 3. 映射为 CategoryResult（丢弃 distance，顺序保留相似度排序）
        return [
            CategoryResult(
                category_path=record.category_path,
                document=record.document,
                record_id=record.id,
            )
            for record, _distance in results
        ]
