# 后端服务对接指南

## 当前状态

当前使用**内存存储模式**，对话历史保存在 `appState.chatHistory` 中，不持久化。

## 切换到后端模式

### 1. 修改配置

在 `src/services/chatHistory.ts` 中，将 `USE_BACKEND` 改为 `true`：

```typescript
const USE_BACKEND = true  // 改为 true
```

### 2. 启动后端服务

```bash
npm install
npm run server
```

后端服务运行在 `http://localhost:3001`

### 3. 启用历史加载

在 `src/components/ConfigPanel.vue` 的 `onMounted` 中，取消注释：

```typescript
onMounted(() => {
  handleLoadConfig(false)
  // 取消下面的注释
  loadHistory()
  // ...
})
```

或者使用配置判断：

```typescript
import { USE_BACKEND } from '../services/chatHistory'

onMounted(() => {
  handleLoadConfig(false)
  if (USE_BACKEND) {
    loadHistory()
  }
  // ...
})
```

## 接口说明

所有接口已统一，无需修改业务代码：

- `saveChatMessage()` - 保存消息
- `getChatHistory()` - 获取历史
- `clearChatHistory()` - 清空历史

## 数据格式

对话消息格式统一：

```typescript
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
}
```

## 多租户支持

当前使用 `default_user`，后续可扩展账号体系，只需修改 `CURRENT_USER` 常量即可。

