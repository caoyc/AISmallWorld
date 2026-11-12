"""动态优化的分类体系。

一个通用的分类路径树管理引擎。不预设任何分类体系，
通过用进废退机制让分类从使用中涌现。

用户可见接口：
    - SearchService: 检索分类（自然语言描述 → 分类结果）
    - CommitService: 入库分类（自然语言归类描述 → 入库结果）
    - MaintenanceService: 遗忘清理（全量衰减 + 清理；业务层按需 run_maintenance()）
"""

from .config import CategorySystemConfig, CoolingRate, EmbeddingConfig, LLMConfig, StorageConfig
from .models import CategoryRecord, CategoryResult, LLMAction
from .service.classify import SearchService
from .service.commit import CommitService
from .service.factory import build_category_system
from .engine.maintenance import MaintenanceService

__all__ = [
    "CategorySystemConfig",
    "CoolingRate",
    "EmbeddingConfig",
    "LLMConfig",
    "StorageConfig",
    "CategoryRecord",
    "CategoryResult",
    "LLMAction",
    "SearchService",
    "CommitService",
    "MaintenanceService",
    "build_category_system",
]
