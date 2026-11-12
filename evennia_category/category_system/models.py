"""动态优化分类体系——数据模型。"""

import time
from dataclasses import dataclass, field


@dataclass
class CategoryRecord:
    """分类路径记录。对应 ChromaDB 中的一条记录。

    Attributes:
        id: 记录唯一标识（UUID）
        category_path: 分类完整路径（Linux 绝对路径格式）
        document: 类别说明（自包含，闭包性）
        embedding: document 的向量
        valid_count: 热度（遗忘机制的作用对象）
        last_update_time: 上次更新时间戳（秒）
    """

    id: str
    category_path: str
    document: str
    embedding: list[float]
    valid_count: float = 1.0
    last_update_time: float = field(default_factory=time.time)


@dataclass
class LLMAction:
    """LLM 返回的单条操作指令。Dispatcher 解析后执行。

    Attributes:
        action: "select"（选用现有）或 "create"（新增）
        record_id: 选用时为已有记录 UUID
        category_path: 分类路径（新增时 LLM 生成）
        document: 类别说明（新增时 LLM 生成，闭包性）
    """

    action: str  # "select" | "create"
    record_id: str | None = None  # select 时有值
    category_path: str | None = None  # create 时有值
    document: str | None = None  # create 时有值


@dataclass
class CategoryResult:
    """返回给用户的单条分类结果。两个用户接口统一使用。

    Attributes:
        category_path: 分类完整路径
        document: 类别说明
        record_id: 记录 UUID
    """

    category_path: str
    document: str
    record_id: str
