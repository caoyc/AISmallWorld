"""LLM 输出解析与操作执行。

包含 parse_llm_response（模块级函数）和 Dispatcher（操作执行器）。
"""

import json
import logging
import re
import time
from uuid import uuid4

from ..config import CategorySystemConfig, CoolingRate
from ...llm.embedder import Embedder
from ..models import CategoryRecord, CategoryResult, LLMAction
from ..storage.category_store import CategoryStore
from .path_validator import PathValidator
from ...forgetting.cooling import NewtonCooling

logger = logging.getLogger(__name__)


def parse_llm_response(response: str) -> list[LLMAction]:
    """解析 LLM 返回的原始文本为结构化操作列表。

    LLM 返回格式约定为 JSON 数组，可能包裹在 markdown code block 中。
    本函数提取 JSON（经 _extract_json，应对围栏/废话/截断）并映射为 LLMAction 对象。

    Args:
        response: LLM 生成的原始文本响应

    Returns:
        解析后的操作列表。解析失败或无有效项时返回空列表。
    """
    data = _extract_json(response)
    if data is None:
        return []

    if not isinstance(data, list):
        logger.warning("LLM 返回的 JSON 不是数组: %s", type(data).__name__)
        return []

    actions = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.warning("LLM 返回的第 %d 项不是对象，跳过", i + 1)
            continue

        action_type = item.get("action")
        if action_type not in ("select", "create"):
            logger.warning("LLM 返回的第 %d 项 action='%s' 无效，跳过", i + 1, action_type)
            continue

        if action_type == "select":
            record_id = item.get("record_id")
            if not record_id:
                logger.warning("LLM 返回的第 %d 项 select 缺少 record_id，跳过", i + 1)
                continue
            actions.append(LLMAction(action="select", record_id=str(record_id)))

        elif action_type == "create":
            category_path = item.get("category_path")
            document = item.get("document")
            if not category_path or not document:
                logger.warning("LLM 返回的第 %d 项 create 缺少 category_path 或 document，跳过", i + 1)
                continue
            actions.append(LLMAction(
                action="create",
                category_path=str(category_path),
                document=str(document),
            ))

    return actions


# markdown json 代码块起始定位符（符合大模型认知习惯，CL-14 §3.1 用户确认）
_JSON_FENCE_START = "```json"


def _extract_json(text: str) -> list | dict | None:
    """从文本中提取 JSON。

    主路径：```json 定位符锚定起始 + 括号匹配定束 + 截断恢复（应对围栏/废话/截断，
    不依赖大模型返回纯 JSON——铁律：大模型可能画蛇添足加废话/不闭合围栏）。
    兜底  ：原直过 + 完整围栏正则（向后兼容无围栏纯 JSON / 完整围栏场景）。

    Args:
        text: 可能包含 JSON 的文本

    Returns:
        解析后的 Python 对象，失败返回 None
    """
    # 主路径
    result = _extract_by_locator(text)
    if result is not None:
        return result
    # 兜底（向后兼容）
    return _extract_legacy(text)


def _extract_by_locator(text: str) -> list | dict | None:
    """主路径：```json 定位符锚定起始 + 括号匹配定束 + 截断恢复。"""
    # 1. 锚定起始：首个 ```json 之后；无围栏则取全文（兜底无围栏场景）
    idx = text.find(_JSON_FENCE_START)
    content = text[idx + len(_JSON_FENCE_START):] if idx >= 0 else text
    # 2. 找首个 [ （JSON 数组起始）
    start = content.find("[")
    if start < 0:
        return None
    # 3. 括号匹配定束（结束不依赖围栏闭合）
    end = _match_brackets(content, start)
    if end is not None:
        try:
            return json.loads(content[start:end + 1])
        except (json.JSONDecodeError, TypeError):
            pass  # 匹配到但解析失败，落截断恢复/兜底
    # 4. 截断恢复（补 ]，返回前 N 个完整对象）
    recovered = _recover_truncated(content, start)
    if recovered is not None:
        try:
            return json.loads(recovered)
        except (json.JSONDecodeError, TypeError):
            pass
    return None


def _match_brackets(s: str, start: int) -> int | None:
    """从 start（[ 位置）括号深度匹配，返回匹配的 ] 索引；截断返回 None。

    处理字符串内括号：``"`` 切换 in_str，``\\`` 转义下一字符不计。
    """
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(s)):
        c = s[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                return i
    return None  # 到末尾未归 0 = 截断


def _recover_truncated(s: str, start: int) -> str | None:
    """截断恢复：截到最后一个完整对象（深度回到 1 时的 }），补 ]。

    返回已完整的前 N 个对象，丢弃残缺对象（部分恢复 > 全丢）。
    """
    depth = 0
    in_str = False
    escape = False
    last_obj_end = -1
    for i in range(start, len(s)):
        c = s[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 1 and c == "}":   # 数组内一个完整对象结束
                last_obj_end = i
    if last_obj_end < 0:
        return None
    return s[start:last_obj_end + 1] + "]"


def _extract_legacy(text: str) -> list | dict | None:
    """兜底：原 _extract_json 逻辑（纯 JSON 直过 + 完整围栏正则）。向后兼容。"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    patterns = [
        r"```json\s*\n(.*?)\n```",
        r"```\s*\n(.*?)\n```",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except (json.JSONDecodeError, TypeError):
                continue
    logger.warning("无法从 LLM 响应中提取 JSON: %s", text)
    return None


class Dispatcher:
    """解析 LLM 结构化输出，执行 boost/create 操作。（需求收集原话 15）

    LLM 返回的 action 列表由 Dispatcher 解析并执行，
    对 CategoryStore 进行实际的增改操作。
    """

    def __init__(self, store: CategoryStore, embedder: Embedder, config: CategorySystemConfig):
        """初始化。

        Args:
            store: 分类存储
            embedder: 向量生成器（create 时需要为新记录生成 embedding）
            config: 系统配置
        """
        self._store = store
        self._embedder = embedder
        self._config = config
        self._cooling_rate = CoolingRate[config.cooling_rate]

    async def execute(self, actions: list[LLMAction]) -> list[CategoryResult]:
        """解析并执行 LLM 返回的操作列表。

        Args:
            actions: LLM 返回的结构化操作列表

        Returns:
            执行后的分类结果列表
        """
        now = time.time()
        results = []

        for action in actions:
            if action.action == "select":
                result = self._execute_select(action, now)
                if result:
                    results.append(result)

            elif action.action == "create":
                result = await self._execute_create(action, now)
                if result:
                    results.append(result)

        return results

    def _execute_select(self, action: LLMAction, now: float) -> CategoryResult | None:
        """执行 select 操作：加热被选中的记录。

        Args:
            action: select 操作
            now: 当前时间戳

        Returns:
            分类结果，失败返回 None
        """
        record = self._store.get(action.record_id)
        if record is None:
            logger.warning("select 操作的记录 %s 不存在，跳过", action.record_id)
            return None

        # 加热算法（原话 10）：先衰减再 +1
        memory_remain = NewtonCooling.newton_cooling(
            record.valid_count, now - record.last_update_time, self._cooling_rate
        )
        new_count = memory_remain + 1
        self._store.update_heat(action.record_id, new_count)

        return CategoryResult(
            category_path=record.category_path,
            document=record.document,
            record_id=record.id,
        )

    async def _execute_create(self, action: LLMAction, now: float) -> CategoryResult | None:
        """执行 create 操作：验证路径、创建记录。

        Args:
            action: create 操作
            now: 当前时间戳

        Returns:
            分类结果，失败返回 None
        """
        # 路径校验并矫正：非法字符→'_'、冗余//与结尾/归一；仅结构性非法（空/非绝对）才跳过
        corrected, error_msg = PathValidator.validate(action.category_path)
        if error_msg:
            logger.warning("create 操作的路径 '%s' 不合法: %s，跳过", action.category_path, error_msg)
            return None
        action.category_path = corrected   # 用矫正后的合法路径建（下游 record/result 取此字段）

        # 创建记录
        embedding = await self._embedder.embed(action.document)
        record_id = str(uuid4())
        record = CategoryRecord(
            id=record_id,
            category_path=action.category_path,
            document=action.document,
            embedding=embedding,
            valid_count=1.0,
            last_update_time=now,
        )
        self._store.add(record)

        return CategoryResult(
            category_path=action.category_path,
            document=action.document,
            record_id=record_id,
        )
