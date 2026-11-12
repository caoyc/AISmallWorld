# evennia_category 环境说明

## 定位(最重要)

**evennia_category 是 evennia_game 的辅助开发工具,不集成到游戏运行时系统。**

- **用途**:开发阶段辅助选用类别——新增物品/分类时,用 category_system 帮忙判断"这个新东西该归到哪个现有类别",保障开发期间分类命名/归属前后一致。
- **不集成**:游戏 Evennia(survival/ + evennia_game/)运行时**完全不 import** evennia_category。它是独立工具,独立环境,独立运行。
- **解耦意义**:category_system 原为 bionic_agent_v4 记忆系统组件(动态涌现:用进废退 + LLM 判定),其"动态演化"特性与游戏"静态分类"需求冲突。作为**开发期离线工具**使用,这一矛盾不复存在——动态机制只在开发时按需触发,不进入游戏数据,LLM 判定结果供人复核而非直接落库。

## 环境

| 项 | 值 |
|---|---|
| 类型 | conda 虚拟环境 |
| 名称 | `evennia_category` |
| Python | 3.12.13 |
| 路径 | `D:\ProgramData\CondaVenv\evennia_category\` |
| python.exe | `D:\ProgramData\CondaVenv\evennia_category\python.exe` |
| pip | 26.1.2 |
| setuptools | 83.0.0 |

### 激活

```bash
conda activate evennia_category
```

或直接用绝对路径(免激活):
```bash
D:/ProgramData/CondaVenv/evennia_category/python.exe ...
```

## 依赖

最小依赖(让 category_system 可 import + 可运行):

| 包 | 版本 | 状态 | 用途 |
|---|---|---|---|
| chromadb | 1.5.9 | ✅ 已装 | 向量存储(CategoryStore,cosine 检索) |
| litellm | 1.91.4 | ✅ 已装 | 统一 LLM provider 封装(LLMClient/Embedder) |

chromadb 装时顺带带入:tokenizers 0.23.1、pydantic_core 2.46.4、onnxruntime、grpcio、httpx 等预编译依赖,均就位。litellm 装时带入:openai 2.48.0、tiktoken 0.13.0、jinja2、jiter 等。

其余依赖为 stdlib:`tomllib`(3.12 内置)、`sqlite3`(共现表)、`math`/`uuid`/`json` 等。

### 安装命令(可复现)

```bash
# 用 aismallworld 同款 conda 建环境(已建,跳过)
# conda create -n evennia_category python=3.12 -y
PY=D:/ProgramData/CondaVenv/evennia_category/python.exe
TUNA=https://pypi.tuna.tsinghua.edu.cn/simple

# chromadb(默认源即可)
$PY -m pip install chromadb

# litellm:必须用清华源 + 强制 wheel,否则默认源取 sdist 会触发 Rust 编译失败
$PY -m pip install litellm -i $TUNA --only-binary :all:
```

> **litellm 装坑**:默认源在 Windows + py3.12 下会取 litellm 的 sdist 触发 Rust/Cargo 编译而失败。清华源(TUNA)有预编译 win wheel,加 `--only-binary :all:` 强制取 wheel 即可绕过,无需装 Rust 工具链。

> aismallworld 环境(游戏 Evennia 用)缺 chromadb/litellm,故 category_system 必须在本独立环境运行,不要混进 aismallworld。

## 目录结构

```
evennia_category/
├── __init__.py            聚合包(使三者成为合法包,支撑相对引用)
├── category_system/       动态涌现分类引擎(主体)
│   ├── config.py / config.toml
│   ├── models.py          CategoryRecord / LLMAction / CategoryResult
│   ├── engine/            dispatcher / maintenance / pmi / path_validator
│   ├── service/           classify(SearchService) / commit(CommitService) / factory
│   ├── storage/           category_store(ChromaDB) / cooccurrence_*(sqlite)
│   └── prompt/            builder(LLM 提示语)
├── forgetting/            牛顿冷却遗忘算法(自包含,纯 stdlib)
│   ├── cooling.py         CoolingRate 枚举 + NewtonCooling
│   └── config.toml        cooling_rate = "DAYS_31"
├── llm/                   LLM 基础设施(自包含,依赖 litellm)
│   ├── client.py          LLMClient(litellm 封装)
│   ├── embedder.py        Embedder
│   ├── config.py / config.toml
│   └── summarizer.py
└── docs/
    └── env.md             本文件
```

### 引用关系

category_system 内部以**相对引用**使用 forgetting/llm(已从原 `bionic_agent_v4.xxx` 改为 `..forgetting.xxx` / `..llm.xxx`,共 14 处)。三者平级,统一由 `evennia_category` 包聚合。

## 关键配置(category_system/config.toml + 子包 config.toml)

| 配置项 | 值 | 说明 |
|---|---|---|
| cooling_rate | DAYS_31 | 牛顿冷却档位(31 天周期) |
| top_k | 7 | 向量检索返回数 |
| delta_t | 0.142857... | 记忆添加频率(1/7 秒) |
| chroma_persist_dir | ./data_v4/chromadb | ChromaDB 持久化目录 |
| collection_name | category_paths | Collection 名 |
| **embedding.model** | `ollama/qwen3-embedding:4b` | 本地 Ollama |
| **embedding.api_base** | `http://localhost:11434` | Ollama 地址 |
| **embedding.dimension** | 1024 | 向量维度 |
| **llm.model** | `anthropic/deepseek-v4-flash` | 火山方舟 ark |
| **llm.api_base** | `https://ark.cn-beijing.volces.com/api/coding` | 火山方舟 |
| **llm.api_key** | (已配置,见 config.toml) | 火山方舟 Key |

> 运行前需确保 **Ollama 本地服务已起**(`localhost:11434`,已拉 `qwen3-embedding:4b` 模型)。

## 基本用法(开发期辅助)

> 前置:`conda activate evennia_category` + Ollama 运行中。

```python
# 在 AISmallWorld/ 目录下,把 evennia_category 加入路径
import sys; sys.path.insert(0, '.')  # 或设 PYTHONPATH=.

from evennia_category.category_system import build_category_system, CategorySystemConfig

# 装配(共现表 sqlite 路径自定)
search, cooccurrence, pmi, maintenance = build_category_system(
    CategorySystemConfig(),
    cooccurrence_db_path="./evennia_category/data/cooccurrence.db",
)

# 开发辅助:判断一段描述该归到哪个现有类别
import asyncio
results = asyncio.run(search.search("一种可以切割东西的锋利石器"))
# → 返回 CategoryResult[]，含 category_path / document / record_id
# 人工复核后，决定游戏 prototype 的分类归属
```

## 验证状态

- [x] 依赖模块复制(forgetting/llm 从 src_frozen/bionic_agent_v4 迁入)
- [x] category_system 移入 + 14 处 import 改相对引用
- [x] evennia_category/__init__.py 建包
- [x] conda 环境创建(Python 3.12.13)
- [x] chromadb 1.5.9 + litellm 1.91.4 安装
- [x] 相对引用深度修正(engine/service/storage 深度=2 用 `...`,config 深度=1 用 `..`)
- [x] `import evennia_category.category_system` 端到端验证通过

> **引用深度修正记录**:factory.py/classify.py/commit.py/dispatcher.py/maintenance.py/pmi.py/cooccurrence_store.py 在 `engine/`、`service/`、`storage/` 子目录下(深度=2,距 evennia_category 两层),需用 `...forgetting`/`...llm`(三个点)才能回到 evennia_category 顶层;config.py 在 category_system 根(深度=1),用 `..forgetting`/`..llm`(两个点)。初次统一用 `..` 导致深度=2 文件 import 失败,已按目录深度分层修正。
