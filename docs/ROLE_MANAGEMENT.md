# 角色管理功能设计方案

## 1. 功能概述

角色管理功能用于管理AI助手的角色，角色对应传给大模型的`user`字段的值。用户可以为不同的AI助手创建、编辑、删除角色，并设置当前使用的角色。

## 2. 数据结构

### 2.1 角色数据模型

```typescript
interface Role {
  id: number              // 角色唯一标识（数据库主键，自增整数）
  name: string            // 角色名称（显示名称）
  user: string            // user字段的值（传给大模型）
  description?: string    // 角色描述（可选）
  avatar?: string         // 角色头像URL（可选）
  createdAt: number       // 创建时间戳（Unix时间戳）
  updatedAt: number       // 更新时间戳（Unix时间戳）
}
```

### 2.2 存储方案

- **后端存储**：使用 SQLite 数据库存储角色数据
- **数据库文件**：`data/chat_history.db`（与聊天历史共用数据库）
- **表名**：`roles`
- **API基础URL**：`http://localhost:3001/api`

## 3. 功能需求

### 3.1 角色列表管理

1. **查看角色列表**
   - 显示所有已创建的角色
   - 显示角色名称、user字段值、描述、头像
   - 标识当前使用的角色

2. **创建角色**
   - 输入角色名称（必填）
   - 输入user字段值（必填，传给大模型）
   - 输入角色描述（可选）
   - 设置角色头像URL（可选）
   - 验证user字段值不能为空

3. **编辑角色**
   - 修改角色名称
   - 修改user字段值
   - 修改角色描述
   - 修改角色头像
   - 验证user字段值不能为空

4. **删除角色**
   - 删除前确认
   - 如果删除的是当前使用的角色，需要提示并清空当前角色

5. **设置当前角色**
   - 选择角色后，将角色的user字段值设置到 `appState.llm.user`
   - 更新UI显示

### 3.2 UI设计

1. **角色管理入口**
   - 在配置面板中添加"角色管理"按钮或菜单项
   - 点击后打开角色管理弹窗

2. **角色管理弹窗**
   - 显示角色列表
   - 提供"新建角色"按钮
   - 每个角色项显示：名称、user字段、描述、头像（如果有）
   - 提供"编辑"、"删除"、"设为当前"操作按钮
   - 标识当前使用的角色

3. **角色编辑表单**
   - 角色名称输入框
   - user字段输入框
   - 角色描述文本域
   - 头像URL输入框
   - 保存/取消按钮

## 4. 实现方案

### 4.1 数据库表结构

在 `server/db.js` 中添加 `roles` 表：

```sql
CREATE TABLE IF NOT EXISTS roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  user TEXT NOT NULL,
  description TEXT,
  avatar TEXT,
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
)

CREATE INDEX IF NOT EXISTS idx_roles_user_id ON roles(user_id);
```

**字段说明**：
- `id`: 主键，自增整数
- `user_id`: 用户ID（格式：`{api_key}` 或 `{api_key}:{user}`），用于多租户隔离
- `name`: 角色名称（显示名称）
- `user`: user字段的值（传给大模型）
- `description`: 角色描述（可选）
- `avatar`: 角色头像URL（可选）
- `created_at`: 创建时间（Unix时间戳）
- `updated_at`: 更新时间（Unix时间戳）

### 4.2 后端API接口

在 `server/index.js` 中实现以下接口：

#### 4.2.1 获取角色列表
```
GET /api/roles
Query参数：
  - userId: 用户ID（必填）

响应：
{
  "success": true,
  "data": Role[]
}
```

#### 4.2.2 创建角色
```
POST /api/roles
Body:
{
  "userId": string,
  "name": string,
  "user": string,
  "description": string (可选),
  "avatar": string (可选)
}

响应：
{
  "success": true,
  "data": Role
}
```

#### 4.2.3 更新角色
```
PUT /api/roles/:id
Body:
{
  "name": string (可选),
  "user": string (可选),
  "description": string (可选),
  "avatar": string (可选)
}
Query参数：
  - userId: 用户ID（必填）

响应：
{
  "success": true,
  "data": Role
}
```

#### 4.2.4 删除角色
```
DELETE /api/roles/:id
Query参数：
  - userId: 用户ID（必填）

响应：
{
  "success": true
}
```

### 4.3 前端服务层

创建 `src/services/roleManagement.ts`：

```typescript
import type { Role } from '../types'

const API_BASE_URL = 'http://localhost:3001/api'

// 获取用户ID（与聊天历史保持一致）
function getUserId(apiKey: string, user: string): string {
  if (!user || user.trim() === '') {
    return apiKey
  }
  return `${apiKey}:${user}`
}

// 获取所有角色
export async function getRoles(apiKey: string, user: string): Promise<Role[]> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/roles?userId=${encodeURIComponent(userId)}`)
  
  if (!response.ok) {
    throw new Error('获取角色列表失败')
  }
  
  const result = await response.json()
  return result.data || []
}

// 创建角色
export async function createRole(
  apiKey: string,
  user: string,
  role: Omit<Role, 'id' | 'createdAt' | 'updatedAt'>
): Promise<Role> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/roles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...role,
      userId
    })
  })
  
  if (!response.ok) {
    throw new Error('创建角色失败')
  }
  
  const result = await response.json()
  return result.data
}

// 更新角色
export async function updateRole(
  id: number,
  apiKey: string,
  user: string,
  updates: Partial<Omit<Role, 'id' | 'createdAt' | 'updatedAt'>>
): Promise<Role> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/roles/${id}?userId=${encodeURIComponent(userId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  
  if (!response.ok) {
    throw new Error('更新角色失败')
  }
  
  const result = await response.json()
  return result.data
}

// 删除角色
export async function deleteRole(id: number, apiKey: string, user: string): Promise<void> {
  const userId = getUserId(apiKey, user)
  const response = await fetch(`${API_BASE_URL}/roles/${id}?userId=${encodeURIComponent(userId)}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    throw new Error('删除角色失败')
  }
}
```

### 4.2 类型定义

在 `src/types/index.ts` 中添加：

```typescript
export interface Role {
  id: string
  name: string
  user: string
  description?: string
  avatar?: string
  createdAt: number
  updatedAt: number
}
```

### 4.3 UI组件

在 `ConfigPanel.vue` 中：

1. 添加角色管理按钮/菜单项
2. 添加角色管理弹窗组件
3. 添加角色编辑表单组件
4. 实现角色列表显示、增删改查功能
5. 实现设置当前角色功能（更新 `appState.llm.user`）

### 4.4 与现有功能集成

1. **聊天历史显示**
   - 当前已使用 `appState.llm.user` 显示AI角色名称
   - 保持不变，角色管理只更新 `appState.llm.user` 的值

2. **配置保存/加载**
   - 角色数据独立存储，不包含在配置中
   - 配置保存/加载时不影响角色数据

3. **数据库用户ID**
   - 当前使用 `{api_key}:{user}` 作为用户ID
   - 角色管理只影响 `user` 字段的值，不影响 `api_key`
   - 切换角色时，user字段变化，用户ID也会变化

## 5. 开发步骤

1. **步骤1**：添加类型定义
   - 在 `src/types/index.ts` 中添加 `Role` 接口
   - 注意：`id` 类型为 `number`（数据库主键）

2. **步骤2**：数据库表创建
   - 在 `server/db.js` 的 `initDatabase()` 函数中添加 `roles` 表创建逻辑
   - 添加索引

3. **步骤3**：数据库操作函数
   - 在 `server/db.js` 中实现：
     - `getRoles(userId)`: 获取用户的所有角色
     - `createRole(userId, role)`: 创建角色
     - `updateRole(id, userId, updates)`: 更新角色
     - `deleteRole(id, userId)`: 删除角色

4. **步骤4**：后端API接口
   - 在 `server/index.js` 中实现 RESTful API：
     - `GET /api/roles`: 获取角色列表
     - `POST /api/roles`: 创建角色
     - `PUT /api/roles/:id`: 更新角色
     - `DELETE /api/roles/:id`: 删除角色
   - 添加 `userId` 验证和权限检查

5. **步骤5**：前端服务层
   - 创建 `src/services/roleManagement.ts`
   - 实现与后端API的交互函数
   - 使用与聊天历史相同的 `getUserId()` 函数

6. **步骤6**：在ConfigPanel中添加UI
   - 添加角色管理入口按钮
   - 添加角色管理弹窗
   - 添加角色编辑表单
   - 实现角色列表显示
   - 调用前端服务层函数

7. **步骤7**：实现设置当前角色功能
   - 点击"设为当前"按钮时，更新 `appState.llm.user`
   - 更新UI显示

8. **步骤8**：测试验证
   - 测试角色的增删改查
   - 测试设置当前角色
   - 测试切换角色后聊天历史显示
   - 测试多租户隔离（不同apiKey/user的角色互不干扰）

## 6. 注意事项

1. **user字段验证**：user字段不能为空，创建/编辑时需要验证（前端和后端都要验证）
2. **当前角色标识**：在角色列表中清晰标识当前使用的角色（通过比较 `appState.llm.user` 和角色的 `user` 字段）
3. **删除当前角色**：删除当前使用的角色时，需要清空 `appState.llm.user`
4. **多租户隔离**：使用 `userId`（格式：`{api_key}` 或 `{api_key}:{user}`）进行数据隔离，确保不同用户/API Key的角色互不干扰
5. **ID类型**：数据库主键为 `INTEGER`，前端 `Role.id` 类型为 `number`
6. **错误处理**：API调用失败时显示错误提示，使用 Toast 通知
7. **数据同步**：角色列表需要从后端加载，创建/更新/删除后需要刷新列表
8. **权限验证**：后端需要验证 `userId`，确保用户只能操作自己的角色
9. **角色数据隔离（重要）**：
   - **设计原则**：只加载用户 apiKey 对应的角色
   - 角色面板只显示当前登录用户（apiKey）对应的伙伴角色
   - 查询角色时，必须使用当前登录的 `apiKey` 作为过滤条件
   - 确保不同用户之间的角色数据完全隔离
10. **角色名称显示规则**：
    - **重要规则**：如果角色名称为空，使用 `user` 字段代替角色名称
    - **单向规则**：不能反过来，即不能使用角色名称代替 `user` 字段
    - 名称为空时，显示 `user` 字段的值（或显示默认值如"AI"）
11. **伙伴角色大模型设置**：
    - **UI 隐藏**：编辑界面中隐藏大模型设置字段（baseURL、model、apiKey）
    - **数据库保留**：数据库表结构中保留这些字段，以备后续扩展
    - **扩展性**：保留字段的目的是为了将来可能为不同角色选用不同模型

## 7. 未来扩展（可选）

1. 角色导入/导出功能
2. 角色预设模板
3. 角色使用统计
4. 云端同步（如果需要）

