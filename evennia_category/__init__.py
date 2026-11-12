"""数字家园分类系统聚合包。

收纳 category_system(动态涌现分类引擎)及其自包含依赖 forgetting(牛顿冷却遗忘)、
llm(Embedder/LLMClient)。三者平级,category_system 内部以相对引用 `..forgetting`/`..llm`
使用依赖。

注:category_system 原为 bionic_agent_v4 记忆系统组件,依赖已去副本化迁入本包,
使其在 aismallworld 环境独立可 import。
"""
