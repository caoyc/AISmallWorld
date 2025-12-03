# 角色管理功能开发进度追踪

## 核心设计原则

### 原则1：业务逻辑一致性

**数字人的业务逻辑跟立绘一样，只是把立绘换成了数字人的细节差别。**

此原则要求：
- 数字人和立绘在业务逻辑上保持一致，仅在实现细节上有差异
- 所有立绘的功能（位置、缩放、显示/隐藏、拖拽等）都应同样适用于数字人
- 设计新功能时，应首先考虑立绘的实现方式，然后将其适配到数字人
- 避免为数字人设计特殊的业务逻辑，除非是数字人特有的技术细节（如SDK连接、截图等）

### 原则2：松耦合可插拔架构

**除集成性质的代码外，数字人的代码使用单独的目录存放，目标是实现可插拔式的松耦合。**

此原则要求：
- **代码隔离**：数字人相关代码（除集成点外）应存放在独立目录中，与立绘代码分离
- **可插拔设计**：数字人功能应设计为可插拔模块，可以独立启用/禁用，不影响立绘功能
- **禁止修改立绘代码**：代码实现中严禁改动立绘的现有代码，适当时机将对立绘也进行类似重构
- **统一抽象模式**：抽象统一模式，以备后续按此模式扩张更多其他类型（如3D模型、视频等）

**架构目标**：
- 立绘、数字人、未来其他类型都作为独立的"角色渲染器"（Renderer）插件
- 通过统一的接口（Interface）与主应用集成
- 每个渲染器独立管理自己的生命周期、状态、事件处理
- 主应用只负责协调和集成，不关心具体渲染器的实现细节

## 一、需求分析

### 1.1 核心需求

#### 1.1.1 账号隔离机制
- **apiKey = 用户账号**：每个 `apiKey` 代表一个独立的用户账号
- **全局 apiKey**：用户登录时输入的 `apiKey`，用于：
  - 查询该账号下的所有角色（用户角色和伙伴角色）
  - 作为用户角色的大模型配置中的固定 `apiKey`
- **数据隔离原则**：只加载用户 apiKey 对应的角色
  - 角色面板（用户角色和伙伴角色）只显示当前登录用户（apiKey）对应的角色
  - 查询角色时，必须使用当前登录的 `apiKey` 作为过滤条件
  - 确保不同用户之间的角色数据完全隔离

#### 1.1.2 角色类型

1. **用户角色**（User Role）
   - 代表用户自己的角色
   - 字段：apiKey（固定，使用登录的apiKey）、头像、角色名称（可选）、位置、缩放、大模型设置
   - 用途：在对话历史中显示为"我"

2. **伙伴角色**（Partner Role，原"角色管理"）
   - 代表 AI 助手的角色
   - 字段：user、type、name、description、avatar、positionX、positionY、scale、baseURL、model、apiKey
   - 用途：在对话历史中显示为 AI 角色名称
   - **大模型设置**：
     - **API Key**：只读显示，使用当前登录的 `globalApiKey`，不可编辑
     - **模型名称**：必填，可编辑。创建时默认值为当前用户角色的模型名称
     - **baseURL**：不显示在界面，创建时默认使用用户角色的 `baseURL`，更新时保留伙伴角色自己的 `baseURL`（如果已设置）
     - **调用大模型**：使用伙伴角色自己的大模型设置（baseURL、model、apiKey），每个伙伴角色可以使用不同配置
     - **数据库保留**：数据库表结构中保留这些字段，以备后续扩展

### 1.2 功能需求

#### 1.2.1 登录流程
- 用户通过输入 `apiKey` 登录
- 登录后加载该 `apiKey` 下的用户角色列表
- 如果已有用户角色，显示列表；如果没有，提示创建

#### 1.2.2 用户角色管理
- **创建/编辑用户角色**：
  - 大模型设置（API Base URL、模型名称、API Key）
  - 角色信息（头像、角色名称）
  - 显示设置（水平位置、垂直位置、缩放比例）
- **设置当前用户角色**：
  - 用户可以选择一个用户角色设为当前角色
  - 设置后，其他菜单（伙伴角色管理、对话历史等）变为可用
  - 只显示该 `apiKey` 下的伙伴角色列表

#### 1.2.3 伙伴角色管理
- 功能保持不变（原"角色管理"功能）
- **重要：只加载用户 apiKey 对应的角色**
- 创建/编辑伙伴角色时，使用当前登录的 `apiKey` 作为 `userId` 的一部分
- 大模型设置字段在 UI 中隐藏，但数据库保留

#### 1.2.4 显示逻辑
- **对话历史中的角色头像**：
  - 用户消息：显示当前用户角色的头像（如果设置了头像）
  - AI 消息：显示当前伙伴角色的头像（如果设置了头像）
  - **点击头像行为**（根据角色类型区分）：
    - **用户角色**：点击头像显示/隐藏（toggle）用户立绘
    - **伙伴角色 - 立绘类型**（type='illustration'）：点击头像显示/隐藏（toggle）伙伴立绘本体
    - **伙伴角色 - 数字人类型**（type='digital_human'）：点击头像显示/隐藏数字人容器（保持连接状态，仅通过CSS控制容器显示/隐藏；如果未连接，点击头像时提示在角色面板连接）
  - **其他规则**：数字人角色的其他应用规则与立绘相同（位置、缩放、头像显示等）
- **角色名称显示规则**：
  - **当前实现**：
    - 用户角色：名称为空时显示"我"（`currentUserRoleInfo.value?.name || '我'`）
    - 伙伴角色：名称为空时显示"AI"（`currentPartnerRoleInfo.value?.name || 'AI'`）
  - **设计规则**：如果角色名称为空，应使用 `user` 字段代替角色名称
  - **单向规则**：不能反过来，即不能使用角色名称代替 `user` 字段
  - **待实现**：将显示逻辑改为：名称为空时使用 `user` 字段代替（而不是使用默认值"我"或"AI"）

### 1.3 数据库设计

#### 1.3.1 用户角色表（user_roles）
```sql
CREATE TABLE IF NOT EXISTS user_roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  api_key TEXT NOT NULL,              -- 用户账号（登录的apiKey）
  name TEXT,                           -- 角色名称（可选）
  type TEXT NOT NULL DEFAULT 'illustration' CHECK(type IN ('digital_human', 'illustration')),  -- 角色类型
  avatar TEXT,                         -- 头像URL
  position_x REAL DEFAULT 50,          -- 水平位置 (0-100)
  position_y REAL DEFAULT 50,          -- 垂直位置 (0-100)
  scale REAL DEFAULT 1.0,              -- 缩放比例 (0.5-2.0)
  base_url TEXT,                       -- 大模型API Base URL（可选）
  model TEXT,                          -- 大模型名称（可选）
  avatar_app_id TEXT,                  -- 数字人 SDK App ID（可选，仅数字人类型）
  avatar_app_secret TEXT,              -- 数字人 SDK App Secret（可选，仅数字人类型）
  is_current INTEGER DEFAULT 0,       -- 是否为当前角色 (0/1)
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
)
```

**字段用途说明**：
- **`type`**：角色类型，`'digital_human'` 或 `'illustration'`，默认为 `'illustration'`
- **`avatar_app_id`**：数字人 SDK App ID，**每个数字人角色独立配置**。每个角色必须单独配置，不存在全局配置。
- **`avatar_app_secret`**：数字人 SDK App Secret，**每个数字人角色独立配置**。每个角色必须单独配置，不存在全局配置。

#### 1.3.2 伙伴角色表（roles）
```sql
CREATE TABLE IF NOT EXISTS roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  api_key TEXT NOT NULL,               -- 用户账号（登录的apiKey），用于用户隔离和过滤
  user TEXT NOT NULL,                   -- user字段的值（传给大模型的user参数，角色标识）
  user_id TEXT NOT NULL,                -- 用户ID（格式：{api_key}:{user}），用于兼容历史数据
  name TEXT,                            -- 角色名称（显示名称，可选）
  type TEXT DEFAULT 'illustration',    -- 角色类型：'digital_human' | 'illustration'
  description TEXT,                     -- 角色描述（可选）
  avatar TEXT,                         -- 角色头像URL（可选）
  position_x REAL DEFAULT 50,          -- 水平位置 (0-100)
  position_y REAL DEFAULT 50,          -- 垂直位置 (0-100)
  scale REAL DEFAULT 1.0,              -- 缩放比例 (0.5-2.0)
  base_url TEXT,                       -- 大模型API Base URL（保留字段，UI隐藏）
  model TEXT,                          -- 大模型名称（保留字段，UI隐藏）
  avatar_app_id TEXT,                  -- 数字人 SDK App ID（可选，仅数字人类型）
  avatar_app_secret TEXT,              -- 数字人 SDK App Secret（可选，仅数字人类型）
  created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
  updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
)
```

**字段用途说明**：
- **`api_key`**：用户账号标识，**用于用户隔离和过滤**。所有查询和操作都按此字段过滤，确保不同用户之间的角色数据完全隔离。
- **`user`**：传给大模型的 `user` 参数值，是角色的业务标识。用于标识不同的AI助手角色。
- **`user_id`**：格式为 `{api_key}:{user}`，**仅用于兼容历史数据**。查询和操作时不使用此字段，所有过滤都基于 `api_key` 字段。
- **`avatar_app_id`**：数字人 SDK App ID，**每个数字人角色独立配置**。每个角色必须单独配置，不存在全局配置。
- **`avatar_app_secret`**：数字人 SDK App Secret，**每个数字人角色独立配置**。每个角色必须单独配置，不存在全局配置。

## 二、已实现功能

### 2.1 后端实现

#### 2.1.1 数据库操作
- ✅ `user_roles` 表创建
- ✅ `roles` 表创建（包含保留字段：baseURL、model、apiKey）
- ✅ 用户角色 CRUD 操作函数
- ✅ 伙伴角色 CRUD 操作函数
- ✅ 数据隔离：基于 `apiKey` 进行过滤

#### 2.1.2 API 接口
- ✅ `GET /api/user-roles?apiKey={apiKey}` - 获取用户角色列表
- ✅ `POST /api/user-roles` - 创建用户角色
- ✅ `PUT /api/user-roles/:id?apiKey={apiKey}` - 更新用户角色
- ✅ `DELETE /api/user-roles/:id?apiKey={apiKey}` - 删除用户角色
- ✅ `PUT /api/user-roles/:id/set-current?apiKey={apiKey}` - 设置当前用户角色
- ✅ `GET /api/roles?apiKey={apiKey}` - 获取伙伴角色列表（按 apiKey 过滤）
- ✅ `POST /api/roles` - 创建伙伴角色（Body 中包含 apiKey）
- ✅ `PUT /api/roles/:id?apiKey={apiKey}` - 更新伙伴角色（按 apiKey 过滤）
- ✅ `DELETE /api/roles/:id?apiKey={apiKey}` - 删除伙伴角色（按 apiKey 过滤）

### 2.2 前端实现

#### 2.2.1 服务层
- ✅ `src/services/userRoleManagement.ts` - 用户角色管理服务
  - `getUserRoles(apiKey)` - 获取用户角色列表
  - `createUserRole(apiKey, role)` - 创建用户角色
  - `updateUserRole(id, apiKey, updates)` - 更新用户角色
  - `deleteUserRole(id, apiKey)` - 删除用户角色
  - `setCurrentUserRole(id, apiKey)` - 设置当前用户角色
- ✅ `src/services/roleManagement.ts` - 伙伴角色管理服务
  - `getRoles(apiKey)` - 获取伙伴角色列表（按 apiKey 过滤）
  - `createRole(apiKey, role)` - 创建伙伴角色（role 中包含 user 字段）
  - `updateRole(id, apiKey, updates)` - 更新伙伴角色（按 apiKey 过滤）
  - `deleteRole(id, apiKey)` - 删除伙伴角色（按 apiKey 过滤）

#### 2.2.2 UI 组件
- ✅ `ConfigPanel.vue` - 配置面板
  - ✅ APIKey 登录功能（独立菜单项）
  - ✅ 用户角色管理模态框
  - ✅ 用户角色创建/编辑表单
  - ✅ 用户角色列表显示
  - ✅ 设置当前用户角色功能
  - ✅ 伙伴角色管理模态框（只显示当前 apiKey 下的角色）
  - ✅ 伙伴角色创建/编辑表单（API Key 只读，模型名称必填可编辑，baseURL 后台自动使用）
  - ✅ 伙伴角色列表显示
  - ✅ 设置当前伙伴角色功能
  - ✅ 自动设置第一个角色为当前角色（用户角色和伙伴角色）

#### 2.2.3 显示逻辑
- ✅ `AvatarRender.vue` - 立绘渲染组件
  - ✅ 支持同时显示用户立绘和伙伴立绘
  - ✅ 根据角色配置设置位置和缩放
  - ✅ 背景图片铺满网页（cover 策略）
- ✅ 对话历史组件
  - ✅ 角色头像显示（仅当角色设置了头像时显示）
  - ✅ 头像点击行为：
    - ✅ 用户角色：点击头像 toggle 用户立绘显示/隐藏
    - ✅ 伙伴角色 - 立绘类型：点击头像 toggle 伙伴立绘显示/隐藏
    - ⚠️ 伙伴角色 - 数字人类型：点击头像显示/隐藏数字人容器（待实现：保持连接状态，仅控制容器显示/隐藏；未连接时提示在角色面板连接）
  - ⚠️ 角色名称显示：
    - ✅ 用户角色：有名称显示名称，无名称显示"我"
    - ✅ 伙伴角色：有名称显示名称，无名称显示"AI"
    - ⚠️ 名称为空时使用 `user` 字段代替（待实现，当前使用默认值）

### 2.3 核心功能实现状态

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 账号隔离 | ✅ 已实现 | 基于 apiKey 进行数据隔离 |
| 用户角色管理 | ✅ 已实现 | CRUD 功能完整 |
| 伙伴角色管理 | ✅ 已实现 | CRUD 功能完整，API Key 只读，模型名称必填，baseURL 后台自动使用 |
| 当前角色设置 | ✅ 已实现 | 用户角色和伙伴角色都支持 |
| 自动设置当前角色 | ✅ 已实现 | 创建第一个角色时自动设置为当前 |
| 角色数据隔离 | ✅ 已实现 | 只加载用户 apiKey 对应的角色 |
| 角色名称显示规则 | ⚠️ 部分实现 | 当前使用默认值（"我"/"AI"），待改为使用 user 字段代替 |
| 立绘显示 | ✅ 已实现 | 支持用户和伙伴立绘同时显示 |
| 头像显示 | ✅ 已实现 | 仅当角色设置了头像时显示 |
| 背景图片铺满 | ✅ 已实现 | 使用 cover 策略 |

## 三、关键设计决策

### 3.1 数据隔离
- **设计原则**：只加载用户 apiKey 对应的角色
- **实现方式**：查询角色时，使用当前登录的 `apiKey` 作为过滤条件，**按 `api_key` 字段过滤**（`WHERE api_key = ?`）
- **效果**：确保不同用户之间的角色数据完全隔离
- **字段说明**：
  - **`api_key`**：用于用户隔离和过滤，所有查询和操作都基于此字段
  - **`user`**：传给大模型的 user 参数值，是角色的业务标识
  - **`user_id`**：格式 `{api_key}:{user}`，仅用于兼容历史数据，查询时不使用

### 3.2 角色名称显示规则
- **设计规则**：如果角色名称为空，应使用 `user` 字段代替角色名称
- **当前实现**：名称为空时使用默认值（用户角色显示"我"，伙伴角色显示"AI"）
- **待实现**：将显示逻辑改为：名称为空时使用 `user` 字段代替（而不是使用默认值）
- **单向规则**：不能反过来，即不能使用角色名称代替 `user` 字段
- **原因**：`user` 字段是传给大模型的关键参数，必须保持唯一性和准确性

### 3.3 伙伴角色大模型设置
- **当前实现**：
  - **API Key**：只读显示，使用当前登录的 `globalApiKey`，不可编辑
  - **模型名称**：必填，可编辑。创建时默认值为当前用户角色的模型名称（`currentUserRole.value?.model`）
  - **baseURL**：不显示在界面，后台自动使用
- **实现逻辑**：
  - **创建角色时**：
    - `model` 默认值为 `currentUserRole.value?.model || ''`
    - `apiKey` 默认值为 `globalApiKey.value`
    - `baseURL` 默认使用当前用户角色的 `baseURL`（`currentUserRole.value?.baseURL`）
  - **更新角色时**：
    - `model` 使用表单中的值（必填，可编辑）
    - `apiKey` 使用 `globalApiKey.value`
    - `baseURL` 如果伙伴角色已有 `baseURL`，保留；否则使用用户角色的 `baseURL`
  - **验证**：`model` 字段为必填，保存时验证不能为空
- **调用大模型时的配置来源**：
  - 调用大模型时使用的是**伙伴角色的大模型设置**（baseURL、model、apiKey）
  - 当设置当前伙伴角色时（`handleSetCurrentRole`），会将伙伴角色的 `baseURL`、`model`、`apiKey` 设置到 `appState.llm`
  - 因此，每个伙伴角色可以使用不同的大模型配置
- **数据库保留**：数据库表结构中保留这些字段，以备后续扩展
- **扩展性**：保留字段的目的是为了将来可能为不同角色选用不同模型

### 3.4 自动设置当前角色
- **用户角色**：创建第一个用户角色时，自动设置为当前角色
- **伙伴角色**：创建第一个伙伴角色时，自动设置为当前角色
- **目的**：提升用户体验，减少手动操作

### 3.5 角色切换与历史记录
- **伙伴角色切换**：切换当前伙伴角色时，同时切换对应的历史记录
- **历史记录绑定**：历史记录与伙伴角色绑定，不是与用户角色绑定
- **实现**：切换角色时调用 `loadHistory()` 重新加载历史记录

## 四、待实现功能

- [ ] **实现角色名称显示规则**：名称为空时使用 `user` 字段代替（而不是使用默认值）
- [ ] **头像裁剪功能**：所有头像设置时都需要经过裁剪
  - 用户角色头像：上传后需要裁剪
  - 伙伴角色头像（立绘）：上传后需要裁剪
  - 数字人截图：截图后需要裁剪
- [ ] **多数字人同时显示**：界面上需要支持多数字人显示，比如：同时显示用户角色和伙伴角色
- [ ] **数字人拖拽摆放**：支持数字人的拖拽摆放功能
- [ ] **点击头像显示/隐藏优化**：点击头像显示/隐藏数字人容器（保持连接状态，仅通过CSS控制容器显示/隐藏；如果未连接，点击头像时提示在角色面板连接）
  - 实现方式：使用现有的裁剪器（Cropper.js），确保所有头像都经过统一的裁剪流程

## 五、已知问题和限制

### 5.1 当前限制
1. **apiKey 安全性**：
   - apiKey 存储在内存中，不持久化到 localStorage
   - 刷新页面后需要重新登录

2. **当前角色**：
   - 每个 apiKey 只能有一个当前用户角色
   - 设置新角色为当前时，自动取消其他角色的当前状态

3. **立绘显示**：
   - 用户立绘和伙伴立绘可以同时显示
   - 需要合理处理位置，避免重叠
   - 只有设置了头像的角色才能切换立绘显示/隐藏

4. **头像显示**：
   - 头像使用立绘原图，通过 CSS 缩小显示
   - 不存储缩略图，节省存储空间
   - 没有头像的角色不显示头像，也不显示切换按钮

### 5.2 注意事项
1. **user字段验证**：user字段不能为空，创建/编辑时需要验证（前端和后端都要验证）
2. **当前角色标识**：在角色列表中清晰标识当前使用的角色
3. **删除当前角色**：删除当前使用的角色时，需要清空相关状态
4. **多租户隔离**：使用 `apiKey` 进行数据隔离，确保不同用户/API Key的角色互不干扰
   - **实现方式**：所有查询和操作都按 `api_key` 字段过滤（`WHERE api_key = ?`）
   - **字段用途**：
     - `api_key`：用于用户隔离和过滤
     - `user`：传给大模型的 user 参数值
     - `user_id`：格式 `{api_key}:{user}`，仅用于兼容历史数据
5. **ID类型**：数据库主键为 `INTEGER`，前端 `Role.id` 和 `UserRole.id` 类型为 `number`
6. **数据同步**：角色列表需要从后端加载，创建/更新/删除后需要刷新列表
7. **权限验证**：后端需要验证 `apiKey`，确保用户只能操作自己的角色

## 六、开发进度总结

### 6.1 已完成
- ✅ 数据库设计和表结构创建
- ✅ 后端 API 接口实现
- ✅ 前端服务层实现
- ✅ UI 组件实现（用户角色和伙伴角色管理）
- ✅ 登录流程实现
- ✅ 数据隔离实现
- ⚠️ 角色名称显示规则（部分实现，待完善为使用 user 字段代替）
- ✅ 立绘显示功能实现
- ✅ 头像显示功能实现
- ✅ 背景图片铺满功能实现

### 6.2 待修复/完善
- ⚠️ **实现角色名称显示规则**
- ⚠️ **头像裁剪功能**
  - **需求**：所有头像设置时都需要经过裁剪
  - **范围**：
    - 用户角色头像上传
    - 伙伴角色头像上传（立绘）
    - 数字人截图
  - **当前状态**：部分头像上传已有裁剪功能，但数字人截图和部分场景未实现
  - **目标**：统一所有头像设置流程，确保都经过裁剪器处理
  - 位置：`src/components/ConfigPanel.vue` 第2251-2259行 `getRoleName()` 函数
  - 当前：名称为空时使用默认值（"我"/"AI"）
  - 目标：名称为空时使用 `user` 字段代替

### 6.3 待开发
- 角色导入/导出功能
- 角色预设模板
- 角色使用统计
- 性能优化（分页、缓存等）

## 七、代码实现现状（用于恢复参考）

### 7.1 头像点击行为实现

**位置**：`src/components/ConfigPanel.vue` 第2566-2582行

**当前实现**（待修改）：
```typescript
// Toggle 立绘显示/隐藏
function toggleIllustration(role: 'user' | 'assistant') {
  if (role === 'user') {
    showUserIllustration.value = !showUserIllustration.value
  } else {
    showPartnerIllustration.value = !showPartnerIllustration.value
  }
}

// 获取 toggle 提示文本
function getToggleIllustrationTitle(role: 'user' | 'assistant'): string {
  if (role === 'user') {
    return showUserIllustration.value ? '隐藏用户立绘' : '显示用户立绘'
  } else {
    return showPartnerIllustration.value ? '隐藏伙伴立绘' : '显示伙伴立绘'
  }
}
```

**待实现**：根据伙伴角色类型区分行为
- 立绘类型（type='illustration'）：toggle 立绘显示/隐藏（使用 `showPartnerIllustration`）
- 数字人类型（type='digital_human'）：toggle 数字人容器显示/隐藏（保持连接状态，仅通过CSS控制容器显示/隐藏；如果未连接，提示在角色面板连接）

**修改方案**：
```typescript
// Toggle 立绘显示/隐藏或数字人显示/隐藏
function toggleIllustration(role: 'user' | 'assistant') {
  if (role === 'user') {
    // 用户角色：始终是立绘
    showUserIllustration.value = !showUserIllustration.value
  } else {
    // 伙伴角色：根据角色类型判断
    const partnerRole = currentPartnerRoleInfo.value
    if (partnerRole?.type === 'digital_human') {
      // 数字人：显示/隐藏容器（保持连接状态，仅控制容器显示/隐藏）
      if (!appState.avatar.connected) {
        // 未连接：提示在角色面板连接
        showToastMessage('数字人未连接，请先在角色列表面板中连接', 'warning')
        return
      }
      // 已连接：toggle 容器显示/隐藏（通过CSS类控制）
      showPartnerDigitalHuman.value = !showPartnerDigitalHuman.value
      } else {
        handleConnect()
      }
    } else {
      // 立绘：显示/隐藏
      showPartnerIllustration.value = !showPartnerIllustration.value
    }
  }
}

// 获取 toggle 提示文本
function getToggleIllustrationTitle(role: 'user' | 'assistant'): string {
  if (role === 'user') {
    return showUserIllustration.value ? '隐藏用户立绘' : '显示用户立绘'
  } else {
    // 伙伴角色：根据角色类型判断
    const partnerRole = currentPartnerRoleInfo.value
    if (partnerRole?.type === 'digital_human') {
      return appState.avatar.connected ? '隐藏数字人' : '显示数字人'
    } else {
      return showPartnerIllustration.value ? '隐藏伙伴立绘' : '显示伙伴立绘'
    }
  }
}
```

### 7.2 编辑面板数字人容器

**设计原则**：遵循"数字人的业务逻辑跟立绘一样，只是把立绘换成了数字人的细节差别"原则。容器管理方式与立绘的头像预览一致。

**位置**：`src/components/ConfigPanel.vue` 第466-471行

**HTML结构**：
```vue
<div class="digital-human-preview-container">
  <div :id="editContainerId" class="digital-human-preview"></div>
  <div v-if="!appState.avatar.connected" class="digital-human-placeholder">
    <span>数字人容器</span>
  </div>
</div>
```

**容器ID生成**（第1078行）：
```typescript
const editContainerId = ref(generateContainerId())
```

**CSS样式**（第4440-4454行）：
```css
.digital-human-preview-container {
  position: relative;
  width: 120px;
  height: 120px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.digital-human-preview {
  width: 100%;
  height: 100%;
  position: relative;
}
```

### 7.3 编辑面板数字人连接

**位置**：`src/components/ConfigPanel.vue` 第1497-1561行

**函数**：`handleConnect()`

**关键逻辑**：
```typescript
// 检查容器是否存在（优先使用编辑界面的容器，如果正在编辑角色）
let containerId: string
let container: HTMLElement | null

if (showRoleEditForm.value && roleForm.value.type === 'digital_human') {
  // 使用编辑界面的容器
  containerId = editContainerId.value
  container = document.getElementById(containerId)
} else {
  // 使用主界面的容器
  containerId = avatarService.getContainerId()
  container = document.getElementById(containerId)
}

// 如果使用编辑界面的容器，传递容器ID给 connect 方法
if (showRoleEditForm.value && roleForm.value.type === 'digital_human') {
  // 直接调用 avatarService.connect，传入编辑界面的容器ID
  // 使用角色自己的 appId 和 appSecret（每个角色必须单独配置，不存在全局配置）
  const avatar = await avatarService.connect(
    {
      appId: roleForm.value.avatarAppId,
      appSecret: roleForm.value.avatarAppSecret
    },
    {
      onSubtitleOn: (text: string) => {
        appState.ui.subTitleText = text
      },
      onSubtitleOff: () => {
        appState.ui.subTitleText = ''
      },
      onStateChange: (state: string) => {
        avatarState.value = state
      }
    },
    editContainerId.value  // 传入编辑界面的容器ID
  )
  appState.avatar.instance = avatar
  appState.avatar.connected = true
} else {
  await appStore.connectAvatar()
}
```

### 7.4 编辑面板数字人断开

**位置**：`src/components/ConfigPanel.vue` 第1563-1571行

**函数**：`handleDisconnect()`

**关键代码**：
```typescript
function handleDisconnect() {
  try {
    appStore.disconnectAvatar()
    showToastMessage('已断开连接', 'success')
  } catch (error) {
    console.error('断开连接失败:', error)
    showToastMessage('断开连接失败', 'error')
  }
}
```

**底层实现**（`src/stores/app.ts`）：
```typescript
disconnectAvatar(): void {
  if (appState.avatar.instance) {
    avatarService.disconnect(appState.avatar.instance)
    appState.avatar.instance = null
    appState.avatar.connected = false
    avatarState.value = ''
  }
}
```

**avatarService.disconnect**（`src/services/avatar.ts`）：
```typescript
disconnect(avatar: any): void {
  if (!avatar) return
  
  try {
    avatar.stop()
    avatar.destroy()
  } catch (error) {
    console.error('断开连接时出错:', error)
  }
}
```

### 7.5 编辑面板数字人截图

**位置**：`src/components/ConfigPanel.vue` 第1573-1739行

**函数**：`handleCaptureDigitalHuman()`

**关键逻辑**：
```typescript
// 获取容器ID（优先使用编辑界面的容器）
let containerId: string
if (showRoleEditForm.value && roleForm.value.type === 'digital_human') {
  containerId = editContainerId.value
} else {
  containerId = avatarService.getContainerId()
}

const container = document.getElementById(containerId)

// 在容器内查找canvas元素
const canvas = container.querySelector('canvas') as HTMLCanvasElement

// 检查canvas尺寸
const width = canvas.width
const height = canvas.height

// 使用WebGL readPixels读取像素数据
const gl = (canvas.getContext('webgl', { preserveDrawingBuffer: true }) || 
            canvas.getContext('webgl2', { preserveDrawingBuffer: true }) || 
            canvas.getContext('experimental-webgl', { preserveDrawingBuffer: true })) as WebGLRenderingContext | null

if (gl) {
  // 等待渲染完成
  await new Promise(resolve => requestAnimationFrame(resolve))
  await new Promise(resolve => requestAnimationFrame(resolve))
  
  // 保存当前状态
  const currentFramebuffer = gl.getParameter(gl.FRAMEBUFFER_BINDING)
  const currentViewport = gl.getParameter(gl.VIEWPORT)
  
  // 绑定到默认framebuffer
  gl.bindFramebuffer(gl.FRAMEBUFFER, null)
  gl.viewport(0, 0, width, height)
  
  // 读取像素数据
  const pixels = new Uint8Array(width * height * 4)
  gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels)
  
  // 恢复状态
  gl.bindFramebuffer(gl.FRAMEBUFFER, currentFramebuffer)
  if (currentViewport && currentViewport.length === 4) {
    gl.viewport(currentViewport[0], currentViewport[1], currentViewport[2], currentViewport[3])
  }
  
  // 检查内容（检查alpha通道）
  let hasContent = false
  for (let i = 3; i < pixels.length; i += 4) {
    if (pixels[i] > 0) {
      hasContent = true
      break
    }
  }
  
  // 转换为ImageData（翻转Y轴）
  const tempCanvas = document.createElement('canvas')
  tempCanvas.width = width
  tempCanvas.height = height
  const tempCtx = tempCanvas.getContext('2d')
  const imageData = tempCtx.createImageData(width, height)
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const srcIndex = (y * width + x) * 4
      const dstIndex = ((height - 1 - y) * width + x) * 4
      imageData.data[dstIndex] = pixels[srcIndex]
      imageData.data[dstIndex + 1] = pixels[srcIndex + 1]
      imageData.data[dstIndex + 2] = pixels[srcIndex + 2]
      imageData.data[dstIndex + 3] = pixels[srcIndex + 3]
    }
  }
  tempCtx.putImageData(imageData, 0, 0)
  
  // 转换为blob并上传
  tempCanvas.toBlob(async (blob) => {
    const formData = new FormData()
    formData.append('avatar', blob, 'digital-human-avatar.png')
    const response = await fetch('http://localhost:3001/api/upload/avatar', {
      method: 'POST',
      body: formData
    })
    const data = await response.json()
    const avatarUrl = data.url || `/uploads/avatars/${data.filename}`
    roleForm.value.avatar = avatarUrl
  }, 'image/png', 1.0)
}
```

**截图大小**：动态，取决于canvas的实际尺寸（通常为容器CSS尺寸 120px × devicePixelRatio）

### 7.6 AvatarRender.vue 数字人显示逻辑

**位置**：`src/components/AvatarRender.vue` 第8-24行

**显示条件**：
```vue
<!-- 数字人 SDK 渲染容器（伙伴角色） -->
<div 
  v-if="currentPartnerRoleType === 'digital_human'"
  :id="containerId" 
  class="sdk-container" 
  :class="{ visible: appState.avatar.connected }"
  :style="partnerAvatarPositionStyle"
/>

<!-- 用户数字人 SDK 渲染容器 -->
<div 
  v-if="currentUserRoleType === 'digital_human'"
  :id="userContainerId" 
  class="sdk-container user-digital-human" 
  :class="{ visible: appState.avatar.connected }"
  :style="userAvatarPositionStyle"
/>
```

**关键点**：
- 显示条件：
  - 伙伴角色：`currentPartnerRoleType === 'digital_human'`
  - 用户角色：`currentUserRoleType === 'digital_human'`
- 可见性控制：
  - **当前实现**：`appState.avatar.connected`（通过CSS类 `visible` 控制，但这是连接状态，不是显示/隐藏状态）
  - **待实现**：需要独立的显示/隐藏状态（例如：`showUserDigitalHuman`、`showPartnerDigitalHuman`），与连接状态分离
- 位置样式：
  - 伙伴角色：`partnerAvatarPositionStyle`（根据角色配置的 positionX、positionY、scale）
  - 用户角色：`userAvatarPositionStyle`（根据角色配置的 positionX、positionY、scale）
- 容器ID：
  - 伙伴角色：`containerId`（通过 `avatarService.getContainerId()` 获取）
  - 用户角色：`userContainerId`（固定为 `'user-digital-human-container'`）

**角色类型判断**（第92-104行）：
```typescript
const currentPartnerRoleType = computed(() => {
  return currentPartnerRole.value?.type || 'digital_human'
})

const currentUserRoleType = computed(() => {
  return currentUserRole.value?.type || 'illustration'
})

const userContainerId = computed(() => {
  return `user-digital-human-container`
})
```

**当前限制**：
- ⚠️ 当前实现：`appState.avatar.connected` 是全局状态，无法同时管理多个数字人的连接状态
- ⚠️ 当前实现：只能同时显示一个数字人（用户角色或伙伴角色），不能同时显示两个
- ⚠️ 当前实现：容器的可见性控制与连接状态绑定（`appState.avatar.connected`），无法独立控制显示/隐藏
- **待实现**：
  - 支持多数字人同时显示，需要为每个数字人维护独立的连接状态和显示/隐藏状态
  - 分离连接状态和显示/隐藏状态：连接后保持连接，仅通过独立的显示/隐藏状态控制容器可见性

### 7.1.4 数字人独立 appId 和 appSecret

**实现状态**：✅ 已实现并测试通过

**测试结果**：
- ✅ 可以为不同角色单独设置 app id 和 secret
- ❌ **问题**：只能显示一个数字人，连接任何角色数字人时，其他数字人一起连接（连接状态被覆盖）

**数据库字段**：
- `roles` 表：`avatar_app_id`、`avatar_app_secret`
- `user_roles` 表：`avatar_app_id`、`avatar_app_secret`

**类型定义**：
- `Role` 接口：`avatarAppId?: string`、`avatarAppSecret?: string`
- `UserRole` 接口：`avatarAppId?: string`、`avatarAppSecret?: string`

**前端实现**：
- 角色表单绑定到 `roleForm.avatarAppId` 和 `roleForm.avatarAppSecret`
- 用户角色表单绑定到 `userRoleForm.avatarAppId` 和 `userRoleForm.avatarAppSecret`
- 连接逻辑使用角色自己的 `avatarAppId` 和 `avatarAppSecret`（每个角色必须单独配置，不存在全局配置）

**后端实现**：
- `createRole`、`updateRole`、`createUserRole`、`updateUserRole` 函数支持保存和读取 `avatar_app_id` 和 `avatar_app_secret`
- API 端点支持接收和返回这些字段

**关键点**：
- ✅ 每个数字人角色都有独立的 appId 和 appSecret
- ✅ 修改一个角色的配置不会影响其他角色
- ✅ 每个角色必须单独配置 appId 和 appSecret，不存在全局配置（除了账号 apikey 有全局配置外，所有角色配置都是独立的）
- ❌ **问题**：连接状态和 SDK 实例是全局的，无法同时管理多个数字人

**已知问题**：
- 连接任何角色数字人时，其他数字人一起连接（连接状态被覆盖）
- 原因：`appState.avatar.connected` 和 `appState.avatar.instance` 是全局状态，只能保存一个数字人的连接状态和实例
- 影响：无法同时显示多个数字人（用户角色和伙伴角色）

## 八、待实现功能详细说明

**设计原则**：遵循"数字人的业务逻辑跟立绘一样，只是把立绘换成了数字人的细节差别"原则。所有立绘的功能（位置、缩放、显示/隐藏、拖拽等）都应同样适用于数字人，仅在技术实现细节上有差异（如SDK连接、截图等）。

### 8.1 多数字人同时显示

**需求**：界面上需要支持多数字人显示，比如：同时显示用户角色和伙伴角色。

**测试结果**：
- ❌ **问题确认**：只能显示一个数字人，连接任何角色数字人时，其他数字人一起连接（连接状态被覆盖）

**当前限制**：
- `appState.avatar.connected` 是全局状态，只能表示一个数字人的连接状态
- `appState.avatar.instance` 只能保存一个 SDK 实例
- 当前实现只能同时显示一个数字人（用户角色或伙伴角色）
- 连接新的数字人时，旧的数字人实例可能没有被正确断开，或者连接状态被覆盖

**实现方案**（待设计）：
- 为每个数字人角色维护独立的连接状态和 SDK 实例
- 修改 `AppState` 结构，支持多个数字人实例（例如：`appState.avatar.instances: Map<roleId, instance>`）
- 更新连接/断开逻辑，支持同时管理多个数字人
- 更新 `AvatarRender.vue`，支持同时渲染多个数字人容器
- 每个数字人容器使用独立的连接状态控制显示/隐藏

### 8.2 数字人拖拽摆放

**需求**：支持数字人的拖拽摆放功能。

**当前状态**：
- ✅ 立绘已支持拖拽摆放（用户立绘和伙伴立绘）
- ❌ 数字人尚未支持拖拽摆放

**实现方案**（待设计）：
- 参考立绘的拖拽实现（`startDragUser`、`startDragPartner`）
- 为数字人容器添加拖拽事件处理
- 更新角色位置配置（positionX、positionY）
- 保存位置到数据库

### 8.3 点击头像显示/隐藏优化

**需求**：点击头像显示/隐藏数字人容器（保持连接状态，仅通过CSS控制容器显示/隐藏；如果未连接，点击头像时提示在角色面板连接）。

**设计原则**：
- **保持连接状态**：连接数字人非常耗时，一旦连接需要保持连接状态，不轻易断开
- **仅控制显示/隐藏**：点击头像只是显示/隐藏容器（通过CSS类控制），不进行连接/断开操作
- **未连接时提示**：如果数字人未连接，点击头像时只提示在角色面板连接，不自动连接

**实现方案**（待实现）：
- 为每个数字人维护独立的显示/隐藏状态（例如：`showUserDigitalHuman`、`showPartnerDigitalHuman`）
- 点击头像时：
  - 如果已连接：toggle 容器的显示/隐藏状态（通过CSS类控制）
  - 如果未连接：提示用户："数字人未连接，请先在角色列表面板中连接"
- 连接操作仅在角色列表面板中进行，不在点击头像时自动连接

## 九、相关文档
- `docs/USER_ROLE_MANAGEMENT.md` - 用户角色管理功能设计文档
- `docs/ROLE_MANAGEMENT.md` - 角色管理功能设计方案

