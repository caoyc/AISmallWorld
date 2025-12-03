# 聊天记录持久化方案文档

## 1. 概述

本文档描述聊天记录的数据库持久化实现方案，使用 SQLite 数据库存储对话历史，支持多租户和完整的增删改查功能。

## 1.1 当前实现状态（开发进度追踪）

### ✅ 已实现部分

#### 1. 前端服务层抽象 (`src/services/chatHistory.ts`)
- ✅ 已创建服务层抽象，支持内存存储和后端API切换
- ✅ 定义了 `USE_BACKEND` 标志（当前为 `false`，使用内存模式）
- ✅ 实现了基础接口：`saveChatMessage`、`getChatHistory`、`clearChatHistory`、`syncMemoryHistory`
- ✅ API 基础URL配置：`http://localhost:3001/api`
- ⚠️ **待更新**：当前接口未包含 `apiKey` 和 `user` 参数
- ⚠️ **待更新**：当前使用固定的 `CURRENT_USER = 'default_user'`，需要改为动态账号格式

#### 2. 后端基础框架
**文件**: `server/index.js`
- ✅ 已创建 Express 服务器基础框架
- ✅ 已配置 CORS 和 JSON 解析中间件
- ✅ 已实现基础路由：`POST /api/chat/history`、`GET /api/chat/history`、`DELETE /api/chat/history`
- ⚠️ **待更新**：API路径为 `/api/chat/history`，需要改为 `/api/chat/messages` 以匹配新方案
- ⚠️ **待更新**：当前使用 `user` 参数，默认值为 `'default_user'`，需要改为 `userId` 并使用账号格式
- ⚠️ **待实现**：缺少批量保存、更新、同步等接口

**文件**: `server/db.js`
- ✅ 已创建数据库连接模块
- ✅ 已实现数据库初始化函数 `initDatabase()`
- ✅ 已实现基础操作：`saveMessage`、`getHistory`、`clearHistory`
- ⚠️ **待更新**：表名为 `chat_history`，需要改为 `chat_messages` 以匹配新方案
- ⚠️ **待更新**：表结构缺少 `character_id`、`created_at`、`updated_at` 字段
- ⚠️ **待更新**：缺少 `updated_at` 字段的自动更新逻辑
- ⚠️ **待实现**：缺少更新消息、批量保存等功能

#### 3. Store 层集成 (`src/stores/app.ts`)
- ✅ 已导入 `saveChatMessage` 和 `syncMemoryHistory`
- ✅ 消息发送时已调用 `saveChatMessage`（第230行、第292行）
- ✅ 已调用 `syncMemoryHistory` 同步内存历史
- ⚠️ **待更新**：`saveChatMessage` 调用未传递 `apiKey` 和 `user` 参数
- ⚠️ **待实现**：组件加载时未调用 `getChatHistory` 加载历史记录

#### 4. 组件层 (`src/components/ConfigPanel.vue`)
- ✅ 已实现对话历史显示功能
- ✅ 已实现消息编辑功能
- ✅ 已导入 `getChatHistory` 和 `USE_BACKEND`（第510行）
- ✅ 已定义 `loadHistory` 函数（第566行），但仅在 `USE_BACKEND` 为 true 时调用
- ⚠️ **待实现**：消息删除功能
- ⚠️ **待更新**：`loadHistory` 函数未传递 `apiKey` 和 `user` 参数

### ❌ 未实现部分

#### 1. 账号格式支持
- ❌ 未实现 `getUserId(apiKey, user)` 函数
- ❌ 所有API调用未传递账号信息（`apiKey` 和 `user`）
- ❌ 后端未验证账号格式

#### 2. 完整的后端API（按新方案）
- ❌ 未实现 `POST /api/chat/messages`（保存单条消息，新路径）
- ❌ 未实现 `POST /api/chat/messages/batch`（批量保存）
- ❌ 未实现 `GET /api/chat/messages`（获取历史，支持分页和筛选）
- ❌ 未实现 `PUT /api/chat/messages/:id`（更新消息）
- ❌ 未实现 `DELETE /api/chat/messages/:id`（删除单条消息）
- ❌ 未实现 `DELETE /api/chat/messages`（清空记录，新路径）
- ❌ 未实现 `POST /api/chat/messages/sync`（同步功能）

#### 3. 数据库表结构更新
- ❌ 表名仍为 `chat_history`，需要改为 `chat_messages`
- ❌ 缺少 `character_id` 字段（可选）
- ❌ 缺少 `created_at` 和 `updated_at` 字段（Unix时间戳格式）
- ❌ 缺少 `updated_at` 的自动更新触发器

#### 4. 前端完整集成
- ❌ 未在组件加载时自动加载历史记录（需要移除 `USE_BACKEND` 判断）
- ❌ 未实现消息删除功能
- ❌ 未处理网络错误和重试机制
- ❌ 未实现消息更新API调用

### 📋 详细代码审查结果

#### `src/services/chatHistory.ts`
**当前状态**:
- 使用 `CURRENT_USER = 'default_user'` 固定用户标识
- API路径：`/api/chat/history`
- 接口签名：`saveChatMessage(role, content, timestamp)` - 缺少 `apiKey` 和 `user`
- 接口签名：`getChatHistory(limit)` - 缺少 `apiKey` 和 `user`

**需要修改**:
1. 添加 `getUserId(apiKey, user)` 函数
2. 更新所有接口签名，添加 `apiKey` 和 `user` 参数
3. 更新API路径为 `/api/chat/messages`
4. 移除 `CURRENT_USER` 常量

#### `server/index.js`
**当前状态**:
- API路径：`/api/chat/history`
- 使用 `user` 参数，默认值 `'default_user'`
- 仅实现3个基础接口

**需要修改**:
1. 更新API路径为 `/api/chat/messages`
2. 将 `user` 参数改为 `userId`，移除默认值
3. 实现所有新方案中的API接口
4. 添加账号格式验证

#### `server/db.js`
**当前状态**:
- 表名：`chat_history`
- 字段：`id, user_id, role, content, timestamp, created_at`
- 缺少：`character_id`, `updated_at`
- `created_at` 使用 `DATETIME` 类型，需要改为 `INTEGER`

**需要修改**:
1. 表名改为 `chat_messages`
2. 添加 `character_id TEXT` 字段
3. 添加 `updated_at INTEGER` 字段
4. 修改 `created_at` 为 `INTEGER` 类型（Unix时间戳）
5. 添加更新消息功能
6. 添加批量保存功能

#### `src/stores/app.ts`
**当前状态**:
- 第230行：`await saveChatMessage('user', processedUserMessage, userChatMessage.timestamp)`
- 第292行：`await saveChatMessage('assistant', finalContent, assistantMessage.timestamp)`
- 未传递 `apiKey` 和 `user` 参数

**需要修改**:
1. 更新 `saveChatMessage` 调用，添加 `llm.apiKey` 和 `llm.user` 参数
2. 在组件加载时调用 `getChatHistory` 加载历史记录

#### `src/components/ConfigPanel.vue`
**当前状态**:
- 第566行：定义了 `loadHistory` 函数
- 第1097行：仅在 `USE_BACKEND` 为 true 时调用 `loadHistory`
- `loadHistory` 函数未传递 `apiKey` 和 `user` 参数

**需要修改**:
1. 更新 `loadHistory` 函数，添加 `apiKey` 和 `user` 参数
2. 移除 `USE_BACKEND` 判断，始终加载历史记录
3. 实现消息删除功能
4. 更新消息编辑功能，调用更新API

### 📋 开发任务清单

#### 阶段一：数据库和账号格式（优先级：高）
- [ ] 更新数据库表结构（表名、字段、类型）
- [ ] 实现 `getUserId(apiKey, user)` 函数
- [ ] 更新所有API接口以支持账号参数
- [ ] 添加账号格式验证

#### 阶段二：后端API实现（优先级：高）
- [ ] 更新API路径为 `/api/chat/messages`
- [ ] 实现 `POST /api/chat/messages`（保存单条消息）
- [ ] 实现 `POST /api/chat/messages/batch`（批量保存）
- [ ] 实现 `GET /api/chat/messages`（获取历史，支持分页和筛选）
- [ ] 实现 `PUT /api/chat/messages/:id`（更新消息）
- [ ] 实现 `DELETE /api/chat/messages/:id`（删除消息）
- [ ] 实现 `DELETE /api/chat/messages`（清空记录）
- [ ] 实现 `POST /api/chat/messages/sync`（同步功能）

#### 阶段三：前端服务层更新（优先级：高）
- [ ] 添加 `getUserId(apiKey, user)` 函数
- [ ] 更新 `saveChatMessage` 添加 `apiKey` 和 `user` 参数
- [ ] 更新 `getChatHistory` 添加 `apiKey` 和 `user` 参数
- [ ] 更新 `clearChatHistory` 添加 `apiKey` 和 `user` 参数
- [ ] 更新 `syncMemoryHistory` 添加 `apiKey` 和 `user` 参数
- [ ] 更新API路径为 `/api/chat/messages`
- [ ] 移除 `CURRENT_USER` 常量

#### 阶段四：Store 层集成（优先级：高）
- [ ] 更新 `sendMessage` 方法传递 `apiKey` 和 `user`
- [ ] 添加历史记录加载逻辑（组件加载时）
- [ ] 更新消息编辑功能调用更新API
- [ ] 添加消息删除功能

#### 阶段五：组件层更新（优先级：中）
- [ ] 在 `onMounted` 中加载历史记录（移除 `USE_BACKEND` 判断）
- [ ] 添加加载状态和错误处理
- [ ] 实现消息删除UI和功能
- [ ] 移除 `USE_BACKEND` 相关条件判断（全部使用后端）

#### 阶段六：测试和优化（优先级：中）
- [ ] 功能测试（增删改查）
- [ ] 账号格式测试（user为空和有值的情况）
- [ ] 性能测试
- [ ] 错误处理测试
- [ ] 网络错误重试机制

### 🔍 代码差异对比

#### 当前实现 vs 新方案

| 项目 | 当前实现 | 新方案 | 状态 |
|------|---------|--------|------|
| 表名 | `chat_history` | `chat_messages` | ❌ 需修改 |
| API路径 | `/api/chat/history` | `/api/chat/messages` | ❌ 需修改 |
| 用户标识 | `user` (默认'default_user') | `userId` ({api_key}:{user}) | ❌ 需修改 |
| 接口参数 | 无 `apiKey` 和 `user` | 需要 `apiKey` 和 `user` | ❌ 需修改 |
| 表字段 | 缺少 `character_id`, `updated_at` | 完整字段 | ❌ 需修改 |
| 时间戳类型 | `DATETIME` | `INTEGER` (Unix时间戳) | ❌ 需修改 |
| 批量操作 | ❌ 未实现 | ✅ 需要 | ❌ 需实现 |
| 更新消息 | ❌ 未实现 | ✅ 需要 | ❌ 需实现 |
| 删除单条 | ❌ 未实现 | ✅ 需要 | ❌ 需实现 |
| 同步功能 | ❌ 未实现 | ✅ 需要 | ❌ 需实现 |

### ✅ 已实现

1. **前端服务层抽象** (`src/services/chatHistory.ts`)
   - ✅ 已创建服务层抽象，支持内存存储和后端API切换
   - ✅ 定义了 `USE_BACKEND` 标志（当前为 `false`）
   - ✅ 实现了 `saveChatMessage`、`getChatHistory`、`clearChatHistory`、`syncMemoryHistory` 接口
   - ⚠️ **待更新**：当前接口未包含 `apiKey` 和 `user` 参数，需要修改为使用 `{api_key}:{user}` 账号格式

2. **后端基础框架** (`server/index.js`, `server/db.js`)
   - ✅ 已创建 Express 服务器基础框架
   - ✅ 已创建数据库连接模块
   - ✅ 数据库表结构已定义（但字段名和设计需要更新以匹配新方案）
   - ⚠️ **待更新**：当前表结构使用 `user_id` 默认值 `'default_user'`，需要移除默认值
   - ⚠️ **待更新**：当前API接口未实现完整的增删改查功能

3. **Store 层集成** (`src/stores/app.ts`)
   - ✅ 已集成 `saveChatMessage` 和 `syncMemoryHistory` 调用
   - ✅ 消息发送时已调用保存接口
   - ⚠️ **待更新**：当前未传递 `apiKey` 和 `user` 参数
   - ⚠️ **待更新**：组件加载时未调用 `getChatHistory` 加载历史记录

4. **组件层** (`src/components/ConfigPanel.vue`)
   - ✅ 已实现对话历史显示功能
   - ✅ 已实现消息编辑功能
   - ⚠️ **待实现**：消息删除功能
   - ⚠️ **待更新**：组件加载时未加载历史记录

### ❌ 未实现

1. **账号格式支持**
   - ❌ 未实现 `getUserId(apiKey, user)` 函数
   - ❌ 所有API调用未传递账号信息
   - ❌ 后端未验证账号格式

2. **完整的后端API**
   - ❌ 未实现 `POST /api/chat/messages`（保存单条消息）
   - ❌ 未实现 `POST /api/chat/messages/batch`（批量保存）
   - ❌ 未实现 `GET /api/chat/messages`（获取历史）
   - ❌ 未实现 `PUT /api/chat/messages/:id`（更新消息）
   - ❌ 未实现 `DELETE /api/chat/messages/:id`（删除消息）
   - ❌ 未实现 `DELETE /api/chat/messages`（清空记录）
   - ❌ 未实现 `POST /api/chat/messages/sync`（同步功能）

3. **数据库表结构更新**
   - ❌ 未移除 `user_id` 的默认值
   - ❌ 未添加 `character_id` 字段（可选）
   - ❌ 索引可能需要优化

4. **前端完整集成**
   - ❌ 未在组件加载时加载历史记录
   - ❌ 未实现消息删除功能
   - ❌ 未处理网络错误和重试机制

### 📋 开发任务清单

#### 阶段一：数据库和账号格式
- [ ] 更新数据库表结构（移除默认值，添加 character_id）
- [ ] 实现 `getUserId(apiKey, user)` 函数
- [ ] 更新所有API接口以支持账号参数

#### 阶段二：后端API实现
- [ ] 实现 `POST /api/chat/messages`（保存单条消息）
- [ ] 实现 `POST /api/chat/messages/batch`（批量保存）
- [ ] 实现 `GET /api/chat/messages`（获取历史，支持分页和筛选）
- [ ] 实现 `PUT /api/chat/messages/:id`（更新消息）
- [ ] 实现 `DELETE /api/chat/messages/:id`（删除消息）
- [ ] 实现 `DELETE /api/chat/messages`（清空记录）
- [ ] 实现 `POST /api/chat/messages/sync`（同步功能）

#### 阶段三：前端服务层更新
- [ ] 更新 `saveChatMessage` 添加 `apiKey` 和 `user` 参数
- [ ] 更新 `getChatHistory` 添加 `apiKey` 和 `user` 参数
- [ ] 更新 `clearChatHistory` 添加 `apiKey` 和 `user` 参数
- [ ] 更新 `syncMemoryHistory` 添加 `apiKey` 和 `user` 参数
- [ ] 移除内存存储相关代码（或标记为废弃）

#### 阶段四：Store 层集成
- [ ] 更新 `sendMessage` 方法传递 `apiKey` 和 `user`
- [ ] 添加历史记录加载逻辑
- [ ] 更新消息编辑功能调用更新API
- [ ] 添加消息删除功能

#### 阶段五：组件层更新
- [ ] 在 `onMounted` 中加载历史记录
- [ ] 添加加载状态和错误处理
- [ ] 实现消息删除UI和功能
- [ ] 移除 `USE_BACKEND` 相关条件判断（全部使用后端）

#### 阶段六：测试和优化
- [ ] 功能测试（增删改查）
- [ ] 账号格式测试（user为空和有值的情况）
- [ ] 性能测试
- [ ] 错误处理测试

## 2. 技术选型

- **数据库**: SQLite（轻量级，适合单机部署）
- **数据库驱动**: `better-sqlite3`（已安装）
- **后端框架**: Express.js（已安装）
- **API 风格**: RESTful API

## 3. 数据库设计

### 3.1 表结构

#### 表名: `chat_messages`

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER | 主键，自增 | PRIMARY KEY AUTOINCREMENT |
| user_id | TEXT | 用户ID（格式：{api_key}:{user}，user为空时仅{api_key}） | NOT NULL |
| role | TEXT | 消息角色 | NOT NULL, CHECK(role IN ('user', 'assistant', 'system')) |
| content | TEXT | 消息内容 | NOT NULL |
| character_id | TEXT | 角色ID（可选，用于角色管理） | NULL |
| timestamp | INTEGER | 时间戳（毫秒） | NOT NULL |
| created_at | INTEGER | 创建时间（Unix时间戳） | NOT NULL, DEFAULT (strftime('%s', 'now')) |
| updated_at | INTEGER | 更新时间（Unix时间戳） | NOT NULL, DEFAULT (strftime('%s', 'now')) |

#### 索引设计

```sql
-- 用户ID和时间戳复合索引，用于快速查询用户的历史记录
CREATE INDEX idx_user_timestamp ON chat_messages(user_id, timestamp DESC);

-- 角色索引，用于按角色筛选
CREATE INDEX idx_role ON chat_messages(role);

-- 时间戳索引，用于时间范围查询
CREATE INDEX idx_timestamp ON chat_messages(timestamp DESC);
```

### 3.2 数据库初始化脚本

```sql
-- 创建聊天消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    character_id TEXT,
    timestamp INTEGER NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_timestamp ON chat_messages(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_role ON chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_messages(timestamp DESC);
```

## 4. API 设计

### 4.1 保存单条消息

**接口**: `POST /api/chat/messages`

**请求体**:
```json
{
  "role": "user",
  "content": "你好",
  "characterId": "char_123",  // 可选
  "timestamp": 1703123456789,  // 可选，默认使用服务器时间
  "userId": "sk-xxx:username"  // 必填，格式：{api_key}:{user}（user为空时仅{api_key}）
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "userId": "sk-xxx:username",
    "role": "user",
    "content": "你好",
    "characterId": "char_123",
    "timestamp": 1703123456789,
    "createdAt": 1703123456789,
    "updatedAt": 1703123456789
  }
}
```

### 4.2 批量保存消息

**接口**: `POST /api/chat/messages/batch`

**请求体**:
```json
{
  "userId": "sk-xxx:username",  // 必填，格式：{api_key}:{user}
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "characterId": "char_123",
      "timestamp": 1703123456789
    },
    {
      "role": "assistant",
      "content": "你好！有什么可以帮助你的吗？",
      "characterId": "char_456",
      "timestamp": 1703123457890
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "count": 2,
    "ids": [1, 2]
  }
}
```

### 4.3 获取聊天历史

**接口**: `GET /api/chat/messages`

**查询参数**:
- `userId` (必填): 用户ID，格式：{api_key}:{user}
- `limit` (可选): 返回数量限制，默认 50
- `offset` (可选): 偏移量，默认 0
- `before` (可选): 时间戳，获取此时间之前的消息
- `after` (可选): 时间戳，获取此时间之后的消息
- `role` (可选): 角色筛选，'user' | 'assistant' | 'system'

**响应**:
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 1,
        "userId": "sk-xxx:username",
        "role": "user",
        "content": "你好",
        "characterId": "char_123",
        "timestamp": 1703123456789,
        "createdAt": 1703123456789,
        "updatedAt": 1703123456789
      }
    ],
    "total": 100,
    "limit": 50,
    "offset": 0
  }
}
```

### 4.4 更新消息

**接口**: `PUT /api/chat/messages/:id`

**请求体**:
```json
{
  "content": "更新后的内容",
  "characterId": "char_123"  // 可选
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "userId": "default_user",
    "role": "user",
    "content": "更新后的内容",
    "characterId": "char_123",
    "timestamp": 1703123456789,
    "createdAt": 1703123456789,
    "updatedAt": 1703123460000
  }
}
```

### 4.5 删除消息

**接口**: `DELETE /api/chat/messages/:id`

**响应**:
```json
{
  "success": true,
  "message": "消息已删除"
}
```

### 4.6 清空用户聊天记录

**接口**: `DELETE /api/chat/messages`

**查询参数**:
- `userId` (可选): 用户ID，默认 'default_user'

**查询参数**:
- `userId` (必填): 用户ID，格式：{api_key}:{user}

**响应**:
```json
{
  "success": true,
  "message": "聊天记录已清空",
  "data": {
    "deletedCount": 50
  }
}
```

### 4.7 同步内存历史到数据库

**接口**: `POST /api/chat/messages/sync`

**请求体**:
```json
{
  "userId": "sk-xxx:username",  // 必填，格式：{api_key}:{user}
  "messages": [
    {
      "role": "user",
      "content": "你好",
      "characterId": "char_123",
      "timestamp": 1703123456789
    }
  ]
}
```

**说明**: 用于将前端内存中的历史记录同步到数据库，避免重复插入。

**响应**:
```json
{
  "success": true,
  "data": {
    "synced": 10,
    "skipped": 5
  }
}
```

## 5. 后端实现

### 5.1 文件结构

```
server/
├── index.js          # Express 服务器入口
├── db.js             # 数据库连接和初始化
├── routes/
│   └── chat.js       # 聊天记录相关路由
└── models/
    └── ChatMessage.js # 数据模型
```

### 5.2 数据库模块 (server/db.js)

```javascript
const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_PATH = path.join(__dirname, '../data/chat.db');
const DB_DIR = path.dirname(DB_PATH);

// 确保数据目录存在
if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

let db = null;

function initDatabase() {
  if (db) return db;
  
  db = new Database(DB_PATH);
  
  // 启用外键约束
  db.pragma('foreign_keys = ON');
  
  // 创建表
  db.exec(`
    CREATE TABLE IF NOT EXISTS chat_messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
      content TEXT NOT NULL,
      character_id TEXT,
      timestamp INTEGER NOT NULL,
      created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
      updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
    );
    
    CREATE INDEX IF NOT EXISTS idx_user_timestamp ON chat_messages(user_id, timestamp DESC);
    CREATE INDEX IF NOT EXISTS idx_role ON chat_messages(role);
    CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_messages(timestamp DESC);
  `);
  
  return db;
}

function getDatabase() {
  if (!db) {
    initDatabase();
  }
  return db;
}

function closeDatabase() {
  if (db) {
    db.close();
    db = null;
  }
}

module.exports = {
  initDatabase,
  getDatabase,
  closeDatabase
};
```

### 5.3 路由模块 (server/routes/chat.js)

主要实现：
- 消息的增删改查
- 批量操作
- 同步功能
- 错误处理
- 数据验证

### 5.4 Express 服务器 (server/index.js)

需要添加：
- CORS 配置
- JSON 解析中间件
- 路由注册
- 错误处理中间件
- 优雅关闭（关闭数据库连接）

## 6. 前端集成

### 6.1 服务层 (src/services/chatHistory.ts)

修改现有服务，移除 localStorage 相关代码，全部改为 API 调用：

```typescript
const API_BASE_URL = 'http://localhost:3000/api'

/**
 * 生成用户ID（账号）
 * 格式：{api_key}:{user}
 * 当user为空时，仅使用 {api_key}
 */
function getUserId(apiKey: string, user: string): string {
  if (!user || user.trim() === '') {
    return apiKey
  }
  return `${apiKey}:${user}`
}

// 保存单条消息
export async function saveChatMessage(
  role: 'user' | 'assistant' | 'system',
  content: string,
  apiKey: string,
  user: string,
  timestamp?: number,
  characterId?: string
): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/chat/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role,
      content,
      userId,
      timestamp: timestamp || Date.now(),
      characterId
    })
  })
  if (!response.ok) throw new Error('保存消息失败')
}

// 获取聊天历史
export async function getChatHistory(
  apiKey: string,
  user: string,
  limit: number = 50,
  offset: number = 0,
  before?: number,
  after?: number
): Promise<ChatMessage[]> {
  const userId = getUserId(apiKey, user)
  const params = new URLSearchParams({
    userId,
    limit: limit.toString(),
    offset: offset.toString()
  })
  if (before) params.append('before', before.toString())
  if (after) params.append('after', after.toString())
  
  const response = await fetch(`${API_BASE_URL}/chat/messages?${params}`)
  if (!response.ok) throw new Error('获取历史记录失败')
  const data = await response.json()
  return data.data.messages
}

// 更新消息
export async function updateChatMessage(
  id: number,
  content: string,
  characterId?: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/messages/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, characterId })
  })
  if (!response.ok) throw new Error('更新消息失败')
}

// 删除消息
export async function deleteChatMessage(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/messages/${id}`, {
    method: 'DELETE'
  })
  if (!response.ok) throw new Error('删除消息失败')
}

// 清空聊天记录
export async function clearChatHistory(apiKey: string, user: string): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/chat/messages?userId=${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  })
  if (!response.ok) throw new Error('清空聊天记录失败')
}

// 同步内存历史到数据库
export async function syncMemoryHistory(
  messages: ChatMessage[],
  apiKey: string,
  user: string
): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/chat/messages/sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, messages })
  })
  if (!response.ok) throw new Error('同步历史记录失败')
}
```

### 6.2 Store 层修改 (src/stores/app.ts)

- 移除内存存储逻辑
- 发送消息时调用 `saveChatMessage`，传入 `llm.apiKey` 和 `llm.user`
- 组件加载时调用 `getChatHistory` 加载历史，传入 `llm.apiKey` 和 `llm.user`
- 编辑消息时调用 `updateChatMessage`
- 删除消息时调用 `deleteChatMessage`

**关键修改点**：
```typescript
// 在 sendMessage 方法中
await saveChatMessage(
  'user',
  processedUserMessage,
  llm.apiKey,  // 传入 API Key（用户账号）
  llm.user || '',  // 传入 user 字段（AI角色，可为空）
  userChatMessage.timestamp
)

// 在组件加载时
const history = await getChatHistory(
  appState.llm.apiKey,  // 用户账号
  appState.llm.user || '',  // AI角色（可为空）
  50
)
appState.chatHistory = history
```

**账号生成逻辑**：
- 系统内部使用 `getUserId(apiKey, user)` 生成账号
- 当 `user` 为空时，账号为 `apiKey`
- 当 `user` 有值时，账号为 `apiKey:user`

### 6.3 组件层修改 (src/components/ConfigPanel.vue)

- 移除 `USE_BACKEND` 标志相关代码
- 在 `onMounted` 中加载历史记录
- 编辑消息后调用更新 API
- 添加删除消息功能（如果需要）

## 7. 数据迁移

### 7.1 从内存到数据库

如果之前有 localStorage 数据，需要提供迁移脚本：

```javascript
// 迁移脚本 (server/migrate.js)
// 从 localStorage 导出数据，然后通过 API 导入到数据库
```

## 8. 错误处理

### 8.1 网络错误

- 前端需要处理网络请求失败的情况
- 可以添加重试机制
- 失败时可以降级到内存存储（仅当前会话）

### 8.2 数据库错误

- 后端需要捕获数据库操作异常
- 返回友好的错误信息
- 记录错误日志

## 9. 性能优化

### 9.1 批量操作

- 使用批量插入 API 减少网络请求
- 前端可以累积多条消息后批量提交

### 9.2 分页加载

- 历史记录使用分页加载，避免一次性加载过多数据
- 支持无限滚动加载更多

### 9.3 索引优化

- 确保索引正确创建
- 根据查询模式调整索引

## 10. 安全性

### 10.1 输入验证

- 后端验证所有输入数据
- 防止 SQL 注入（使用参数化查询）
- 限制内容长度

### 10.2 用户隔离

- 确保用户只能访问自己的数据
- 验证 userId 参数

## 11. 测试计划

### 11.1 单元测试

- 数据库操作函数测试
- API 路由测试

### 11.2 集成测试

- 前后端联调测试
- 数据持久化验证

### 11.3 性能测试

- 大量数据插入测试
- 查询性能测试

## 12. 部署说明

### 12.1 数据库文件位置

- 数据库文件存储在 `data/chat.db`
- 需要确保 `data` 目录有写入权限
- 建议将 `data` 目录添加到 `.gitignore`

### 12.2 环境变量

- 数据库路径可配置
- API 端口可配置
- CORS 配置可调整

## 13. 用户标识说明

### 13.1 用户ID生成规则

用户ID格式：`{api_key}:{user}`

- `api_key`: 来自 `appState.llm.apiKey`
- `user`: 来自 `appState.llm.user`（如果为空则使用空字符串）

**示例**：
- API Key: `sk-1234567890abcdef`
- User: `alice`
- 生成的 User ID: `sk-1234567890abcdef:alice`

- API Key: `sk-1234567890abcdef`
- User: `` (空)
- 生成的 User ID: `sk-1234567890abcdef:`

### 13.2 多租户支持

当前通过 `{api_key}:{user}` 组合实现用户隔离：
- 不同的 API Key 对应不同的用户空间
- 同一个 API Key 下，不同的 user 字段也对应不同的用户空间
- 后续可扩展完整的用户认证系统

### 13.2 数据备份

- 定期备份数据库
- 导出/导入功能

### 13.3 数据统计

- 消息数量统计
- 活跃度分析

## 14. 实施步骤

1. **阶段一**: 数据库设计和初始化
   - 创建数据库表结构
   - 实现数据库连接模块

2. **阶段二**: 后端 API 开发
   - 实现所有 API 接口
   - 添加错误处理和验证

3. **阶段三**: 前端服务层改造
   - 修改 `chatHistory.ts` 为纯 API 调用
   - 移除所有 localStorage 相关代码

4. **阶段四**: Store 层集成
   - 修改 `app.ts` 使用 API
   - 实现历史记录加载

5. **阶段五**: 组件层更新
   - 更新 `ConfigPanel.vue`
   - 添加加载状态和错误处理

6. **阶段六**: 测试和优化
   - 功能测试
   - 性能优化
   - 错误处理完善

