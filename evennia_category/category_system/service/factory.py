"""category_system 自包含装配工厂（配置内化·CL4-04 §3.5；CL PMI 回归扩为建库+共现+PMI 一条龙）。

配置内化原则：工厂归 category_system，入参用 category_system 自己的 CategorySystemConfig
（不再寄生根 summary 的 SummaryConfig）。

自包含（CL PMI 回归）：build_category_system 一次性建出 分类器(SearchService) + 一个 CategoryStore
（分类加热与 PMI 边际共读同一份）+ 共现表（为 PMI 而生）+ PMI（log_N/alpha 由 config.cooling_rate+
delta_t 推导，不寄生 ClusterConfig）。返回 (SearchService, CooccurrenceService, PMICalculator,
MaintenanceService)，供 cluster_system 装配单线接线——assembly 不再自建 CategoryStore/共现/PMI，
根除两库漂移
（PMI 用分类加热的库 → vc_a/vc_b 有值 → 跨 cat 边可成）。
"""
import math

from ..config import CategorySystemConfig, CoolingRate


def build_category_system(config: CategorySystemConfig, cooccurrence_db_path: str):
    """实例化 category_system 自包含单元：分类器 + 共现表 + PMI（一个 CategoryStore，分类加热与 PMI 边际共读）。

    配置内化：入参 config 为 CategorySystemConfig（storage/embedding/llm/cooling_rate/delta_t）。
    cooccurrence_db_path 由调用方（assembly）按实例数据目录给入（共现 sqlite 落实例目录）。
    PMI 的 log_N/alpha 从 config.cooling_rate+delta_t 推导——与原 ClusterConfig 同源（CoolingRate+dt 纯函数）。

    Args:
        config: category_system 配置（storage/embedding/llm/cooling_rate/delta_t）。
        cooccurrence_db_path: 共现表 sqlite 落库路径（由 assembly 按实例数据目录给入）。

    Returns:
        (search, cooccurrence, pmi, maintenance)：SearchService（分类器）、CooccurrenceService（共现表）、
        PMICalculator、MaintenanceService（遗忘清理，共用同一个 CategoryStore；供业务层按需 run_maintenance()）。
    """
    import chromadb
    from .classify import SearchService
    from ..engine.dispatcher import Dispatcher
    from ...llm.client import LLMClient
    from ...llm.embedder import Embedder
    from ..prompt.builder import PromptBuilder
    from ..storage.category_store import CategoryStore
    from ..storage.cooccurrence_store import CooccurrenceStore
    from ..storage.cooccurrence_service import CooccurrenceService
    from ...forgetting.cooling import NewtonCooling
    from ..engine.pmi import PMICalculator
    from ..engine.maintenance import MaintenanceService

    # —— 一个 CategoryStore（分类加热 + PMI 边际共读同一份；根除两库漂移）——
    chroma_client = chromadb.PersistentClient(path=config.storage.chroma_persist_dir)
    store = CategoryStore(chroma_client, config.storage.collection_name, config.embedding.dimension)

    # —— 分类器（SearchService：分类即加热上面的 store）——
    embedder = Embedder(config.embedding)
    llm_client = LLMClient(config.llm.model, config.llm.api_base, config.llm.api_key or "",
                           config.llm.timeout, num_gpu=config.llm.num_gpu)
    pb = PromptBuilder(config)
    disp = Dispatcher(store, embedder, config)
    search = SearchService(store, embedder, pb, llm_client, disp, config)

    # —— 共现表（为 PMI 而生）+ PMI（log_N/alpha 自 category config 推导）——
    cooling = CoolingRate[config.cooling_rate]
    cooccurrence = CooccurrenceService(CooccurrenceStore(cooccurrence_db_path, cooling))
    log_N = math.log(NewtonCooling.steady_state_total(cooling, config.delta_t))
    pmi = PMICalculator(log_N, cooling, cooccurrence, store)

    # —— 遗忘清理（共用同一个 CategoryStore：衰减/清理与分类加热同源；供业务层按需 run_maintenance()）——
    maintenance = MaintenanceService(store, config)

    return search, cooccurrence, pmi, maintenance
