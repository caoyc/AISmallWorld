"""提示语构建。将向量检索结果封装为 LLM 提示语。三种场景对应三种构建方法。

所有场景共享一套核心准则（见 _core_principles），承载分类体系的设计意图：
用进废退 + 概念本身 + 常识优先 + 唯一判断标准是"让体系更优"。
"""

from ..models import CategoryRecord


class PromptBuilder:
    """将向量检索结果封装为 LLM 提示语。三种场景对应三种构建方法。"""

    def __init__(self, config):
        """初始化。

        Args:
            config: CategorySystemConfig
        """
        self._config = config

    def _core_principles(self) -> str:
        """所有场景共享的核心准则。承载体系设计意图。"""
        return (
            "核心准则（高于具体动作）：\n"
            "- 分类不追求学术严谨，而追求契合常识体验\n"
            '- 分类的核心是"概念本身"：为这个概念选择或创建最契合它本身的归类节点，而非它的相关概念（如来源、衍生、分类学上下级）\n'
            "- 每一次选用或创建，唯一判断标准是：是否让整个分类体系更合理——可在现有路径下创建子分类，也可整条路径全新创建\n"
            "- 只据实际出现的需求处理，不臆测、不预设，追求反映客观，未出现就是不存在\n"
            "- 系统通过\"用进废退\"运作——频繁引用的分类被强化、长期不用的自然衰减，"
            "逐渐浮现出更合理的体系（类似蚁群觅食演化出最短路径）"
        )

    def build_for_search(self, results: list[tuple[CategoryRecord, float]],
                         description: str) -> str:
        """构建检索场景的提示语。

        场景：用户描述一个概念，LLM 在候选类别中选用最契合的，或在确有必要时新建。
        检索不是目的，而是优化分类体系的必要前提——每次选用强化对应路径（用进），
        每次合理的新建都在补全体系。

        Args:
            results: [(CategoryRecord, distance), ...] 向量检索结果
            description: 用户输入的自然语言描述

        Returns:
            完整的提示语文本
        """
        candidates = ""
        for i, (record, distance) in enumerate(results, 1):
            candidates += (
                f"  {i}. id: {record.id} | "
                f"路径: {record.category_path} | "
                f"描述: {record.document} | "
                f"热度: {record.valid_count:.1f}（热度反映该分类被强化的程度，越高越稳固）\n"
            )

        prompt = f"""你是一个分类体系的维护助手。

{self._core_principles()}

本次任务：用户提供待查询的概念、描述或两者的组合，系统返回该概念对应的路径类别——已有契合类别则选用（并强化），没有契合的则为该概念新建一个。检索是优化体系的前提，而非目的：每次选用强化对应路径（用进），每次合理新建补全体系。

用户描述：{description}
候选类别（按语义相似度排序）：
{candidates}
选用与创建规则：
- 路径格式：Linux 绝对路径（/开头），层级用 / 分隔
- 依用户描述提供的上下文，匹配最契合"概念本身"的归类；候选热度可作为该路径稳固程度的参考
- 契合判定：只有刻画"概念本身"的候选才算契合；若候选都只是与概念关联（实例、可作用对象、相关物）而非概念本身，不要将就 select，应为该概念新建类别
- 一致性目标：同一类型应归到同一路径；同词多义的不同语义对应不同归类
- 创建唯一性：即使概念多义且上下文不足，也只创建一条路径，不同时创建多个（如"苹果"无上下文时，创建"水果/苹果"或"手机/苹果"均可）；偏向哪条无妨——遗忘机制对偏好有较强包容度
- 返回覆盖性：当上下文不足以判定单一语义时，若已有多条路径都契合，应输出多个 select 一并返回（如"苹果"无上下文，且"水果/苹果"与"手机/苹果"都已存在，则两者都 select 返回）
- 新建的 document 必须自包含，三段式：①特征描述 ②边界定义 ③特例声明（③可选，确有特例才写，不得生编；）

输出格式：JSON 数组（以 ```json 代码块包裹），每个元素为以下之一：
- 选用：{{"action": "select", "record_id": "候选列表中对应的完整 UUID"}}
- 新建：{{"action": "create", "category_path": "/路径（Linux 绝对路径）", "document": "三段式自包含描述"}}

请以 ```json 开头，将 JSON 数组用 markdown 代码块包裹输出，除代码块外不要输出任何其他内容。"""
        return prompt

    def build_for_commit(self, results: list[tuple[CategoryRecord, float]],
                         description: str) -> str:
        """构建入库场景的提示语。

        场景：用户提供一个设计好的路径类别（及可选描述），或仅描述归类意图；
        系统据此入库，返回实际入库的路径类别。路径明确时如实采用；仅意图时参考现有候选、理解用户意图确定路径。

        Args:
            results: [(CategoryRecord, distance), ...] 向量检索结果（参考）
            description: 用户提交的路径类别、描述、或两者的组合

        Returns:
            完整的提示语文本
        """
        references = ""
        if results:
            for i, (record, distance) in enumerate(results, 1):
                references += (
                    f"  {i}. 路径: {record.category_path} | "
                    f"描述: {record.document}\n"
                )
        else:
            references = "  （无现有类别）\n"

        prompt = f"""你是一个分类体系的入库助手。

{self._core_principles()}

本次任务：用户提交路径类别（及可选描述）或归类意图；系统入库，并返回实际入库的路径类别。

用户提交：{description}
现有类别（参考，按语义相似度排序）：
{references}
入库规则：
- 路径格式：Linux 绝对路径（/开头），层级用 / 分隔
- 描述：用户提供了则采用用户的；未提供则为该路径补自包含的三段式描述（①特征描述 ②边界定义 ③特例声明，③可选、确有特例才写、不得生编；）
- 返回实际入库的路径类别

输出格式：JSON 数组（以 ```json 代码块包裹），每个元素：
- {{"action": "create", "category_path": "/路径（Linux 绝对路径）", "document": "三段式自包含描述"}}

请以 ```json 开头，将 JSON 数组用 markdown 代码块包裹输出，除代码块外不要输出任何其他内容。"""
        return prompt

    def build_empty(self, description: str) -> str:
        """构建类库为空时的提示语。

        场景：系统首次使用，无现有类别，LLM 根据描述为概念创建初始归类路径。

        Args:
            description: 用户输入的自然语言描述

        Returns:
            完整的提示语文本
        """
        prompt = f"""你是一个分类体系的初始化助手。类库当前为空，请根据描述为概念创建初始归类路径。

{self._core_principles()}

本次任务：从零开始为概念落位。聚焦概念本身，不预设整个体系。

用户描述：{description}
规则：
- 路径格式：Linux 绝对路径（/开头），层级用 / 分隔
- 创建唯一性：即使概念多义且上下文不足，也只创建一条路径，不同时创建多个（如"苹果"无上下文时，创建"水果/苹果"或"手机/苹果"均可）；偏向哪条无妨——遗忘机制对偏好有较强包容度
- 新建的 document 必须自包含，三段式：①特征描述 ②边界定义 ③特例声明（③可选，确有特例才写，不得生编；）

输出格式：JSON 数组（以 ```json 代码块包裹），每个元素：
- {{"action": "create", "category_path": "/路径（Linux 绝对路径）", "document": "三段式自包含描述"}}

请以 ```json 开头，将 JSON 数组用 markdown 代码块包裹输出，除代码块外不要输出任何其他内容。"""
        return prompt
